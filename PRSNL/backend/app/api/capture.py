from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Request
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
from app.models.schemas import CaptureRequest, CaptureResponse, ItemStatus
from app.middleware.rate_limit import capture_limiter
import logging
import asyncpg
from app.monitoring.metrics import VIDEO_CAPTURE_REQUESTS, VIDEO_DOWNLOAD_OUTCOMES, VIDEO_DOWNLOAD_DURATION_SECONDS, VIDEO_PROCESSING_DURATION_SECONDS
import time
from app.api.instagram_handler import process_instagram_bookmark
from app.services.websocket_manager import websocket_manager
from app.utils.media_detector import MediaDetector

logger = logging.getLogger(__name__)

router = APIRouter()

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

from app.services.cache import invalidate_cache, CacheKeys

@router.post("/capture", status_code=status.HTTP_201_CREATED, response_model=CaptureResponse)
@capture_limiter
@invalidate_cache(patterns=[f"{CacheKeys.STATS}:*", f"{CacheKeys.SEARCH}:*"])
async def capture_item(request: Request, capture_request: CaptureRequest, background_tasks: BackgroundTasks, db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Capture a new item (web page, note, file, etc.)."""
    # Check if files are provided in the request
    has_files = hasattr(capture_request, 'uploaded_files') and capture_request.uploaded_files
    
    # Check for highlight field as well (legacy field name)
    has_highlight = hasattr(capture_request, 'highlight') and capture_request.highlight
    
    if not capture_request.url and not capture_request.content and not has_files and not has_highlight:
        VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
        raise InvalidInput("Either URL, content, or files must be provided.")
    
    item_id = uuid4()
    item_type = 'article'
    
    try:
        # Check for duplicate URL if URL is provided
        if capture_request.url:
            existing_item = await db_connection.fetchrow("""
                SELECT id, title, created_at, status
                FROM items
                WHERE url = $1
                LIMIT 1
            """, str(capture_request.url))
            
            if existing_item:
                raise InvalidInput(
                    f"This URL already exists in your knowledge base. "
                    f"Item: '{existing_item['title']}' (created {existing_item['created_at'].strftime('%Y-%m-%d')})"
                )
        
        # Detect media type
        media_info = None
        item_type = 'article'  # Default to article
        
        if capture_request.url:
            media_info = MediaDetector.detect_media_type(str(capture_request.url))
            
            if media_info['type'] == 'video':
                item_type = 'video'
                video_processor = VideoProcessor()
                video_info = await video_processor.get_video_info(str(capture_request.url))
                
                # Skip validation for Instagram to allow bookmarking
                if media_info.get('platform') != 'instagram':
                    # Perform video validation before inserting initial record
                    try:
                        await video_processor.validate_video_url(str(capture_request.url))
                    except ValueError as e:
                        VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
                        raise InvalidInput(f"Video validation failed: {e}")
            elif media_info['type'] == 'image':
                item_type = 'image'
            elif media_info['type'] == 'article':
                item_type = 'article'
            # Add other media types as needed
        
        # Insert initial item record with metadata for capture type
        metadata = {
            "capture_type": capture_request.type if hasattr(capture_request, 'type') else 'page',
            "media_info": media_info,
            "type": item_type,  # Store item type in metadata
            "content_type": capture_request.content_type  # Store user-selected content type
        }
        logger.info(f"Creating item {item_id} with type {item_type}, URL: {capture_request.url}")
        
        # For content-only captures, store content in raw_content field
        # Handle both content and highlight fields (highlight is legacy field name)
        initial_content = capture_request.content if capture_request.content else capture_request.highlight if hasattr(capture_request, 'highlight') else None
        
        await db_connection.execute("""
            INSERT INTO items (id, url, title, raw_content, status, type, metadata, content_type, enable_summarization)
            VALUES ($1, $2, $3, $4, 'pending', $5, $6::jsonb, $7, $8)
        """, item_id, str(capture_request.url) if capture_request.url else None, capture_request.title or 'Untitled', initial_content, item_type, json.dumps(metadata), capture_request.content_type or 'auto', capture_request.enable_summarization or False)
        
        logger.info(f"Successfully inserted item {item_id} into database")
        
        # Process tags if provided
        if capture_request.tags:
            for tag_name in capture_request.tags:
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
            # Special handling for Instagram
            if capture_request.url and 'instagram.com' in str(capture_request.url).lower():
                background_tasks.add_task(process_instagram_bookmark, item_id, str(capture_request.url))
            else:
                # Process video metadata quickly, then enhance with AI in background
                background_tasks.add_task(process_video_metadata_fast, item_id, str(capture_request.url))
        else:
            # Let the worker handle all non-video processing
            logger.info(f"Item {item_id} will be processed by worker")
        
        VIDEO_CAPTURE_REQUESTS.labels(status='success').inc()
        logger.info(f"Capture initiated successfully for item {item_id}")
        
        # No duplicate check needed here - already checked before item creation
        duplicate_info = None
        
        return CaptureResponse(
            id=item_id,
            status=ItemStatus.PENDING,
            message="Item capture initiated",
            duplicate_info=duplicate_info
        )
        
    except InvalidInput:
        # Re-raise InvalidInput exceptions without wrapping them
        raise
    except Exception as e:
        logger.error(f"Failed to capture item: {str(e)}", exc_info=True)
        # Update item status to failed if initial insertion happened
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE items
                    SET status = 'failed',
                        metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                    WHERE id = $1
                """, item_id, str(e))
        except Exception as update_error:
            logger.error(f"Failed to update item status: {update_error}")
        VIDEO_CAPTURE_REQUESTS.labels(status='internal_error').inc()
        raise InternalServerError(f"Failed to capture item: {e}")


