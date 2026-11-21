# Installation Guide

This guide describes how to install the Music Tools API with Docker and without Docker. For the API endpoints, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md). For a production server, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites

### Resources

The resource values below are estimates. The real needs depend on the audio length and the Demucs model.

- **Operating system**: Linux, macOS, or Windows
- **CPU**: 2 cores or more
- **RAM**: 4 GB or more. Stem separation needs more memory.
- **Disk space**: Enough space for the Docker image or the Python packages, and for the Demucs models
- **Network**: Internet access to download packages and models

### Software

- **Python**: 3.10 or later. The Docker image uses Python 3.10. CI runs on Python 3.12.
- **FFmpeg**: Converts audio files. Required for a manual installation. The Docker image includes it.
- **Redis**: Stores the rate limit counters. Optional. Without Redis, the rate limiter uses memory, and `/health` reports Redis as unhealthy.
- **Docker** with Docker Compose: Optional. Recommended for most users.

## Install with Docker (recommended)

### 1. Install Docker

- **Windows and macOS**: Install Docker Desktop from https://www.docker.com.
- **Linux**: Follow the Docker installation guide for your distribution.

### 2. Clone the repository and start the service

```bash
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API
cp .env.example .env
mkdir -p data/uploads data/outputs data/logs
docker compose up -d --build
```

The `.env` file must exist before you start the service. Compose mounts it into the container. The `data/` folders store the uploads, the outputs, and the logs.

### 3. Check the service

```bash
curl http://localhost:8001/health
```

The API runs on host port 8001. Compose maps this port to port 8000 in the container. To use another host port, change the `ports` value in `docker-compose.yml`.

The Swagger UI at `http://localhost:8001/docs` is available only when `DEBUG=true`. The Compose file sets `DEBUG=false`.

## Install without Docker

### Step 1: Install the system packages

#### macOS

```bash
# Install Homebrew first. See https://brew.sh.
brew install python@3.10 ffmpeg redis
brew services start redis
```

#### Ubuntu and Debian

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### CentOS, RHEL, and Fedora

```bash
# CentOS and RHEL: install the EPEL repository first.
sudo yum install -y epel-release
sudo yum install -y python3 python3-pip ffmpeg redis

# Fedora: use dnf instead of yum.
# sudo dnf install -y python3 python3-pip ffmpeg redis

sudo systemctl start redis
sudo systemctl enable redis
```

#### Windows

1. Install Python 3.10 or later from https://www.python.org.
2. Install FFmpeg from https://ffmpeg.org. Add the `bin` folder to the `PATH` variable.
3. Install Redis from https://redis.io, or use Windows Subsystem for Linux (WSL). Redis is optional.

### Step 2: Clone the repository

```bash
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API
```

### Step 3: Create a virtual environment

```bash
python3 -m venv venv

# Linux and macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### Step 4: Install the Python packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

The `requirements.txt` file installs Demucs with the `quantized` extra, and the audio packages. The `mdx_extra_q` model needs that extra.

### Step 5: Create the configuration file

```bash
cp .env.example .env
```

Edit `.env` if you need other values. See [Configuration](#configuration).

### Step 6: Start the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000

# For development, add --reload:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API runs on port 8000 in this mode.

## Production setup

For a production server, use the steps in [DEPLOYMENT.md](DEPLOYMENT.md). The main steps are:

- Use the Docker Compose setup. Start the Nginx service with `docker compose --profile production up -d`.
- Set `DEBUG=false`.
- Set `REQUIRE_API_KEY=true` and provide `VALID_API_KEYS`.

### Run without Docker under systemd

Use an ASGI server for the process. The example below uses Gunicorn with the Uvicorn worker. Install both packages in the virtual environment first:

```bash
pip install gunicorn uvicorn
```

Create `/etc/systemd/system/music-tools-api.service`:

```ini
[Unit]
Description=Music Tools API
After=network.target redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/music-tools-api
Environment=PATH=/opt/music-tools-api/venv/bin
ExecStart=/opt/music-tools-api/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start music-tools-api
sudo systemctl enable music-tools-api
```

The service loads `.env` from the working directory.

## Configuration

Set the values in `.env`. The file `.env.example` lists all settings with comments. These are the most common settings:

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Files
MAX_FILE_SIZE_MB=100
CLEANUP_INTERVAL_HOURS=24
FILE_RETENTION_HOURS=48

# Audio processing
DEFAULT_AUDIO_QUALITY=0
DEFAULT_AUDIO_FORMAT=mp3
DEFAULT_DEMUCS_MODEL=htdemucs
DEFAULT_STEM_FORMAT=mp3

# Redis (rate limit counters)
REDIS_URL=redis://localhost:6379/0

# API keys (optional)
REQUIRE_API_KEY=false
VALID_API_KEYS=key1,key2
```

Inside Docker, Compose sets `REDIS_URL` to `redis://redis:6379/0`. Keep that value for Docker.

### Busy servers

- Increase the number of Gunicorn workers with `-w`. Each worker keeps its own memory-based rate limit state when Redis is not available.
- Set `MAX_FILE_SIZE_MB` to a higher value only when the server has enough disk space.
- Lower `FILE_RETENTION_HOURS` to free disk space sooner.

### GPU support

Demucs uses CUDA only when the installed PyTorch build supports CUDA and a GPU is visible to the process. The application does not set a device. Check the support with this command:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

If the result is `False` and you have an NVIDIA GPU, install a PyTorch build that matches your CUDA version. See https://pytorch.org.

## Verification

### Check the service

```bash
# Health (port 8000 for a manual run, 8001 for Docker)
curl http://localhost:8000/health

# Swagger UI (only when DEBUG=true)
curl http://localhost:8000/docs

# YouTube info (GET endpoint)
curl "http://localhost:8000/api/v1/youtube-info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Run the test suite

The tests use a fake Demucs. They need no GPU and no network access.

```bash
pip install -r requirements-core.txt pytest httpx
python -m pytest -q
```

## Troubleshooting

### FFmpeg not found

```bash
ffmpeg -version
```

If the command fails, install FFmpeg. See Step 1.

### Redis connection error

```bash
redis-cli ping
```

The response is `PONG` when Redis runs. Start Redis if it does not run:

```bash
sudo systemctl start redis-server   # Linux
brew services start redis           # macOS
```

If Redis is not needed for your test, set `ENABLE_RATE_LIMITING=false`. The `/health` check does not report Redis then.

### Permission errors

```bash
sudo chown -R "$USER":"$USER" /path/to/music-tools-api
```

### Port already in use

```bash
lsof -i :8000
```

Stop the process that uses the port, or start the API on another port. Use the `--port` option of `uvicorn`. The `API_PORT` value does not change the port of a `uvicorn` command line.

## Getting help

- Read the [README](README.md) for an overview.
- Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details.
- Open an issue on GitHub for a specific problem.
- Read the container logs (`docker compose logs music-tools-api`) or the standard output of the process.

## Monitoring

- `/health` returns the status of each check. The check details appear only for callers with a valid API key, or when API keys are off.
- `/api/v1/stats` returns the storage use and the file counts.
- `/metrics` returns Prometheus metrics. It includes request counts, request durations, memory use, and processing times. It needs a valid API key when `REQUIRE_API_KEY=true`.

### Logs

The application writes logs to standard output. It does not write a log file. Use `docker compose logs -f music-tools-api` with Docker. Under systemd, use `journalctl -u music-tools-api`.
