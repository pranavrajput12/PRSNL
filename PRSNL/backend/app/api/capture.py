from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
import asyncio
import json
from uuid import uuid4

from app.core.exceptions import InvalidInput, InternalServerError
from app.core.capture_engine import CaptureEngine
from app.services.video_processor import VideoProcessor
from app.services.llm_processor import LLMProcessor
from app.db.database import get_db_pool, get_db_connection, update_item_embedding
from app.services.embedding_service import embedding_service
import logging
import asyncpg
from app.monitoring.metrics import VIDEO_CAPTURE_REQUESTS, VIDEO_DOWNLOAD_OUTCOMES, VIDEO_DOWNLOAD_DURATION_SECONDS, VIDEO_PROCESSING_DURATION_SECONDS
import time

logger = logging.getLogger(__name__)

router = APIRouter()

class CaptureRequest(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = []
    type: Optional[str] = "page"  # "page" or "selection"

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
        VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
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
                    VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
                    raise InvalidInput(f"Video validation failed: {e}")
        
        # Insert initial item record with metadata for capture type
        metadata = {"capture_type": request.type}
        await db_connection.execute("""
            INSERT INTO items (id, url, title, status, item_type, metadata)
            VALUES ($1, $2, $3, 'pending', $4, $5::jsonb)
        """, item_id, str(request.url) if request.url else None, request.title or 'Untitled', item_type, json.dumps(metadata))
        
        # Process tags if provided
        if request.tags:
            for tag_name in request.tags:
                # Get or create tag
                tag_id = await db_connection.fetchval("""
                    INSERT INTO tags (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, tag_name.lower())
                
                # Link tag to item
                await db_connection.execute("""
                    INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, item_id, tag_id)
        
        if item_type == 'video':
            # Process video in background
            background_tasks.add_task(process_video_item, item_id, str(request.url))
        else:
            # Process regular item in background
            capture_engine = CaptureEngine()
            background_tasks.add_task(capture_engine.process_item, item_id, str(request.url) if request.url else None, request.content)
        
        VIDEO_CAPTURE_REQUESTS.labels(status='success').inc()
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
        VIDEO_CAPTURE_REQUESTS.labels(status='internal_error').inc()
        raise InternalServerError(f"Failed to capture item: {e}")


async def process_video_item(item_id: uuid4, url: str):
    """Process a video item in the background"""
    video_processor = VideoProcessor()
    video_processor.set_progress_callback(lambda p: _update_video_processing_progress(item_id, p))
    pool = await get_db_pool()
    llm_processor = LLMProcessor()
    start_time = time.time()
    try:
        # Download and process video
        logger.info(f"Processing video from {url}")
        video_data = await video_processor.download_video(url)
        download_duration = time.time() - start_time
        VIDEO_DOWNLOAD_DURATION_SECONDS.labels(platform=video_data.platform, outcome='success').observe(download_duration)

        # Transcribe video
        await websocket_manager.send_personal_message(f"Transcribing video for item {item_id}...", str(item_id))
        transcription = await video_processor.transcribe_video(video_data.video_path)
        if transcription:
            async with pool.acquire() as conn:
                await conn.execute("UPDATE items SET transcription = $1 WHERE id = $2", transcription, item_id)
                logger.info(f"Stored transcription for item {item_id}")
            await websocket_manager.send_personal_message(f"Transcription complete for item {item_id}.", str(item_id))
        else:
            await websocket_manager.send_personal_message(f"Transcription failed for item {item_id}.", str(item_id))

        # Process with AI for intelligent summary and tags
        logger.info(f"Analyzing video content with AI for item {item_id}")
        ai_content = f"""
Video Title: {video_data.title}
Description: {video_data.description}
Platform: {video_data.platform}
Duration: {video_data.duration} seconds
Uploader: {video_data.metadata.get('uploader', 'Unknown')}
View Count: {video_data.metadata.get('view_count', 'Unknown')}

Full Description:
{video_data.description or 'No description available'}
"""
        
        processed_content = await llm_processor.process(
            content=ai_content,
            url=url,
            title=video_data.title
        )
        
        # Merge AI-generated tags with existing tags
        all_tags = list(set(processed_content.tags))
        
        # Update metadata with AI analysis
        enhanced_metadata = video_data.metadata.copy()
        enhanced_metadata['ai_analysis'] = {
            'summary': processed_content.summary,
            'tags': processed_content.tags,
            'processed_at': time.time()
        }
        
        # Update item with video data and AI analysis
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
                processed_content.title or video_data.title,  # Use AI title if available
                processed_content.summary,  # Use AI-generated summary
                video_data.video_path,
                video_data.duration,
                video_data.thumbnail_path,
                video_data.platform,
                json.dumps(enhanced_metadata)  # Include AI analysis in metadata
            )
            
            # Generate and store embedding
            if processed_content.summary:
                embedding = await embedding_service.get_embedding(processed_content.summary)
                if embedding:
                    await update_item_embedding(str(item_id), embedding)
                    logger.info(f"Generated and stored embedding for video item {item_id}")
            
            # Add AI-generated tags
            if processed_content.tags:
                for tag_name in processed_content.tags:
                    # Get or create tag
                    tag_id = await conn.fetchval("""
                        INSERT INTO tags (name) VALUES ($1)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """, tag_name.lower())
                    
                    # Link tag to item
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, item_id, tag_id)
            
            # Also insert into attachments table
            await conn.execute("""
                INSERT INTO attachments (item_id, file_path, file_type, mime_type, metadata)
                VALUES ($1, $2, 'video', 'video/mp4', $3)
            """,
                item_id,
                video_data.video_path,
                json.dumps(video_data.metadata) if isinstance(video_data.metadata, dict) else video_data.metadata
            )
            
        logger.info(f"Successfully processed video item {item_id}")
        VIDEO_DOWNLOAD_OUTCOMES.labels(platform=video_data.platform, outcome='success').inc()
        
    except Exception as e:
        logger.error(f"Error processing video item {item_id}: {str(e)}", exc_info=True)
        download_duration = time.time() - start_time
        VIDEO_DOWNLOAD_DURATION_SECONDS.labels(platform='unknown', outcome='failed').observe(download_duration) # Platform might be unknown on failure
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                WHERE id = $1
            """, item_id, str(e))
        VIDEO_DOWNLOAD_OUTCOMES.labels(platform='unknown', outcome='failed').inc() # Platform might be unknown on failure
