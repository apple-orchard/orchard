"""
Background ingestion job management system.
Handles async processing of document ingestion without blocking the API.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration."""
    TEXT_INGESTION = "text_ingestion"
    FILE_INGESTION = "file_ingestion"
    DIRECTORY_INGESTION = "directory_ingestion"
    BATCH_INGESTION = "batch_ingestion"


@dataclass
class IngestionJob:
    """Represents an ingestion job."""
    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    error_message: str = ""
    chunks_created: int = 0
    total_items: int = 0
    processed_items: int = 0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
        return data

    def update_progress(self, processed: int, total: int, message: str = ""):
        """Update job progress."""
        self.processed_items = processed
        self.total_items = total
        self.progress = processed / total if total > 0 else 0.0
        if message:
            self.message = message


class IngestionJobManager:
    """Manages background ingestion jobs."""

    def __init__(self, max_concurrent_jobs: int = 3):
        self.jobs: Dict[str, IngestionJob] = {}
        self.max_concurrent_jobs = max_concurrent_jobs
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        self._lock = threading.Lock()

    def create_job(self, job_type: JobType, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new ingestion job."""
        job_id = str(uuid.uuid4())

        job = IngestionJob(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )

        with self._lock:
            self.jobs[job_id] = job

        # Log job creation with relevant metadata
        meta_info = ""
        if metadata:
            if "file_path" in metadata:
                meta_info = f" - file: {metadata['file_path']}"
            elif "directory_path" in metadata:
                meta_info = f" - directory: {metadata['directory_path']}"
            elif "message_count" in metadata:
                meta_info = f" - {metadata['message_count']} messages"
            elif "text_length" in metadata:
                meta_info = f" - {metadata['text_length']:,} characters"

        logger.info(f"📝 Created ingestion job {job_id} ({job_type.value}){meta_info}")
        return job_id

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        """Get job by ID."""
        with self._lock:
            return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None) -> List[IngestionJob]:
        """List all jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self.jobs.values())

        if status:
            jobs = [job for job in jobs if job.status == status]

        # Sort by creation time, newest first
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it's pending."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                job.message = "Job cancelled by user"
                logger.info(f"Cancelled job {job_id}")
                return True
        return False

    def submit_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> None:
        """Submit a job for background execution."""
        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        def job_wrapper():
            """Wrapper to handle job execution with status updates."""
            try:
                with self._lock:
                    if job.status == JobStatus.CANCELLED:
                        logger.info(f"Job {job_id} was cancelled before execution")
                        return
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now()
                    job.message = "Processing..."

                logger.info(f"🚀 Starting job {job_id} ({job.job_type.value})")

                # Execute the actual task
                result = task_func(job, *args, **kwargs)

                with self._lock:
                    if job.status != JobStatus.CANCELLED:
                        job.status = JobStatus.COMPLETED
                        job.completed_at = datetime.now()
                        job.progress = 1.0
                        chunks_created = result.get("chunks_created", 0)
                        job.chunks_created = chunks_created

                        # Create a more informative completion message
                        if chunks_created > 0:
                            job.message = result.get("message", f"Completed successfully - {chunks_created} chunks created")
                        else:
                            job.message = result.get("message", "Completed successfully")
                            
                        # Store error details if any
                        if result.get("errors"):
                            job.error_message = "; ".join(result.get("errors", []))

                # Calculate execution time
                execution_time = (job.completed_at - job.started_at).total_seconds() if job.started_at else 0.0
                logger.info(f"✅ Completed job {job_id} in {execution_time:.2f}s - {job.chunks_created} chunks created")

            except Exception as e:
                error_msg = str(e)
                error_traceback = traceback.format_exc()

                with self._lock:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now()
                    job.error_message = error_msg
                    job.message = f"Failed: {error_msg}"

                # Calculate execution time even for failed jobs
                if job.started_at:
                    execution_time = (job.completed_at - job.started_at).total_seconds()
                    logger.error(f"❌ Job {job_id} failed after {execution_time:.2f}s: {error_msg}")
                else:
                    logger.error(f"❌ Job {job_id} failed before starting: {error_msg}")

                # Log full traceback for debugging
                logger.debug(f"Full traceback for job {job_id}:\n{error_traceback}")

        # Submit to thread pool
        self.executor.submit(job_wrapper)
        logger.info(f"📋 Queued job {job_id} for execution (type: {job.job_type.value})")

    def cleanup_old_jobs(self, max_age_hours: int = 24, max_jobs: int = 100):
        """Clean up old completed/failed jobs."""
        with self._lock:
            # Sort jobs by creation time
            all_jobs = sorted(self.jobs.values(), key=lambda x: x.created_at, reverse=True)

            # Keep active jobs and recent completed/failed jobs
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            jobs_to_keep = []

            for job in all_jobs:
                # Always keep active jobs
                if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                    jobs_to_keep.append(job)
                # Keep recent jobs within max_jobs limit
                elif len(jobs_to_keep) < max_jobs and job.created_at.timestamp() > cutoff_time:
                    jobs_to_keep.append(job)

            # Update jobs dict
            self.jobs = {job.job_id: job for job in jobs_to_keep}

            removed_count = len(all_jobs) - len(jobs_to_keep) if jobs_to_keep is not None else len(all_jobs)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old ingestion jobs")

    def get_stats(self) -> Dict[str, Any]:
        """Get job manager statistics."""
        with self._lock:
            jobs = list(self.jobs.values())

        stats = {
            "total_jobs": len(jobs),
            "pending": len([j for j in jobs if j.status == JobStatus.PENDING]),
            "running": len([j for j in jobs if j.status == JobStatus.RUNNING]),
            "completed": len([j for j in jobs if j.status == JobStatus.COMPLETED]),
            "failed": len([j for j in jobs if j.status == JobStatus.FAILED]),
            "cancelled": len([j for j in jobs if j.status == JobStatus.CANCELLED]),
            "total_chunks_created": sum(j.chunks_created for j in jobs if j.status == JobStatus.COMPLETED)
        }

        return stats


# Global job manager instance
job_manager = IngestionJobManager()


def start_background_cleanup():
    """Start background cleanup task."""
    def cleanup_loop():
        while True:
            try:
                job_manager.cleanup_old_jobs()
            except Exception as e:
                logger.error(f"Error in job cleanup: {e}")

            # Sleep for 1 hour
            threading.Event().wait(3600)

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Started background job cleanup task")