# Music Tools API Documentation

## Overview

The Music Tools API has REST endpoints for two tasks:

- It downloads the audio of a YouTube video.
- It separates an uploaded audio file into stems (vocals, drums, bass, and other) with Demucs.

The examples in this document use port 8000, the port of a manual run. Docker Compose publishes the API on host port 8001.

## Base URL

Docker Compose maps the API to host port 8001. A manual run (`python main.py`) uses port 8000.

```
http://localhost:8000
```

## Interactive documentation

The Swagger UI, ReDoc, and the OpenAPI schema exist only when `DEBUG=true`. Otherwise they return HTTP 404.

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

## Authentication

API key checks are off by default (`REQUIRE_API_KEY=false`). To turn them on, set `REQUIRE_API_KEY=true` and set `VALID_API_KEYS` to a comma-separated list of keys. Send a key in the `X-API-Key` header.

When checks are on, these routes require a valid key:

- `POST /api/v1/youtube-to-mp3` and `GET /api/v1/youtube-info`
- `POST /api/v1/separate-stems`, `GET /api/v1/models`, and `GET /api/v1/formats`
- All `/api/v1/download/...` routes, `GET /api/v1/stats`, and `POST /api/v1/cleanup`
- `GET /metrics`

These routes never require a key: `GET /` and `GET /health`. When checks are on, `/health` shows only the status of each check to callers without a valid key.

A missing key returns HTTP 401:

```json
{
  "detail": "API key required. Provide X-API-Key header."
}
```

An invalid key returns HTTP 401 with the detail `Invalid API key`.

## Rate limits

Rate limits apply when `ENABLE_RATE_LIMITING=true` (the default). The limit applies per client IP address.

| Route | Limit |
|-------|-------|
| `POST /api/v1/youtube-to-mp3` | 3 per minute |
| `POST /api/v1/separate-stems` | 3 per minute |
| `GET /api/v1/download/...` (files and stems) | 20 per minute |
| `GET /api/v1/download/{file_id}/info`, `GET /api/v1/models`, `GET /api/v1/stats`, `GET /health`, `GET /` | 60 per minute |
| `GET /api/v1/youtube-info`, `GET /api/v1/formats`, `POST /api/v1/cleanup` | No limit |

The limit values come from `RATE_LIMIT_HEAVY_OPERATIONS`, `RATE_LIMIT_LIGHT_OPERATIONS`, and `RATE_LIMIT_INFO_OPERATIONS`.

A client over the limit receives HTTP 429:

```json
{
  "error": "Rate limit exceeded: 60 per 1 minute"
}
```

The client address comes from the socket. The `X-Forwarded-For` header counts only when the direct peer is listed in `TRUSTED_PROXIES` (default `127.0.0.1,::1`).

## Errors

The API uses two body formats for errors.

**Routing, validation, and authentication errors** use FastAPI's `detail` field:

```json
{
  "detail": "Invalid file_id format"
}
```

A validation error (HTTP 422) returns a list in `detail`. Each item has `loc`, `msg`, and `type`.

**Processing errors** return the same body shape as a success, with `success` set to `false` and an `error` text. The status code gives the cause. The error text does not include Demucs output or server paths.

| Status | Meaning | Routes |
|--------|---------|--------|
| 400 | Invalid parameter, invalid YouTube URL path or query, invalid UUID, unsupported model or format, invalid stem name | Most routes |
| 401 | API key missing or invalid | Routes that need a key |
| 404 | File not found | Download routes |
| 413 | Upload larger than `MAX_FILE_SIZE_MB` | `POST /api/v1/separate-stems` |
| 422 | Invalid request body: URL on another host, unsupported `audio_format`, `audio_quality` outside 0 to 10 | `POST /api/v1/youtube-to-mp3` |
| 429 | Rate limit exceeded | Routes with a limit |
| 500 | Internal error or separation failed | Any route |
| 502 | Download failed | `POST /api/v1/youtube-to-mp3` |
| 503 | Server busy or low memory. The response has the header `Retry-After: 30`. | `POST /api/v1/separate-stems` |
| 504 | Request time limit reached | Any route |
| 507 | Disk full | `POST /api/v1/separate-stems` |

