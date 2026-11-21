# Music Tools API

I built this REST API to download audio from YouTube and separate recordings into vocals, drums, bass, and other instruments using Demucs.

It runs as a self-hosted service and can be integrated into other applications.

I build, deploy, and operate this service myself. The service uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download from YouTube, [FFmpeg](https://ffmpeg.org/) to convert audio, and [Demucs](https://github.com/adefossez/demucs) to separate stems. I wrote the API, the job handling, and the deployment files around these tools. I did not develop the Demucs models.

## Key features

- **YouTube audio downloads.** Convert a video to mp3, m4a, wav, flac, aac, or opus. Set the quality from 0 (best) to 10 (smallest). A link with a `list=` parameter downloads only the video in the link, not the playlist.
- **Stem separation.** Split an uploaded file into vocals, drums, bass, and other. Request all stems or only some of them. Choose one of four Demucs models.
- **Audio formats.** Upload mp3, wav, flac, m4a, aac, ogg, opus, or wma. Save stems as wav, mp3, or flac.
- **Background threads.** Downloads and separations run in worker threads, so the server stays responsive while a job runs. A request waits until its job ends. The API does not report progress.
- **REST API.** Most endpoints return JSON and use the `/api/v1` prefix.
- **Optional API keys and rate limits.** Enable `X-API-Key` checks with one setting. Each route has a rate limit per client IP address.

## Quick start with Docker

### Prerequisites

- Docker with Docker Compose (the `docker compose` command).
- Free host ports 8001 (API) and 6380 (Redis).
- Enough disk space for the Docker image and the Demucs models. The first build downloads large packages, so it takes time.

### Steps

```bash
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API
cp .env.example .env
mkdir -p data/uploads data/outputs data/logs
docker compose up -d --build
```

Check that the service runs:

```bash
curl http://localhost:8001/health
```

A healthy service returns HTTP 200 and `"status": "healthy"`. HTTP 503 means that a check failed. The response shows the failed check when the request has a valid API key, or when API keys are off.

Notes:

- Compose maps host port 8001 to container port 8000. To use another host port, change the `ports` value in `docker-compose.yml`.
- Compose sets `REDIS_URL` for the API container. Do not change `REDIS_URL` in `.env` for Docker.
- The Compose file sets `DEBUG=false`. The Swagger UI and ReDoc pages are available only when `DEBUG=true`. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md).
- The Nginx service starts only with the production profile: `docker compose --profile production up -d`. See [DEPLOYMENT.md](DEPLOYMENT.md).
- For a manual installation without Docker, see [INSTALLATION.md](INSTALLATION.md).

## API usage examples

The examples use port 8001 (Docker). If API keys are on, add this header to each request: `-H "X-API-Key: $MUSIC_TOOLS_API_KEY"`. Set `MUSIC_TOOLS_API_KEY` in your shell first.

### Download audio from YouTube

```bash
curl -X POST "http://localhost:8001/api/v1/youtube-to-mp3" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio_quality": 0, "audio_format": "mp3"}'
```

The response contains these fields:

```json
{
  "success": true,
  "file_id": "<file id>",
  "filename": "<video title>.mp3",
  "metadata": {"title": "...", "duration": 0, "thumbnail_url": "...", "uploader": "..."},
  "download_url": "/api/v1/download/<file id>"
}
```

Download the file with the `download_url` value:

```bash
curl -o song.mp3 "http://localhost:8001/api/v1/download/<file id>"
```

### Separate an uploaded file into stems

```bash
curl -X POST "http://localhost:8001/api/v1/separate-stems" \
  -F "file=@song.mp3" \
  -F "model=htdemucs" \
  -F "output_format=mp3" \
  -F "stems=vocals,drums"
```

Omit the `stems` field to get all four stems. The response contains a `job_id` and one download URL for each stem:

