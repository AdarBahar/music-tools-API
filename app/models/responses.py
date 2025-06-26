"""
Pydantic models for API responses
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """Video metadata model"""
    title: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds
    thumbnail_url: Optional[str] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    description: Optional[str] = None


class YouTubeToMP3Response(BaseModel):
    """Response model for YouTube to MP3 conversion"""
    success: bool
    message: Optional[str] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None
    file_size_mb: Optional[float] = None
    metadata: Optional[VideoMetadata] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class StemFiles(BaseModel):
    """Model for stem file URLs"""
    vocals: Optional[str] = None
    drums: Optional[str] = None
    bass: Optional[str] = None
    other: Optional[str] = None


class StemSeparationResponse(BaseModel):
    """Response model for stem separation"""
    success: bool
    message: Optional[str] = None
    job_id: Optional[str] = None
    stems: Optional[StemFiles] = None
    processing_time_seconds: Optional[float] = None
    error: Optional[str] = None


class DownloadInfo(BaseModel):
    """Model for download information"""
    file_id: str
    filename: str
    file_size_mb: float
    content_type: str
    created_at: str


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: Optional[str] = None
    uptime_seconds: Optional[float] = None


class StatsResponse(BaseModel):
    """Statistics response model"""
    directories: Dict[str, Dict[str, Any]]
    total_files: int
    total_size_mb: float
    cleanup_info: Dict[str, Any]
