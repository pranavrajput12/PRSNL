import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.core.exceptions import InternalServerError, ItemNotFound
from app.db.database import get_db_pool
from app.models.schemas import Item, ItemStatus, ItemUpdate
from app.services.cache import cache_service, CacheKeys

router = APIRouter()

@router.get("/items/{item_id}")
async def get_item_detail(item_id: UUID):
    """Retrieve details of a specific item by ID."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔵 Getting item detail for ID: {item_id}")
    
    # Try cache first
    cache_key = cache_service.make_key(CacheKeys.ITEM, str(item_id))
    cached = await cache_service.get(cache_key)
    if cached:
        logger.info(f"🔵 Returning cached item for {item_id}")
        return cached
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get item with tags including video-specific fields
            query = """
                SELECT 
                    i.id,
                    i.title,
                    i.url,
                    i.summary,
                    i.processed_content as content,
                    i.type as type,
                    i.content_type,
                    i.created_at,
                    i.updated_at,
                    i.transcription,
                    COALESCE(i.thumbnail_url, i.metadata->'video_metadata'->>'thumbnail', i.metadata->>'thumbnail_url') as thumbnail_url,
                    COALESCE(i.metadata->'video_metadata'->>'platform', i.metadata->>'platform', i.platform) as platform,
                    COALESCE(i.duration, (i.metadata->'video_metadata'->'video_info'->>'duration')::int, (i.metadata->>'duration')::int) as duration,
                    i.metadata->>'file_path' as file_path,
                    i.metadata,
                    CASE 
                        WHEN cu.slug IS NOT NULL THEN '/c/' || cu.category || '/' || cu.slug
                        ELSE NULL
                    END as permalink,
                    COALESCE(
                        ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL),
                        ARRAY[]::TEXT[]
                    ) as tags
                FROM items i
                LEFT JOIN content_urls cu ON i.id = cu.item_id
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.id = $1
                GROUP BY i.id, cu.slug, cu.category, i.transcription, i.platform, i.duration
            """
            
            row = await conn.fetchrow(query, item_id)
            
            if not row:
                raise ItemNotFound(item_id)
                
            # Debug log
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔵 Row data for {item_id}: type={row.get('type')}, platform={row.get('platform')}, thumbnail_url={row.get('thumbnail_url')}, duration={row.get('duration')}")
            logger.info(f"🔵 Metadata type: {type(row.get('metadata'))}")
            if row.get('metadata'):
                logger.info(f"🔵 Metadata keys: {list(row.get('metadata').keys()) if isinstance(row.get('metadata'), dict) else 'Not a dict'}")
            
            # Transform thumbnail URL for container paths
            thumbnail_url = row.get("thumbnail_url")
            if thumbnail_url and thumbnail_url.startswith("/app/media/"):
                thumbnail_url = thumbnail_url.replace("/app/media/", "/media/")
            
            # Parse metadata for video-specific data
            metadata = {}
            if row.get("metadata"):
                if isinstance(row["metadata"], dict):
                    metadata = row["metadata"]
                elif isinstance(row["metadata"], str):
                    try:
                        metadata = json.loads(row["metadata"])
                    except:
                        logger.warning(f"Failed to parse metadata for item {item_id}")
                        metadata = {}
            
            video_metadata = metadata.get('video_metadata', {})
            
            # Extract video-specific fields from metadata and AI analysis
            ai_analysis = metadata.get('ai_analysis', {})
            
            logger.info(f"🔍 Parsed metadata has keys: {list(metadata.keys())}")
            logger.info(f"🔍 AI analysis has keys: {list(ai_analysis.keys())}")
            
            # Get key_moments from metadata (if available from transcript extraction)
            key_moments = metadata.get('key_moments', [])
            
            # Get learning objectives from metadata or generate from AI key points
            learning_objectives = metadata.get('learning_objectives') or video_metadata.get('learning_objectives', [])
            if not learning_objectives and ai_analysis.get('key_points'):
                # Convert key points to learning objectives
                learning_objectives = [f"Understand {point.lower()}" for point in ai_analysis.get('key_points', [])]
            
            chapters = metadata.get('chapters') or video_metadata.get('chapters', [])
            
            # If no key_moments from transcript, generate from AI key_points
            if not key_moments and ai_analysis.get('key_points'):
                # Convert AI key points to key moments format
                key_moments = [
                    {
                        "timestamp": f"{i:02d}:00",  # Placeholder timestamps
                        "description": point,
                        "text": point
                    }
                    for i, point in enumerate(ai_analysis.get('key_points', []))
                ]
            
            # Get topics from AI analysis tags
            key_topics = metadata.get('key_topics') or ai_analysis.get('tags', [])
            
            # If no chapters but we have key_moments, convert them to chapters
            if not chapters and key_moments:
                chapters = [
                    {
                        "timestamp": moment.get("timestamp", "00:00"),
                        "title": f"Chapter {i+1}: Key Insight",
                        "description": moment.get("description", moment.get("text", ""))
                    }
                    for i, moment in enumerate(key_moments)
                ]
            
            # Use AI summary if main summary is empty
            summary = row["summary"]
            if not summary and ai_analysis.get('summary'):
                summary = ai_analysis.get('summary')
            
            result = {
                "id": str(row["id"]),
                "title": row["title"],
                "url": row["url"],
                "content": row["content"],
                "summary": summary,
                "type": row["type"],
                "content_type": row["content_type"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "tags": row["tags"],
                "status": ItemStatus.COMPLETED,
                "access_count": 0,
                "accessed_at": row["created_at"].isoformat(),
                "thumbnail_url": thumbnail_url,
                "platform": row["platform"],
                "duration": row["duration"],
                "file_path": row["file_path"],
                "transcription": row["transcription"],
                "transcript": row["transcription"],  # Alias for frontend compatibility
                "has_transcript": bool(row["transcription"]),  # Boolean flag for frontend
                # Video-specific fields from metadata
                "learning_objectives": learning_objectives,
                "chapters": chapters,
                "key_moments": key_moments,
                "key_topics": key_topics,
                "metadata": metadata,
                "permalink": row["permalink"]
            }
            
            # Cache the result
            await cache_service.set(cache_key, result, settings.CACHE_TTL_ITEM)
            
            logger.info(f"🟢 Final result for {item_id}: platform={result.get('platform')}, thumbnail_url={result.get('thumbnail_url')}, duration={result.get('duration')}")
            logger.info(f"🟢 Result has transcript: {bool(result.get('transcript'))}, has_transcript: {result.get('has_transcript')}, key_moments count: {len(result.get('key_moments', []))}")
            
            return result
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve item {item_id}: {e}")

@router.patch("/items/{item_id}", response_model=Item)
async def update_item(item_id: UUID, item_update: ItemUpdate):
    """Update an existing item."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Check if item exists
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                    UUID(item_id)
                )
                
                if not exists:
                    raise ItemNotFound(item_id)
                
                # Update item fields if provided
                update_fields = []
                params = [item_id]
                param_count = 2
                
                if item_update.title is not None:
                    update_fields.append(f"title = ${param_count}")
                    params.append(item_update.title)
                    param_count += 1
                
                if item_update.summary is not None:
                    update_fields.append(f"summary = ${param_count}")
                    params.append(item_update.summary)
                    param_count += 1
                
                if update_fields:
                    update_fields.append("updated_at = NOW()")
                    update_query = f"""
                        UPDATE items 
                        SET {', '.join(update_fields)}
                        WHERE id = $1
                    """
                    await conn.execute(update_query, *params)
                
                # Handle tags update
                if item_update.tags is not None:
                    # Delete existing tags
                    await conn.execute(
                        "DELETE FROM item_tags WHERE item_id = $1",
                        UUID(item_id)
                    )
                    
                    # Insert new tags
                    for tag_name in item_update.tags:
                        # Get or create tag
                        tag_id = await conn.fetchval(
                            """
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                            """,
                            tag_name.lower()
                        )
                        
                        # Link tag to item
                        await conn.execute(
                            "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)",
                            item_id, tag_id
                        )
                
                # Invalidate cache for this item
                cache_key = cache_service.make_key(CacheKeys.ITEM, str(item_id))
                await cache_service.delete(cache_key)
                
                # Also invalidate search and timeline caches
                await cache_service.clear_pattern(f"{CacheKeys.SEARCH}:*")
                await cache_service.clear_pattern(f"{CacheKeys.TIMELINE}:*")
                
                # Return the updated item
                return await get_item_detail(item_id)
                
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to update item {item_id}: {e}")

@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Check if item exists
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                    UUID(item_id)
                )
                
                if not exists:
                    raise ItemNotFound(item_id)
                
                # Delete item tags first (due to foreign key)
                await conn.execute(
                    "DELETE FROM item_tags WHERE item_id = $1",
                    UUID(item_id)
                )
                
                # Delete the item
                await conn.execute(
                    "DELETE FROM items WHERE id = $1",
                    UUID(item_id)
                )
                
                return {"message": "Item deleted successfully", "id": item_id}
                
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to delete item {item_id}: {e}")
