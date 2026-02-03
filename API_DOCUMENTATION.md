# Music Tools API Documentation

## Overview

The Music Tools API provides REST endpoints for YouTube to MP3 conversion and audio stem separation using AI. The API is built with FastAPI and provides automatic interactive documentation.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Authentication

The API supports optional API key authentication. By default, authentication is disabled. For production use, enable API key authentication by setting `REQUIRE_API_KEY=true` in the environment and providing `VALID_API_KEYS` with comma-separated keys. All authenticated requests must include the `X-API-Key` header.

**Note:** Sensitive API documentation (`/docs`, `/redoc`, `/openapi.json`) is automatically disabled in production when `DEBUG=false`.

## Rate Limiting

The API includes rate limiting via slowapi. Different operation types have different limits:
- **Light operations** (health checks, info queries): Higher rate limit
- **Heavy operations** (conversions, stem separation): Lower rate limit

Rate limiting can be enabled/disabled via `ENABLE_RATE_LIMITING=true` in the environment. Limits are enforced per client IP address or API key hash in production.

## File Naming Convention

The API uses intelligent file naming to make downloads easy to organize and identify.

### YouTube Downloads

Files are named using the video title for immediate recognition:

- **Format**: `{Video Title}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3`
- **Benefits**: No random UUIDs, human-readable filenames

### Stem Separation

Stem files preserve the relationship with their source:

- **With Original Filename**: `{Original Filename} - {stem_type}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3`
- **Fallback**: `{stem_type}.{format}` (when no original filename available)
- **Stem Types**: vocals, drums, bass, other

### Character Sanitization

For filesystem compatibility, the following rules apply:

- **Allowed Characters**: Letters, numbers, spaces, hyphens (-), underscores (_), periods (.), parentheses ()
- **Removed Characters**: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
- **Length Limit**: Filenames are truncated to 200 characters maximum
- **Encoding**: UTF-8 compatible

### Examples

| Input | Output Filename |
|-------|----------------|
| `Song: Title/Mix` | `Song Title Mix.mp3` |
| `Artist - Song (Official Video)` | `Artist - Song (Official Video).mp3` |
| `Very Long Title That Exceeds...` | `Very Long Title That Exceeds The Character Limit And Gets Truncated Properly To Avoid Filesystem Issues While Still Maintaining Readability And Usefulness For The End User Who Wants To Identify Their Downloaded Files Easily.mp3` |

## Endpoints

### Health Check

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "music-tools-api"
}
```

### YouTube to MP3 Conversion

#### POST /api/v1/youtube-to-mp3
Convert a YouTube video to MP3 format.

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
- `url` (required): YouTube video URL
- `audio_quality` (optional): Audio quality 0-10 (0=best, 10=worst, default: 0)
- `audio_format` (optional): Output format (mp3, m4a, wav, flac, aac, opus, default: mp3)
- `extract_metadata` (optional): Extract video metadata (default: true)

#### Audio Quality Reference

The `audio_quality` parameter accepts integer values from 0 to 10:

| Value | Quality Level | Typical Bitrate | File Size (4min) | Use Case |
|-------|---------------|----------------|------------------|----------|
| 0     | Best          | ~320 kbps      | ~9-10 MB        | Archival, audiophiles |
| 1     | Excellent     | ~280 kbps      | ~8-9 MB         | High-end listening |
| 2     | Very High     | ~256 kbps      | ~7-8 MB         | Premium quality |
| 3     | High          | ~224 kbps      | ~6-7 MB         | High quality listening |
| 4     | Good          | ~192 kbps      | ~5-6 MB         | Good quality |
| 5     | Default       | ~160 kbps      | ~4-5 MB         | General use (balanced) |
| 6     | Acceptable    | ~128 kbps      | ~3-4 MB         | Standard quality |
| 7     | Lower         | ~112 kbps      | ~3 MB           | Mobile, streaming |
| 8     | Poor          | ~96 kbps       | ~2-3 MB         | Low bandwidth |
| 9     | Very Poor     | ~80 kbps       | ~2 MB           | Very low bandwidth |
| 10    | Worst         | ~64 kbps       | ~2 MB           | Voice, podcasts only |

**Quality Examples:**
```json
// Best quality (recommended for music)
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "audio_quality": 0,
  "audio_format": "mp3"
}

