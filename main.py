"""
Music Tools API - Standalone Audio Processing Service

A complete REST API service for YouTube to MP3 conversion and AI-powered audio stem separation.
This service provides high-quality audio processing capabilities with a simple REST interface.

Features:
- YouTube to MP3 conversion with configurable quality
- AI-powered audio stem separation using Meta's Demucs
- Multiple audio format support
- Background task processing
- Automatic file cleanup
- Docker containerization support

Author: Adar Bahar
License: MIT
Version: 1.0.0
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api.routes import youtube, stems, downloads
from app.core.config import settings
from app.core.cleanup import start_cleanup_scheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Music Tools API Service...")
    
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    logger.info(f"API Service started on {settings.API_HOST}:{settings.API_PORT}")
    yield
    
    # Shutdown
    logger.info("Shutting down Music Tools API Service...")


# Create FastAPI app
app = FastAPI(
    title="Music Tools API",
    description="""
    A standalone REST API service for audio processing that provides:

    🎵 **YouTube to MP3 Conversion**
    - Convert YouTube videos to high-quality MP3 files
    - Multiple audio format support (mp3, m4a, wav, flac, aac, opus)
    - Configurable audio quality and metadata extraction

    🎛️ **AI-Powered Audio Stem Separation**
    - Separate audio into vocals, drums, bass, and other instruments
    - Multiple Demucs model support for different use cases
    - GPU acceleration support for faster processing

    📊 **Features**
    - Real-time progress tracking
    - Automatic file cleanup
    - Background task processing
    - Comprehensive error handling
    """,
    version="1.0.0",
    contact={
        "name": "Adar Bahar",
        "url": "https://github.com/AdarBahar/music-tools-api",
        "email": "adar@bahar.co.il",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(youtube.router, prefix="/api/v1", tags=["YouTube"])
app.include_router(stems.router, prefix="/api/v1", tags=["Stem Separation"])
app.include_router(downloads.router, prefix="/api/v1", tags=["Downloads"])

# Mount static files for downloads
app.mount("/static", StaticFiles(directory=settings.OUTPUT_DIR), name="static")


@app.get("/")
async def root():
    """
    Root endpoint with API information

    Returns basic information about the Music Tools API service including
    available endpoints and documentation links.
    """
    return {
        "name": "Music Tools API",
        "description": "Standalone audio processing service for YouTube to MP3 conversion and AI-powered stem separation",
        "version": "1.0.0",
        "status": "running",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "youtube_to_mp3": "/api/v1/youtube-to-mp3",
            "youtube_info": "/api/v1/youtube-info",
            "separate_stems": "/api/v1/separate-stems",
            "download": "/api/v1/download/{file_id}",
            "health": "/health",
            "stats": "/api/v1/stats"
        },
        "features": [
            "YouTube to MP3 conversion",
            "AI-powered audio stem separation",
            "Multiple audio format support",
            "Background task processing",
            "Automatic file cleanup"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "music-tools-api"}


def main():
    """
    Main entry point for the Music Tools API service.

    This function can be called directly or used as a console script entry point.
    It starts the FastAPI application using Uvicorn with configuration from settings.
    """
    import uvicorn

    logger.info("Starting Music Tools API service...")
    logger.info(f"Configuration: Host={settings.API_HOST}, Port={settings.API_PORT}, Debug={settings.DEBUG}")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )


if __name__ == "__main__":
    main()
