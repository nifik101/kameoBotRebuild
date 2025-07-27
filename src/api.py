"""
FastAPI application for KameoBot.

This module contains the FastAPI application for KameoBot, including endpoints for
loans, bidding, configuration, and system status.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.services.job_service import get_job_service, get_loan_fetch_service
from src.websocket_handler import get_websocket_manager

logger = logging.getLogger(__name__)

app = FastAPI(title="KameoBot Async API", version="1.0.0")


class StandardResponse(BaseModel):
    status: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class BiddingRequest(BaseModel):
    loan_id: int
    amount: int
    payment_option: str = "ip"


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


# Secure CORS configuration
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # Common React dev port
    "http://localhost:5173",  # Vite default port
]

# Only allow all origins in development/test mode
if os.getenv("ENVIRONMENT") == "development" or os.getenv("TEST_MODE") == "1":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Serve docs directory for demo HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
if os.path.isdir(DOCS_DIR):
    app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")


@app.on_event("startup")
async def startup_event():
    """Cleanup old jobs on startup and start scheduler"""
    job_service = get_job_service()
    job_service.cleanup_old_jobs()
    job_service.start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler on shutdown"""
    job_service = get_job_service()
    job_service.stop_scheduler()


@app.post("/api/jobs/fetch-loans", response_model=StandardResponse)
async def start_fetch_loans(limit: int = 12, page: int = 1):
    """Start an asynchronous job that fetches loans. Returns a job ID."""
    # Validate parameters
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    
    # Start loan fetch job
    loan_fetch_service = get_loan_fetch_service()
    test_mode = os.getenv("TEST_MODE") == "1"
    job_id = loan_fetch_service.start_fetch_loans_job(limit=limit, page=page, test_mode=test_mode)
    
    return StandardResponse(
        status="pending", 
        data={"job_id": job_id, "message": "Job started successfully"}
    )


@app.get("/api/jobs/{job_id}", response_model=StandardResponse)
async def get_job_status(job_id: str):
    """Poll the status of a previously started job."""
    job_service = get_job_service()
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StandardResponse(**job)


@app.get("/api/jobs", response_model=Dict[str, Any])
async def list_jobs():
    """List all active jobs (for debugging)"""
    job_service = get_job_service()
    return job_service.list_jobs()


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a specific job"""
    job_service = get_job_service()
    success = job_service.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": f"Job {job_id} marked as cancelled"}


# Loan Operations Endpoints
@app.post("/api/loans/fetch", response_model=StandardResponse)
async def fetch_loans_direct(max_pages: int = 10):
    """Fetch loans directly (synchronous operation)."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        result = service.fetch_and_save_loans(max_pages)
        return StandardResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"Error fetching loans: {e}")
        return StandardResponse(status="error", error=str(e))


@app.post("/api/loans/analyze", response_model=StandardResponse)
async def analyze_loans():
    """Analyze all available loan fields."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        result = service.analyze_loan_fields()
        return StandardResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"Error analyzing loans: {e}")
        return StandardResponse(status="error", error=str(e))


@app.get("/api/loans/stats", response_model=StandardResponse)
async def get_loan_statistics():
    """Get database loan statistics."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        stats = service.get_loan_statistics()
        return StandardResponse(status="success", data=stats)
    except Exception as e:
        logger.error(f"Error getting loan statistics: {e}")
        return StandardResponse(status="error", error=str(e))


@app.get("/api/loans", response_model=StandardResponse)
async def get_loans(page: int = 1, limit: int = 50):
    """Get loans from database with pagination."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        result = service.get_loans_from_database(page=page, limit=limit)
        return StandardResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"Error getting loans: {e}")
        return StandardResponse(status="error", error=str(e))


# Bidding Operations Endpoints
@app.get("/api/bidding/loans", response_model=StandardResponse)
async def list_available_loans(max_pages: int = 3):
    """List available loans for bidding."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        loans = service.list_available_loans(max_pages)
        return StandardResponse(status="success", data={"loans": loans})
    except Exception as e:
        logger.error(f"Error listing available loans: {e}")
        return StandardResponse(status="error", error=str(e))


@app.get("/api/bidding/analyze/{loan_id}", response_model=StandardResponse)
async def analyze_loan_for_bidding(loan_id: int):
    """Analyze a specific loan for bidding potential."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        analysis = service.analyze_loan_for_bidding(loan_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Could not analyze loan")
        
        return StandardResponse(status="success", data=analysis)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing loan {loan_id}: {e}")
        return StandardResponse(status="error", error=str(e))


@app.post("/api/bidding/bid", response_model=StandardResponse)
async def place_bid(request: BiddingRequest):
    """Place a bid on a loan."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        result = service.place_bid(request.loan_id, request.amount, request.payment_option)
        return StandardResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"Error placing bid: {e}")
        return StandardResponse(status="error", error=str(e))


