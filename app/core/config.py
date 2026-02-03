"""
Configuration settings for the Music Tools API Service
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # File Storage
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # File Limits
    MAX_FILE_SIZE_MB: int = 100
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Memory Management
    MEMORY_LIMIT_MB: int = 2048  # 2GB memory limit for processing
    MEMORY_WARNING_THRESHOLD_MB: int = 1536  # Warning at 1.5GB
    MAX_CONCURRENT_OPERATIONS: int = 3  # Limit concurrent heavy operations
    STREAMING_CHUNK_SIZE: int = 8192  # 8KB chunks for streaming uploads
    PROCESS_MEMORY_LIMIT_MB: int = 4096  # 4GB limit for subprocess operations
    MEMORY_CHECK_INTERVAL: int = 10  # Check memory every 10 seconds during processing
    
    # File Upload Validation
    ALLOWED_AUDIO_EXTENSIONS: list = [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma"]
    ALLOWED_MIME_TYPES: list = [
        "audio/mpeg",       # MP3
        "audio/wav",        # WAV
        "audio/x-wav",      # WAV (alternative)
        "audio/flac",       # FLAC
        "audio/mp4",        # M4A/AAC
        "audio/aac",        # AAC
        "audio/ogg",        # OGG
        "audio/opus",       # OPUS
        "audio/x-ms-wma",   # WMA
        "application/octet-stream"  # Generic binary (needs content validation)
    ]
    
    # Cleanup Configuration
    CLEANUP_INTERVAL_HOURS: int = 24
    FILE_RETENTION_HOURS: int = 48
    
    # YouTube Download Settings
    DEFAULT_AUDIO_QUALITY: int = 0  # 0 = best, 10 = worst
    DEFAULT_AUDIO_FORMAT: str = "mp3"
    SUPPORTED_AUDIO_FORMATS: list = ["mp3", "m4a", "wav", "flac", "aac", "opus"]
    
    # Demucs Settings
    DEFAULT_DEMUCS_MODEL: str = "htdemucs"
    SUPPORTED_DEMUCS_MODELS: list = [
        "htdemucs",
        "htdemucs_ft", 
        "mdx_extra",
        "mdx_extra_q"
    ]
    DEFAULT_STEM_FORMAT: str = "mp3"
    SUPPORTED_STEM_FORMATS: list = ["wav", "mp3", "flac"]
    
    # Request Timeout Settings (in seconds)
    API_REQUEST_TIMEOUT: int = 120  # 2 minutes for regular API requests
    YOUTUBE_DOWNLOAD_TIMEOUT: int = 600  # 10 minutes for YouTube downloads
    STEM_SEPARATION_TIMEOUT: int = 1800  # 30 minutes for stem separation
    FILE_UPLOAD_TIMEOUT: int = 300  # 5 minutes for file uploads
    
    # Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    REQUIRE_API_KEY: bool = False
    VALID_API_KEYS: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # Rate Limiting
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_STORAGE_URI: str = REDIS_URL
    # Rate limits per minute for different operation types
    RATE_LIMIT_HEAVY_OPERATIONS: str = "3/minute"  # Stem separation, YouTube downloads
    RATE_LIMIT_LIGHT_OPERATIONS: str = "20/minute"  # Downloads, models list
    RATE_LIMIT_INFO_OPERATIONS: str = "60/minute"  # Health checks, info endpoints

    @property
    def valid_api_keys_list(self) -> list:
        """Parse comma-separated API keys into a list"""
        if not self.VALID_API_KEYS:
            return []
        return [key.strip() for key in self.VALID_API_KEYS.split(',') if key.strip()]
    
    @property
    def allowed_origins_list(self) -> list:
        """Parse comma-separated origins into a list"""
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields to be ignored


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
