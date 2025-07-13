import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages storage for media files, including cleanup and metrics."""

    def __init__(self, media_dir: str = None):
        if media_dir is None:
            media_dir = settings.MEDIA_DIR
        self.media_dir = Path(media_dir)
        self.videos_dir = self.media_dir / "videos"
        self.thumbnails_dir = self.media_dir / "thumbnails"
        self.temp_dir = self.media_dir / "temp"

        # Ensure directories exist
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def cleanup_orphaned_files(self):
        """Removes video and thumbnail files that are no longer referenced in the database."""
        logger.info("Starting orphaned file cleanup...")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get all file paths from the database
            db_file_paths = set()
            records = await conn.fetch("SELECT file_path FROM attachments WHERE file_path IS NOT NULL")
            for record in records:
                db_file_paths.add(record['file_path'])
            
            # Also check items table for video_url and thumbnail_url
            item_records = await conn.fetch("SELECT video_url, thumbnail_url FROM items WHERE type = 'video'")
            for record in item_records:
                if record['video_url']:
                    db_file_paths.add(record['video_url'])
                if record['thumbnail_url']:
                    db_file_paths.add(record['thumbnail_url'])

        # Check video files
        deleted_videos = 0
        for root, _, files in os.walk(self.videos_dir):
            for file in files:
                file_path = Path(root) / file
                if str(file_path) not in db_file_paths:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted orphaned video file: {file_path}")
                        deleted_videos += 1
                    except OSError as e:
                        logger.error(f"Error deleting orphaned video file {file_path}: {e}")
        
        # Check thumbnail files
        deleted_thumbnails = 0
        for root, _, files in os.walk(self.thumbnails_dir):
            for file in files:
                file_path = Path(root) / file
                if str(file_path) not in db_file_paths:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted orphaned thumbnail file: {file_path}")
                        deleted_thumbnails += 1
                    except OSError as e:
                        logger.error(f"Error deleting orphaned thumbnail file {file_path}: {e}")

        logger.info(f"Orphaned file cleanup complete. Deleted {deleted_videos} videos and {deleted_thumbnails} thumbnails.")

    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """Removes temporary files older than a specified duration."""
        logger.info(f"Starting temporary file cleanup (older than {older_than_hours} hours)...")
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_temp_files = 0

        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if modified_time < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Deleted old temporary file: {file_path}")
                        deleted_temp_files += 1
                except OSError as e:
                    logger.error(f"Error deleting temporary file {file_path}: {e}")
        logger.info(f"Temporary file cleanup complete. Deleted {deleted_temp_files} files.")

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Calculates and returns storage usage metrics."""
        total_size_bytes = 0
        video_size_bytes = 0
        thumbnail_size_bytes = 0
        temp_size_bytes = 0

        for root, _, files in os.walk(self.media_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size
                    total_size_bytes += file_size
                    if self.videos_dir in file_path.parents:
                        video_size_bytes += file_size
                    elif self.thumbnails_dir in file_path.parents:
                        thumbnail_size_bytes += file_size
                    elif self.temp_dir in file_path.parents:
                        temp_size_bytes += file_size
                except OSError as e:
                    logger.warning(f"Could not get size for {file_path}: {e}")

        return {
            "total_size_bytes": total_size_bytes,
            "total_size_gb": round(total_size_bytes / (1024**3), 2),
            "video_size_bytes": video_size_bytes,
            "video_size_gb": round(video_size_bytes / (1024**3), 2),
            "thumbnail_size_bytes": thumbnail_size_bytes,
            "thumbnail_size_gb": round(thumbnail_size_bytes / (1024**3), 2),
            "temp_size_bytes": temp_size_bytes,
            "temp_size_gb": round(temp_size_bytes / (1024**3), 2),
            "last_updated": datetime.now().isoformat()
        }

    # Placeholder for future quota system
    async def check_user_quota(self, user_id: str) -> Dict[str, Any]:
        """Checks storage quota for a given user (future-proofing)."""
        # This would involve querying user-specific storage limits and current usage
        logger.info(f"Checking quota for user {user_id} - not yet implemented.")
        return {"user_id": user_id, "quota_enabled": False, "current_usage_gb": 0, "limit_gb": -1}

    # Placeholder for future backup strategy
    async def initiate_backup(self):
        """Initiates a backup of media files (future-proofing)."""
        logger.info("Initiating media backup - not yet implemented.")
        return {"status": "backup_not_implemented"}

    # Placeholder for CDN-ready file structure (already handled by current path structure)
    def get_cdn_path(self, file_path: str) -> str:
        """Generates a CDN-ready path for a given internal file path."""
        # Assuming media_dir is the base for CDN. Example: /app/media/videos/2025/01/uuid.mp4 -> /videos/2025/01/uuid.mp4
        relative_path = Path(file_path).relative_to(self.media_dir)
        return f"/{relative_path}"