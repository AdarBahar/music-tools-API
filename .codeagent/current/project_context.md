# Project Context

## Project paths and deployment context

**Repository**: `/Users/adar/Code/music-tools-API/`  
**Main Application**: `main.py` (FastAPI application)  
**API Base URL**: `http://localhost:8001` (Docker), `http://localhost:8000` (Direct)  
**Docker Service**: `music-tools-API` (port 8001:8000)  
**Dependencies**: Redis (container port 6379, host port 6380), Docker/Docker Compose  
**Data Volumes**: `./data/uploads`, `./data/outputs`, `./data/logs`  
**Environment**: `.env` file (mounted read-only in Docker)  
**Package Management**: `requirements.txt`, `pyproject.toml`  

## System Overview

Music Tools API is a standalone REST API service for audio processing that provides:

1. **YouTube to MP3 Conversion**: Convert YouTube videos to high-quality audio files with configurable quality and format options
2. **AI-Powered Audio Stem Separation**: Separate audio into vocals, drums, bass, and other instruments using Meta's Demucs models

## Current Architecture

- **Framework**: FastAPI with async support
- **Background Tasks**: Worker threads in the API process. Celery is listed as a dependency but not used.
- **AI Models**: Demucs (htdemucs, htdemucs_ft, mdx_extra, mdx_extra_q)
- **File Processing**: yt-dlp for YouTube downloads, Demucs for stem separation
- **Containerization**: Docker with docker-compose orchestration
- **File Management**: Automatic cleanup scheduler, configurable retention

## Key Features

- Clean filename generation using video titles (no random IDs)
- Smart stem naming preserving original filenames with suffixes
- GPU use depends on the PyTorch build and the host. The code sets no device.
- Multiple audio formats (mp3, m4a, wav, flac, aac, opus)
- No progress tracking. Jobs run in worker threads. The request waits until the job ends.
- Configurable quality settings (0-10 scale)
- Professional-grade output suitable for remixing

## Recent Status

- CodeAgent Kit integration completed (Feb 2, 2026)
- Project fully functional with Docker deployment
- Complete API documentation and examples available