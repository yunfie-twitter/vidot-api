"""Progress tracking utilities for download jobs."""

import logging
from rq import get_current_job

logger = logging.getLogger(__name__)


def update_progress(progress: float) -> None:
    """
    Update job progress in Redis.
    
    Args:
        progress: Progress percentage (0-100)
    """
    try:
        job = get_current_job()
        if job:
            job.meta['progress'] = progress
            job.save_meta()
    except Exception as e:
        logger.warning(f"Failed to update progress: {str(e)}")
