# Music Tools API

A complete, standalone REST API service for audio processing that provides YouTube to MP3 conversion and AI-powered audio stem separation functionality. This project is fully self-contained and ready to deploy without any external dependencies.

## 🚀 Features

### 🎵 YouTube to MP3 Conversion
- Convert YouTube videos to high-quality MP3 files
- Configurable audio quality (0-10, where 0 is best)
- Multiple audio format support (mp3, m4a, wav, flac, aac, opus)
- Automatic metadata extraction (title, duration, thumbnail, uploader)
- **Clean filename generation** using video titles (no random IDs)
- Real-time progress tracking for downloads
- Support for playlists and individual videos

### 🎛️ AI-Powered Audio Stem Separation
- Advanced audio source separation using Meta's Demucs AI models
- Separate any audio into: **vocals**, **drums**, **bass**, and **other instruments**
- **4 specialized models** optimized for different music types and use cases
- Configurable output formats (wav, mp3, flac) with quality options
- **Smart stem naming** that preserves original filename with stem suffix
- Selective stem extraction (extract only specific instruments)
- GPU acceleration support for faster processing (3-5x speedup)
- Professional-grade quality suitable for remixing and analysis

## API Endpoints

### YouTube to MP3
```
POST /api/v1/youtube-to-mp3
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "audio_quality": 0,
  "audio_format": "mp3",
  "extract_metadata": true
}
```

**Parameters:**
- `url`: YouTube video URL (required)
- `audio_quality`: Integer 0-10 (0=best quality, 10=worst quality, default: 0)
- `audio_format`: Output format - mp3, m4a, wav, flac, aac, opus (default: mp3)
- `extract_metadata`: Extract video metadata (default: true)

