"""
Stem separation API routes
"""

import os
import logging
import tempfile
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.models.responses import StemSeparationResponse, StemFiles
from app.services.stem_service import StemSeparationService, SecurityError
from app.core.auth import verify_api_key
from app.core.cleanup import temp_file_manager, cleanup_file, register_cleanup_on_exit
from app.core.memory_management import (
    memory_monitor, streaming_handler, operation_limiter
)
from app.core.metrics import MetricsContext
from app.core.upload_validation import upload_validator

# Use Uvicorn's configured logger so logs reliably appear in journalctl/systemd.
logger = logging.getLogger("uvicorn.error")
router = APIRouter()

# Initialize limiter for this module
limiter = Limiter(key_func=get_remote_address) if settings.ENABLE_RATE_LIMITING else None


async def _schedule_stem_cleanup(stem_file_paths: List[str], delay_hours: int):
    """
    Background task to schedule cleanup of stem files after delay period
    
    Args:
        stem_file_paths: List of stem file paths to cleanup
        delay_hours: Hours to wait before cleanup
    """
    import asyncio
    from app.core.cleanup import cleanup_files
    
    # Wait for the specified delay
    await asyncio.sleep(delay_hours * 3600)
    
    # Clean up the files
    cleaned_count = cleanup_files(stem_file_paths)
    logger.info(f"Background cleanup removed {cleaned_count}/{len(stem_file_paths)} stem files")


@(limiter.limit(settings.RATE_LIMIT_HEAVY_OPERATIONS) if limiter else (lambda f: f))
@router.post(
    "/separate-stems",
    response_model=StemSeparationResponse,
    summary="Separate audio into stems",
    description="Upload an audio file and separate it into individual stems (vocals, drums, bass, other) using AI. Requires authentication when enabled.",
    dependencies=[Depends(verify_api_key)]
)
async def separate_stems(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to separate"),
    model: str = Form(default=settings.DEFAULT_DEMUCS_MODEL, description="Demucs model to use"),
    output_format: str = Form(default=settings.DEFAULT_STEM_FORMAT, description="Output format for stems"),
    stems: Optional[str] = Form(default=None, description="Comma-separated list of stems to extract (vocals,drums,bass,other). If empty or null, extracts all stems.")
) -> StemSeparationResponse:
    """
    Separate audio file into stems
    
    - **file**: Audio file to upload (MP3, WAV, FLAC, M4A, etc.)
    - **model**: Demucs model to use (htdemucs, htdemucs_ft, mdx_extra, etc.)
    - **output_format**: Output format for stems (wav, mp3, flac)
    - **stems**: Specific stems to extract (comma-separated: vocals,drums,bass,other). If empty or null, extracts all stems.
    
    Returns separated stem files and download URLs.
    """
    try:
        logger.info(f"Stem separation request received: model={model}, format={output_format}, stems={stems}")
        logger.info(f"File info: filename={file.filename}, content_type={file.content_type}")
        
        # Memory check before processing
        stats = memory_monitor.get_memory_stats()
        logger.info(f"Memory status - Available: {stats.available_memory_mb:.1f}MB, Process: {stats.process_memory_mb:.1f}MB")
        
        # Comprehensive file type and content validation
        is_valid, error_message = await upload_validator.validate_upload(file)
        if not is_valid:
            logger.warning(f"File validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file: {error_message}"
            )
        
        # Get file size after validation
        file_size = await upload_validator.validate_and_get_size(file)
        logger.info(f"File validation passed: {file.filename} ({file_size / (1024*1024):.2f}MB)")
        
        # Reset file position after validation
        await file.seek(0)
        
        # Stream upload to temporary file to avoid loading into memory
        temp_file_path = await streaming_handler.stream_upload_to_temp(file)
        
        # Register cleanup on exit to ensure cleanup even if process crashes
        register_cleanup_on_exit(str(temp_file_path))
        
        # Use context manager for guaranteed cleanup
        async with temp_file_manager(str(temp_file_path)) as managed_temp_path:
            try:
                # Validate model
                if model not in settings.supported_demucs_models_list:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported model. Supported: {settings.supported_demucs_models_list}"
                    )
                
                # Validate output format
                if output_format not in settings.SUPPORTED_STEM_FORMATS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported format. Supported: {settings.SUPPORTED_STEM_FORMATS}"
                    )
                
                # Parse stems list - default to all stems if empty/null
                requested_stems = None
                valid_stems = ['vocals', 'drums', 'bass', 'other']

                if stems and stems.strip():  # Check for non-empty string
                    requested_stems = [s.strip() for s in stems.split(',') if s.strip()]
                    for stem in requested_stems:
                        if stem not in valid_stems:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid stem '{stem}'. Valid stems: {valid_stems}"
                            )
                # If stems is None, empty string, or only whitespace, requested_stems remains None
                # This will default to all stems in the service layer
                
                # Process the separation with memory management
                stem_service = StemSeparationService()
                
                # Track processing time with metrics
                with MetricsContext("stem_separation"):
                    result = await stem_service.separate_stems(
                        audio_file_path=managed_temp_path,
                        model=model,
                        output_format=output_format,
                        stems=requested_stems,
                        original_filename=file.filename
                    )
                
                if not result['success']:
                    return StemSeparationResponse(
                        success=False,
                        error=result.get('error', 'Unknown error occurred')
                    )
                
                # Generate download URLs for stems
                stem_files = StemFiles()
                for stem_name, file_path in result['stem_files'].items():
                    download_url = f"/api/v1/download/{result['job_id']}/{os.path.basename(file_path)}"
                    setattr(stem_files, stem_name, download_url)
                
                # Schedule cleanup of generated stem files for later (after download period)
                background_tasks.add_task(
                    _schedule_stem_cleanup, 
                    list(result['stem_files'].values()),
                    settings.FILE_RETENTION_HOURS
                )
                
                return StemSeparationResponse(
                    success=True,
                    message="Stems separated successfully",
                    job_id=result['job_id'],
                    stems=stem_files,
                    processing_time_seconds=result['processing_time_seconds']
                )
                
            except SecurityError as e:
                # Handle security validation errors specifically
                logger.error(f"Security validation failed: {type(e).__name__}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters"
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in separate_stems: {type(e).__name__}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
        # temp_file_manager automatically cleans up the temporary file here
    
    except SecurityError as e:
        # Handle security validation errors specifically
        logger.error(f"Security validation failed: {type(e).__name__}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request parameters"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in separate_stems: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(e).__name__}"
        )


