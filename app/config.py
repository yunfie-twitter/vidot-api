from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    port: int = 8000
    
    # Download Directory
    download_dir: str = "/app/downloads"
    
    # yt-dlp Configuration
    ytdlp_path: str = "yt-dlp"
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Queue Configuration
    queue_concurrency: int = 2
    queue_name: str = "download_queue"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
