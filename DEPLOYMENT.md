# Music Tools API - Deployment Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM (8GB+ recommended)
- FFmpeg (included in Docker image)

### 1. Clone and Setup
```bash
cd api-service
cp .env.example .env
# Edit .env file as needed
```

### 2. Start the Service
```bash
./scripts/start.sh
```

### 3. Access the API
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Manual Installation

### Prerequisites
- Python 3.8+
- FFmpeg
- Redis (for background tasks)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env file
```

### 3. Start Redis
```bash
redis-server
```

### 4. Start the API
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Production Deployment

### Docker Compose with Nginx
```bash
# Start with production profile
docker-compose --profile production up -d

# Or customize nginx.conf and start
docker-compose up -d
```

### Environment Variables
Key production settings in `.env`:
```bash
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE_MB=100
CLEANUP_INTERVAL_HOURS=24
FILE_RETENTION_HOURS=48
REQUIRE_API_KEY=true
VALID_API_KEYS=your-secret-key-1,your-secret-key-2
```

### SSL/HTTPS Setup
1. Obtain SSL certificates
2. Update `nginx.conf` with SSL configuration
3. Mount certificates in `docker-compose.yml`

### Monitoring
- Health endpoint: `/health`
- Storage stats: `/api/v1/stats`
- Docker logs: `docker-compose logs -f`

## Performance Tuning

### Hardware Recommendations
- **CPU**: 4+ cores (8+ for heavy usage)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: SSD for better I/O performance
- **GPU**: CUDA-compatible GPU for faster stem separation

### Docker Resource Limits
Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4.0'
```

### File Cleanup
- Automatic cleanup runs every 24 hours (configurable)
- Manual cleanup: `curl -X POST http://localhost:8000/api/v1/cleanup`
- Files older than 48 hours are removed (configurable)

## Scaling

### Horizontal Scaling
- Run multiple API instances behind a load balancer
- Share Redis instance between instances
- Use shared storage for uploads/outputs

### Background Processing
- Celery workers for long-running tasks
- Redis as message broker
- Separate worker containers for stem separation

## Security

### API Key Authentication
```bash
REQUIRE_API_KEY=true
VALID_API_KEYS=key1,key2,key3
```

Use in requests:
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/youtube-to-mp3
```

### Rate Limiting
Configure in `nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
```

### File Upload Security
- File size limits enforced
- File type validation
- Temporary file cleanup

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Increase Docker memory limits
   - Reduce concurrent operations
   - Enable swap if needed

2. **Slow Stem Separation**
   - Use GPU acceleration
   - Reduce audio file size
   - Use faster Demucs models

3. **Disk Space Issues**
   - Reduce file retention time
   - Increase cleanup frequency
   - Monitor storage usage

### Logs
```bash
# Docker logs
docker-compose logs -f music-tools-api

# Application logs
tail -f data/logs/app.log
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Storage stats
curl http://localhost:8000/api/v1/stats

# Container status
docker-compose ps
```

## Backup and Recovery

### Data Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
cp .env .env.backup
```

### Recovery
```bash
# Restore data
tar -xzf backup-YYYYMMDD.tar.gz

# Restart services
docker-compose restart
```

## Updates

### Update API Service
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Dependencies
```bash
# Update requirements.txt
pip install -r requirements.txt --upgrade

# Rebuild Docker image
docker-compose build --no-cache
```
