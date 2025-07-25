from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime

from src.services.job_service import get_job_service, get_loan_fetch_service

logger = logging.getLogger(__name__)

app = FastAPI(title="KameoBot Async API", version="1.0.0")


class StandardResponse(BaseModel):
    status: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Secure CORS configuration
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # Common React dev port
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    job_service = get_job_service()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": job_service.get_active_job_count()
    } 