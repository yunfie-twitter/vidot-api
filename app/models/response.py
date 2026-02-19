"""Response models for vidot-api."""

from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import JobStatus


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
