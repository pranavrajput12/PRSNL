from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import UUID
import os
import logging

from app.core.exceptions import ItemNotFound, InternalServerError, InvalidInput
from app.db.database import get_db_pool
from app.models.video import VideoItem, VideoMetadata, VideoTranscodeRequest, VideoTranscodeResponse, VideoDeleteResponse
from app.services.video_processor import VideoProcessor
from app.core.background_tasks import background_tasks

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/videos/{item_id}/stream", response_class=FileResponse)
async def stream_video(item_id: UUID):
    """Stream a video file by item ID."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow("SELECT video_path FROM items WHERE id = $1 AND item_type = 'video' AND status = 'completed'", item_id)
        if not item or not item['video_path']:
            raise ItemNotFound(f"Video with ID {item_id} not found or not ready.")
        
        video_path = item['video_path']
        if not os.path.exists(video_path):
            raise InternalServerError(f"Video file not found on disk: {video_path}")
        
        return FileResponse(video_path, media_type="video/mp4")

@router.get("/videos/{item_id}/metadata", response_model=VideoItem)
async def get_video_metadata(item_id: UUID):
    """Retrieve video metadata by item ID."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow("SELECT * FROM items WHERE id = $1 AND item_type = 'video'", item_id)
        if not item:
            raise ItemNotFound(f"Video with ID {item_id} not found.")
        
        # Assuming metadata is stored as JSONB in the 'metadata' column
        # and other fields map directly
        video_metadata = VideoMetadata(**item['metadata'].get('video_metadata', {})) if item['metadata'] else VideoMetadata()
        
        return VideoItem(
            id=item['id'],
            url=item['url'],
            title=item['title'],
            description=item['summary'], # Assuming summary is used for description
            author=item['metadata'].get('author'),
            duration=item['duration'],
            video_path=item['file_path'],
            thumbnail_path=item['thumbnail_url'],
            platform=item['platform'],
            metadata=video_metadata,
            downloaded_at=item['created_at'], # Assuming created_at is download time
            status=item['status']
        )

async def _transcode_video_task(item_id: UUID, quality: str):
    """Background task for video transcoding."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("UPDATE items SET status = 'transcoding' WHERE id = $1", item_id)
            logger.info(f"Starting transcoding for video {item_id} to quality {quality}")
            
            # Simulate transcoding process
            await asyncio.sleep(10) # Replace with actual transcoding logic
            
            # Update status and metadata
            await conn.execute("UPDATE items SET status = 'completed', metadata = jsonb_set(COALESCE(metadata, '{}'), '{transcoded_quality}', to_jsonb($2::text), true) WHERE id = $1", item_id, quality)
            logger.info(f"Finished transcoding for video {item_id}")
        except Exception as e:
            logger.error(f"Error during transcoding for video {item_id}: {e}", exc_info=True)
            await conn.execute("UPDATE items SET status = 'failed', metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text), true) WHERE id = $1", item_id, str(e))

@router.post("/videos/{item_id}/transcode", response_model=VideoTranscodeResponse)
async def request_video_transcode(item_id: UUID, request: VideoTranscodeRequest, background_tasks: BackgroundTasks):
    """Request transcoding of a video to a different quality."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow("SELECT id, status FROM items WHERE id = $1 AND item_type = 'video'", item_id)
        if not item:
            raise ItemNotFound(f"Video with ID {item_id} not found.")
        
        if item['status'] == 'transcoding':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video is already being transcoded.")
        
        # Add transcoding task to background
        background_tasks.add_task(_transcode_video_task, item_id, request.quality)
        
        return VideoTranscodeResponse(
            message="Video transcoding initiated",
            task_id=item_id, # Using item_id as task_id for simplicity
            status="started"
        )

async def _delete_video_task(item_id: UUID, video_path: str, thumbnail_path: Optional[str]):
    """Background task for deleting video files and database entries."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            # Delete from attachments table first
            await conn.execute("DELETE FROM attachments WHERE item_id = $1", item_id)
            # Delete from items table
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
            
            # Delete video file from disk
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Deleted video file: {video_path}")
            
            # Delete thumbnail directory
            if thumbnail_path:
                thumbnail_dir = Path(thumbnail_path).parent # Get the directory containing thumbnails
                if thumbnail_dir.exists() and thumbnail_dir.is_dir():
                    shutil.rmtree(thumbnail_dir)
                    logger.info(f"Deleted thumbnail directory: {thumbnail_dir}")
            
            logger.info(f"Successfully deleted video item {item_id} and associated files.")
        except Exception as e:
            logger.error(f"Error deleting video item {item_id}: {e}", exc_info=True)

@router.delete("/videos/{item_id}", response_model=VideoDeleteResponse)
async def delete_video(item_id: UUID, background_tasks: BackgroundTasks):
    """Delete a video and its associated files."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow("SELECT video_path, thumbnail_url FROM items WHERE id = $1 AND item_type = 'video'", item_id)
        if not item:
            raise ItemNotFound(f"Video with ID {item_id} not found.")
        
        video_path = item['video_path']
        thumbnail_url = item['thumbnail_url']

        background_tasks.add_task(_delete_video_task, item_id, video_path, thumbnail_url)
        
        return VideoDeleteResponse(
            message="Video deletion initiated",
            item_id=item_id
        )