```json
{
  "success": true,
  "job_id": "<job id>",
  "stems": {
    "vocals": "/api/v1/download/<job id>/<file name> - vocals.mp3",
    "drums": "/api/v1/download/<job id>/<file name> - drums.mp3",
    "bass": null,
    "other": null
  },
  "processing_time_seconds": 0.0
}
```

A stem that you did not request is `null`. The request stays open until the separation ends. Use a long client timeout. The server stops a separation after `STEM_SEPARATION_TIMEOUT` seconds (1800 by default).

For all endpoints, parameters, and error codes, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Authentication and configuration

### API keys

API key checks are off by default. To enable them, set these values in `.env`:

```bash
REQUIRE_API_KEY=true
VALID_API_KEYS=first-key,second-key
```

Send a key in the `X-API-Key` header. Use long random keys. Do not store keys in source control.

When checks are on, the YouTube, download, stem, model, format, and metrics routes require a valid key. The root route and `/health` do not require a key. When checks are on, `/health` shows check details only to callers with a valid key.

### Rate limits

Rate limits apply per client IP address. The default values are:

| Route | Limit |
|-------|-------|
| `POST /api/v1/youtube-to-mp3` | 3 per minute |
| `POST /api/v1/separate-stems` | 3 per minute |
| File downloads | 20 per minute |
| Info routes (models, stats, download info, health) | 60 per minute |

`GET /api/v1/youtube-info` has no rate limit. The API uses the address of the direct client, unless the client connects through a proxy in `TRUSTED_PROXIES`.

### Main settings

The table lists the most common settings. The file `.env.example` lists all settings.

| Setting | Default | Purpose |
|---------|---------|---------|
| `DEBUG` | `false` | Enable the Swagger UI, ReDoc, and reload |
| `MAX_FILE_SIZE_MB` | `100` | Upload size limit |
| `FILE_RETENTION_HOURS` | `48` | How long output files stay on disk |
| `CLEANUP_INTERVAL_HOURS` | `24` | How often the cleanup job runs |
| `DEFAULT_AUDIO_QUALITY` | `0` | Default YouTube audio quality |
| `DEFAULT_AUDIO_FORMAT` | `mp3` | Default YouTube audio format |
| `DEFAULT_DEMUCS_MODEL` | `htdemucs` | Default separation model |
| `DEFAULT_STEM_FORMAT` | `mp3` | Default stem format |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for rate limit counters |
| `REQUIRE_API_KEY` | `false` | Enable API key checks |
| `VALID_API_KEYS` | (empty) | Comma-separated list of valid keys |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | Allowed CORS origins |
| `TRUSTED_PROXIES` | `127.0.0.1,::1` | Proxies that may set `X-Forwarded-For` |
| `ENABLE_RATE_LIMITING` | `true` | Enable rate limits |

Redis stores the rate limit counters. If Redis is not available, the rate limiter uses memory, and `/health` reports the Redis check as unhealthy.

## Development and testing

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-core.txt pytest httpx
python main.py          # starts the API on http://localhost:8000
python -m pytest -q     # runs the test suite
```

- The tests use a fake Demucs. They need no GPU and no network access.
- For real separation, run `pip install -r requirements-audio.txt`. This command installs PyTorch and Demucs.
- The `mdx_extra_q` model needs the `demucs[quantized]` extra. The requirement files install it.
- CI runs the test suite on Python 3.12. The Docker image uses Python 3.10.

## Documentation

| Document | Contents |
|----------|----------|
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Endpoints, parameters, responses, and errors |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker deployment, Nginx, API keys, and HTTPS |
| [INSTALLATION.md](INSTALLATION.md) | Manual installation on each operating system |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## Acknowledgments

- [Demucs](https://github.com/adefossez/demucs) provides the stem separation models and code.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) downloads audio from YouTube.
- [FFmpeg](https://ffmpeg.org/) converts audio files.
- [FastAPI](https://fastapi.tiangolo.com/), [Redis](https://redis.io/), [slowapi](https://github.com/laurentS/slowapi), and [Pydantic](https://docs.pydantic.dev/) provide the web, storage, and validation layers.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
