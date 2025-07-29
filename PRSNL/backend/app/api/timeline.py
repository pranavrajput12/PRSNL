from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status, Request, Depends
from pydantic import BaseModel

from app.core.exceptions import InternalServerError
from app.db.database import get_db_pool
from app.core.auth import get_current_user, get_current_user_optional, User
from app.core.url_mappings import generate_permalink_sql

router = APIRouter()

class TimelineItem(BaseModel):
    id: UUID
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None
    platform: Optional[str] = None
    type: str = "article"
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    file_path: Optional[str] = None
    status: str = "completed"
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    tags: List[str] = []
    permalink: Optional[str] = None

    class Config:
        populate_by_name = True

class TimelineResponse(BaseModel):
    items: List[TimelineItem]
    next_cursor: Optional[str] = None

@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = None,
    page: Optional[int] = Query(None, description="Page number (for backward compatibility)"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve a chronological list of captured items using cursor-based pagination."""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    i.id,
                    i.title,
                    i.url,
                    i.summary,
                    COALESCE(i.metadata->'video_metadata'->>'platform', i.metadata->>'platform') as platform,
                    i.type as type,
                    i.category,
                    COALESCE(i.thumbnail_url, i.metadata->'video_metadata'->>'thumbnail', i.metadata->>'thumbnail_url') as thumbnail_url,
                    COALESCE(i.duration, (i.metadata->'video_metadata'->'video_info'->>'duration')::int, (i.metadata->>'duration')::int) as duration,
                    i.metadata->>'file_path' as file_path,
                    i.status,
                    i.created_at,
                    i.updated_at,
                    CASE 
                        WHEN i.type = 'article' THEN '/articles/' || i.id
                        WHEN i.type = 'video' THEN '/videos/' || i.id
                        WHEN i.type = 'recipe' THEN '/recipes/' || i.id
                        WHEN i.type = 'bookmark' THEN '/bookmarks/' || i.id
                        WHEN i.type = 'code' THEN '/code/' || i.id
                        WHEN i.type = 'document' THEN '/documents/' || i.id
                        WHEN i.type = 'conversation' THEN '/conversations/' || i.id
                        WHEN i.type = 'repository' THEN '/repositories/' || i.id
                        WHEN i.type = 'screenshot' THEN '/screenshots/' || i.id
                        ELSE '/items/' || i.id
                    END as permalink,
                    COALESCE(
                        ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL),
                        ARRAY[]::TEXT[]
                    ) as tags
                FROM items i
                LEFT JOIN content_urls cu ON i.id = cu.item_id
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.status IN ('completed', 'bookmark', 'pending', 'failed', 'processed')
            """
            params = []
            
            # Add user filter if authenticated, otherwise show all items
            if current_user:
                query += " AND i.user_id = $1"
                params.append(str(current_user.id))
            if cursor:
                try:
                    # The cursor is the created_at timestamp of the last item
                    cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                    query += f" AND i.created_at < ${len(params) + 1}"
                    params.append(cursor_dt)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid cursor format.")

            query += f" GROUP BY i.id, cu.slug, cu.category ORDER BY i.created_at DESC LIMIT ${len(params) + 1}"
            params.append(limit)

            rows = await conn.fetch(query, *params)
            
            items = []
            for row in rows:
                thumbnail_url = row["thumbnail_url"]
                if thumbnail_url and thumbnail_url.startswith("/app/media/"):
                    thumbnail_url = thumbnail_url.replace("/app/media/", "/media/")
                    
                items.append({
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "summary": row["summary"],
                    "platform": row["platform"],
                    "type": row["type"],
                    "category": row["category"],
                    "thumbnail_url": thumbnail_url,
                    "duration": row["duration"],
                    "file_path": row["file_path"],
                    "status": row["status"],
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                    "tags": row["tags"],
                    "permalink": row["permalink"]
                })

            next_cursor = None
            if len(items) == limit:
                next_cursor = items[-1]["createdAt"].isoformat()

            return {
                "items": items,
                "next_cursor": next_cursor
            }
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve timeline: {e}")
