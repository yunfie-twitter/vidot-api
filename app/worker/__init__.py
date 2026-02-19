"""Worker package for vidot-api download processing."""

from app.worker.downloader import download_video

__all__ = [
    "download_video",
]
