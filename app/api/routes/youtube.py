"""
YouTube to MP3 API routes
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.requests import YouTubeToMP3Request
from app.models.responses import YouTubeToMP3Response, ErrorResponse
from app.services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)
router = APIRouter()


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
    """
)
async def youtube_to_mp3(
    request: YouTubeToMP3Request,
    background_tasks: BackgroundTasks
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
        youtube_service = YouTubeService()
        
        # Download the audio
        result = youtube_service.download_audio(
            url=str(request.url),
            audio_quality=request.audio_quality,
            audio_format=request.audio_format,
            extract_metadata=request.extract_metadata
        )
        
        if not result['success']:
            return YouTubeToMP3Response(
                success=False,
                error=result.get('error', 'Unknown error occurred')
            )
        
        # Generate download URL
        download_url = f"/api/v1/download/{result['file_id']}"
        
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
        logger.error(f"Error in youtube_to_mp3: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/youtube-info",
    summary="Get YouTube video information",
    description="Extract metadata from a YouTube video without downloading"
)
async def get_youtube_info(url: str):
    """
    Get YouTube video information without downloading
    
    - **url**: YouTube video URL
    
    Returns video metadata including title, duration, thumbnail, etc.
    """
    try:
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
        logger.error(f"Error getting YouTube info: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract video information: {str(e)}"
        )
