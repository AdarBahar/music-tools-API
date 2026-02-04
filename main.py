"""
Music Tools API - Standalone Audio Processing Service

A complete REST API service for YouTube to MP3 conversion and AI-powered audio stem separation.
This service provides high-quality audio processing capabilities with a simple REST interface.

Features:
- YouTube to MP3 conversion with configurable quality
- AI-powered audio stem separation using Meta's Demucs
- Multiple audio format support
- Background task processing
- Automatic file cleanup
- Docker containerization support

Author: Adar Bahar
License: MIT
Version: 1.0.0
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import youtube, stems, downloads
from app.core.config import settings
from app.core.cleanup import start_cleanup_scheduler
from app.core.auth import log_security_event
from app.core.metrics import init_metrics, record_request, update_memory_metrics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure security logger
security_logger = logging.getLogger("security")
security_handler = logging.StreamHandler()
security_handler.setFormatter(
    logging.Formatter("%(asctime)s - SECURITY - %(levelname)s - %(message)s")
)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Initialize rate limiter if enabled
limiter = None
if settings.ENABLE_RATE_LIMITING:
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=settings.RATE_LIMIT_STORAGE_URI,
            default_limits=["100/minute"]
        )
        logger.info("Rate limiting enabled with Redis storage")
    except Exception as e:
        logger.warning(f"Failed to initialize rate limiter: {type(e).__name__}. Rate limiting disabled.")
        limiter = None
else:
    logger.info("Rate limiting disabled in configuration")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Music Tools API Service...")
    
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    # Initialize metrics system
    init_metrics()
    
    logger.info(f"API Service started on {settings.API_HOST}:{settings.API_PORT}")
    yield
    
    # Shutdown
    logger.info("Shutting down Music Tools API Service...")


# Create FastAPI app
# Disable documentation endpoints in production (when DEBUG=false)
docs_url = "/docs" if settings.DEBUG else None
redoc_url = "/redoc" if settings.DEBUG else None
openapi_url = "/openapi.json" if settings.DEBUG else None

app = FastAPI(
    title="Music Tools API",
    description="""
    A standalone REST API service for audio processing that provides:

    🎵 **YouTube to MP3 Conversion**
    - Convert YouTube videos to high-quality MP3 files
    - Multiple audio format support (mp3, m4a, wav, flac, aac, opus)
    - Configurable audio quality and metadata extraction

    🎛️ **AI-Powered Audio Stem Separation**
    - Separate audio into vocals, drums, bass, and other instruments
    - Multiple Demucs model support for different use cases
    - GPU acceleration support for faster processing

    📊 **Features**
    - Real-time progress tracking
    - Automatic file cleanup
    - Background task processing
    - Comprehensive error handling
    """,
    version="1.0.0",
    contact={
        "name": "Adar Bahar",
        "url": "https://github.com/AdarBahar/music-tools-api",
        "email": "adar@bahar.co.il",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan
)

# Add CORS middleware with proper security configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # Specific domains only
    allow_credentials=False,  # Disable credentials for security
    allow_methods=["GET", "POST"],  # Only required methods
    allow_headers=["X-API-Key", "Content-Type"],  # Required headers only
)

# Add rate limiter to app state and exception handler
if limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting middleware configured")

# Add metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware for collecting metrics"""
    import time
    
    start_time = time.time()
    
    # Update memory metrics periodically
    update_memory_metrics()
    
    try:
        response = await call_next(request)
        
        # Record request metrics
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        record_request(method, endpoint, status_code, duration)
        
        return response
        
    except Exception as e:
        # Record error metrics
        duration = time.time() - start_time
        endpoint = request.url.path 
        method = request.method
        
        record_request(method, endpoint, 500, duration)
        raise


# Add security event logging middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Middleware for security event logging"""
    try:
        response = await call_next(request)
        
        # Log authentication events
        if response.status_code == 401:
            await log_security_event(
                request, 
                "authentication_failure", 
                {"endpoint": str(request.url), "method": request.method}
            )
        
        return response
    except Exception as e:
        # Log security-related exceptions
        await log_security_event(
            request,
            "request_error",
            {"endpoint": str(request.url), "error": str(e)}
        )
        raise