> 📖 **Detailed Quality Guide**: See [API Documentation](API_DOCUMENTATION.md#audio-quality-reference) for complete audio quality and format specifications.

**Response:**
```json
{
  "success": true,
  "file_id": "abc123",
  "filename": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3",
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
    "duration": 213,
    "thumbnail_url": "https://...",
    "uploader": "Rick Astley"
  },
  "download_url": "/api/v1/download/abc123"
}
```

> 💡 **Filename Format**: Files are named using the video title for easy identification. Special characters are sanitized for filesystem compatibility.

### Audio Stem Separation
```
POST /api/v1/separate-stems
```

**Request:** Multipart form data
```bash
curl -X POST "http://localhost:8001/api/v1/separate-stems" \
  -F "file=@your-audio.mp3" \
  -F "model=htdemucs" \
  -F "output_format=mp3"
  # Note: stems parameter omitted - defaults to all stems (vocals,drums,bass,other)
```

**Parameters:**
- `file`: Audio file to upload (required) - MP3, WAV, FLAC, M4A, AAC, OPUS
- `model`: AI model to use (default: htdemucs)
- `output_format`: Output format - wav, mp3, flac (default: mp3)
- `stems`: Specific stems to extract - vocals, drums, bass, other (default: all stems if empty/null)

#### Available AI Models

| Model | Best For | Quality | Speed |
|-------|----------|---------|-------|
| `htdemucs` | General music (default) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| `htdemucs_ft` | Vocal separation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| `mdx_extra` | Electronic/EDM music | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| `mdx_extra_q` | Fast processing | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Quick Model Selection:**
- **Vocals**: Use `htdemucs_ft` for best vocal isolation
- **Electronic**: Use `mdx_extra` for EDM/electronic music
- **General**: Use `htdemucs` for rock, pop, and most music
- **Speed**: Use `mdx_extra_q` for fastest processing

**Response:**
```json
{
  "success": true,
  "job_id": "def456",
  "stems": {
    "vocals": "/api/v1/download/def456/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3",
    "drums": "/api/v1/download/def456/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - drums.mp3",
    "bass": "/api/v1/download/def456/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - bass.mp3",
    "other": "/api/v1/download/def456/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - other.mp3"
  },
  "processing_time_seconds": 127.5
}
```

> 💡 **Stem Naming**: When separating stems from uploaded files, the original filename is preserved with the stem type appended (e.g., `Song Title - vocals.mp3`). This makes it easy to identify which stems belong to which source file.

> 📖 **Complete Model Guide**: See [API Documentation](API_DOCUMENTATION.md#stem-separation) for detailed model comparisons, processing times, and advanced usage examples.

### Model & Format Discovery
```
GET /api/v1/models     # Get available AI models
GET /api/v1/formats    # Get supported output formats
```

**Get Available Models:**
```bash
curl http://localhost:8001/api/v1/models
# Returns: List of Demucs models with descriptions and recommendations
```

**Get Supported Formats:**
```bash
curl http://localhost:8001/api/v1/formats
# Returns: List of output formats with quality and file size info
```

### File Download
```
GET /api/v1/download/{file_id}
GET /api/v1/download/{job_id}/{stem_name}
```

Download converted audio files or separated stems.

## 📁 File Naming Convention

The API uses intelligent file naming to make your downloads easy to organize and identify:

### YouTube Downloads
- **Format**: `{Video Title}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3`
- **Benefits**: No random IDs, immediately recognizable filenames

### Stem Separation
- **Format**: `{Original Filename} - {stem_type}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3`
- **Fallback**: If no original filename is available, uses `{stem_type}.{format}`

### Character Handling
- Special characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) are removed for filesystem compatibility
- Preserves spaces, hyphens, underscores, periods, and parentheses
- Long titles are truncated to 200 characters to avoid filesystem limits

## 🚀 Quick Start

### Option 1: Docker (Recommended)
The easiest way to get started is with Docker:

```bash
# Clone the repository
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API

# Start the service
docker-compose up -d

# Check if it's running
curl http://localhost:8001/health
```

**If you get port conflicts:**
```bash
# Run the port conflict resolver
./scripts/fix-port-conflicts.sh

# Or manually resolve:
# 1. If Redis port 6379 is in use, the Docker setup uses port 6380 externally
# 2. Update .env file: REDIS_URL=redis://localhost:6380/0
# 3. Start again: docker-compose up -d
```

### Option 2: Manual Installation

#### Prerequisites
- Python 3.8 or higher
- FFmpeg installed on your system
- Redis server (for background tasks)

#### Installation Steps
```bash
# 1. Clone the repository
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env file as needed

# 5. Start Redis (if not using Docker)
redis-server

# 6. Run the API
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

Once the service is running, you can access the interactive documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

> **Note**: If running manually (not with Docker), use port 8000 instead of 8001.

### Production API

The API is deployed and available at:
- **Base URL**: https://apitools.bahar.co.il
- **Swagger UI**: https://apitools.bahar.co.il/docs
- **Health Check**: https://apitools.bahar.co.il/health

## 🔐 Authentication

The API uses API key authentication. Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://apitools.bahar.co.il/api/v1/youtube-to-mp3 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

See [Authentication Guide](.codeagent/docs/authentication.md) for detailed setup instructions.

## 🔌 Integration Guide

For integrating the API into your applications, see the comprehensive [Integration Guide](.codeagent/docs/app_integration.md) which includes:

- Complete Node.js client implementation
- All endpoint documentation with request/response schemas
- Error handling and retry logic
- Rate limiting guidance
- Best practices for production use

## ⚙️ Configuration

The service can be configured using environment variables. Copy `.env.example` to `.env` and modify as needed:

### Core Settings
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: false)

### File Management
- `MAX_FILE_SIZE_MB`: Maximum upload size in MB (default: 100)
- `CLEANUP_INTERVAL_HOURS`: File cleanup interval (default: 24)
- `FILE_RETENTION_HOURS`: How long to keep files (default: 48)

### Audio Processing
- `DEFAULT_AUDIO_QUALITY`: YouTube download quality 0-10 (default: 0)
- `DEFAULT_AUDIO_FORMAT`: Default audio format (default: mp3)
- `DEFAULT_DEMUCS_MODEL`: AI model for stem separation (default: htdemucs)
- `DEFAULT_STEM_FORMAT`: Output format for stems (default: mp3)

### Background Tasks
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB (8GB+ recommended for stem separation)
- **Storage**: 10GB free space (for temporary files and AI models)
- **OS**: Linux, macOS, or Windows

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **GPU**: NVIDIA GPU with CUDA support (optional, significantly speeds up stem separation)
- **Storage**: SSD with 50GB+ free space

### Software Dependencies
- **Python**: 3.8 or higher
- **FFmpeg**: For audio processing
- **Redis**: For background task queue
- **Docker**: For containerized deployment (optional)

## 🔧 Installation Details

### Installing FFmpeg

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
Download from https://ffmpeg.org/ and add to PATH

### Installing Redis

#### macOS
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

#### Windows
Download from https://redis.io/ or use Docker

## 📊 Performance Notes

- **First Run**: Downloads ~2GB of AI models automatically
- **YouTube Downloads**: 10-60 seconds depending on video length and quality
- **Stem Separation**: 2-10 minutes depending on audio length and hardware
- **GPU Acceleration**: Can reduce stem separation time by 5-10x
- **Concurrent Processing**: Supports multiple simultaneous requests

## � Production Deployment

For deploying to a production server (Hetzner, AWS, DigitalOcean, etc.), see the [Deployment Guide](.codeagent/docs/hetzner_fastapi_deployment.md) which covers:

- Creating a dedicated user for isolation
- Setting up Python virtual environment
- Configuring systemd service
- Nginx reverse proxy setup
- SSL certificate with Let's Encrypt
- Firewall configuration
- Security best practices

## 📋 Additional Documentation

| Document | Description |
|----------|-------------|
| [Deployment Guide](.codeagent/docs/hetzner_fastapi_deployment.md) | Production server setup |
| [Integration Guide](.codeagent/docs/app_integration.md) | API integration with Node.js examples |
| [Authentication](.codeagent/docs/authentication.md) | API key management |
| [Logs Guide](.codeagent/docs/logs.md) | Accessing and analyzing logs |
| [API Documentation](API_DOCUMENTATION.md) | Detailed API reference |

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
