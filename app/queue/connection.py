"""Redis connection management."""

import logging
from typing import Optional
from redis import Redis
from rq import Queue

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection and queue instances
redis_conn: Optional[Redis] = None
queue: Optional[Queue] = None


def init_redis() -> None:
    """
    Initialize Redis connection and RQ queue.
    
    This function is idempotent and can be called multiple times.
    Creates global redis_conn and queue instances.
    """
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
    """
    Get Redis connection instance.
    
    Automatically initializes connection if not already initialized.
    
    Returns:
        Redis connection instance
    """
    if redis_conn is None:
        init_redis()
    return redis_conn


def get_queue() -> Queue:
    """
    Get RQ queue instance.
    
    Automatically initializes queue if not already initialized.
    
    Returns:
        RQ Queue instance
    """
    if queue is None:
        init_redis()
    return queue
