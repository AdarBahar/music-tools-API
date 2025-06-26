"""
File download API routes
"""

import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.cleanup import get_directory_stats, cleanup_all_directories
from app.models.responses import DownloadInfo, StatsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/download/{file_id}",
    summary="Download converted audio file",
    description="Download a converted audio file by its file ID"
)
async def download_file(file_id: str):
    """
    Download a converted audio file
    
    - **file_id**: Unique identifier for the file
    
    Returns the audio file for download.
    """
    try:
        # Find the file in the output directory
        output_dir = settings.OUTPUT_DIR
        
        # Look for files that contain the file_id
        matching_files = []
        for file_path in output_dir.rglob("*"):
            if file_path.is_file() and file_id in file_path.name:
                matching_files.append(file_path)
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Use the first matching file
        file_path = matching_files[0]
        
        # Determine content type based on file extension
        content_type = _get_content_type(file_path.suffix)
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/download/{job_id}/{filename}",
    summary="Download specific stem file",
    description="Download a specific stem file from a separation job"
)
async def download_stem_file(job_id: str, filename: str):
    """
    Download a specific stem file
    
    - **job_id**: Unique identifier for the separation job
    - **filename**: Name of the stem file to download
    
    Returns the stem file for download.
    """
    try:
        # Construct the file path
        file_path = settings.OUTPUT_DIR / job_id / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Stem file not found"
            )
        
        # Determine content type
        content_type = _get_content_type(file_path.suffix)
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading stem file {job_id}/{filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/download/{file_id}/info",
    response_model=DownloadInfo,
    summary="Get file information",
    description="Get information about a downloadable file"
)
async def get_file_info(file_id: str) -> DownloadInfo:
    """
    Get information about a file
    
    - **file_id**: Unique identifier for the file
    
    Returns file metadata and information.
    """
    try:
        # Find the file
        output_dir = settings.OUTPUT_DIR
        matching_files = []
        
        for file_path in output_dir.rglob("*"):
            if file_path.is_file() and file_id in file_path.name:
                matching_files.append(file_path)
        
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        file_path = matching_files[0]
        file_stats = file_path.stat()
        
        return DownloadInfo(
            file_id=file_id,
            filename=file_path.name,
            file_size_mb=round(file_stats.st_size / (1024 * 1024), 2),
            content_type=_get_content_type(file_path.suffix),
            created_at=str(file_stats.st_ctime)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info for {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get storage statistics",
    description="Get statistics about file storage and cleanup status"
)
async def get_storage_stats() -> StatsResponse:
    """
    Get storage statistics
    
    Returns information about file storage, cleanup status, and directory statistics.
    """
    try:
        # Get directory statistics
        directories = {
            "uploads": get_directory_stats(settings.UPLOAD_DIR),
            "outputs": get_directory_stats(settings.OUTPUT_DIR),
            "temp": get_directory_stats(settings.TEMP_DIR)
        }
        
        # Calculate totals
        total_files = sum(d.get("file_count", 0) for d in directories.values() if isinstance(d, dict))
        total_size_mb = sum(d.get("total_size_mb", 0) for d in directories.values() if isinstance(d, dict))
        
        # Cleanup info
        cleanup_info = {
            "cleanup_interval_hours": settings.CLEANUP_INTERVAL_HOURS,
            "file_retention_hours": settings.FILE_RETENTION_HOURS,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB
        }
        
        return StatsResponse(
            directories=directories,
            total_files=total_files,
            total_size_mb=round(total_size_mb, 2),
            cleanup_info=cleanup_info
        )
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post(
    "/cleanup",
    summary="Trigger manual cleanup",
    description="Manually trigger cleanup of old files"
)
async def manual_cleanup():
    """
    Manually trigger cleanup of old files
    
    Removes files older than the configured retention period.
    """
    try:
        results = cleanup_all_directories()
        total_removed = sum(r.get("removed_files", 0) for r in results.values())
        
        return {
            "success": True,
            "message": f"Cleanup completed. Removed {total_removed} files.",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


def _get_content_type(file_extension: str) -> str:
    """Get MIME content type for file extension"""
    content_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.m4a': 'audio/mp4',
        '.aac': 'audio/aac',
        '.opus': 'audio/opus',
        '.ogg': 'audio/ogg'
    }
    
    return content_types.get(file_extension.lower(), 'application/octet-stream')