// Balanced quality/size (default)
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "audio_quality": 5,
  "audio_format": "mp3"
}

// Small file size (for mobile/streaming)
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "audio_quality": 8,
  "audio_format": "mp3"
}
```

#### Supported Audio Formats

The `audio_format` parameter supports the following formats:

| Format | Extension | Description | Quality | File Size |
|--------|-----------|-------------|---------|-----------|
| `mp3`  | .mp3      | MPEG Audio Layer 3 (default) | Good | Medium |
| `m4a`  | .m4a      | MPEG-4 Audio | Very Good | Medium |
| `wav`  | .wav      | Waveform Audio File | Lossless | Large |
| `flac` | .flac     | Free Lossless Audio Codec | Lossless | Large |
| `aac`  | .aac      | Advanced Audio Coding | Good | Small |
| `opus` | .opus     | Opus Audio Codec | Excellent | Small |

**Format Recommendations:**
- **MP3**: Universal compatibility, good quality/size balance
- **M4A**: Better quality than MP3 at same bitrate, Apple ecosystem
- **FLAC**: Lossless quality, larger files, audiophile choice
- **WAV**: Uncompressed, largest files, studio quality
- **AAC**: Good for mobile devices, smaller files
- **OPUS**: Best quality/size ratio, modern codec

**Response:**
```json
{
  "success": true,
  "message": "Audio downloaded and converted successfully",
  "file_id": "abc123-def456-ghi789",
  "filename": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3",
  "file_size_mb": 3.45,
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
    "duration": 213,
    "thumbnail_url": "https://...",
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1234567890,
    "description": "The official video for..."
  },
  "download_url": "/api/v1/download/abc123-def456-ghi789"
}
```

#### Filename Convention

YouTube downloads use the video title as the filename for easy identification:
- **Format**: `{Video Title}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster).mp3`
- **Character Sanitization**: Special characters are removed for filesystem compatibility
- **Length Limit**: Titles are truncated to 200 characters if needed

#### GET /api/v1/youtube-info
Get YouTube video information without downloading.

**Parameters:**
- `url` (required): YouTube video URL

**Response:**
```json
{
  "success": true,
  "info": {
    "title": "Video Title",
    "duration": 213,
    "thumbnail": "https://...",
    "uploader": "Channel Name",
    "upload_date": "20091025",
    "view_count": 1234567890,
    "description": "Video description...",
    "formats_available": 25,
    "audio_formats": [...]
  }
}
```

### Stem Separation

#### POST /api/v1/separate-stems
Separate an audio file into individual stems using AI-powered source separation.

**Request:** Multipart form data
- `file` (required): Audio file to upload (MP3, WAV, FLAC, M4A, AAC, OPUS)
- `model` (optional): Demucs model to use (default: htdemucs)
- `output_format` (optional): Output format for stems (default: mp3)
- `stems` (optional): Comma-separated stems to extract (vocals,drums,bass,other). **Defaults to all stems if empty or null.**

#### Supported Demucs Models

| Model | Description | Best For | Recommended |
|-------|-------------|----------|-------------|
| `htdemucs` | Hybrid Transformer Demucs | General music, best overall quality | ✅ **Default** |
| `htdemucs_ft` | Fine-tuned Hybrid Transformer | Vocal-heavy tracks, improved vocals | ⭐ Vocals |
| `mdx_extra` | MDX Extra | Electronic music, EDM | 🎵 Electronic |
| `mdx_extra_q` | MDX Extra Quantized | Faster processing, good quality | ⚡ Speed |

#### Model Selection Guide

**For Vocal Separation:**
- Primary: `htdemucs_ft` (fine-tuned for vocals)
- Alternative: `htdemucs` (excellent overall)

**For Electronic/EDM Music:**
- Primary: `mdx_extra` (optimized for electronic)
- Fast option: `mdx_extra_q` (quantized, faster)

**For Rock/Pop/General Music:**
- Primary: `htdemucs` (best overall quality)
- Alternative: `htdemucs_ft` (if vocals are priority)

**For Speed Priority:**
- Primary: `mdx_extra_q` (fastest processing)
- Alternative: Any model with specific stems only

#### Output Formats

| Format | Quality | File Size | Use Case |
|--------|---------|-----------|----------|
| `wav` | Uncompressed, highest quality | Large | Professional/studio work |
| `mp3` | Compressed, good quality | Medium | General use (default) |
| `flac` | Lossless compression | Medium-Large | Archival quality |

#### Stem Types
All models separate audio into 4 stems:
- **`vocals`**: Lead and backing vocals
- **`drums`**: Drum kit and percussion
- **`bass`**: Bass guitar and low-frequency instruments
- **`other`**: All other instruments (guitars, keyboards, etc.)

#### Processing Times
- **Small file (3-4 min)**: 2-5 minutes
- **Medium file (5-8 min)**: 5-10 minutes
- **Large file (10+ min)**: 10-20 minutes
- **GPU acceleration**: 3-5x faster (if available)

#### Example Requests

**Basic separation (all stems):**
```bash
curl -X POST "http://localhost:8001/api/v1/separate-stems" \
  -F "file=@your-audio.mp3" \
  -F "model=htdemucs" \
  -F "output_format=mp3"
