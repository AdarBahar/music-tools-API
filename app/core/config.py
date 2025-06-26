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
    
    # Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    REQUIRE_API_KEY: bool = False
    VALID_API_KEYS: list = []

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
