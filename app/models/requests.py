"""
Pydantic models for API requests
"""

from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field, field_validator

from app.core.config import settings


class YouTubeToMP3Request(BaseModel):
    """Request model for YouTube to MP3 conversion"""
    
    url: HttpUrl = Field(
        ...,
        description="YouTube video URL (supports youtube.com, youtu.be, music.youtube.com)",
        json_schema_extra={"example": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    audio_quality: int = Field(
        default=settings.DEFAULT_AUDIO_QUALITY,
        ge=0, le=10,
        description="Audio quality scale: 0=best quality (~320kbps), 5=balanced (~160kbps), 10=smallest files (~64kbps)",
        json_schema_extra={"example": 0}
    )
    audio_format: str = Field(
        default=settings.DEFAULT_AUDIO_FORMAT,
        description="Output audio format: mp3, m4a, wav, flac, aac, opus",
        json_schema_extra={"example": "mp3"}
    )
    extract_metadata: bool = Field(
        default=True,
        description="Extract video metadata (title, duration, thumbnail, etc.)",
        json_schema_extra={"example": True}
    )
    
    @field_validator('audio_format')
    @classmethod
    def validate_audio_format(cls, v):
        if v not in settings.SUPPORTED_AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format. Supported: {settings.SUPPORTED_AUDIO_FORMATS}")
        return v
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        from urllib.parse import urlparse
        youtube_domains = {
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'www.youtu.be', 'music.youtube.com'
        }
        if urlparse(str(v)).hostname not in youtube_domains:
            raise ValueError("URL must be a valid YouTube URL")
        return v


class StemSeparationRequest(BaseModel):
    """Request model for stem separation (used with form data)"""
    
    model: str = Field(
        default=settings.DEFAULT_DEMUCS_MODEL,
        description="Demucs model to use for separation"
    )
    output_format: str = Field(
        default=settings.DEFAULT_STEM_FORMAT,
        description="Output format for stems"
    )
    stems: Optional[List[str]] = Field(
        default=None,
        description="Specific stems to extract (default: all)"
    )
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        if v not in settings.SUPPORTED_DEMUCS_MODELS:
            raise ValueError(f"Unsupported model. Supported: {settings.SUPPORTED_DEMUCS_MODELS}")
        return v
    
    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v):
        if v not in settings.SUPPORTED_STEM_FORMATS:
            raise ValueError(f"Unsupported format. Supported: {settings.SUPPORTED_STEM_FORMATS}")
        return v
    
    @field_validator('stems')
    @classmethod
    def validate_stems(cls, v):
        if v is not None:
            valid_stems = ['vocals', 'drums', 'bass', 'other']
            for stem in v:
                if stem not in valid_stems:
                    raise ValueError(f"Invalid stem '{stem}'. Valid stems: {valid_stems}")
        return v
