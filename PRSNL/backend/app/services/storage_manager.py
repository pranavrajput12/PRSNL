import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import asyncio

from app.config import settings
from app.db.database import get_db_pool
from app.monitoring.metrics import STORAGE_USAGE_BYTES, ORPHANED_FILE_CLEANUP_TOTAL, TEMP_FILE_CLEANUP_TOTAL

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages storage of media files, including quotas and cleanup."""

    def __init__(self, base_dir: str = "/app/media"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir = self.base_dir / "videos"
        self.thumbnails_dir = self.base_dir / "thumbnails"
        self.temp_dir = self.base_dir / "temp"

        self.videos_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

    async def get_storage_metrics(self) -> Dict:
        """
        Returns current storage usage metrics.
        """
        total_bytes = 0
        used_bytes = 0
        free_bytes = 0

        try:
            total, used, free = shutil.disk_usage(self.base_dir)
            total_bytes = total
            used_bytes = used
            free_bytes = free
        except Exception as e:
            logger.error(f"Error getting disk usage for {self.base_dir}: {e}")

        # Calculate size of managed directories
        videos_size = sum(f.stat().st_size for f in self.videos_dir.rglob('*') if f.is_file())
        thumbnails_size = sum(f.stat().st_size for f in self.thumbnails_dir.rglob('*') if f.is_file())
        temp_size = sum(f.stat().st_size for f in self.temp_dir.rglob('*') if f.is_file())

        STORAGE_USAGE_BYTES.labels(type='videos').set(videos_size)
        STORAGE_USAGE_BYTES.labels(type='thumbnails').set(thumbnails_size)
        STORAGE_USAGE_BYTES.labels(type='temp').set(temp_size)

        return {
            "total_disk_space": total_bytes,
            "used_disk_space": used_bytes,
            "free_disk_space": free_bytes,
            "managed_videos_size": videos_size,
            "managed_thumbnails_size": thumbnails_size,
            "managed_temp_size": temp_size,
            "unit": "bytes"
        }

    async def cleanup_orphaned_files(self):
        """
        Removes video and thumbnail files that are no longer referenced in the database.
        """
        logger.info("Starting orphaned file cleanup...")
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Get all file_paths from the database
                db_file_paths = set()
                rows = await conn.fetch("SELECT file_path FROM items WHERE file_path IS NOT NULL")
                for row in rows:
                    db_file_paths.add(row['file_path'])
                
                rows = await conn.fetch("SELECT file_path FROM attachments WHERE file_path IS NOT NULL")
                for row in rows:
                    db_file_paths.add(row['file_path'])

            deleted_count = 0
            deleted_size = 0

            # Check video files
            for video_file in self.videos_dir.rglob('*.mp4'): # Assuming all videos are converted to mp4
                if str(video_file) not in db_file_paths:
                    try:
                        file_size = video_file.stat().st_size
                        os.remove(video_file)
                        deleted_count += 1
                        deleted_size += file_size
                        logger.info(f"Deleted orphaned video file: {video_file}")
                    except OSError as e:
                        logger.error(f"Error deleting orphaned video file {video_file}: {e}")
            
            # Check thumbnail directories (each video has its own thumbnail directory)
            for thumbnail_dir in self.thumbnails_dir.iterdir():
                if thumbnail_dir.is_dir():
                    video_exists = False
                    for path in db_file_paths:
                        if thumbnail_dir.name in path: # Simple substring match
                            video_exists = True
                            break
                    
                    if not video_exists:
                        try:
                            dir_size = sum(f.stat().st_size for f in thumbnail_dir.rglob('*') if f.is_file())
                            shutil.rmtree(thumbnail_dir)
                            deleted_count += 1
                            deleted_size += dir_size
                            logger.info(f"Deleted orphaned thumbnail directory: {thumbnail_dir}")
                        except OSError as e:
                            logger.error(f"Error deleting orphaned thumbnail directory {thumbnail_dir}: {e}")

            logger.info(f"Orphaned file cleanup complete. Deleted {deleted_count} files/directories, total size {deleted_size} bytes.")
            ORPHANED_FILE_CLEANUP_TOTAL.labels(status='success').inc()
        except Exception as e:
            logger.error(f"Error during orphaned file cleanup: {e}")
            ORPHANED_FILE_CLEANUP_TOTAL.labels(status='failed').inc()

    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Removes temporary files older than a specified duration.
        """
        logger.info(f"Starting temporary file cleanup (older than {older_than_hours} hours)...")
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            deleted_count = 0
            deleted_size = 0

            for temp_file in self.temp_dir.rglob('*'):
                if temp_file.is_file():
                    try:
                        modified_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                        if modified_time < cutoff_time:
                            file_size = temp_file.stat().st_size
                            os.remove(temp_file)
                            deleted_count += 1
                            deleted_size += file_size
                            logger.info(f"Deleted old temp file: {temp_file}")
                    except OSError as e:
                        logger.error(f"Error deleting old temp file {temp_file}: {e}")

            logger.info(f"Temporary file cleanup complete. Deleted {deleted_count} files, total size {deleted_size} bytes.")
            TEMP_FILE_CLEANUP_TOTAL.labels(status='success').inc()
        except Exception as e:
            logger.error(f"Error during temporary file cleanup: {e}")
            TEMP_FILE_CLEANUP_TOTAL.labels(status='failed').inc()
