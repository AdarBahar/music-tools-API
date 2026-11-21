# Security

## Project paths and deployment context

**Secrets Management**: Environment variables from the `.env` file  
**API Security**: API key checks, off by default (`REQUIRE_API_KEY=false`)  
**File Security**: Upload validation, automatic cleanup  
**Network**: Docker network with a fixed Nginx address, configurable ports  

## Authentication and Authorization

**Current State**: API key checks exist. Turn them on with `REQUIRE_API_KEY=true` and `VALID_API_KEYS`.  
**Protected Routes**: The YouTube, download, stem, model, format, and `/metrics` routes require a valid key when checks are on.  
**Open Routes**: `/` and `/health`. `/health` shows check details only to callers with a valid key.  
**Key Comparison**: Constant time (`hmac.compare_digest`).

## File Upload Security

- **File Size Limits**: Configurable via `MAX_FILE_SIZE_MB` (default: 100 MB)
- **File Type Validation**: Extension, MIME type, and content checks in `app/core/upload_validation.py`
- **Upload Directory**: Isolated in container (`/app/uploads`)
- **Automatic Cleanup**: Files deleted after retention period

## Network Security

- **Container Isolation**: Docker network with a fixed address for Nginx (`172.28.0.10`)
- **Port Exposure**: The Compose file publishes the API on host port 8001 and Redis on host port 6380. The production profile also publishes ports 80 and 443 for Nginx.
- **Redis**: Published on host port 6380 in `docker-compose.yml`. Restrict this port with a firewall on a public server.
- **CORS**: Configured in FastAPI middleware (`ALLOWED_ORIGINS`)
- **Trusted Proxies**: Only addresses in `TRUSTED_PROXIES` may set `X-Forwarded-For`

## Data Protection

- **Temporary Storage**: All files treated as temporary
- **No User Data**: No persistent user information stored
- **File Cleanup**: Automatic deletion after `FILE_RETENTION_HOURS`
- **Logs**: Standard output only. Demucs output and server paths are logged, not sent to clients.

## Environment Variables

Sensitive configuration via environment variables:
- `REDIS_URL`: Redis connection string (rate limit storage)
- `VALID_API_KEYS`: Comma-separated API keys

**Security Note**: `.env` file should not be committed to version control

## Known Security TODOs

1. **Public exposure of Redis**: Compose publishes port 6380. Consider removing the port mapping.
2. **Input Validation**: Enhanced URL and file validation
3. **HTTPS**: SSL/TLS configuration for production (see `DEPLOYMENT.md`)
4. **Monitoring**: Security event logging and monitoring

## Threat Considerations

- **File Upload Abuse**: Mitigated by size limits, rate limits, and cleanup
- **YouTube URL Abuse**: Host, path, and query checks in `app/api/routes/youtube.py`
- **Resource Exhaustion**: CPU/memory intensive operations (rate limits and memory checks apply)
- **Data Exposure**: No persistent sensitive data stored
