# Installation Guide

This guide provides detailed installation instructions for the Music Tools API across different environments and platforms.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended for stem separation)
- **Storage**: 10GB free space (for temporary files and AI models)
- **Network**: Internet connection for downloading dependencies and AI models

### Software Requirements
- **Python**: 3.8 or higher
- **FFmpeg**: For audio processing
- **Redis**: For background task queue (optional for basic usage)
- **Docker**: For containerized deployment (optional)

## 🚀 Quick Start (Docker - Recommended)

The fastest way to get started is using Docker:

### 1. Install Docker
- **Windows/macOS**: Download Docker Desktop from https://docker.com
- **Linux**: Follow your distribution's Docker installation guide

### 2. Clone and Start
```bash
# Clone the repository
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API

# Start the service
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health
```

### 3. Access the API
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Manual Installation

### Step 1: Install System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 ffmpeg redis
brew services start redis
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv ffmpeg redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### CentOS/RHEL/Fedora
```bash
# Install EPEL repository (CentOS/RHEL)
sudo yum install -y epel-release  # CentOS/RHEL
# OR for Fedora:
# sudo dnf install -y epel-release

# Install dependencies
sudo yum install -y python3 python3-pip ffmpeg redis  # CentOS/RHEL
# OR for Fedora:
# sudo dnf install -y python3 python3-pip ffmpeg redis

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### Windows
1. **Install Python**: Download from https://python.org (3.8+)
2. **Install FFmpeg**: 
   - Download from https://ffmpeg.org
   - Add to PATH environment variable
3. **Install Redis**:
   - Download from https://redis.io
   - Or use Windows Subsystem for Linux (WSL)

### Step 2: Clone Repository
```bash
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API
```

### Step 3: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### Step 4: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env  # or your preferred editor
```

### Step 6: Start the Service
```bash
# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000

# Or for development with auto-reload:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🏭 Production Deployment

### Option 1: Docker Compose (Recommended)

#### 1. Prepare Production Environment
```bash
# Clone repository
git clone https://github.com/AdarBahar/music-tools-API.git
cd music-tools-API

# Create production environment file
cp .env.example .env
```

#### 2. Configure Production Settings
Edit `.env` file:
```bash
# Production settings
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# Security
REQUIRE_API_KEY=true
VALID_API_KEYS=your-secret-key-1,your-secret-key-2

# Performance
MAX_FILE_SIZE_MB=500
CLEANUP_INTERVAL_HOURS=6
FILE_RETENTION_HOURS=24

# Redis
REDIS_URL=redis://redis:6379/0
```

#### 3. Start Production Services
```bash
# Start with Nginx reverse proxy
docker-compose --profile production up -d

# Or without Nginx (if you have your own reverse proxy)
docker-compose up -d music-tools-api redis
```

### Option 2: Manual Production Setup

#### 1. Install Production Dependencies
```bash
# Install additional production tools
pip install gunicorn

# Or use uWSGI
pip install uwsgi
```

#### 2. Create Systemd Service (Linux)
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

#### 3. Start and Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl start music-tools-api
sudo systemctl enable music-tools-api
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# File Management
MAX_FILE_SIZE_MB=100
CLEANUP_INTERVAL_HOURS=24
FILE_RETENTION_HOURS=48

# Audio Processing
DEFAULT_AUDIO_QUALITY=0
DEFAULT_AUDIO_FORMAT=mp3
DEFAULT_DEMUCS_MODEL=htdemucs
DEFAULT_STEM_FORMAT=mp3

# Background Tasks
REDIS_URL=redis://localhost:6379/0

# Security (Optional)
REQUIRE_API_KEY=false
VALID_API_KEYS=key1,key2,key3
```

### Performance Tuning

#### For High-Performance Setups
```bash
# Increase worker processes
gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker

# Increase file size limits
MAX_FILE_SIZE_MB=1000

# Reduce cleanup frequency for busy systems
CLEANUP_INTERVAL_HOURS=6
FILE_RETENTION_HOURS=12
```

#### For GPU Acceleration
Ensure CUDA is installed and available:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch if needed
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🧪 Verification

### Test Installation
```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Test YouTube info extraction (GET endpoint)
curl "http://localhost:8000/api/v1/youtube-info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Run Test Suite
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## 🔍 Troubleshooting

### Common Issues

#### FFmpeg Not Found
```bash
# Verify FFmpeg installation
ffmpeg -version

# Install if missing (see Step 1 above)
```

#### Redis Connection Error
```bash
# Check Redis status
redis-cli ping

# Start Redis if not running
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS
```

#### Permission Errors
```bash
# Fix directory permissions
sudo chown -R $USER:$USER /path/to/music-tools-api
chmod -R 755 /path/to/music-tools-api
```

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process or use different port
API_PORT=8001 uvicorn main:app --port 8001
```

### Getting Help
- Check the [README](README.md) for basic information
- Review [API Documentation](API_DOCUMENTATION.md) for endpoint details
- Open an issue on GitHub for specific problems
- Check logs for detailed error messages

## 📈 Monitoring

### Health Checks
The API provides health check endpoints:
- `/health`: Basic health status
- `/api/v1/stats`: Storage and processing statistics

### Logging
Logs are written to:
- **Console**: Standard output (development)
- **Files**: `logs/` directory (production)
- **Docker**: Container logs (`docker logs music-tools-api`)

### Metrics
Monitor these key metrics:
- Response times
- Error rates
- File processing times
- Storage usage
- Memory and CPU usage
