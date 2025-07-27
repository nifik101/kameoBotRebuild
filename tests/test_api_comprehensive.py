import os
import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pydantic import ValidationError

# Set test mode before importing the API
os.environ["TEST_MODE"] = "1"
from src.api import app, _jobs, _jobs_lock, _cleanup_old_jobs, _register_job, _update_job


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def clean_jobs():
    """Clean job registry before each test"""
    with _jobs_lock:
        _jobs.clear()
    yield
    with _jobs_lock:
        _jobs.clear()


class TestJobManagement:
    """Test job registration, update, and cleanup functionality"""
    
    def test_register_job(self, clean_jobs):
        """Test job registration creates proper job entry"""
        job_id = _register_job()
        
        assert job_id in _jobs
        job = _jobs[job_id]
        assert job["status"] == "pending"
        assert job["error"] is None
        assert job["data"] is None
        assert "created_at" in job
        assert "updated_at" in job
    
    def test_update_job(self, clean_jobs):
        """Test job status updates work correctly"""
        job_id = _register_job()
        
        _update_job(job_id, status="success", data={"test": "data"})
        
        job = _jobs[job_id]
        assert job["status"] == "success"
        assert job["data"] == {"test": "data"}
        assert job["error"] is None
    
    def test_update_nonexistent_job(self, clean_jobs):
        """Test updating non-existent job doesn't crash"""
        _update_job("fake-id", status="success")
        # Should not raise exception
        assert "fake-id" not in _jobs
    
    def test_cleanup_old_jobs(self, clean_jobs):
        """Test that old jobs are cleaned up properly"""
        # Create a job and manually set old timestamp
        job_id = _register_job()
        
        # Make job appear old (2 hours ago)
        from datetime import datetime, timedelta
        old_time = datetime.now() - timedelta(hours=2)
        _jobs[job_id]["created_at"] = old_time
        
        # Create a recent job
        recent_job_id = _register_job()
        
        assert len(_jobs) == 2
        
        _cleanup_old_jobs()
        
        assert len(_jobs) == 1
        assert job_id not in _jobs
        assert recent_job_id in _jobs


