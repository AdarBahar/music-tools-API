"""
YouTube download service using yt-dlp
"""

import os
import uuid
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp
from yt_dlp.utils import DownloadError

from app.core.config import settings
from app.models.responses import VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for downloading YouTube videos and extracting audio"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.temp_dir = settings.TEMP_DIR
    
    def download_audio(
        self,
        url: str,
        audio_quality: int = 0,
        audio_format: str = "mp3",
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Download audio from YouTube URL
        
        Args:
            url: YouTube video URL
            audio_quality: Audio quality (0=best, 10=worst)
            audio_format: Output audio format
            extract_metadata: Whether to extract video metadata
            
        Returns:
            Dictionary with download results
        """
        file_id = str(uuid.uuid4())
        
        try:
            # Create temporary directory for this download
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_download_dir:
                
                # Configure yt-dlp options
                output_template = os.path.join(temp_download_dir, f"{file_id}.%(ext)s")
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'extractaudio': True,
                    'audioformat': audio_format,
                    'audioquality': str(audio_quality),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': str(audio_quality),
                    }],
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': settings.YOUTUBE_DOWNLOAD_TIMEOUT,
                    'fragment_retries': 3,
                    'retries': 3,
                }

                # Add cookies file if configured
                if hasattr(settings, 'YOUTUBE_COOKIES_FILE') and settings.YOUTUBE_COOKIES_FILE:
                    cookies_path = Path(settings.YOUTUBE_COOKIES_FILE)
                    if cookies_path.exists():
                        ydl_opts['cookiefile'] = str(cookies_path)
                    else:
                        logger.warning(f"Configured cookies file not found: {settings.YOUTUBE_COOKIES_FILE}")
                        # Try browser cookies as fallback
                        try:
                            ydl_opts['cookiesfrombrowser'] = ('firefox', None)
                        except Exception:
                            pass
                else:
                    # Try to use cookies from browser as fallback
                    try:
                        ydl_opts['cookiesfrombrowser'] = ('firefox', None)
                    except Exception:
                        pass
                
                # Extract info first if metadata is requested
                metadata = None
                if extract_metadata:
                    try:
                        metadata_opts = {'quiet': True}
                        # Add cookies file if configured
                        if hasattr(settings, 'YOUTUBE_COOKIES_FILE') and settings.YOUTUBE_COOKIES_FILE:
                            cookies_path = Path(settings.YOUTUBE_COOKIES_FILE)
                            if cookies_path.exists():
                                metadata_opts['cookiefile'] = str(cookies_path)
                            else:
                                # Try browser cookies as fallback
                                try:
                                    metadata_opts['cookiesfrombrowser'] = ('firefox', None)
                                except Exception:
                                    pass
                        else:
                            # Try to use cookies from browser as fallback
                            try:
                                metadata_opts['cookiesfrombrowser'] = ('firefox', None)
                            except Exception:
                                pass

                        with yt_dlp.YoutubeDL(metadata_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            metadata = self._extract_metadata(info)
                    except Exception as e:
                        logger.warning(f"Failed to extract metadata: {e}")
                
                # Download the audio
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(temp_download_dir, file_id)
                if not downloaded_file:
                    raise FileNotFoundError("Downloaded file not found")
                
                # Move to output directory with proper filename
                final_filename = self._generate_filename(metadata, file_id, audio_format)
                final_path = self.output_dir / final_filename
                
                # Ensure output directory exists
                self.output_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file to final location (handles cross-device moves)
                shutil.move(downloaded_file, final_path)
                
                # Get file size
                file_size_mb = final_path.stat().st_size / (1024 * 1024)
                
                return {
                    'success': True,
                    'file_id': file_id,
                    'filename': final_filename,
                    'file_path': final_path,
                    'file_size_mb': round(file_size_mb, 2),
                    'metadata': metadata
                }
                
        except DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            return {
                'success': False,
                'error': f"Download failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def _extract_metadata(self, info: Dict[str, Any]) -> VideoMetadata:
        """Extract metadata from yt-dlp info"""
        return VideoMetadata(
            title=info.get('title'),
            duration=info.get('duration'),
            thumbnail_url=info.get('thumbnail'),
            uploader=info.get('uploader'),
            upload_date=info.get('upload_date'),
            view_count=info.get('view_count'),
            description=info.get('description', '')[:500] if info.get('description') else None
        )
    
    def _find_downloaded_file(self, directory: str, file_id: str) -> Optional[str]:
        """Find the downloaded file in the directory"""
        for filename in os.listdir(directory):
            if filename.startswith(file_id):
                return os.path.join(directory, filename)
        return None
    
    def _generate_filename(
        self,
        metadata: Optional[VideoMetadata],
        file_id: str,
        audio_format: str
    ) -> str:
        """Generate a safe filename for the downloaded audio"""
        if metadata and metadata.title:
            # Clean the title for use as filename
            safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_', '.', '(', ')')).strip()
            safe_title = safe_title[:200]  # Increased length limit for full titles
            filename = f"{safe_title}.{audio_format}"
        else:
            filename = f"audio_{file_id}.{audio_format}"

        return filename