@app.middleware("http")
async def log_bad_requests_middleware(request: Request, call_next):
    """Log extra context for 400/422 responses (especially multipart uploads).

    This is intentionally narrow to avoid noisy logs: we only emit for
    `/api/v1/separate-stems` and only on 400/422.
    """
    response = await call_next(request)

    path = request.url.path
    if path == "/api/v1/separate-stems" and response.status_code in (400, 422):
        uvicorn_logger = logging.getLogger("uvicorn.error")
        headers = request.headers
        http_version = request.scope.get("http_version")

        uvicorn_logger.warning(
            "Bad request to %s %s (status=%s, http=%s, ct=%s, cl=%s, te=%s, origin=%s, ua=%s, xff=%s)",
            request.method,
            path,
            response.status_code,
            http_version,
            headers.get("content-type"),
            headers.get("content-length"),
            headers.get("transfer-encoding"),
            headers.get("origin"),
            headers.get("user-agent"),
            headers.get("x-forwarded-for"),
        )

    return response


# Add timeout middleware for API requests
@app.middleware("http") 
async def timeout_middleware(request: Request, call_next):
    """Middleware for request timeouts"""
    import asyncio
    from fastapi.responses import JSONResponse
    
    # Determine timeout based on endpoint
    path = request.url.path
    if "/separate-stems" in path:
        timeout = settings.STEM_SEPARATION_TIMEOUT
    elif "/youtube-to-mp3" in path or "/youtube-info" in path:
        timeout = settings.YOUTUBE_DOWNLOAD_TIMEOUT  
    elif "/health" in path or "/api/v1/stats" in path:
        timeout = 30  # Short timeout for health/info endpoints
    else:
        timeout = settings.API_REQUEST_TIMEOUT
    
    try:
        response = await asyncio.wait_for(
            call_next(request), 
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.warning(f"Request timeout ({timeout}s) for {request.method} {path}")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "error": f"Request timeout after {timeout} seconds",
                "timeout_seconds": timeout
            }
        )

# Include API routes
app.include_router(youtube.router, prefix="/api/v1", tags=["YouTube"])
app.include_router(stems.router, prefix="/api/v1", tags=["Stem Separation"])
app.include_router(downloads.router, prefix="/api/v1", tags=["Downloads"])

# Mount static files for downloads
app.mount("/static", StaticFiles(directory=settings.OUTPUT_DIR), name="static")


@limiter.limit(settings.RATE_LIMIT_INFO_OPERATIONS) if limiter else lambda f: f
@app.get("/")
async def root(request: Request):
    """
    Root endpoint with API information

    Returns basic information about the Music Tools API service including
    available endpoints and documentation links.
    """
    documentation = {
        "enabled": bool(settings.DEBUG),
        "swagger_ui": "/docs" if settings.DEBUG else None,
        "redoc": "/redoc" if settings.DEBUG else None,
    }

    return {
        "name": "Music Tools API",
        "description": "Standalone audio processing service for YouTube to MP3 conversion and AI-powered stem separation",
        "version": "1.0.0",
        "status": "running",
        "documentation": documentation,
        "endpoints": {
            "youtube_to_mp3": "/api/v1/youtube-to-mp3",
            "youtube_info": "/api/v1/youtube-info",
            "separate_stems": "/api/v1/separate-stems",
            "download": "/api/v1/download/{file_id}",
            "health": "/health",
            "metrics": "/metrics",
            "stats": "/api/v1/stats"
        },
        "features": [
            "YouTube to MP3 conversion",
            "AI-powered audio stem separation",
            "Multiple audio format support",
            "Background task processing",
            "Automatic file cleanup"
        ]
    }


