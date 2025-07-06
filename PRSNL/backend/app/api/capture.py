from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
import asyncio
from uuid import uuid4

from app.core.exceptions import InvalidInput, InternalServerError
from app.core.capture_engine import CaptureEngine
from app.services.video_processor import VideoProcessor
from app.db.database import get_db_pool, get_db_connection
import logging
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter()

class CaptureRequest(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    content: Optional[str] = None

async def _update_video_processing_progress(item_id: uuid4, progress_data: Dict):
    """Updates the item's metadata with progress information."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE items
            SET metadata = jsonb_set(COALESCE(metadata, '{}'), '{processing_progress}', to_jsonb($2::jsonb), true)
            WHERE id = $1
        """, item_id, progress_data)
    logger.info(f"Item {item_id} progress: {progress_data.get('status')} {progress_data.get('percent', 0):.1f}%")

@router.post("/capture", status_code=status.HTTP_201_CREATED, response_model=dict)
async def capture_item(request: CaptureRequest, background_tasks: BackgroundTasks, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Capture a new item (web page, note, etc.)."""
    if not request.url and not request.content:
        raise InvalidInput("Either URL or content must be provided.")
    
    item_id = uuid4()
    item_type = 'article'
    
    try:
        if request.url:
            video_processor = VideoProcessor()
            video_info = await video_processor.get_video_info(str(request.url))
            
            if video_info and video_info.get('platform') != 'unknown':
                item_type = 'video'
                # Perform video validation before inserting initial record
                try:
                    await video_processor.validate_video_url(str(request.url))
                except ValueError as e:
                    raise InvalidInput(f"Video validation failed: {e}")
        
        # Insert initial item record
        await db_connection.execute("""
            INSERT INTO items (id, url, title, status, item_type)
            VALUES ($1, $2, $3, 'pending', $4)
        """, item_id, str(request.url) if request.url else None, request.title or 'Untitled', item_type)
        
        if item_type == 'video':
            # Process video in background
            background_tasks.add_task(process_video_item, item_id, str(request.url))
        else:
            # Process regular item in background
            capture_engine = CaptureEngine()
            background_tasks.add_task(capture_engine.process_item, item_id, str(request.url) if request.url else None, request.content)
        
        return {
            "message": "Item capture initiated",
            "item_id": str(item_id),
            "item_type": item_type
        }
        
    except Exception as e:
        logger.error(f"Failed to capture item: {str(e)}")
        # Update item status to failed if initial insertion happened
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                WHERE id = $1
            """, item_id, str(e))
        raise InternalServerError(f"Failed to capture item: {e}")


async def process_video_item(item_id: uuid4, url: str):
    """Process a video item in the background"""
    video_processor = VideoProcessor()
    video_processor.set_progress_callback(lambda p: _update_video_processing_progress(item_id, p))
    pool = await get_db_pool()
    try:
        # Download and process video
        logger.info(f"Processing video from {url}")
        video_data = await video_processor.download_video(url)
        
        # Update item with video data
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET
                    title = $2,
                    summary = $3,
                    file_path = $4,
                    duration = $5,
                    thumbnail_url = $6,
                    platform = $7,
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{video_metadata}', to_jsonb($8::jsonb), true),
                    status = 'completed',
                    updated_at = NOW()
                WHERE id = $1
            """,
                item_id,
                video_data.title,
                video_data.description,
                video_data.video_path,
                video_data.duration,
                video_data.thumbnail_path,
                video_data.platform,
                video_data.metadata
            )
            
            # Also insert into attachments table
            await conn.execute("""
                INSERT INTO attachments (item_id, file_path, file_type, mime_type, metadata)
                VALUES ($1, $2, 'video', 'video/mp4', $3)
            """,
                item_id,
                video_data.video_path,
                video_data.metadata
            )
            
        logger.info(f"Successfully processed video item {item_id}")
        
    except Exception as e:
        logger.error(f"Error processing video item {item_id}: {str(e)}", exc_info=True)
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                WHERE id = $1
            """, item_id, str(e))
