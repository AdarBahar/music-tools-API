"""
Stem separation API routes
"""

import os
import logging
import tempfile
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.responses import StemSeparationResponse, StemFiles
from app.services.stem_service import StemSeparationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/separate-stems",
    response_model=StemSeparationResponse,
    summary="Separate audio into stems",
    description="Upload an audio file and separate it into individual stems (vocals, drums, bass, other) using AI"
)
async def separate_stems(
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
        # Validate file size
        if file.size and file.size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Validate model
        if model not in settings.SUPPORTED_DEMUCS_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported model. Supported: {settings.SUPPORTED_DEMUCS_MODELS}"
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
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process the separation
            stem_service = StemSeparationService()
            result = stem_service.separate_stems(
                audio_file_path=temp_file_path,
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
            
            return StemSeparationResponse(
                success=True,
                message="Stems separated successfully",
                job_id=result['job_id'],
                stems=stem_files,
                processing_time_seconds=result['processing_time_seconds']
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in separate_stems: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/models",
    summary="Get available Demucs models",
    description="List all available Demucs models for stem separation"
)
async def get_available_models():
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
    for model in settings.SUPPORTED_DEMUCS_MODELS:
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
    description="List all supported output formats for stems"
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
