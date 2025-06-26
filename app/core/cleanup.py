"""
File cleanup utilities for managing temporary files and old downloads
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import List

from .config import settings

logger = logging.getLogger(__name__)


def cleanup_old_files(directory: Path, max_age_hours: int = None) -> int:
    """
    Remove files older than max_age_hours from directory
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours (default: settings.FILE_RETENTION_HOURS)
    
    Returns:
        Number of files removed
    """
    if max_age_hours is None:
        max_age_hours = settings.FILE_RETENTION_HOURS
    
    if not directory.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    removed_count = 0
    
    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Removed old file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to remove file {file_path}: {e}")
        
        # Remove empty directories
        for dir_path in directory.rglob("*"):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.debug(f"Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Directory might not be empty due to race conditions
                    
    except Exception as e:
        logger.error(f"Error during cleanup of {directory}: {e}")
    
    return removed_count


def cleanup_all_directories() -> dict:
    """
    Clean up all configured directories
    
    Returns:
        Dictionary with cleanup results
    """
    results = {}
    
    directories_to_clean = [
        (settings.UPLOAD_DIR, "uploads"),
        (settings.OUTPUT_DIR, "outputs"), 
        (settings.TEMP_DIR, "temp")
    ]
    
    for directory, name in directories_to_clean:
        try:
            removed = cleanup_old_files(directory)
            results[name] = {
                "removed_files": removed,
                "status": "success"
            }
            if removed > 0:
                logger.info(f"Cleaned up {removed} files from {name} directory")
        except Exception as e:
            results[name] = {
                "removed_files": 0,
                "status": "error",
                "error": str(e)
            }
            logger.error(f"Failed to clean {name} directory: {e}")
    
    return results


def periodic_cleanup():
    """Run periodic cleanup in background thread"""
    while True:
        try:
            logger.info("Starting periodic cleanup...")
            results = cleanup_all_directories()
            total_removed = sum(r.get("removed_files", 0) for r in results.values())
            logger.info(f"Periodic cleanup completed. Removed {total_removed} files total.")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
        
        # Sleep for configured interval
        time.sleep(settings.CLEANUP_INTERVAL_HOURS * 3600)


def start_cleanup_scheduler():
    """Start the background cleanup scheduler"""
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    logger.info(f"Started cleanup scheduler (interval: {settings.CLEANUP_INTERVAL_HOURS}h)")


def get_directory_stats(directory: Path) -> dict:
    """
    Get statistics about a directory
    
    Args:
        directory: Directory to analyze
        
    Returns:
        Dictionary with directory statistics
    """
    if not directory.exists():
        return {
            "exists": False,
            "file_count": 0,
            "total_size_mb": 0,
            "oldest_file_age_hours": 0
        }
    
    file_count = 0
    total_size = 0
    oldest_time = time.time()
    current_time = time.time()
    
    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
                oldest_time = min(oldest_time, file_path.stat().st_mtime)
    except Exception as e:
        logger.error(f"Error getting stats for {directory}: {e}")
        return {"error": str(e)}
    
    oldest_age_hours = (current_time - oldest_time) / 3600 if file_count > 0 else 0
    
    return {
        "exists": True,
        "file_count": file_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest_file_age_hours": round(oldest_age_hours, 2)
    }
