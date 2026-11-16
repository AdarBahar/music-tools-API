"""
YouTube to MP3 API routes
"""

import logging
import re
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.models.requests import YouTubeToMP3Request
from app.models.responses import YouTubeToMP3Response, ErrorResponse
from app.services.youtube_service import YouTubeService
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.rate_limit import limit
from app.core.metrics import MetricsContext

logger = logging.getLogger(__name__)
router = APIRouter()


_YOUTUBE_HOSTS = {
    'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com',
    'youtu.be', 'www.youtu.be',
}
# Query parameters that YouTube adds to normal links. Others are rejected.
_SAFE_QUERY_PARAMS = {
    'v', 'list', 't', 'start', 'end', 'index',
    'feature', 'ab_channel', 'si', 'pp', 'app', 'lc',
}


def validate_youtube_url(url: str) -> bool:
    """
    Validate that a URL is a legitimate YouTube URL

    Checks the scheme, the host name (not a substring), the path format
    and the query parameter names.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if parsed.hostname not in _YOUTUBE_HOSTS:
            return False

        if 'youtu.be' in parsed.hostname:
            # youtu.be format: /VIDEO_ID
            if not re.match(r'^/[\w\-]+$', parsed.path):
                return False
        elif parsed.path not in ('', '/') and not re.match(r'^/[\w/\-]+$', parsed.path):
            return False

        for param in parsed.query.split('&'):
            if param and param.split('=')[0] not in _SAFE_QUERY_PARAMS:
                return False

        return True
    except Exception:
        return False


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
@limit(settings.RATE_LIMIT_HEAVY_OPERATIONS)
async def youtube_to_mp3(
    request: Request,
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
            # download_audio is blocking (yt-dlp, ffmpeg). Run it in a worker thread
            # so the event loop keeps serving other requests.
            result = await run_in_threadpool(
                youtube_service.download_audio,
                url=str(youtube_request.url),
                audio_quality=youtube_request.audio_quality,
                audio_format=youtube_request.audio_format,
                extract_metadata=youtube_request.extract_metadata
            )
        
        if not result['success']:
            # 502: the upstream download failed. Keep the same body shape as a success.
            return JSONResponse(
                status_code=502,
                content=YouTubeToMP3Response(
                    success=False,
                    error=result.get('error', 'Unknown error occurred')
                ).model_dump()
            )
        
        # Generate download URL
        download_url = f"/api/v1/download/{result['file_id']}"
        
        # The periodic cleanup job removes the file after FILE_RETENTION_HOURS.

        return YouTubeToMP3Response(
            success=True,
            message="Audio downloaded and converted successfully",
            file_id=result['file_id'],
            filename=result['filename'],
            file_size_mb=result['file_size_mb'],
            metadata=result.get('metadata'),
            download_url=download_url
        )
        
    except HTTPException:
        raise
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
        from app.services.youtube_service import build_cookie_opts

        opts = {'quiet': True, 'noplaylist': True}
        opts.update(build_cookie_opts())

        def _extract():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)

        # yt-dlp blocks. Run it in a worker thread.
        info = await run_in_threadpool(_extract)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting YouTube info: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Failed to extract video information"
        )
