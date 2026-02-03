"""
Memory management utilities for audio processing operations
"""

import os
import gc
import psutil
import asyncio
import threading
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import resource

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    used_percentage: float
    process_memory_mb: float
    

class MemoryMonitor:
    """Monitor system and process memory usage"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.is_monitoring = False
        self.memory_alerts = []
        
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        try:
            # System memory
            memory = psutil.virtual_memory()
            
            # Process memory
            process_memory = self.process.memory_info()
            
            return MemoryStats(
                total_memory_mb=memory.total / 1024 / 1024,
                available_memory_mb=memory.available / 1024 / 1024,
                used_memory_mb=memory.used / 1024 / 1024,
                used_percentage=memory.percent,
                process_memory_mb=process_memory.rss / 1024 / 1024
            )
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats(0, 0, 0, 0, 0)
    
    def check_memory_available(self, required_mb: int) -> bool:
        """Check if enough memory is available for operation"""
        stats = self.get_memory_stats()
        
        # Check system memory
        if stats.available_memory_mb < required_mb:
            logger.warning(f"Insufficient system memory: {stats.available_memory_mb}MB available, {required_mb}MB required")
            return False
            
        # Check process memory limit
        if stats.process_memory_mb + required_mb > settings.MEMORY_LIMIT_MB:
            logger.warning(f"Process memory limit exceeded: {stats.process_memory_mb}MB + {required_mb}MB > {settings.MEMORY_LIMIT_MB}MB")
            return False
            
        return True
    
    def check_memory_warning(self) -> bool:
        """Check if memory usage is approaching warning threshold"""
        stats = self.get_memory_stats()
        
        if stats.process_memory_mb > settings.MEMORY_WARNING_THRESHOLD_MB:
            logger.warning(f"Memory usage warning: {stats.process_memory_mb}MB > {settings.MEMORY_WARNING_THRESHOLD_MB}MB threshold")
            return True
            
        return False
    
    def force_cleanup(self):
        """Force garbage collection and cleanup"""
        try:
            gc.collect()
            logger.debug("Forced garbage collection completed")
        except Exception as e:
            logger.error(f"Error during forced cleanup: {e}")


class StreamingFileHandler:
    """Handle file uploads with streaming to avoid loading entire file into memory"""
    
    @staticmethod
    async def stream_upload_to_temp(upload_file, chunk_size: int = None) -> Path:
        """
        Stream uploaded file to temporary file without loading into memory
        
        Args:
            upload_file: FastAPI UploadFile object
            chunk_size: Size of chunks to read (default from settings)
            
        Returns:
            Path to temporary file
        """
        if chunk_size is None:
            chunk_size = settings.STREAMING_CHUNK_SIZE
        
        # Create temporary file
        suffix = Path(upload_file.filename or "audio").suffix or ".tmp"
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=settings.TEMP_DIR)
        
        try:
            total_size = 0
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                # Stream file contents in chunks
                while True:
                    chunk = await upload_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    temp_file.write(chunk)
                    total_size += len(chunk)
                    
                    # Check file size limit
                    if total_size > settings.MAX_FILE_SIZE_BYTES:
                        raise ValueError(f"File size exceeds limit: {total_size} > {settings.MAX_FILE_SIZE_BYTES}")
            
            logger.info(f"Streamed upload to temporary file: {temp_path} ({total_size} bytes)")
            return Path(temp_path)
            
        except Exception:
            # Clean up on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise


class ProcessResourceManager:
    """Manage memory and CPU resources for subprocess operations"""
    
    def __init__(self):
        self.active_processes: Dict[int, Dict[str, Any]] = {}
        self.memory_monitor = MemoryMonitor()
    
    def set_process_limits(self, memory_limit_mb: int = None):
        """Set resource limits for current process"""
        if memory_limit_mb is None:
            memory_limit_mb = settings.PROCESS_MEMORY_LIMIT_MB
        
        try:
            # Set memory limit (in bytes)
            memory_limit_bytes = memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
            logger.debug(f"Set process memory limit: {memory_limit_mb}MB")
        except Exception as e:
            logger.warning(f"Failed to set process memory limit: {e}")
    
    def monitor_process(self, process, operation_name: str):
        """Monitor a subprocess for memory usage"""
        def _monitor():
            try:
                proc = psutil.Process(process.pid)
                max_memory = 0
                
                while process.poll() is None:
                    try:
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        max_memory = max(max_memory, memory_mb)
                        
                        if memory_mb > settings.PROCESS_MEMORY_LIMIT_MB:
                            logger.error(f"Process {operation_name} exceeded memory limit: {memory_mb}MB")
                            process.terminate()
                            break
                        
                        time.sleep(settings.MEMORY_CHECK_INTERVAL)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                
                logger.info(f"Process {operation_name} completed. Peak memory usage: {max_memory:.1f}MB")
                
            except Exception as e:
                logger.error(f"Error monitoring process {operation_name}: {e}")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=_monitor, daemon=True)
        monitor_thread.start()


class ConcurrentOperationLimiter:
    """Limit concurrent heavy operations to prevent memory exhaustion"""
    
    def __init__(self):
        self.active_operations = 0
        self.operation_lock = asyncio.Lock()
        self.memory_monitor = MemoryMonitor()
    
    @asynccontextmanager
    async def acquire_operation_slot(self, operation_name: str, estimated_memory_mb: int):
        """
        Acquire a slot for heavy operation with memory checking
        
        Args:
            operation_name: Name of the operation for logging
            estimated_memory_mb: Estimated memory usage
        """
        async with self.operation_lock:
            # Check concurrent operation limit
            if self.active_operations >= settings.MAX_CONCURRENT_OPERATIONS:
                raise RuntimeError(f"Maximum concurrent operations reached: {self.active_operations}/{settings.MAX_CONCURRENT_OPERATIONS}")
            
            # Check memory availability
            if not self.memory_monitor.check_memory_available(estimated_memory_mb):
                raise RuntimeError(f"Insufficient memory for operation {operation_name}: requires {estimated_memory_mb}MB")
            
            self.active_operations += 1
            logger.info(f"Started operation {operation_name} ({self.active_operations}/{settings.MAX_CONCURRENT_OPERATIONS} active)")
        
        try:
            yield
        finally:
            async with self.operation_lock:
                self.active_operations -= 1
                logger.info(f"Completed operation {operation_name} ({self.active_operations}/{settings.MAX_CONCURRENT_OPERATIONS} active)")
                
                # Force cleanup after heavy operation
                gc.collect()


class MemoryEfficientProcessor:
    """Memory-efficient file processing utilities"""
    
    @staticmethod
    async def copy_file_chunked(src_path: Path, dst_path: Path, chunk_size: int = None) -> None:
        """
        Copy file in chunks to avoid loading entire file into memory
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            chunk_size: Size of chunks to copy
        """
        if chunk_size is None:
            chunk_size = settings.STREAMING_CHUNK_SIZE * 128  # Larger chunks for file copy
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        def _copy():
            with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
        
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, _copy)
    
    @staticmethod
    def estimate_processing_memory(file_size_bytes: int, operation_type: str) -> int:
        """
        Estimate memory requirements for different operations
        
        Args:
            file_size_bytes: Input file size in bytes
            operation_type: Type of operation ('stem_separation', 'format_conversion', etc.)
            
        Returns:
            Estimated memory usage in MB
        """
        file_size_mb = file_size_bytes / 1024 / 1024
        
        if operation_type == 'stem_separation':
            # Demucs typically uses 3-5x file size in memory
            return int(file_size_mb * 4)
        elif operation_type == 'format_conversion':
            # FFmpeg uses roughly 2x file size
            return int(file_size_mb * 2)
        else:
            # Default estimate
            return int(file_size_mb * 2)


# Global instances
memory_monitor = MemoryMonitor()
operation_limiter = ConcurrentOperationLimiter()
process_manager = ProcessResourceManager()
streaming_handler = StreamingFileHandler()
efficient_processor = MemoryEfficientProcessor()