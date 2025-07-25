from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import uuid4
import threading
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from src.services.loan_collector import LoanCollectorService
from src.config import KameoConfig

logger = logging.getLogger(__name__)

app = FastAPI(title="KameoBot Async API", version="1.0.0")


class JobStatus(str):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class StandardResponse(BaseModel):
    status: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# In-memory job registry (simple demo – replace with DB/Redis for prod)
_jobs: Dict[str, Dict[str, Any]] = {}


def _register_job() -> str:
    job_id = str(uuid4())
    _jobs[job_id] = {"status": JobStatus.PENDING, "error": None, "data": None}
    return job_id


def _update_job(job_id: str, *, status: str, error: Optional[str] = None, data: Any = None):
    if job_id in _jobs:
        _jobs[job_id].update({"status": status, "error": error, "data": data})


# Enable CORS for localhost frontend/demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "*"],  # simple for demo
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve docs directory for demo HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
if os.path.isdir(DOCS_DIR):
    app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")


# === Example async job: fetch loans ===

def _fetch_loans_job(job_id: str, limit: int = 12, page: int = 1):
    """Background job to fetch loans via LoanCollectorService or dummy in test mode"""
    try:
        if os.getenv("TEST_MODE") == "1":
            # Return dummy data quickly for local tests
            dummy_loans = [{"id": 1, "title": "Dummy Loan", "amount": 100000}]
            _update_job(job_id, status=JobStatus.SUCCESS, data={"loans": dummy_loans})
            return

        config = KameoConfig()  # type: ignore[arg-type]  # load from env
        svc = LoanCollectorService(config)
        loans = svc.fetch_loans(limit=limit, page=page)
        _update_job(job_id, status=JobStatus.SUCCESS, data={"loans": loans})
    except Exception as exc:
        logger.exception("Fetch loans job failed")
        _update_job(job_id, status=JobStatus.FAILED, error=str(exc))


@app.post("/api/jobs/fetch-loans", response_model=StandardResponse)
async def start_fetch_loans(background_tasks: BackgroundTasks, limit: int = 12, page: int = 1):
    """Start an asynchronous job that fetches loans. Returns a job ID."""
    job_id = _register_job()
    background_tasks.add_task(_fetch_loans_job, job_id, limit, page)
    return StandardResponse(status=JobStatus.PENDING, data={"job_id": job_id})


@app.get("/api/jobs/{job_id}", response_model=StandardResponse)
async def get_job_status(job_id: str):
    """Poll the status of a previously started job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return StandardResponse(**job) 