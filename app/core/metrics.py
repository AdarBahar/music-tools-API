"""
Prometheus metrics collection for Music Tools API
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global metrics instances
REQUEST_COUNT = None
REQUEST_DURATION = None  
MEMORY_USAGE = None
PROCESSING_TIME = None
ERROR_COUNT = None
ACTIVE_OPERATIONS = None

def init_metrics():
    """Initialize Prometheus metrics"""
    global REQUEST_COUNT, REQUEST_DURATION, MEMORY_USAGE, PROCESSING_TIME, ERROR_COUNT, ACTIVE_OPERATIONS
    
    try:
        from prometheus_client import Counter, Histogram, Gauge
        
        REQUEST_COUNT = Counter(
            'api_requests_total', 
            'Total API requests', 
            ['method', 'endpoint', 'status']
        )
        
        REQUEST_DURATION = Histogram(
            'api_request_duration_seconds', 
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        MEMORY_USAGE = Gauge(
            'api_memory_usage_bytes',
            'Current memory usage in bytes',
            ['type']  # system, process
        )
        
        PROCESSING_TIME = Histogram(
            'api_processing_duration_seconds',
            'Processing duration for operations', 
            ['operation_type']  # youtube_download, stem_separation
        )
        
        ERROR_COUNT = Counter(
            'api_errors_total',
            'Total API errors',
            ['endpoint', 'error_type']
        )
        
        ACTIVE_OPERATIONS = Gauge(
            'api_active_operations',
            'Currently active operations',
            ['operation_type']
        )
        
        logger.info("Prometheus metrics initialized successfully")
        return True
        
    except ImportError:
        logger.warning("prometheus_client not available - metrics disabled")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
        return False


def record_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record API request metrics"""
    if REQUEST_COUNT and REQUEST_DURATION:
        try:
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=endpoint, 
                status=str(status_code)
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.debug(f"Failed to record request metrics: {e}")


def record_memory_usage(system_bytes: Optional[int] = None, process_bytes: Optional[int] = None):
    """Record memory usage metrics"""
    if MEMORY_USAGE:
        try:
            if system_bytes is not None:
                MEMORY_USAGE.labels(type='system').set(system_bytes)
            if process_bytes is not None:
                MEMORY_USAGE.labels(type='process').set(process_bytes)
        except Exception as e:
            logger.debug(f"Failed to record memory metrics: {e}")


def record_processing_time(operation_type: str, duration: float):
    """Record processing time for operations"""
    if PROCESSING_TIME:
        try:
            PROCESSING_TIME.labels(operation_type=operation_type).observe(duration)
        except Exception as e:
            logger.debug(f"Failed to record processing time: {e}")


def record_error(endpoint: str, error_type: str):
    """Record error metrics"""
    if ERROR_COUNT:
        try:
            ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()
        except Exception as e:
            logger.debug(f"Failed to record error metrics: {e}")


def set_active_operations(operation_type: str, count: int):
    """Set active operations count"""
    if ACTIVE_OPERATIONS:
        try:
            ACTIVE_OPERATIONS.labels(operation_type=operation_type).set(count)
        except Exception as e:
            logger.debug(f"Failed to set active operations: {e}")


def update_memory_metrics():
    """Update memory metrics from system"""
    try:
        import psutil
        
        # System memory
        memory = psutil.virtual_memory()
        record_memory_usage(system_bytes=memory.used)
        
        # Process memory
        process = psutil.Process()
        process_memory = process.memory_info().rss
        record_memory_usage(process_bytes=process_memory)
        
    except ImportError:
        pass  # psutil not available
    except Exception as e:
        logger.debug(f"Failed to update memory metrics: {e}")


class MetricsContext:
    """Context manager for tracking operation metrics"""
    
    def __init__(self, operation_type: str):
        self.operation_type = operation_type
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        # Increment active operations
        set_active_operations(self.operation_type, 1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            record_processing_time(self.operation_type, duration)
        
        # Decrement active operations
        set_active_operations(self.operation_type, 0)
        
        # Record error if exception occurred
        if exc_type:
            record_error(self.operation_type, exc_type.__name__)


def metrics_available() -> bool:
    """Check if metrics are available"""
    return REQUEST_COUNT is not None