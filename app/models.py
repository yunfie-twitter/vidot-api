from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
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


class DownloadRequest(BaseModel):
    """Request model for download endpoint."""
    url: str = Field(..., description="Video URL to download")
    format: DownloadFormat = Field(..., description="Output format (mp4 or mp3)")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        return v.strip()


class DownloadResponse(BaseModel):
    """Response model for download endpoint."""
    job_id: str = Field(..., alias="jobId", description="Unique job identifier")
    
    class Config:
        populate_by_name = True


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(default=0.0, description="Download progress (0-100)")
    file_path: Optional[str] = Field(default=None, alias="filePath", description="Downloaded file path")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        populate_by_name = True
