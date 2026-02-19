"""Request models for vidot-api."""

from pydantic import BaseModel, Field, field_validator

from app.models.enums import DownloadFormat


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
