# app/utils/cleanup.py
"""Automatic cleanup of old files from downloads/"""

import asyncio
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


async def cleanup_old_files(
    directory: Path = Path("downloads"), 
    max_age_hours: int = 1,
    file_pattern: str = "*.mp3"
) -> int:
    """Delete files older than max_age_hours from directory"""
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist")
        return 0
    
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for file_path in directory.glob(file_pattern):
            if not file_path.is_file():
                continue
            
            file_age = now - file_path.stat().st_mtime
            
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted: {file_path.name} (age: {file_age / 3600:.1f}h)")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup: {deleted_count} file(s) deleted")
        
        return deleted_count
    
    except Exception as e:
        logger.error(f"Cleanup error: {e}", exc_info=True)
        return deleted_count


async def cleanup_task(
    interval_minutes: int = 30,
    max_age_hours: int = 1,
    directory: Path = Path("downloads")
) -> None:
    """Background task for periodic file cleanup"""
    logger.info(f"Cleanup task started: interval={interval_minutes}m, max_age={max_age_hours}h")
    
    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)
            await cleanup_old_files(directory, max_age_hours)
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cleanup task error: {e}", exc_info=True)
