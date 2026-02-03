# Deployment

## Project paths and deployment context

**Production Method**: Docker Compose  
**Local Development**: Direct Python or Docker  
**Port Configuration**: 8001 (external) → 8000 (internal)  
**Data Persistence**: `./data/` directory with subdirectories  
**Redis Dependency**: Required for background task processing  

## Build and Deploy Steps

### Docker Deployment (Recommended)

```bash
# Clone and navigate to repository
git clone <repository-url>
cd music-tools-API

# Build and start services
docker-compose up -d

# Verify deployment
curl http://localhost:8001/docs
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (required)
redis-server

# Run application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Services and Dependencies

- **music-tools-API**: Main FastAPI application container
- **redis**: Background task broker and cache
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
- `REDIS_URL`: Background task configuration

## Health Checks and Monitoring

- Health endpoint: `/health` (TODO: implement)
- API documentation: `/docs` (Swagger UI)
- Metrics endpoint: `/metrics` (TODO: implement)

## Rollback Notes

- Docker: `docker-compose down && git checkout <previous-commit> && docker-compose up -d`
- Direct: Stop service, `git checkout <previous-commit>`, restart with previous environment
- Data safety: Volumes persist during rollbacks, manual cleanup if needed

## Resource Requirements

- **Minimum**: 2GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 4GB RAM, 4 CPU cores, 50GB storage
- **GPU**: Optional for 3-5x faster Demucs processing