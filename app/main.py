from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.models import DownloadRequest, DownloadResponse, JobStatusResponse, JobStatus
from app.queue import enqueue_download, get_job_status, init_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting vidot-api server...")
    
    # Ensure download directory exists
    os.makedirs(settings.download_dir, exist_ok=True)
    logger.info(f"Download directory: {settings.download_dir}")
    
    # Initialize Redis connection
    init_redis()
    logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down vidot-api server...")


app = FastAPI(
    title="vidot-api",
    description="Python yt-dlp Download API with Redis Queue",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "service": "vidot-api",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/download", response_model=DownloadResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Download"])
async def create_download(request: DownloadRequest):
    """
    Create a new download job.
    
    The job will be queued and processed asynchronously.
    Returns a jobId to check the status and retrieve results.
    """
    try:
        job_id = enqueue_download(request.url, request.format.value)
        logger.info(f"Download job created: {job_id} for URL: {request.url}")
        return DownloadResponse(jobId=job_id)
    except Exception as e:
        logger.error(f"Failed to create download job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download job: {str(e)}"
        )


@app.get("/download/{job_id}", response_model=JobStatusResponse, tags=["Download"])
async def get_download_status(job_id: str):
    """
    Get the status of a download job.
    
    Returns the current status, progress, file path (if finished), and error (if failed).
    """
    try:
        job_status = get_job_status(job_id)
        
        if job_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )
        
        return job_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
