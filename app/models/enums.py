"""Enum definitions for vidot-api."""

from enum import Enum


class DownloadFormat(str, Enum):
    """Supported download formats."""
    MP4 = "mp4"
    MP3 = "mp3"


class JobStatus(str, Enum):
    """Job execution status."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