```

**Vocals only (faster):**
```bash
curl -X POST "http://localhost:8001/api/v1/separate-stems" \
  -F "file=@your-audio.mp3" \
  -F "model=htdemucs_ft" \
  -F "output_format=wav" \
  -F "stems=vocals"
```

**Electronic music optimized:**
```bash
curl -X POST "http://localhost:8001/api/v1/separate-stems" \
  -F "file=@your-edm-track.mp3" \
  -F "model=mdx_extra" \
  -F "output_format=flac" \
  -F "stems=vocals,drums,bass,other"
```

**Response:**
```json
{
  "success": true,
  "message": "Stems separated successfully",
  "job_id": "def456-ghi789-jkl012",
  "stems": {
    "vocals": "/api/v1/download/def456-ghi789-jkl012/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3",
    "drums": "/api/v1/download/def456-ghi789-jkl012/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - drums.mp3",
    "bass": "/api/v1/download/def456-ghi789-jkl012/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - bass.mp3",
    "other": "/api/v1/download/def456-ghi789-jkl012/Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - other.mp3"
  },
  "processing_time_seconds": 127.45
}
```

#### Stem Parameter Behavior

The `stems` parameter controls which stems to extract:

- **Default Behavior**: If `stems` is empty, null, or omitted, **all stems are extracted** (vocals, drums, bass, other)
- **Specific Stems**: Provide comma-separated values to extract only specific stems
- **Valid Values**: vocals, drums, bass, other

**Examples:**
```bash
# Extract all stems (default behavior)
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "model=htdemucs"

# Extract only vocals
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "stems=vocals"

# Extract vocals and drums only
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@audio.mp3" \
  -F "stems=vocals,drums"
```

#### Stem Filename Convention

Stem files are named to preserve the relationship with their source file:
- **Format**: `{Original Filename} - {stem_type}.{format}`
- **Example**: `Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) - vocals.mp3`
- **Fallback**: If no original filename is available, uses `{stem_type}.{format}` (e.g., `vocals.mp3`)
- **Stem Types**: vocals, drums, bass, other

#### GET /api/v1/models
Get available Demucs models with descriptions and recommendations.

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "name": "htdemucs",
      "description": "Hybrid Transformer Demucs - Best overall quality",
      "recommended": true
    },
    {
      "name": "htdemucs_ft",
      "description": "Fine-tuned Hybrid Transformer Demucs - Improved vocals",
      "recommended": false
    },
    {
      "name": "mdx_extra",
      "description": "MDX Extra - Good for electronic music",
      "recommended": false
    },
    {
      "name": "mdx_extra_q",
      "description": "MDX Extra Quantized - Faster processing",
      "recommended": false
    }
  ],
  "default_model": "htdemucs"
}
```

