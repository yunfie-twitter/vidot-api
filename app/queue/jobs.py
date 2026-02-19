"""Job enqueue and status retrieval operations."""

import logging
from typing import Optional
from rq.job import Job

from app.models import JobStatusResponse
from app.queue.connection import get_redis, get_queue
from app.queue.status import determine_job_status

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: str) -> str:
    """
    Remove characters from a string that could be used to inject
    additional log entries (for example, newlines).
    
    Args:
        value: String to sanitize
    
    Returns:
        Sanitized string with \r and \n removed
    """
    # Guard against None, though in our usage we only pass strings
    if value is None:
        return ""
    return value.replace("\r", "").replace("\n", "")


def enqueue_download(url: str, format: str) -> str:
    """
    Enqueue a download job to RQ.
    
    Args:
        url: Video URL to download
        format: Output format (mp4 or mp3)
    
    Returns:
        Job ID (UUID string)
    
    Example:
        >>> job_id = enqueue_download(
        ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     "mp4"
        ... )
        >>> print(job_id)  # 'abc123-def456-ghi789'
    """
    from app.worker import download_video
    
    q = get_queue()
    job = q.enqueue(
        download_video,
        url,
        format,
        job_timeout='30m',
        result_ttl=86400,  # Keep results for 24 hours
        failure_ttl=86400   # Keep failure info for 24 hours
    )
    
    # Sanitize values for logging to prevent log injection
    safe_url = _sanitize_for_log(url)
    safe_format = _sanitize_for_log(format)
    logger.info(f"Job enqueued: {job.id} for URL: {safe_url} (format: {safe_format})")
    return job.id


def get_job_status(job_id: str) -> Optional[JobStatusResponse]:
    """
    Get the status of a job by its ID.
    
    Args:
        job_id: Job ID to query
    
    Returns:
        JobStatusResponse with current status, progress, file path, and error,
        or None if job not found
    
    Example:
        >>> response = get_job_status('abc123-def456')
        >>> if response:
        ...     print(f"Status: {response.status}")
        ...     print(f"Progress: {response.progress}%")
    """
    try:
        job = Job.fetch(job_id, connection=get_redis())
    except Exception as e:
        # Sanitize values for logging to prevent log injection
        safe_job_id = _sanitize_for_log(job_id)
        safe_error = _sanitize_for_log(str(e))
        logger.error(f"Job not found: {safe_job_id} - {safe_error}")
        return None
    
    # Determine status using status module
    status, progress, file_path, error = determine_job_status(job)
    
    return JobStatusResponse(
        status=status,
        progress=progress,
        filePath=file_path,
        error=error
    )
