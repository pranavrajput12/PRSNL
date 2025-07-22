import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional
from uuid import uuid4, UUID

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from app.api.instagram_handler import process_instagram_bookmark
from app.core.capture_engine import CaptureEngine
from app.core.exceptions import InternalServerError, InvalidInput
from app.db.database import get_db_connection, get_db_pool, update_item_embedding
from app.middleware.rate_limit import capture_limiter, capture_throttle_limiter
from app.middleware.user_context import require_user_id
from app.models.schemas import CaptureRequest, CaptureResponse, ItemStatus
from app.monitoring.metrics import (
    VIDEO_CAPTURE_REQUESTS,
    VIDEO_DOWNLOAD_DURATION_SECONDS,
    VIDEO_DOWNLOAD_OUTCOMES,
    VIDEO_PROCESSING_DURATION_SECONDS,
)
from app.services.embedding_service import embedding_service
from app.services.llm_processor import LLMProcessor
from app.services.preview_service import preview_service
from app.services.repository_analyzer import repository_analyzer
from app.services.video_processor import VideoProcessor
from app.services.websocket_manager import websocket_manager
from app.utils.media_detector import MediaDetector
from app.utils.url_classifier import URLClassifier

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Force debug level for capture logging

router = APIRouter()


def _is_repository_url(url: str) -> bool:
    """Check if URL is a repository URL (GitHub, GitLab, Bitbucket)"""
    repo_patterns = [
        r'github\.com/[^/]+/[^/]+/?$',
        r'gitlab\.com/[^/]+/[^/]+/?$',
        r'bitbucket\.org/[^/]+/[^/]+/?$'
    ]
    
    for pattern in repo_patterns:
        if re.search(pattern, url.lower()):
            return True
    return False

@router.get("/capture/debug") 
async def debug_capture():
    """Debug endpoint to test if routes work"""
    print("🚨 DEBUG ROUTE CALLED")
    logger.info("🔍 DEBUG ROUTE CALLED")
    return {"status": "debug_route_works", "message": "Route is accessible"}

@router.post("/capture/test")
async def test_capture():
    """Simple test route to verify routing works"""
    print("🚨 TEST CAPTURE ROUTE CALLED")
    return {"status": "test_works", "message": "Test route is working"}

@router.post("/capture/ping")
async def ping_capture():
    """Minimal smoke test with direct DB insert"""
    print("🚨 PING CAPTURE ROUTE CALLED")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO public.items (id, title, type, content_type, enable_summarization, status) 
                VALUES (gen_random_uuid(), 'Ping Test', 'article', 'auto', false, 'pending')
            """)
            return {"ok": True, "message": "Ping successful - direct insert worked"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

@router.get("/capture/test-db")
async def test_database():
    """Test database connection separately"""
    logger.info("🔍 DB TEST ROUTE CALLED")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            # Test basic connection
            result = await conn.fetchval("SELECT 1")
            logger.info(f"🔍 DB TEST: {result}")
            
            # Test columns
            columns = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'items' 
                ORDER BY column_name
            """)
            logger.info(f"🔍 ALL COLUMNS: {[r['column_name'] for r in columns]}")
            
            return {"status": "success", "columns": [r['column_name'] for r in columns]}
        except Exception as e:
            logger.error(f"🔍 DEBUG ERROR: {e}")
            return {"status": "error", "error": str(e)}

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

from app.services.cache import CacheKeys, invalidate_cache


