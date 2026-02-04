"""
YouTube to MP3 API routes
"""

import logging
import re
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.requests import YouTubeToMP3Request
from app.models.responses import YouTubeToMP3Response, ErrorResponse
from app.services.youtube_service import YouTubeService
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.cleanup import cleanup_file
from app.core.metrics import MetricsContext

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize limiter for this module
limiter = Limiter(key_func=get_remote_address) if settings.ENABLE_RATE_LIMITING else None


def validate_youtube_url(url: str) -> bool:
    """
    Validate that URL is a legitimate YouTube URL

    Args:
        url: URL string to validate

    Returns:
        bool: True if URL is valid YouTube URL, False otherwise

    Validates against:
    - Domain: youtube.com, youtu.be, or their www variants
    - Format: Valid path structure for YouTube
    - Safe query parameters only
    """
    try:
        parsed = urlparse(url)

        # Check for valid YouTube domains
        valid_domains = [
            'youtube.com', 'www.youtube.com',
            'youtu.be', 'www.youtu.be',
            'm.youtube.com'
        ]

        if parsed.netloc not in valid_domains:
            return False

        # Check for valid paths and query parameters
        if 'youtu.be' in parsed.netloc:
            # youtu.be format: /VIDEO_ID
            if not re.match(r'^/[\w\-]+$', parsed.path):
                return False
        else:
            # youtube.com format: /watch?v=VIDEO_ID or /playlist?list=...
            if not (parsed.query or parsed.path in ['/', '']):
                if not re.match(r'^/[\w/\-_]+$', parsed.path):
                    return False

            # Validate query parameters - only allow known safe parameters
            if parsed.query:
                safe_params = {'v', 'list', 't', 'start', 'end', 'index'}
                for param in parsed.query.split('&'):
                    if not param:
                        continue
                    param_name = param.split('=')[0]
                    if param_name not in safe_params:
                        return False

        return True
    except Exception:
        return False


async def _schedule_file_cleanup(file_path: str, delay_hours: int):
    """
    Background task to schedule cleanup of downloaded files after delay period
    
    Args:
        file_path: Path to file to cleanup
        delay_hours: Hours to wait before cleanup
    """
    import asyncio
    
    # Wait for the specified delay
    await asyncio.sleep(delay_hours * 3600)
    
    # Clean up the file
    if cleanup_file(file_path):
        logger.info(f"Background cleanup removed file: {file_path}")
    else:
        logger.warning(f"Background cleanup failed for file: {file_path}")


@(limiter.limit(settings.RATE_LIMIT_HEAVY_OPERATIONS) if limiter else (lambda f: f))
@router.post(
    "/youtube-to-mp3",
    response_model=YouTubeToMP3Response,
    summary="Convert YouTube video to MP3",
    description="""
    Download and convert a YouTube video to audio format with configurable quality and metadata extraction.

    **Audio Quality Scale (0-10):**
    - 0: Best quality (~320 kbps, larger files)
    - 5: Balanced quality (~160 kbps, medium files)
    - 10: Smallest files (~64 kbps, lower quality)

    **Supported Formats:** mp3, m4a, wav, flac, aac, opus
    
    **Authentication:** Requires valid API key when authentication is enabled.
    """,
    dependencies=[Depends(verify_api_key)]
)
async def youtube_to_mp3(
    request: Request,
    background_tasks: BackgroundTasks,
    youtube_request: YouTubeToMP3Request
) -> YouTubeToMP3Response:
    """
    Convert YouTube video to MP3
    
    - **url**: YouTube video URL (required)
    - **audio_quality**: Audio quality from 0 (best) to 10 (worst)
    - **audio_format**: Output audio format (mp3, m4a, wav, flac, etc.)
    - **extract_metadata**: Whether to extract video metadata
    
    Returns the converted audio file information and download URL.
    """
    try:
        # Validate YouTube URL format
        if not validate_youtube_url(str(youtube_request.url)):
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL"
            )

        youtube_service = YouTubeService()

        # Download the audio with metrics tracking
        with MetricsContext("youtube_download"):
            result = youtube_service.download_audio(
                url=str(youtube_request.url),
                audio_quality=youtube_request.audio_quality,
                audio_format=youtube_request.audio_format,
                extract_metadata=youtube_request.extract_metadata
            )
        
        if not result['success']:
            return YouTubeToMP3Response(
                success=False,
                error=result.get('error', 'Unknown error occurred')
            )
        
        # Generate download URL
        download_url = f"/api/v1/download/{result['file_id']}"
        
        # Schedule cleanup of downloaded file after retention period
        background_tasks.add_task(
            _schedule_file_cleanup, 
            result['file_path'],
            settings.FILE_RETENTION_HOURS
        )
        
        return YouTubeToMP3Response(
            success=True,
            message="Audio downloaded and converted successfully",
            file_id=result['file_id'],
            filename=result['filename'],
            file_size_mb=result['file_size_mb'],
            metadata=result.get('metadata'),
            download_url=download_url
        )
        
    except Exception as e:
        logger.error(f"Error in youtube_to_mp3: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/youtube-info",
    summary="Get YouTube video information",
    description="Extract metadata from a YouTube video without downloading. Requires authentication when enabled.",
    dependencies=[Depends(verify_api_key)]
)
async def get_youtube_info(url: str):
    """
    Get YouTube video information without downloading
    
    - **url**: YouTube video URL
    
    Returns video metadata including title, duration, thumbnail, etc.
    """
    try:
        # Validate YouTube URL format
        if not validate_youtube_url(url):
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL"
            )

        import yt_dlp

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                "success": True,
                "info": {
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "thumbnail": info.get('thumbnail'),
                    "uploader": info.get('uploader'),
                    "upload_date": info.get('upload_date'),
                    "view_count": info.get('view_count'),
                    "description": info.get('description', '')[:500] if info.get('description') else None,
                    "formats_available": len(info.get('formats', [])),
                    "audio_formats": [
                        f for f in info.get('formats', []) 
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none'
                    ][:5]  # Show first 5 audio formats
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting YouTube info: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Failed to extract video information"
        )
