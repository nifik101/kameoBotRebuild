"""
Job service for managing background jobs and their lifecycle.
Separates business logic from API layer for better architecture.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


from src.config import KameoConfig
from src.services.loan_collector import LoanCollectorService

logger = logging.getLogger(__name__)


class JobStatus:
    """Job status constants"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobService:
    """Service for managing background jobs"""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._jobs_lock = threading.Lock()
        self._cleanup_interval_hours = 1
        self._scheduler = BackgroundScheduler(daemon=True)
    
    def start_scheduler(self):
        """Start the background cleanup scheduler"""
        if not self._scheduler.running:
            self._scheduler.add_job(
                self.cleanup_old_jobs,
                trigger=IntervalTrigger(hours=self._cleanup_interval_hours),
                id="job_cleanup_task",
                name="Periodic Job Cleanup",
                replace_existing=True,
            )
            self._scheduler.start()
            logger.info("Started periodic job cleanup scheduler.")

    def stop_scheduler(self):
        """Stop the background cleanup scheduler"""
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Stopped periodic job cleanup scheduler.")

    def create_job(self) -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid4())
        with self._jobs_lock:
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "error": None,
                "data": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        logger.info(f"Created job {job_id}")
        return job_id
    
    def update_job(self, job_id: str, *, status: str, error: Optional[str] = None, data: Any = None) -> bool:
        """Update job status and return success"""
        with self._jobs_lock:
            if job_id not in self._jobs:
                logger.warning(f"Attempted to update non-existent job {job_id}")
                return False
            
            self._jobs[job_id].update({
                "status": status,
                "error": error,
                "data": data,
                "updated_at": datetime.now()
            })
        
        logger.info(f"Updated job {job_id} to status {status}")
        return True
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if job:
                # Return copy without internal timestamps for API
                return {
                    "status": job["status"],
                    "error": job["error"],
                    "data": job["data"]
                }
        return None
    
    def list_jobs(self) -> Dict[str, Any]:
        """List all jobs with summary"""
        with self._jobs_lock:
            return {
                "total_jobs": len(self._jobs),
                "jobs": [
                    {
                        "job_id": job_id,
                        "status": job["status"],
                        "created_at": job["created_at"].isoformat(),
                        "updated_at": job["updated_at"].isoformat()
                    }
                    for job_id, job in self._jobs.items()
                ]
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job by ID"""
        return self.update_job(job_id, status=JobStatus.CANCELLED)
    
    def cleanup_old_jobs(self) -> int:
        """Remove jobs older than cleanup interval"""
        cutoff = datetime.now() - timedelta(hours=self._cleanup_interval_hours)
        
        with self._jobs_lock:
            to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.get('created_at', datetime.now()) < cutoff
            ]
            
            for job_id in to_remove:
                del self._jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
        
        return len(to_remove)
    
    def get_active_job_count(self) -> int:
        """Get count of active jobs"""
        with self._jobs_lock:
            return len(self._jobs)


class LoanFetchJobService:
    """Service for loan fetching jobs"""
    
    def __init__(self, job_service: JobService):
        self.job_service = job_service
    
    def start_fetch_loans_job(self, limit: int = 12, page: int = 1, test_mode: bool = False) -> str:
        """Start a loan fetching job and return job ID"""
        job_id = self.job_service.create_job()
        
        # Start background task
        import threading
        thread = threading.Thread(
            target=self._execute_fetch_loans,
            args=(job_id, limit, page, test_mode),
            daemon=True
        )
        thread.start()
        
        return job_id
    
    def _execute_fetch_loans(self, job_id: str, limit: int, page: int, test_mode: bool):
        """Execute loan fetching in background"""
        try:
            if test_mode:
                # Return dummy data for testing
                dummy_loans = [
                    {"id": 1, "title": "Dummy Loan 1", "amount": 100000, "interest_rate": 7.5},
                    {"id": 2, "title": "Dummy Loan 2", "amount": 250000, "interest_rate": 8.2}
                ]
                self.job_service.update_job(
                    job_id, 
                    status=JobStatus.SUCCESS, 
                    data={"loans": dummy_loans}
                )
                return
            
            # Load configuration
            try:
                config = KameoConfig()
            except Exception as e:
                error_msg = f"Configuration error: {str(e)}"
                logger.error(error_msg)
                self.job_service.update_job(job_id, status=JobStatus.FAILED, error=error_msg)
                return
            
            # Execute loan fetching
            try:
                service = LoanCollectorService(config)
                loans = service.fetch_loans(limit=limit, page=page)
                
                if not loans:
                    self.job_service.update_job(
                        job_id,
                        status=JobStatus.SUCCESS,
                        data={"loans": [], "message": "No loans found"}
                    )
                else:
                    self.job_service.update_job(
                        job_id,
                        status=JobStatus.SUCCESS,
                        data={"loans": loans}
                    )
                    
            except Exception as e:
                error_msg = f"Loan fetching failed: {str(e)}"
                logger.exception("Loan fetching job failed")
                self.job_service.update_job(job_id, status=JobStatus.FAILED, error=error_msg)
                
        except Exception as e:
            # Catch-all for unexpected errors
            error_msg = f"Unexpected job error: {str(e)}"
            logger.exception("Unexpected error in loan fetch job")
            self.job_service.update_job(job_id, status=JobStatus.FAILED, error=error_msg)


# Global service instances
_job_service = JobService()
_loan_fetch_service = LoanFetchJobService(_job_service)


def get_job_service() -> JobService:
    """Get the global job service instance"""
    return _job_service


def get_loan_fetch_service() -> LoanFetchJobService:
    """Get the global loan fetch service instance"""
    return _loan_fetch_service 