async def process_video_metadata_fast(item_id: uuid4, url: str):
    """Fast video metadata processing without AI - AI enhancement happens in background"""
    video_processor = VideoProcessor()
    pool = await get_db_pool()
    start_time = time.time()
    
    try:
        # Get video info without downloading
        logger.info(f"🔵 Fast processing video metadata from {url}")
        video_info = await video_processor.get_video_info(url)
        
        if not video_info:
            raise ValueError("Could not extract video information")
        
        # Get media detection info for embed URL
        media_info = MediaDetector.detect_media_type(url)
        
        # Create basic metadata without AI processing
        basic_metadata = {
            'video_info': video_info,
            'media_info': media_info,
            'embed_url': media_info.get('embed_url', url),
            'platform': video_info.get('platform', 'unknown'),
            'downloaded': False,
            'streaming_url': url,
            'processing_status': 'basic_complete',  # Flag for AI enhancement
            'processed_at': time.time()
        }
        
        # Update item with basic video metadata (fast)
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET
                    title = $2,
                    summary = $3,
                    duration = $4,
                    thumbnail_url = $5,
                    video_url = $6,
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{video_metadata}', to_jsonb($7::jsonb), true),
                    status = 'completed',
                    updated_at = NOW()
                WHERE id = $1
            """,
                item_id,
                video_info.get('title', 'Unknown'),
                video_info.get('description', 'No description available')[:500],  # Brief summary
                video_info.get('duration'),
                video_info.get('thumbnail'),
                media_info.get('embed_url', url),
                json.dumps(basic_metadata)
            )
        
        logger.info(f"🟢 Fast video metadata processing completed for item {item_id} in {time.time() - start_time:.2f}s")
        
        # Now enhance with AI in background (non-blocking)
        # We'll use asyncio.create_task to run in background
        asyncio.create_task(enhance_video_with_ai(item_id, url, video_info, media_info))
        
    except Exception as e:
        logger.error(f"🔴 Error in fast video processing for item {item_id}: {str(e)}", exc_info=True)
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'failed',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                WHERE id = $1
            """, item_id, str(e))


