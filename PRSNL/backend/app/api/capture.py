from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
from uuid import uuid4

from app.core.exceptions import InvalidInput, InternalServerError
from app.core.capture_engine import CaptureEngine
from app.services.video_processor import VideoProcessor
from app.db.database import get_db_pool
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CaptureRequest(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None

@router.post("/capture", status_code=status.HTTP_201_CREATED, response_model=dict)
async def capture_item(request: CaptureRequest, background_tasks: BackgroundTasks):
    """Capture a new item (web page, note, etc.)."""
    if not request.url and not request.content:
        raise InvalidInput("Either URL or content must be provided.")
    
    try:
        pool = await get_db_pool()
        item_id = uuid4()
        
        # Detect if URL is a video
        is_video = False
        if request.url:
            video_domains = ['instagram.com', 'youtube.com', 'youtu.be', 'tiktok.com']
            is_video = any(domain in request.url for domain in video_domains)
        
        # Insert initial item record
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO items (id, url, title, status, item_type)
                VALUES ($1, $2, $3, 'pending', $4)
            """, item_id, request.url, request.title or 'Untitled', 'video' if is_video else 'article')
        
        if is_video:
            # Process video in background
            background_tasks.add_task(process_video_item, item_id, request.url)
        else:
            # Process regular item in background
            capture_engine = CaptureEngine()
            background_tasks.add_task(capture_engine.process_item, item_id, request.url)
        
        return {
            "message": "Item capture initiated",
            "item_id": str(item_id),
            "item_type": 'video' if is_video else 'article'
        }
        
    except Exception as e:
        logger.error(f"Failed to capture item: {str(e)}")
        raise InternalServerError(f"Failed to capture item: {e}")


async def process_video_item(item_id, url):
    """Process a video item in the background"""
    try:
        video_processor = VideoProcessor()
        pool = await get_db_pool()
        
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
                    metadata = $8,
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
        logger.error(f"Error processing video item {item_id}: {str(e)}")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                WHERE id = $1
            """, item_id, str(e))
