"""
File upload validation utilities
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class UploadValidationError(Exception):
    """Raised when file upload validation fails"""
    pass


class FileUploadValidator:
    """Comprehensive file upload validation"""
    
    # Audio file magic numbers (first few bytes)
    AUDIO_SIGNATURES = {
        b'\xFF\xFB': 'MP3',
        b'\xFF\xF3': 'MP3',
        b'\xFF\xF2': 'MP3',
        b'RIFF': 'WAV',
        b'fLaC': 'FLAC',
        b'\x00\x00\x00\x20ftypM4A': 'M4A',
        b'\x00\x00\x00\x18ftypmp42': 'M4A',
        b'OggS': 'OGG',
        b'\x30\x26\xB2\x75\x8E\x66\xCF\x11': 'WMA'
    }
    
    def __init__(self):
        self.max_size_bytes = settings.MAX_FILE_SIZE_BYTES
        self.allowed_extensions = [ext.lower() for ext in settings.ALLOWED_AUDIO_EXTENSIONS]
        self.allowed_mime_types = [mime.lower() for mime in settings.ALLOWED_MIME_TYPES]
    
    async def validate_upload(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive upload validation
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # 1. Basic file object validation
            if not file or not file.filename:
                return False, "No file provided or filename missing"
            
            # 2. File extension validation
            file_ext = Path(file.filename).suffix.lower()
            if not file_ext:
                return False, "File must have a valid extension"
            
            if file_ext not in self.allowed_extensions:
                return False, f"Unsupported file extension '{file_ext}'. Allowed: {', '.join(self.allowed_extensions)}"
            
            # 3. MIME type validation
            content_type = getattr(file, 'content_type', None)
            if content_type:
                content_type_lower = content_type.lower()
                if content_type_lower not in self.allowed_mime_types:
                    return False, f"Unsupported file type '{content_type}'. Allowed audio files only."
            
            # 4. File size validation (if available)
            if hasattr(file, 'size') and file.size is not None:
                if file.size > self.max_size_bytes:
                    return False, f"File too large ({file.size / (1024*1024):.1f}MB). Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
                
                if file.size == 0:
                    return False, "File is empty"
            
            # 5. Content validation (magic number check)
            await self._validate_file_content(file)
            
            logger.info(f"File upload validation passed: {file.filename} ({file_ext}, {content_type})")
            return True, None
            
        except UploadValidationError as e:
            logger.warning(f"File upload validation failed: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error during file validation: {e}")
            return False, "File validation failed due to internal error"
    
    async def _validate_file_content(self, file: UploadFile) -> None:
        """
        Validate file content by reading magic numbers
        
        Args:
            file: UploadFile to validate
            
        Raises:
            UploadValidationError: If content validation fails
        """
        try:
            # Save current position
            current_pos = await file.seek(0)
            
            # Read first 32 bytes for magic number detection
            header = await file.read(32)
            
            # Reset file position
            await file.seek(0)
            
            if not header or len(header) < 4:
                raise UploadValidationError("File appears to be empty or corrupted")
            
            # Check for known audio file signatures
            is_valid_audio = False
            detected_type = "Unknown"
            
            for signature, file_type in self.AUDIO_SIGNATURES.items():
                if header.startswith(signature) or signature in header[:16]:
                    is_valid_audio = True
                    detected_type = file_type
                    break
            
            # Additional checks for specific formats
            if not is_valid_audio:
                # Check for MP4/M4A containers with different signatures
                if b'ftyp' in header[:12]:
                    is_valid_audio = True
                    detected_type = "M4A/MP4"
                # Check for ID3 tagged MP3 files
                elif header.startswith(b'ID3'):
                    is_valid_audio = True
                    detected_type = "MP3 (ID3)"
            
            if not is_valid_audio:
                # Log the header for debugging
                header_hex = header[:16].hex() if header else "empty"
                logger.warning(f"Unknown file signature: {header_hex}")
                raise UploadValidationError(
                    f"File does not appear to be a valid audio file. "
                    f"Please upload MP3, WAV, FLAC, M4A, or other supported audio formats."
                )
            
            logger.debug(f"File content validation passed: detected {detected_type} format")
            
        except UploadValidationError:
            raise
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            raise UploadValidationError("Unable to validate file content")
    
    async def validate_and_get_size(self, file: UploadFile) -> int:
        """
        Validate file and determine actual size by reading content
        
        Args:
            file: UploadFile to validate and measure
            
        Returns:
            File size in bytes
            
        Raises:
            HTTPException: If validation fails
        """
        # First run standard validation
        is_valid, error_msg = await self.validate_upload(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # If size is not available, calculate it by reading the file
        if not hasattr(file, 'size') or file.size is None:
            try:
                # Save current position
                await file.seek(0)
                
                # Read file in chunks to measure size
                total_size = 0
                chunk_size = 8192  # 8KB chunks
                
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    total_size += len(chunk)
                    
                    # Check size limit during reading
                    if total_size > self.max_size_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large (>{total_size / (1024*1024):.1f}MB). Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
                        )
                
                # Reset file position for later use
                await file.seek(0)
                
                return total_size
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error measuring file size: {e}")
                raise HTTPException(status_code=400, detail="Unable to validate file size")
        
        return file.size


# Global validator instance
upload_validator = FileUploadValidator()


def validate_file_extension(filename: str) -> bool:
    """
    Quick file extension validation utility
    
    Args:
        filename: Name of file to validate
        
    Returns:
        True if extension is allowed
    """
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in [ext.lower() for ext in settings.ALLOWED_AUDIO_EXTENSIONS]


def get_content_type_from_extension(filename: str) -> str:
    """
    Get appropriate content type from file extension
    
    Args:
        filename: Name of file
        
    Returns:
        MIME type string
    """
    ext = Path(filename).suffix.lower() if filename else ""
    
    ext_to_mime = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".opus": "audio/opus",
        ".wma": "audio/x-ms-wma"
    }
    
    return ext_to_mime.get(ext, "application/octet-stream")