async def enhance_video_with_ai(item_id: uuid4, url: str, video_info: dict, media_info: dict):
    """Enhance video with AI analysis in background"""
    pool = await get_db_pool()
    llm_processor = LLMProcessor()
    
    try:
        logger.info(f"🔵 Enhancing video {item_id} with AI analysis")
        
        # Process with AI for intelligent summary and tags
        ai_content = f"""
Video Title: {video_info.get('title', 'Unknown')}
Description: {video_info.get('description', 'No description available')}
Platform: {video_info.get('platform', 'Unknown')}
Duration: {video_info.get('duration', 0)} seconds
Author: {video_info.get('author', 'Unknown')}
"""
        
        processed_content = await llm_processor.process_content(
            content=ai_content,
            url=url,
            title=video_info.get('title', 'Unknown')
        )
        
        # Update metadata with AI analysis
        enhanced_metadata = {
            'video_info': video_info,
            'media_info': media_info,
            'embed_url': media_info.get('embed_url', url),
            'platform': video_info.get('platform', 'unknown'),
            'downloaded': False,
            'streaming_url': url,
            'processing_status': 'ai_complete',
            'ai_analysis': {
                'summary': processed_content.summary,
                'tags': processed_content.tags,
                'key_points': processed_content.key_points,
                'sentiment': processed_content.sentiment,
                'reading_time': processed_content.reading_time,
                'entities': processed_content.entities,
                'questions': processed_content.questions,
                'processed_at': time.time()
            }
        }
        
        # Update item with AI analysis
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET
                    title = $2,
                    summary = $3,
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{video_metadata}', to_jsonb($4::jsonb), true),
                    updated_at = NOW()
                WHERE id = $1
            """,
                item_id,
                processed_content.title or video_info.get('title', 'Unknown'),
                processed_content.summary,
                json.dumps(enhanced_metadata)
            )
            
            # Generate and store embedding
            if processed_content.summary:
                try:
                    embedding = await embedding_service.generate_embedding(processed_content.summary)
                    if embedding:
                        await update_item_embedding(str(item_id), embedding)
                        logger.info(f"🟢 Generated embedding for video item {item_id}")
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for video {item_id}: {e}")
            
            # Add AI-generated tags
            if processed_content.tags:
                for tag_name in processed_content.tags:
                    tag_id = await conn.fetchval("""
                        INSERT INTO tags (name) VALUES ($1)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """, tag_name.lower())
                    
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, item_id, tag_id)
        
        logger.info(f"🟢 AI enhancement completed for video item {item_id}")
        
    except Exception as e:
        logger.error(f"🔴 Error enhancing video {item_id} with AI: {str(e)}", exc_info=True)
        # Don't fail the item, just log the error - basic metadata is already saved




async def process_video_item(item_id: uuid4, url: str):
    """Process a video item with download (only when explicitly requested)"""
    video_processor = VideoProcessor()
    
    # Create async wrapper for the callback
    async def update_progress(progress):
        await _update_video_processing_progress(item_id, progress)
    
    # Note: This might need adjustment based on how set_progress_callback works
    # If it expects a sync function, we'll need a different approach
    video_processor.set_progress_callback(lambda p: asyncio.create_task(update_progress(p)))
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
Uploader: {video_data.item_metadata.get('uploader', 'Unknown')}
View Count: {video_data.item_metadata.get('view_count', 'Unknown')}

Full Description:
{video_data.description or 'No description available'}
"""
        
        processed_content = await llm_processor.process_content(
            content=ai_content,
            url=url,
            title=video_data.title
        )
        
        # Merge AI-generated tags with existing tags
        all_tags = list(set(processed_content.tags))
        
        # Update metadata with AI analysis
        enhanced_metadata = video_data.item_metadata.copy()
        enhanced_metadata['ai_analysis'] = {
            'summary': processed_content.summary,
            'tags': processed_content.tags,
            'key_points': processed_content.key_points,
            'sentiment': processed_content.sentiment,
            'reading_time': processed_content.reading_time,
            'entities': processed_content.entities,
            'questions': processed_content.questions,
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
            
            # Generate and store embedding (optional - don't fail if embedding service is down)
            if processed_content.summary:
                try:
                    embedding = await embedding_service.generate_embedding(processed_content.summary)
                    if embedding:
                        await update_item_embedding(str(item_id), embedding)
                        logger.info(f"Generated and stored embedding for video item {item_id}")
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for video {item_id}: {e}")
                    # Continue processing - embeddings are optional
            
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
                json.dumps(video_data.item_metadata) if isinstance(video_data.item_metadata, dict) else video_data.item_metadata
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


class CheckDuplicateRequest(BaseModel):
    url: HttpUrl


class CheckDuplicateResponse(BaseModel):
    is_duplicate: bool
    existing_item: Optional[Dict] = None


@router.post("/capture/check-duplicate", response_model=CheckDuplicateResponse)
async def check_duplicate_url(
    request: CheckDuplicateRequest,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Check if a URL already exists in the knowledge base before capture."""
    existing_item = await db_connection.fetchrow("""
        SELECT id, title, created_at, status, summary
        FROM items
        WHERE url = $1
        LIMIT 1
    """, str(request.url))
    
    if existing_item:
        return CheckDuplicateResponse(
            is_duplicate=True,
            existing_item={
                "id": str(existing_item['id']),
                "title": existing_item['title'],
                "created_at": existing_item['created_at'].isoformat(),
                "status": existing_item['status'],
                "summary": existing_item['summary']
            }
        )
    
    return CheckDuplicateResponse(is_duplicate=False)