@limiter.limit(settings.RATE_LIMIT_INFO_OPERATIONS) if limiter else lambda f: f
@router.get(
    "/models",
    summary="Get available Demucs models",
    description="List all available Demucs models for stem separation. Requires authentication when enabled.",
    dependencies=[Depends(verify_api_key)]
)
async def get_available_models(request: Request):
    """
    Get list of available Demucs models
    
    Returns a list of supported models with descriptions.
    """
    models_info = {
        "htdemucs": {
            "name": "htdemucs",
            "description": "Hybrid Transformer Demucs - Best overall quality",
            "recommended": True
        },
        "htdemucs_ft": {
            "name": "htdemucs_ft",
            "description": "Fine-tuned Hybrid Transformer Demucs - Improved vocals",
            "recommended": False
        },
        "mdx_extra": {
            "name": "mdx_extra",
            "description": "MDX Extra - Good for electronic music",
            "recommended": False
        },
        "mdx_extra_q": {
            "name": "mdx_extra_q",
            "description": "MDX Extra Quantized - Faster processing",
            "recommended": False
        }
    }
    
    available_models = []
    for model in settings.supported_demucs_models_list:
        if model in models_info:
            available_models.append(models_info[model])
        else:
            available_models.append({
                "name": model,
                "description": f"Demucs model: {model}",
                "recommended": False
            })
    
    return {
        "success": True,
        "models": available_models,
        "default_model": settings.DEFAULT_DEMUCS_MODEL
    }


@router.get(
    "/formats",
    summary="Get supported output formats",
    description="List all supported output formats for stems. Requires authentication when enabled.",
    dependencies=[Depends(verify_api_key)]
)
async def get_supported_formats():
    """
    Get list of supported output formats
    
    Returns a list of supported audio formats for stem output.
    """
    formats_info = {
        "wav": {
            "format": "wav",
            "description": "WAV - Uncompressed, highest quality",
            "file_size": "Large",
            "recommended": True
        },
        "mp3": {
            "format": "mp3",
            "description": "MP3 - Compressed, good quality, smaller files",
            "file_size": "Medium",
            "recommended": False
        },
        "flac": {
            "format": "flac",
            "description": "FLAC - Lossless compression",
            "file_size": "Medium-Large",
            "recommended": False
        }
    }
    
    available_formats = []
    for format_name in settings.SUPPORTED_STEM_FORMATS:
        if format_name in formats_info:
            available_formats.append(formats_info[format_name])
        else:
            available_formats.append({
                "format": format_name,
                "description": f"Audio format: {format_name}",
                "file_size": "Unknown",
                "recommended": False
            })
    
    return {
        "success": True,
        "formats": available_formats,
        "default_format": settings.DEFAULT_STEM_FORMAT
    }
