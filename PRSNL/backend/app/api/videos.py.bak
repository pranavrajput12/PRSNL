from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import UUID
import os
import logging
import asyncpg

from app.db.database import get_db_connection
from app.models.video import VideoInDB
from app.services.storage_manager import StorageManager
from app.core.background_tasks import background_tasks
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/videos/{video_id}/stream", summary="Stream Video", response_class=Response)
async def stream_video(video_id: UUID, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Streams a video file by its ID."""
    record = await db_connection.fetchrow(
        "SELECT file_path FROM items WHERE id = $1 AND item_type = 'video'",
        video_id
    )
    if not record or not record['file_path']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    file_path = record['file_path']
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk.")

    # Determine media type (MIME type)
    # A more robust solution would use a library like `python-magic` or `mimetypes`
    # For now, assume MP4 as per current processing
    media_type = "video/mp4"

    return FileResponse(file_path, media_type=media_type)

@router.get("/videos/{video_id}/metadata", summary="Get Video Metadata", response_model=VideoInDB)
async def get_video_metadata(video_id: UUID, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Retrieves metadata for a specific video by its ID."""
    record = await db_connection.fetchrow(
        "SELECT * FROM items WHERE id = $1 AND item_type = 'video'",
        video_id
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video metadata not found.")
    
    # Manually map record to VideoInDB as fetchrow returns a Record object
    video_data = {
        "id": record['id'],
        "url": record['url'],
        "title": record['title'],
        "description": record['summary'], # Assuming summary is used for description
        "author": record['metadata'].get('video_metadata', {}).get('uploader', record['metadata'].get('video_metadata', {}).get('channel')),
        "duration": record['duration'],
        "video_path": record['file_path'],
        "thumbnail_path": record['thumbnail_url'],
        "platform": record['platform'],
        "metadata": record['metadata'].get('video_metadata'),
        "downloaded_at": record['created_at'], # Assuming created_at is download time
        "status": record['status']
    }
    
    return VideoInDB(**video_data)

@router.post("/videos/{video_id}/transcode", summary="Request Video Transcoding", response_model=dict)
async def request_video_transcode(video_id: UUID, target_quality: str, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Requests transcoding of a video to a different quality. (Placeholder - not fully implemented)"""
    # This would typically involve a background task to re-process the video
    # For now, just acknowledge the request.
    logger.info(f"Transcode request for video {video_id} to {target_quality} received.")
    
    # Check if video exists
    record = await db_connection.fetchrow(
        "SELECT id FROM items WHERE id = $1 AND item_type = 'video'",
        video_id
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    # In a real scenario, you'd add a task to a queue here
    background_tasks.add_task(process_transcode_request, video_id, target_quality)

    return {"message": f"Transcoding request for video {video_id} to {target_quality} submitted.", "status": "accepted"}

async def process_transcode_request(video_id: UUID, target_quality: str):
    """Background task to simulate video transcoding."""
    logger.info(f"Simulating transcoding for video {video_id} to {target_quality}...")
    await asyncio.sleep(10) # Simulate work
    logger.info(f"Transcoding for video {video_id} to {target_quality} completed (simulated).")
    # In a real implementation, update DB status, file paths etc.

@router.delete("/videos/{video_id}", summary="Delete Video", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: UUID, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Deletes a video and its associated files from storage and database."""
    record = await db_connection.fetchrow(
        "SELECT file_path, thumbnail_url FROM items WHERE id = $1 AND item_type = 'video'",
        video_id
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    file_path = record['file_path']
    thumbnail_url = record['thumbnail_url']

    # Delete from database first to prevent orphaned files on disk if disk deletion fails
    await db_connection.execute("DELETE FROM attachments WHERE item_id = $1", video_id)
    await db_connection.execute("DELETE FROM items WHERE id = $1", video_id)

    # Delete files from disk in background
    background_tasks.add_task(delete_video_files_from_disk, file_path, thumbnail_url)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def delete_video_files_from_disk(video_path: str, thumbnail_path: Optional[str]):
    """Background task to delete video and thumbnail files from disk."""
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
            logger.info(f"Deleted video file from disk: {video_path}")
        except OSError as e:
            logger.error(f"Error deleting video file {video_path}: {e}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            # Assuming thumbnail_path is the base path for thumbnails (e.g., /app/media/thumbnails/uuid)
            # Need to delete the directory containing all sizes
            thumbnail_dir = Path(thumbnail_path).parent
            if thumbnail_dir.exists() and thumbnail_dir.name == Path(thumbnail_path).name: # Ensure we are deleting the correct directory
                import shutil
                shutil.rmtree(thumbnail_dir)
                logger.info(f"Deleted thumbnail directory from disk: {thumbnail_dir}")
            else:
                os.remove(thumbnail_path)
                logger.info(f"Deleted thumbnail file from disk: {thumbnail_path}")
        except OSError as e:
            logger.error(f"Error deleting thumbnail file {thumbnail_path}: {e}")