@app.get("/api/bidding/history", response_model=StandardResponse)
async def get_bidding_history():
    """Get bidding history."""
    try:
        # For now, return empty array - in a real implementation you'd fetch from database
        history = []
        return StandardResponse(status="success", data={"history": history})
    except Exception as e:
        logger.error(f"Error getting bidding history: {e}")
        return StandardResponse(status="error", error=str(e))


# Configuration Endpoints
@app.get("/api/config", response_model=StandardResponse)
async def get_configuration():
    """Get current configuration."""
    try:
        from src.config import KameoConfig
        from src.database.config import DatabaseConfig
        
        kameo_config = KameoConfig()
        db_config = DatabaseConfig()
        
        # Don't expose sensitive information like passwords
        config_data = {
            "kameo": {
                "email": kameo_config.email,
                "base_url": kameo_config.base_url,
                "connect_timeout": kameo_config.connect_timeout,
                "read_timeout": kameo_config.read_timeout,
                "max_redirects": kameo_config.max_redirects,
                "user_agent": kameo_config.user_agent,
                "totp_secret": "***" if kameo_config.totp_secret else None,
            },
            "database": {
                "db_url": db_config.db_url,
                "pool_size": db_config.pool_size,
                "max_overflow": db_config.max_overflow,
                "pool_timeout": db_config.pool_timeout,
                "pool_recycle": db_config.pool_recycle,
                "echo": db_config.echo,
                "create_tables": db_config.create_tables,
                "backup_enabled": db_config.backup_enabled,
                "backup_interval_hours": db_config.backup_interval_hours,
                "backup_retention_days": db_config.backup_retention_days,
            }
        }
        
        return StandardResponse(status="success", data=config_data)
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return StandardResponse(status="error", error=str(e))


@app.post("/api/config/test", response_model=StandardResponse)
async def test_configuration():
    """Test current configuration."""
    try:
        from src.database.connection import get_database_manager

        # Test database connection
        try:
            db_manager = get_database_manager()
            database_connected = db_manager.health_check()
        except Exception:
            database_connected = False

        # Test Kameo API connection (placeholder)
        kameo_accessible = True  # In a real implementation, test actual API connectivity

        return StandardResponse(
            status="success", 
            data={
                "database_connected": database_connected,
                "kameo_accessible": kameo_accessible
            }
        )
    except Exception as e:
        logger.error(f"Error testing configuration: {e}")
        return StandardResponse(status="error", error=str(e))


# System Status Endpoints
@app.get("/api/system/status", response_model=StandardResponse)
async def get_system_status():
    """Get comprehensive system status."""
    try:
        from src.database.connection import get_database_manager
        
        # Database status
        try:
            db_manager = get_database_manager()
            database_connected = db_manager.health_check()
        except Exception:
            database_connected = False

        # API status
        api_accessible = True  # We're responding, so API is accessible

        # Job status
        job_service = get_job_service()
        active_jobs = job_service.get_active_job_count()

        # Loan statistics
        try:
            from src.cli import KameoBotCLI
            cli_instance = KameoBotCLI()
            loan_stats = cli_instance.get_loan_statistics()
            total_loans_count = loan_stats.get('total_loans', 0) if isinstance(loan_stats, dict) else 0
        except Exception:
            total_loans_count = 0

        status = {
            "database_connected": database_connected,
            "api_accessible": api_accessible,
            "active_jobs": active_jobs,
            "total_loans_count": total_loans_count,
            "timestamp": datetime.now().isoformat()
        }

        return StandardResponse(status="success", data=status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return StandardResponse(status="error", error=str(e))


# Demo Operations
@app.post("/api/demo", response_model=StandardResponse)
async def run_demo():
    """Run demo functionality."""
    try:
        from src.config import KameoConfig
        from src.services.loan_operations_service import LoanOperationsService
        
        config = KameoConfig()
        service = LoanOperationsService(config)
        result = service.run_demo()
        return StandardResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        return StandardResponse(status="error", error=str(e))


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    websocket_manager = get_websocket_manager()
    connection_id = await websocket_manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            await websocket_manager.handle_client_message(connection_id, data)

    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        websocket_manager.disconnect(connection_id)


# WebSocket Management Endpoints
@app.get("/api/websocket/connections")
async def get_websocket_connections():
    """Get information about active WebSocket connections."""
    websocket_manager = get_websocket_manager()
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "connections": websocket_manager.get_connection_info()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    job_service = get_job_service()
    websocket_manager = get_websocket_manager()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": job_service.get_active_job_count(),
        "websocket_connections": websocket_manager.get_connection_count()
    }