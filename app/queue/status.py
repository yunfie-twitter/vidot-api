"""Job status determination logic."""

import logging
from typing import Tuple, Optional
from rq.job import Job

from app.models import JobStatus

logger = logging.getLogger(__name__)


def determine_job_status(
    job: Job
) -> Tuple[JobStatus, float, Optional[str], Optional[str]]:
    """
    Determine job status, progress, file path, and error from RQ job.
    
    Args:
        job: RQ Job instance
    
    Returns:
        Tuple of (status, progress, file_path, error)
        - status: JobStatus enum value
        - progress: Progress percentage (0-100)
        - file_path: Path to downloaded file (if finished)
        - error: Error message (if failed)
    
    Example:
        >>> job = Job.fetch('some-job-id', connection=redis)
        >>> status, progress, path, error = determine_job_status(job)
    """
    if job.is_finished:
        return (
            JobStatus.FINISHED,
            100.0,
            job.result if job.result else None,
            None
        )
    
    elif job.is_failed:
        error_msg = str(job.exc_info) if job.exc_info else "Unknown error"
        return (
            JobStatus.FAILED,
            0.0,
            None,
            error_msg
        )
    
    elif job.is_started:
        # Get progress from job meta if available
        progress = job.meta.get('progress', 0.0) if job.meta else 0.0
        return (
            JobStatus.STARTED,
            progress,
            None,
            None
        )
    
    else:  # queued
        return (
            JobStatus.QUEUED,
            0.0,
            None,
            None
        )