@limiter.limit(settings.RATE_LIMIT_INFO_OPERATIONS) if limiter else lambda f: f
@app.get("/health")
async def health_check(request: Request):
    """
    Comprehensive health check endpoint
    
    Returns detailed health information including:
    - Service status
    - Redis connectivity 
    - Disk space availability
    - Memory usage
    - System dependencies
    """
    from datetime import datetime
    import shutil
    from fastapi.responses import JSONResponse
    
    health_status = {
        "status": "healthy",
        "service": "music-tools-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check Redis connectivity (only if rate limiting is enabled)
    if settings.ENABLE_RATE_LIMITING:
        try:
            # Try to import redis client
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "url": settings.REDIS_URL
            }
            await redis_client.close()
        except ImportError:
            health_status["checks"]["redis"] = {
                "status": "not_available",
                "message": "Redis client not installed"
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy", 
                "error": str(e),
                "url": settings.REDIS_URL
            }
            health_status["status"] = "unhealthy"
    else:
        health_status["checks"]["redis"] = {
            "status": "disabled",
            "message": "Rate limiting disabled"
        }
    
    # Check disk space
    try:
        total, used, free = shutil.disk_usage(settings.BASE_DIR)
        free_gb = free / (1024**3)
        total_gb = total / (1024**3)
        usage_percent = (used / total) * 100
        
        disk_healthy = free_gb > 1.0 and usage_percent < 95  # At least 1GB free and <95% full
        
        health_status["checks"]["disk_space"] = {
            "status": "healthy" if disk_healthy else "unhealthy",
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2), 
            "usage_percent": round(usage_percent, 1)
        }
        
        if not disk_healthy:
            health_status["status"] = "unhealthy"
            
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check memory usage
    try:
        import psutil
        memory = psutil.virtual_memory()
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024 * 1024)
        
        memory_healthy = (
            memory.percent < 90 and  # System memory < 90%
            process_memory_mb < settings.MEMORY_LIMIT_MB  # Process within limits
        )
        
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory_healthy else "warning",
            "system_usage_percent": round(memory.percent, 1),
            "process_memory_mb": round(process_memory_mb, 1),
            "memory_limit_mb": settings.MEMORY_LIMIT_MB
        }
        
        if not memory_healthy:
            health_status["status"] = "degraded" if health_status["status"] == "healthy" else "unhealthy"
            
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "not_available",
            "message": "psutil not installed"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check directory accessibility
    for dir_name, dir_path in [
        ("uploads", settings.UPLOAD_DIR),
        ("outputs", settings.OUTPUT_DIR), 
        ("temp", settings.TEMP_DIR)
    ]:
        try:
            dir_path.mkdir(exist_ok=True)
            accessible = dir_path.exists() and dir_path.is_dir()
            health_status["checks"][f"{dir_name}_directory"] = {
                "status": "healthy" if accessible else "unhealthy",
                "path": str(dir_path),
                "exists": accessible
            }
            if not accessible:
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"][f"{dir_name}_directory"] = {
                "status": "unhealthy",
                "path": str(dir_path),
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
    
    # Return appropriate HTTP status code
    status_code = {
        "healthy": 200,
        "degraded": 200,  # Still operational but with warnings
        "unhealthy": 503  # Service unavailable
    }.get(health_status["status"], 503)
    
    return JSONResponse(health_status, status_code=status_code)


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format for monitoring systems.
    Includes:
    - Request counts and durations
    - Memory usage statistics
    - Processing times for operations
    - Error counts
    - Active operation counts
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        from app.core.metrics import metrics_available, update_memory_metrics
        
        if not metrics_available():
            return Response(
                content="# Metrics not available - prometheus_client not installed\n",
                media_type="text/plain"
            )
        
        # Update memory metrics before generating output
        update_memory_metrics()
        
        # Generate Prometheus metrics
        metrics_data = generate_latest()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
        
    except ImportError:
        return Response(
            content="# Metrics not available - prometheus_client not installed\n", 
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {e}\n",
            media_type="text/plain"
        )


def main():
    """
    Main entry point for the Music Tools API service.

    This function can be called directly or used as a console script entry point.
    It starts the FastAPI application using Uvicorn with configuration from settings.
    """
    import uvicorn

    logger.info("Starting Music Tools API service...")
    logger.info(f"Configuration: Host={settings.API_HOST}, Port={settings.API_PORT}, Debug={settings.DEBUG}")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )


if __name__ == "__main__":
    main()
