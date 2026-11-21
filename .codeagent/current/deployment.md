# Deployment

## Project paths and deployment context

**Production Method**: Docker Compose  
**Local Development**: Direct Python or Docker  
**Port Configuration**: 8001 (external) → 8000 (internal)  
**Data Persistence**: `./data/` directory with subdirectories  
**Redis Dependency**: Optional. Stores the rate limit counters. Without Redis, the rate limiter uses memory.  

## Build and Deploy Steps

### Docker Deployment (Recommended)

```bash
# Clone and navigate to repository
git clone <repository-url>
cd music-tools-API

# Build and start services
docker-compose up -d

# Verify deployment
curl http://localhost:8001/docs   # 404 unless DEBUG=true
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (optional, for rate limit storage)
redis-server

# Run application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Services and Dependencies

- **music-tools-API**: Main FastAPI application container
- **redis**: Rate limit counter storage
- **nginx**: Load balancer and reverse proxy (optional)

## Data Volumes

- `./data/uploads`: Temporary file uploads
- `./data/outputs`: Processed audio files
- `./data/logs`: Application logs

## Environment Configuration

Key environment variables (see `.env` file):
- `API_HOST`, `API_PORT`: Server binding
- `MAX_FILE_SIZE_MB`: Upload limits
- `CLEANUP_INTERVAL_HOURS`, `FILE_RETENTION_HOURS`: File management
- `DEFAULT_DEMUCS_MODEL`: AI model selection
- `REDIS_URL`: Redis connection (rate limit storage)

## Health Checks and Monitoring

- Health endpoint: `/health`
- API documentation: `/docs` (Swagger UI)
- Metrics endpoint: `/metrics` (needs an API key when `REQUIRE_API_KEY=true`)

## Rollback Notes

- Docker: `docker-compose down && git checkout <previous-commit> && docker-compose up -d`
- Direct: Stop service, `git checkout <previous-commit>`, restart with previous environment
- Data safety: Volumes persist during rollbacks, manual cleanup if needed

## Resource Requirements

- **Minimum**: 2GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 4GB RAM, 4 CPU cores, 50GB storage
- **GPU**: Optional. The Docker image is CPU-only and the code sets no device. Demucs uses CUDA only when the PyTorch build and the host support it.