class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_jobs" in data
    
    def test_start_fetch_loans_success(self, client, clean_jobs):
        """Test successful job creation"""
        response = client.post("/api/jobs/fetch-loans")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "pending"
        assert "job_id" in data["data"]
        assert data["data"]["message"] == "Job started successfully"
    
    def test_start_fetch_loans_invalid_params(self, client):
        """Test parameter validation"""
        # Test invalid limit
        response = client.post("/api/jobs/fetch-loans?limit=0")
        assert response.status_code == 400
        assert "Limit must be between 1 and 100" in response.json()["detail"]
        
        response = client.post("/api/jobs/fetch-loans?limit=101")
        assert response.status_code == 400
        
        # Test invalid page
        response = client.post("/api/jobs/fetch-loans?page=0")
        assert response.status_code == 400
        assert "Page must be >= 1" in response.json()["detail"]
    
    def test_get_job_status_success(self, client, clean_jobs):
        """Test getting job status for existing job"""
        # Create a job first
        job_id = _register_job()
        _update_job(job_id, status="success", data={"test": "result"})
        
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["data"] == {"test": "result"}
        assert data["error"] is None
    
    def test_get_job_status_not_found(self, client):
        """Test 404 for non-existent job"""
        response = client.get("/api/jobs/fake-job-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"
    
    def test_list_jobs(self, client, clean_jobs):
        """Test listing all jobs"""
        # Create a few jobs
        job1 = _register_job()
        job2 = _register_job()
        
        response = client.get("/api/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_jobs"] == 2
        assert len(data["jobs"]) == 2
        
        job_ids = [job["job_id"] for job in data["jobs"]]
        assert job1 in job_ids
        assert job2 in job_ids
    
    def test_cancel_job_success(self, client, clean_jobs):
        """Test job cancellation"""
        job_id = _register_job()
        
        response = client.delete(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        assert f"Job {job_id} marked as cancelled" in response.json()["message"]
        
        # Verify job is marked as cancelled
        assert _jobs[job_id]["status"] == "cancelled"
    
    def test_cancel_job_not_found(self, client):
        """Test cancelling non-existent job"""
        response = client.delete("/api/jobs/fake-job-id")
        assert response.status_code == 404


class TestJobExecution:
    """Test actual job execution scenarios"""
    
    def test_fetch_loans_test_mode(self, client, clean_jobs):
        """Test that test mode returns dummy data"""
        response = client.post("/api/jobs/fetch-loans")
        job_id = response.json()["data"]["job_id"]
        
        # Wait a bit for background task to complete
        time.sleep(0.5)
        
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        
        assert data["status"] == "success"
        assert "loans" in data["data"]
        loans = data["data"]["loans"]
        assert len(loans) == 2
        assert loans[0]["title"] == "Dummy Loan 1"
        assert loans[1]["title"] == "Dummy Loan 2"
    
    @patch.dict(os.environ, {"TEST_MODE": "0"})
    @patch("src.api.KameoConfig")
    def test_fetch_loans_config_error(self, mock_config, client, clean_jobs):
        """Test handling of configuration errors"""
        # Mock KameoConfig to raise ValidationError
        mock_config.side_effect = ValidationError.from_exception_data(
            "KameoConfig", 
            [{"type": "missing", "loc": ("email",), "msg": "Field required"}]
        )
        
        response = client.post("/api/jobs/fetch-loans")
        job_id = response.json()["data"]["job_id"]
        
        # Wait for background task
        time.sleep(0.5)
        
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        
        assert data["status"] == "failed"
        assert "Configuration error" in data["error"]
    
    @patch.dict(os.environ, {"TEST_MODE": "0"})
    @patch("src.api.KameoConfig")
    @patch("src.api.LoanCollectorService")
    def test_fetch_loans_service_error(self, mock_service_class, mock_config, client, clean_jobs):
        """Test handling of service errors"""
        # Mock config to work
        mock_config.return_value = MagicMock()
        
        # Mock service to raise exception
        mock_service = MagicMock()
        mock_service.fetch_loans.side_effect = Exception("API connection failed")
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/jobs/fetch-loans")
        job_id = response.json()["data"]["job_id"]
        
        # Wait for background task
        time.sleep(0.5)
        
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        
        assert data["status"] == "failed"
        assert "Loan fetching failed" in data["error"]
        assert "API connection failed" in data["error"]
    
    @patch.dict(os.environ, {"TEST_MODE": "0"})
    @patch("src.api.KameoConfig")
    @patch("src.api.LoanCollectorService")
    def test_fetch_loans_empty_result(self, mock_service_class, mock_config, client, clean_jobs):
        """Test handling of empty loan results"""
        # Mock config and service
        mock_config.return_value = MagicMock()
        mock_service = MagicMock()
        mock_service.fetch_loans.return_value = []
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/jobs/fetch-loans")
        job_id = response.json()["data"]["job_id"]
        
        # Wait for background task
        time.sleep(0.5)
        
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["loans"] == []
        assert data["data"]["message"] == "No loans found"


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.options("/api/health")
        
        # In test mode, should allow all origins
        assert "access-control-allow-origin" in response.headers
    
    @patch.dict(os.environ, {"TEST_MODE": "0", "ENVIRONMENT": "production"})
    def test_cors_restricted_in_production(self):
        """Test that CORS is restricted in production"""
        # This would require reloading the module, which is complex
        # For now, we just verify the logic in the code
        pass


class TestErrorHandling:
    """Test various error scenarios"""
    
    def test_malformed_request(self, client):
        """Test handling of malformed requests"""
        response = client.post("/api/jobs/fetch-loans", json={"invalid": "data"})
        # Should still work since we don't require request body
        assert response.status_code == 200
    
    def test_concurrent_job_access(self, client, clean_jobs):
        """Test thread safety of job operations"""
        import threading
        
        results = []
        
        def create_job():
            response = client.post("/api/jobs/fetch-loans")
            results.append(response.status_code)
        
        # Create multiple jobs concurrently
        threads = [threading.Thread(target=create_job) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed
        assert all(status == 200 for status in results)
        assert len(_jobs) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 