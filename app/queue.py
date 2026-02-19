from redis import Redis
from rq import Queue
from rq.job import Job
import logging
from typing import Optional

from app.config import settings
from app.models import JobStatusResponse, JobStatus

logger = logging.getLogger(__name__)

# Global Redis connection
redis_conn: Optional[Redis] = None
queue: Optional[Queue] = None


def _sanitize_for_log(value: str) -> str:
    """
    Remove characters from a string that could be used to inject
    additional log entries (for example, newlines).
    """
    # Guard against None, though in our usage we only pass strings
    if value is None:
        return ""
    return value.replace("\r", "").replace("\n", "")


def init_redis() -> None:
    """Initialize Redis connection and queue."""
    global redis_conn, queue
    
    redis_conn = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password if settings.redis_password else None,
        db=settings.redis_db,
        decode_responses=True
    )
    
    queue = Queue(
        name=settings.queue_name,
        connection=redis_conn
    )
    
    logger.info(f"Redis queue '{settings.queue_name}' initialized")


def get_redis() -> Redis:
    """Get Redis connection."""
    if redis_conn is None:
        init_redis()
    return redis_conn


def get_queue() -> Queue:
    """Get RQ queue instance."""
    if queue is None:
        init_redis()
    return queue


def enqueue_download(url: str, format: str) -> str:
    """
    Enqueue a download job.
    
    Args:
        url: Video URL to download
        format: Output format (mp4 or mp3)
    
    Returns:
        Job ID
    """
    from app.worker import download_video
    
    q = get_queue()
    job = q.enqueue(
        download_video,
        url,
        format,
        job_timeout='30m',
        result_ttl=86400,  # Keep results for 24 hours
        failure_ttl=86400
    )
    
    safe_url = url.replace('\r', '').replace('\n', '')
    safe_format = format.replace('\r', '').replace('\n', '')
    logger.info(f"Job enqueued: {job.id} for URL: {safe_url} (format: {safe_format})")
    return job.id


def get_job_status(job_id: str) -> Optional[JobStatusResponse]:
    """
    Get the status of a job.
    
    Args:
        job_id: Job ID
    
    Returns:
        JobStatusResponse or None if job not found
    """
    try:
        job = Job.fetch(job_id, connection=get_redis())
    except Exception as e:
        safe_job_id = _sanitize_for_log(job_id)
        safe_error = _sanitize_for_log(str(e))
        logger.error(f"Job not found: {safe_job_id} - {safe_error}")
        return None
    
    # Determine status
    if job.is_finished:
        status = JobStatus.FINISHED
        progress = 100.0
        file_path = job.result if job.result else None
        error = None
    elif job.is_failed:
        status = JobStatus.FAILED
        progress = 0.0
        file_path = None
        error = str(job.exc_info) if job.exc_info else "Unknown error"
    elif job.is_started:
        status = JobStatus.STARTED
        # Get progress from job meta if available
        progress = job.meta.get('progress', 0.0) if job.meta else 0.0
        file_path = None
        error = None
    else:  # queued
        status = JobStatus.QUEUED
        progress = 0.0
        file_path = None
        error = None
    
    return JobStatusResponse(
        status=status,
        progress=progress,
        filePath=file_path,
        error=error
    )