## Endpoints

### GET /health

Check the health of the service. This route needs no key.

The response has an overall `status` (`healthy`, `degraded`, or `unhealthy`) and a `checks` object. The HTTP status is 200 for `healthy` and `degraded`, and 503 for `unhealthy`. The `redis` check appears with `ENABLE_RATE_LIMITING=true`. With rate limits off, it shows `"status": "disabled"`.

With a valid key, or when checks are off, each check has details:

```json
{
  "status": "healthy",
  "service": "music-tools-api",
  "timestamp": "...",
  "version": "1.0.0",
  "checks": {
    "redis": {"status": "healthy", "url": "redis://localhost:6379/0"},
    "disk_space": {"status": "healthy", "free_gb": "...", "total_gb": "...", "usage_percent": "..."},
    "memory": {"status": "healthy", "system_usage_percent": "...", "process_memory_mb": "...", "memory_limit_mb": "..."},
    "uploads_directory": {"status": "healthy", "path": "...", "exists": true},
    "outputs_directory": {"status": "healthy", "path": "...", "exists": true},
    "temp_directory": {"status": "healthy", "path": "...", "exists": true}
  }
}
```

Without a valid key, each entry in `checks` contains only `status`.

### POST /api/v1/youtube-to-mp3

Download the audio of a YouTube video and convert it.