@router.post("/capture", status_code=status.HTTP_201_CREATED)
@capture_throttle_limiter
async def capture_item(request: Request, capture_request: CaptureRequest, background_tasks: BackgroundTasks, user_id: UUID = Depends(require_user_id)):
    """Capture a new item (web page, note, file, etc.)."""
    print(f"🚨 CAPTURE FUNCTION CALLED: {capture_request.url}")  # Force print
    logger.error(f"🚨 CAPTURE FUNCTION CALLED: {capture_request.url}")  # Force error level
    logger.info(f"🔍 CAPTURE API DEBUG: Starting capture for URL: {capture_request.url}")
    
    # Use the same database connection method as timeline API
    pool = await get_db_pool()
    
    # Check if files are provided in the request
    has_files = hasattr(capture_request, 'uploaded_files') and capture_request.uploaded_files
    
    # Check for highlight field as well (legacy field name)
    has_highlight = hasattr(capture_request, 'highlight') and capture_request.highlight
    
    if not capture_request.url and not capture_request.content and not has_files and not has_highlight:
        VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
        raise InvalidInput("Either URL, content, or files must be provided.")
    
    # Validate content_type if provided  
    VALID_CONTENT_TYPES = {
        'article', 'video', 'document', 'image', 'note', 'link', 'tutorial', 
        'audio', 'code', 'development', 'github_repo', 'github_document', 'auto'
    }
    # Note: github_course is not included as courses are AI-generated, not captured
    if capture_request.content_type and capture_request.content_type not in VALID_CONTENT_TYPES:
        raise InvalidInput(f"Invalid content_type '{capture_request.content_type}'. "
                          f"Valid types: {', '.join(sorted(VALID_CONTENT_TYPES))}")
    
    item_id = uuid4()
    item_type = 'article'
    
    async with pool.acquire() as db_connection:
        logger.info(f"🔍 DB CONNECTION TYPE: {type(db_connection)}")
        logger.info(f"🔍 DB CONNECTION INFO: {db_connection.get_server_version() if hasattr(db_connection, 'get_server_version') else 'No version method'}")
        logger.info(f"🔍 CONNECTION DSN: {getattr(db_connection, '_addr', 'Unknown')}")
        params = getattr(db_connection, '_params', None)
        logger.info(f"🔍 CONNECTION PARAMS: {params}")
        if params:
            logger.info(f"🔍 CONNECTION DB: {getattr(params, 'database', 'Unknown')}")
            logger.info(f"🔍 CONNECTION USER: {getattr(params, 'user', 'Unknown')}")
        else:
            logger.info("🔍 No connection params available")
        
        try:
            # Check for duplicate URL if URL is provided
            if capture_request.url:
                existing_item = await db_connection.fetchrow("""
                    SELECT id, title, created_at, status
                    FROM items
                    WHERE url = $1 AND user_id = $2
                    LIMIT 1
                """, str(capture_request.url), str(user_id))
                
                if existing_item:
                    raise InvalidInput(
                        f"This URL already exists in your knowledge base. "
                        f"Item: '{existing_item['title']}' (created {existing_item['created_at'].strftime('%Y-%m-%d')})"
                    )
            
            # Determine item type - prioritize user content_type choice
            media_info = None
            item_type = 'article'  # Default fallback
            
            # Rule 1: Auto-detect GitHub URLs with specific types (only in auto mode)
            if (capture_request.url and 'github.com' in str(capture_request.url).lower() and 
                (not capture_request.content_type or capture_request.content_type == 'auto')):
                
                # Get detailed GitHub classification
                url_classification = URLClassifier.classify_url(str(capture_request.url))
                github_type = url_classification.get('content_type', 'development')
                
                # Map to item types
                if github_type == 'github_document':
                    item_type = 'github_document'
                elif github_type == 'github_repo':
                    item_type = 'github_repo'
                else:
                    item_type = 'development'  # Fallback
                
                capture_request.content_type = github_type
                logger.info(f"🐙 GitHub URL auto-detected: {github_type} → type: {item_type}")
                
                # Auto-fill development fields for GitHub
                if not capture_request.programming_language and url_classification.get('programming_language'):
                    capture_request.programming_language = url_classification['programming_language']
                if not capture_request.project_category and url_classification.get('project_category'):
                    capture_request.project_category = url_classification['project_category']
                    
            # Rule 2: If user explicitly chose content_type, respect it (except 'auto' and GitHub override)
            elif capture_request.content_type and capture_request.content_type != 'auto':
                # Map content_type to item_type
                if capture_request.content_type == 'video':
                    item_type = 'video'
                elif capture_request.content_type == 'document':
                    item_type = 'document'
                elif capture_request.content_type == 'image':
                    item_type = 'image'
                elif capture_request.content_type == 'note':
                    item_type = 'note'
                elif capture_request.content_type == 'tutorial':
                    item_type = 'tutorial'
                elif capture_request.content_type == 'article':
                    item_type = 'article'
                elif capture_request.content_type == 'link':
                    item_type = 'link'
                elif capture_request.content_type == 'github_repo':
                    item_type = 'github_repo'
                elif capture_request.content_type == 'github_document':
                    item_type = 'github_document'
                else:
                    # For other content types, use the content_type as item_type
                    item_type = capture_request.content_type
                    
                logger.info(f"🎯 Using user-selected content_type: {capture_request.content_type} → type: {item_type}")
            
            # Rule 3: Auto-detection only when content_type='auto' or not specified
            elif capture_request.url and (not capture_request.content_type or capture_request.content_type == 'auto'):
                # First check for development content
                url_classification = URLClassifier.classify_url(str(capture_request.url))
                
                if url_classification['is_development']:
                    # Check if this is a repository URL
                    if _is_repository_url(str(capture_request.url)):
                        item_type = 'repository'
                        logger.info(f"🔍 Auto-detected repository URL → type: {item_type}")
                    else:
                        # Auto-classify as development content
                        item_type = 'development'
                        
                        # Auto-fill development fields if not provided by user
                        if not capture_request.programming_language and url_classification['programming_language']:
                            capture_request.programming_language = url_classification['programming_language']
                        
                        if not capture_request.project_category and url_classification['project_category']:
                            capture_request.project_category = url_classification['project_category']
                        
                        if not capture_request.difficulty_level and url_classification['difficulty_level']:
                            capture_request.difficulty_level = url_classification['difficulty_level']
                        
                        # Set career-related flag if detected
                        if url_classification['is_career_related']:
                            capture_request.is_career_related = True
                        
                        logger.info(f"🔍 Auto-detected development content: {url_classification['platform']} → type: {item_type}")
                        logger.info(f"🔍 Auto-filled: lang={capture_request.programming_language}, category={capture_request.project_category}, difficulty={capture_request.difficulty_level}")
                elif _is_repository_url(str(capture_request.url)):
                    # Direct repository URL detection
                    item_type = 'repository'
                    logger.info(f"🔍 Auto-detected repository URL → type: {item_type}")
                else:
                    # Fall back to media detection
                    media_info = MediaDetector.detect_media_type(str(capture_request.url))
                    
                    if media_info['type'] == 'video':
                        item_type = 'video'
                    elif media_info['type'] == 'image':
                        item_type = 'image'
                    elif media_info['type'] == 'article':
                        item_type = 'article'
                        
                    logger.info(f"🔍 Auto-detected from URL: {media_info['type']} → type: {item_type}")
            
            # Rule 4: Special case - if no summarization requested for URL, treat as simple link
            # Exception: Don't convert development content or videos to link (they need rich preview)
            if (capture_request.url and not capture_request.enable_summarization and 
                capture_request.content_type not in ['video', 'document', 'image', 'development'] and
                item_type not in ['development', 'video']):
                item_type = 'link'
                logger.info("🔗 No summarization requested for URL → type: link")
            
            # Handle video processing if item is determined to be video
            if item_type == 'video' and capture_request.url:
                if not media_info:
                    media_info = MediaDetector.detect_media_type(str(capture_request.url))
                    
                video_processor = VideoProcessor()
                video_info = await video_processor.get_video_info(str(capture_request.url))
                
                # Skip validation for Instagram and YouTube to avoid downloading
                if media_info.get('platform') not in ['instagram', 'youtube']:
                    # Perform video validation before inserting initial record
                    try:
                        await video_processor.validate_video_url(str(capture_request.url))
                    except ValueError as e:
                        VIDEO_CAPTURE_REQUESTS.labels(status='validation_failed').inc()
                        raise InvalidInput(f"Video validation failed: {e}")
        
            # Determine platform based on item type and URL
            platform = None
            if item_type in ['github_repo', 'github_document']:
                platform = 'github'
            elif media_info and media_info.get('platform'):
                platform = media_info['platform']
            elif capture_request.url and 'youtube.com' in str(capture_request.url).lower():
                platform = 'youtube'
            elif capture_request.url and 'vimeo.com' in str(capture_request.url).lower():
                platform = 'vimeo'
        
            # Insert initial item record with metadata for capture type
            metadata = {
                "capture_type": capture_request.type if hasattr(capture_request, 'type') else 'page',
                "media_info": media_info,
                "type": item_type,  # Store item type in metadata
                "content_type": capture_request.content_type,  # Store user-selected content type
                "platform": platform  # Store platform in metadata as well
            }
            
            # Generate rich preview for ALL GitHub URLs (regardless of item type)
            if capture_request.url and 'github.com' in str(capture_request.url).lower():
                try:
                    logger.info(f"🔍 Generating GitHub preview for URL: {capture_request.url}")
                    preview_data = await preview_service.generate_preview(str(capture_request.url), 'development')
                    if preview_data and preview_data.get('type') != 'error':
                        metadata['rich_preview'] = preview_data
                        logger.info(f"🟢 GitHub preview generated successfully for {capture_request.url}")
                    else:
                        logger.warning(f"🟡 GitHub preview generation failed or returned error for {capture_request.url}")
                except Exception as e:
                    logger.error(f"🔴 Error generating GitHub preview: {e}")
                    # Don't fail the entire capture if preview generation fails
                    pass
            # Also generate rich preview for development content (non-GitHub)
            elif (item_type == 'development' or capture_request.content_type == 'development') and capture_request.url:
                try:
                    logger.info(f"🔍 Generating rich preview for development content: {capture_request.url}")
                    preview_data = await preview_service.generate_preview(str(capture_request.url), 'development')
                    if preview_data and preview_data.get('type') != 'error':
                        metadata['rich_preview'] = preview_data
                        logger.info(f"🟢 Rich preview generated successfully for {capture_request.url}")
                    else:
                        logger.warning(f"🟡 Rich preview generation failed or returned error for {capture_request.url}")
                except Exception as e:
                    logger.error(f"🔴 Error generating rich preview: {e}")
                    # Don't fail the entire capture if preview generation fails
                    pass
            logger.info(f"Creating item {item_id} with type {item_type}, URL: {capture_request.url}")
            
            # For content-only captures, store content in raw_content field
            # Handle both content and highlight fields (highlight is legacy field name)
            initial_content = capture_request.content if capture_request.content else capture_request.highlight if hasattr(capture_request, 'highlight') else None
            
            # Repository-specific processing
            repository_metadata = None
            if item_type == 'repository' and capture_request.url:
                try:
                    logger.info(f"🔍 Analyzing repository: {capture_request.url}")
                    repo_analysis = await repository_analyzer.analyze_repository(str(capture_request.url))
                    repository_metadata = repo_analysis.dict()
                    
                    # Auto-fill title if not provided
                    if not capture_request.title:
                        capture_request.title = f"{repo_analysis.owner}/{repo_analysis.repo_name}"
                    
                    # Auto-fill content if not provided
                    if not initial_content and repo_analysis.description:
                        initial_content = repo_analysis.description
                    
                    # Auto-fill development fields from AI analysis
                    if repo_analysis.ai_analysis:
                        if not capture_request.programming_language and repo_analysis.language:
                            capture_request.programming_language = repo_analysis.language.lower()
                        
                        if not capture_request.project_category and repo_analysis.category:
                            capture_request.project_category = repo_analysis.category
                        
                        if not capture_request.difficulty_level and repo_analysis.difficulty:
                            capture_request.difficulty_level = repo_analysis.difficulty
                    
                    logger.info(f"🔍 Repository analysis completed: {repo_analysis.repo_name}")
                    logger.info(f"🔍 Tech stack: {repo_analysis.tech_stack}")
                    logger.info(f"🔍 Category: {repo_analysis.category}")
                    
                except Exception as e:
                    logger.error(f"🔍 Repository analysis failed: {e}")
                    # Continue with basic repository metadata
                    repository_metadata = {
                        "repo_url": str(capture_request.url),
                        "analysis_error": str(e),
                        "needs_manual_categorization": True
                    }
        
            # Add detailed debugging for the INSERT statement
            logger.info("🔍 ABOUT TO EXECUTE INSERT:")
            logger.info(f"🔍 - item_id: {item_id}")
            logger.info(f"🔍 - url: {capture_request.url}")
            logger.info(f"🔍 - title: {capture_request.title}")
            logger.info(f"🔍 - type: {item_type}")
            logger.info(f"🔍 - content_type: {capture_request.content_type}")
            logger.info(f"🔍 - enable_summarization: {capture_request.enable_summarization}")
            logger.info(f"🔍 - metadata: {json.dumps(metadata)}")
            
            # Test the database connection first
            try:
                test_result = await db_connection.fetchval("SELECT 1")
                logger.info(f"🔍 DB CONNECTION TEST: {test_result}")
            except Exception as e:
                logger.error(f"🔍 DB CONNECTION TEST FAILED: {e}")
            
            # Test if the table exists and columns exist
            try:
                columns_check = await db_connection.fetch("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'items' 
                    AND column_name IN ('content_type', 'enable_summarization')
                    ORDER BY column_name
                """)
                logger.info(f"🔍 COLUMN CHECK RESULT: {[row['column_name'] for row in columns_check]}")
            except Exception as e:
                logger.error(f"🔍 COLUMN CHECK FAILED: {e}")
            
            # Now try the actual INSERT
            sql_query = """
                INSERT INTO public.items (
                    id, url, title, raw_content, status, type, content_type, enable_summarization, metadata,
                    programming_language, project_category, difficulty_level, is_career_related, platform,
                    repository_metadata, user_id
                )
                VALUES ($1, $2, $3, $4, 'pending', $5, $6, $7, $8::jsonb, $9, $10, $11, $12, $13, $14::jsonb, $15)
            """
            params = (
                item_id, 
                str(capture_request.url) if capture_request.url else None, 
                capture_request.title or 'Untitled', 
                initial_content, 
                item_type, 
                capture_request.content_type, 
                capture_request.enable_summarization, 
                json.dumps(metadata),
                capture_request.programming_language,
                capture_request.project_category,
                capture_request.difficulty_level,
                capture_request.is_career_related,
                platform,
                json.dumps(repository_metadata) if repository_metadata else None,
                str(user_id)  # Convert UUID to string
            )
            
            logger.info(f"🔍 EXACT SQL QUERY: {sql_query}")
            logger.info(f"🔍 EXACT PARAMS: {params}")
            
            # Step 3: Log search_path and current_schema
            try:
                search_path_row = await db_connection.fetchrow("SHOW search_path")
                logger.warning(f"🔍 search_path = {search_path_row['search_path']}")
                schema_row = await db_connection.fetchrow("SELECT current_schema()")
                logger.warning(f"🔍 current_schema = {schema_row['current_schema']}")
            except Exception as e:
                logger.error(f"🔍 SCHEMA CHECK FAILED: {e}")
            
            # Step 4: Enhanced SQL execution with detailed logging
            try:
                await db_connection.execute(sql_query, *params)
                logger.info(f"🔍 INSERT SUCCESSFUL for item_id: {item_id}")
            except Exception as e:
                logger.error("🚨 FAILED SQL: %s — ARGS: %r", sql_query, params)
                logger.error(f"🔍 INSERT FAILED: {e}")
                logger.error(f"🔍 INSERT ERROR TYPE: {type(e)}")
                logger.error(f"🔍 INSERT ERROR DETAILS: {str(e)}")
                raise
            
            logger.info(f"Successfully inserted item {item_id} into database")
            
            # Process tags if provided
            if capture_request.tags:
                for tag_name in capture_request.tags:
                    # Get or create tag for this user
                    # First check if tag exists
                    tag_id = await db_connection.fetchval("""
                        SELECT id FROM tags WHERE name = $1
                    """, tag_name.lower())
                    
                    if not tag_id:
                        # Create new tag with user_id
                        tag_id = await db_connection.fetchval("""
                            INSERT INTO tags (name, user_id) VALUES ($1, $2)
                            RETURNING id
                        """, tag_name.lower(), user_id)
                    
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
                    # Process video metadata quickly, then enhance with AI in background if requested
                    background_tasks.add_task(process_video_metadata_fast, item_id, str(capture_request.url), capture_request.enable_summarization)
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


async def process_video_metadata_fast(item_id: uuid4, url: str, enable_summarization: bool = False):
    """Fast video metadata processing - AI enhancement happens only if requested"""
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
        
        # Only enhance with AI if summarization is requested
        if enable_summarization:
            logger.info(f"🤖 AI summarization enabled for video {item_id}, starting AI enhancement")
            # Run AI enhancement in background (non-blocking)
            asyncio.create_task(enhance_video_with_ai(item_id, url, video_info, media_info))
        else:
            logger.info(f"🚫 AI summarization disabled for video {item_id}, keeping original metadata")
        
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
                video_info.get('title', 'Unknown'),  # Always use original video title, not AI-generated
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
                    # First check if tag exists
                    tag_id = await conn.fetchval("""
                        SELECT id FROM tags WHERE name = $1
                    """, tag_name.lower())
                    
                    if not tag_id:
                        # Create new tag
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
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
Uploader: {video_data.metadata.get('uploader', 'Unknown')}
View Count: {video_data.metadata.get('view_count', 'Unknown')}

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
        enhanced_metadata = video_data.metadata.copy()
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
                    # First check if tag exists
                    tag_id = await conn.fetchval("""
                        SELECT id FROM tags WHERE name = $1
                    """, tag_name.lower())
                    
                    if not tag_id:
                        # Create new tag
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
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


class CheckDuplicateRequest(BaseModel):
    url: HttpUrl


class CheckDuplicateResponse(BaseModel):
    is_duplicate: bool
    existing_item: Optional[Dict] = None


@router.post("/capture/check-duplicate", response_model=CheckDuplicateResponse)
async def check_duplicate_url(
    request: CheckDuplicateRequest,
    db_connection: asyncpg.Connection = Depends(get_db_connection),
    user_id: UUID = Depends(require_user_id)
):
    """Check if a URL already exists in the knowledge base before capture."""
    existing_item = await db_connection.fetchrow("""
        SELECT id, title, created_at, status, summary
        FROM items
        WHERE url = $1 AND user_id = $2
        LIMIT 1
    """, str(request.url), user_id)
    
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