#### GET /api/v1/formats
Get supported output formats for stem separation.

**Response:**
```json
{
  "success": true,
  "formats": [
    {
      "format": "wav",
      "description": "WAV - Uncompressed, highest quality",
      "file_size": "Large",
      "recommended": true
    },
    {
      "format": "mp3",
      "description": "MP3 - Compressed, good quality, smaller files",
      "file_size": "Medium",
      "recommended": false
    },
    {
      "format": "flac",
      "description": "FLAC - Lossless compression",
      "file_size": "Medium-Large",
      "recommended": false
    }
  ],
  "default_format": "mp3"
}
```

#### GET /api/v1/formats
Get supported output formats.

**Response:**
```json
{
  "success": true,
  "formats": [
    {
      "format": "wav",
      "description": "WAV - Uncompressed, highest quality",
      "file_size": "Large",
      "recommended": true
    },
    {
      "format": "mp3",
      "description": "MP3 - Compressed, good quality, smaller files",
      "file_size": "Medium",
      "recommended": false
    }
  ],
  "default_format": "mp3"
}
```

### File Downloads

#### GET /api/v1/download/{file_id}
Download a converted audio file.

**Parameters:**
- `file_id`: Unique file identifier from conversion

**Response:** Binary audio file

#### GET /api/v1/download/{job_id}/{filename}
Download a specific stem file.

**Parameters:**
- `job_id`: Job identifier from stem separation
- `filename`: Name of the stem file (e.g., "Song Title - vocals.mp3" or "vocals.mp3")

**Response:** Binary audio file

#### GET /api/v1/download/{file_id}/info
Get file information.

**Response:**
```json
{
  "file_id": "abc123-def456-ghi789",
  "filename": "audio_file.mp3",
  "file_size_mb": 3.45,
  "content_type": "audio/mpeg",
  "created_at": "1634567890.123"
}
```

### Storage Management

#### GET /api/v1/stats
Get storage statistics.

**Response:**
```json
{
  "directories": {
    "uploads": {
      "exists": true,
      "file_count": 5,
      "total_size_mb": 25.67,
      "oldest_file_age_hours": 12.5
    },
    "outputs": {
      "exists": true,
      "file_count": 15,
      "total_size_mb": 156.78,
      "oldest_file_age_hours": 8.2
    },
    "temp": {
      "exists": true,
      "file_count": 0,
      "total_size_mb": 0,
      "oldest_file_age_hours": 0
    }
  },
  "total_files": 20,
  "total_size_mb": 182.45,
  "cleanup_info": {
    "cleanup_interval_hours": 24,
    "file_retention_hours": 48,
    "max_file_size_mb": 100
  }
}
```

#### POST /api/v1/cleanup
Trigger manual cleanup of old files.

**Response:**
```json
{
  "success": true,
  "message": "Cleanup completed. Removed 5 files.",
  "details": {
    "uploads": {
      "removed_files": 2,
      "status": "success"
    },
    "outputs": {
      "removed_files": 3,
      "status": "success"
    },
    "temp": {
      "removed_files": 0,
      "status": "success"
    }
  }
}
```

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "success": false,
  "error": "Error description",
  "details": {
    "additional": "error details"
  }
}
```

Common HTTP status codes:
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (file not found)
- `413`: Payload Too Large (file too big)
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

## File Size Limits

- Maximum upload size: 100MB (configurable)
- Supported audio formats: MP3, WAV, FLAC, M4A, AAC, OGG

## Processing Times

- YouTube downloads: 10-60 seconds
- Stem separation: 2-10 minutes (depends on audio length and hardware)
- GPU acceleration significantly improves stem separation speed

## Configuration

Environment variables:
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 100)
- `CLEANUP_INTERVAL_HOURS`: Cleanup interval (default: 24)
- `FILE_RETENTION_HOURS`: File retention period (default: 48)
- `DEFAULT_DEMUCS_MODEL`: Default separation model (default: htdemucs)

## Examples

See the `examples/` directory for:
- `test_api.py`: Python test script
- `python_client.py`: Python client library
- `curl_examples.sh`: cURL command examples