**Request body (JSON):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | required | A YouTube URL. The host must be `youtube.com`, `www.youtube.com`, `m.youtube.com`, `music.youtube.com`, `youtu.be`, or `www.youtu.be`. |
| `audio_quality` | integer | `0` | 0 to 10. See [Audio quality](#audio-quality). |
| `audio_format` | string | `mp3` | `mp3`, `m4a`, `wav`, `flac`, `aac`, or `opus` |
| `extract_metadata` | boolean | `true` | `true` returns the `metadata` object. `false` skips the metadata request. |

A URL with a `list=` parameter downloads one video. It does not download the playlist.

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio_quality": 0, "audio_format": "mp3"}'
```

**Response:**

```json
{
  "success": true,
  "message": "Audio downloaded and converted successfully",
  "file_id": "<UUID>",
  "filename": "<video title>.mp3",
  "file_size_mb": 0.0,
  "metadata": {
    "title": "...",
    "duration": 0,
    "thumbnail_url": "...",
    "uploader": "...",
    "upload_date": "YYYYMMDD",
    "view_count": 0,
    "description": "..."
  },
  "download_url": "/api/v1/download/<UUID>"
}
```

The `metadata` value is `null` when `extract_metadata` is `false`. Use the `download_url` value with the download route. The file stays on the server until `FILE_RETENTION_HOURS` has passed (48 hours by default).

#### Audio quality

The effect of `audio_quality` depends on the format:

- **mp3**: The value is passed to the LAME encoder as the variable bitrate setting. 0 gives the highest quality and the largest file. 10 gives the lowest quality and the smallest file. The bitrate depends on the audio content.
- **m4a and aac**: The value is mapped to the AAC encoder quality range. 0 gives the highest quality.
- **wav, flac, and opus**: The value has no effect.

The mapping comes from the yt-dlp source code. The m4a and aac output was not checked with a real download.

#### Filename

The file is stored as `<file_id> - <title>.<format>`. The response `filename` and the download name show `<title>.<format>`. The title keeps only letters and digits (in any language), spaces, `-`, `_`, `.`, `(`, and `)`. All other characters are removed. The title is limited to 200 UTF-8 bytes.

| Video title | Filename |
|-------------|----------|
| `Song: Title/Mix` | `Song TitleMix.mp3` |
| `Artist - Song (Official Video)` | `Artist - Song (Official Video).mp3` |
| `Mr. Song` | `Mr. Song.mp3` |

### GET /api/v1/youtube-info

Get the metadata of a YouTube video. The service does not download the audio.

**Query parameter:**
- `url` (required): A YouTube URL. The same host and path rules apply as for the POST route.

**Response:**

```json
{
  "success": true,
  "info": {
    "title": "...",
    "duration": 0,
    "thumbnail": "...",
    "uploader": "...",
    "upload_date": "YYYYMMDD",
    "view_count": 0,
    "description": "...",
    "formats_available": 0,
    "audio_formats": []
  }
}
```

The `description` value is cut to 500 characters. The `audio_formats` list shows up to five audio-only formats.

### POST /api/v1/separate-stems

Separate an uploaded audio file into stems.

**Request (multipart form data):**

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `file` | yes | none | The audio file. The file extension must be `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.opus`, or `.wma`. The size limit is `MAX_FILE_SIZE_MB` (100 MB by default). |
| `model` | no | `htdemucs` | One of the models below. |
| `output_format` | no | `mp3` | `wav`, `mp3`, or `flac` |
| `stems` | no | all stems | Comma-separated values: `vocals`, `drums`, `bass`, `other`. An empty value or an omitted field returns all four stems. |

**Models:**

| Model | Description |
|-------|-------------|
| `htdemucs` | The default model. Hybrid Transformer Demucs, version 4. |
| `htdemucs_ft` | A fine-tuned version of `htdemucs`. The upstream project notes that it takes about four times as long. |
| `mdx_extra` | An MDX-Net model trained with extra training data. |
| `mdx_extra_q` | A quantized version of `mdx_extra`. It is smaller. The upstream project notes that it can be slightly less accurate. It needs the `demucs[quantized]` extra, which the requirement files install. |

The model descriptions come from the upstream Demucs project, at https://github.com/adefossez/demucs.

**Output formats:**

| Format | Description |
|--------|-------------|
| `wav` | Uncompressed. The largest files. |
| `mp3` | Encoded at a fixed 192 kbps (constant bitrate). |
| `flac` | Lossless compression. |

**Stem names:** `vocals`, `drums`, `bass`, and `other`. Each request returns the stems that you request. The other stems are `null` in the response.

**Example: all stems:**

```bash
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@your-audio.mp3" \
  -F "model=htdemucs" \
  -F "output_format=mp3"
```

**Example: vocals and drums only:**

```bash
curl -X POST "http://localhost:8000/api/v1/separate-stems" \
  -F "file=@your-audio.mp3" \
  -F "model=htdemucs" \
  -F "output_format=wav" \
  -F "stems=vocals,drums"
```

**Response:**

```json
{
  "success": true,
  "message": "Stems separated successfully",
  "job_id": "<UUID>",
  "stems": {
    "vocals": "/api/v1/download/<UUID>/<name> - vocals.mp3",
    "drums": "/api/v1/download/<UUID>/<name> - drums.mp3",
    "bass": "/api/v1/download/<UUID>/<name> - bass.mp3",
    "other": "/api/v1/download/<UUID>/<name> - other.mp3"
  },
  "processing_time_seconds": 0.0
}
```

The stem URLs contain the file name of each stem. A request that asks for only some stems returns `null` for the others.

The request stays open until the separation ends. Use a long client timeout. Processing time depends on the audio length, the model, and the hardware. The project does not publish benchmark figures. The Docker setup runs Demucs on the CPU, because the Compose file does not request a GPU.

#### Stem filename

- **With an original name**: `<upload name without extension> - <stem>.<format>`
- **Without an original name**: `<stem>.<format>`, for example `vocals.mp3`

The upload name keeps letters and digits (in any language), spaces, `-`, `_`, `(`, `)`, and `,`. Every other character becomes `_`. The name is limited to 200 UTF-8 bytes.

| Upload name | Stem file name |
|-------------|----------------|
| `Mr. Song.mp3` | `Mr_ Song - vocals.mp3` |
| `Artist - Song (Official Video).mp3` | `Artist - Song (Official Video) - vocals.mp3` |

### GET /api/v1/models

List the Demucs models and the default model.

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

The `description` and `recommended` values come from the server code. They are not benchmark results. Use the model table in this document for the upstream facts.

### GET /api/v1/formats

List the output formats for stem separation and the default format.

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

### GET /api/v1/download/{file_id}

Download a converted audio file.

- `file_id`: The UUID that the YouTube route returned.
- Returns the file as an attachment. The `Content-Type` header depends on the file extension (for example `audio/mpeg` for `.mp3`).
- Returns 400 if `file_id` is not a UUID. Returns 404 if the file does not exist.

### GET /api/v1/download/{job_id}/{filename}

Download one stem file.

- `job_id`: The UUID that the stem route returned.
- `filename`: The stem file name. Use the value from the `stems` object of the response. Encode spaces as `%20` in a URL.
- Returns 400 if the job ID is not a UUID or the file name is not valid. Returns 404 if the file does not exist.

### GET /api/v1/download/{file_id}/info

Get the information of a converted file.

```json
{
  "file_id": "<UUID>",
  "filename": "<title>.mp3",
  "file_size_mb": 0.0,
  "content_type": "audio/mpeg",
  "created_at": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}
```

The `created_at` value is an ISO 8601 UTC time.

### GET /api/v1/stats

Get storage statistics for the upload, output, and temp directories.

```json
{
  "directories": {
    "uploads": {"exists": true, "file_count": 0, "total_size_mb": 0.0, "oldest_file_age_hours": 0},
    "outputs": {"exists": true, "file_count": 0, "total_size_mb": 0.0, "oldest_file_age_hours": 0},
    "temp": {"exists": true, "file_count": 0, "total_size_mb": 0.0, "oldest_file_age_hours": 0}
  },
  "total_files": 0,
  "total_size_mb": 0.0,
  "cleanup_info": {
    "cleanup_interval_hours": 24,
    "file_retention_hours": 48,
    "max_file_size_mb": 100
  }
}
```

### POST /api/v1/cleanup

Remove the files that are older than `FILE_RETENTION_HOURS`. The periodic cleanup job runs the same task every `CLEANUP_INTERVAL_HOURS`.

```json
{
  "success": true,
  "message": "Cleanup completed. Removed 0 files.",
  "details": {
    "uploads": {"removed_files": 0, "status": "success"},
    "outputs": {"removed_files": 0, "status": "success"},
    "temp": {"removed_files": 0, "status": "success"}
  }
}
```

## Upload limits

- **Maximum size**: `MAX_FILE_SIZE_MB` (100 MB by default). A larger upload returns 413.
- **Accepted extensions**: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.opus`, `.wma`. The service checks the extension and the MIME type.

## Request time limits

The server stops a request after these times:

- Stem separation: `STEM_SEPARATION_TIMEOUT` (1800 seconds)
- YouTube download and info: `YOUTUBE_DOWNLOAD_TIMEOUT` (600 seconds)
- Health and stats: 30 seconds
- All other routes: `API_REQUEST_TIMEOUT` (120 seconds)

A request that reaches its limit returns HTTP 504.

## Configuration

The file `.env.example` lists all settings with comments. These settings are the most common:

| Setting | Default | Description |
|---------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server host |
| `API_PORT` | `8000` | Server port for a manual run |
| `DEBUG` | `false` | Enables the documentation pages and the reload mode |
| `MAX_FILE_SIZE_MB` | `100` | Upload size limit |
| `CLEANUP_INTERVAL_HOURS` | `24` | How often the cleanup job runs |
| `FILE_RETENTION_HOURS` | `48` | How long output files stay on the server |
| `DEFAULT_AUDIO_QUALITY` | `0` | Default `audio_quality` |
| `DEFAULT_AUDIO_FORMAT` | `mp3` | Default `audio_format` |
| `DEFAULT_DEMUCS_MODEL` | `htdemucs` | Default `model` |
| `DEFAULT_STEM_FORMAT` | `mp3` | Default `output_format` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection (rate limit storage) |
| `REQUIRE_API_KEY` | `false` | Turns on API key checks |
| `VALID_API_KEYS` | (empty) | Comma-separated list of valid keys |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | Allowed CORS origins |
| `TRUSTED_PROXIES` | `127.0.0.1,::1` | Proxies that may set `X-Forwarded-For` |
| `ENABLE_RATE_LIMITING` | `true` | Turns on rate limits |

## Examples

The `examples/` directory contains:

- `test_api.py`: A Python test script
- `python_client.py`: A Python client
- `curl_examples.sh`: cURL examples
