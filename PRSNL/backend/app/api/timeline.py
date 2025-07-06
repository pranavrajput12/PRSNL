from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.core.exceptions import InternalServerError
from app.db.database import get_db_pool

router = APIRouter()

class TimelineItem(BaseModel):
    id: UUID
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None
    platform: Optional[str] = None
    item_type: str = "article"
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    file_path: Optional[str] = None
    createdAt: datetime  # Frontend expects camelCase
    updatedAt: Optional[datetime] = None  # Frontend expects camelCase
    tags: List[str] = []
    
    class Config:
        # Allow both snake_case and camelCase
        populate_by_name = True

class TimelineResponse(BaseModel):
    items: List[TimelineItem]
    total: int
    page: int
    pageSize: int

@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Retrieve a chronological list of captured items."""
    try:
        offset = (page - 1) * limit
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get items with their tags
            query = """
                SELECT 
                    i.id,
                    i.title,
                    i.url,
                    i.summary,
                    i.platform,
                    i.item_type,
                    i.thumbnail_url,
                    i.duration,
                    i.file_path,
                    i.created_at,
                    i.updated_at,
                    COALESCE(
                        ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL),
                        ARRAY[]::TEXT[]
                    ) as tags
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.status = 'completed'
                GROUP BY i.id
                ORDER BY i.created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            rows = await conn.fetch(query, limit, offset)
            
            items = []
            for row in rows:
                # Convert container paths to accessible URLs
                thumbnail_url = row["thumbnail_url"]
                if thumbnail_url and thumbnail_url.startswith("/app/media/"):
                    thumbnail_url = thumbnail_url.replace("/app/media/", "/media/")
                    
                items.append({
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "summary": row["summary"],
                    "platform": row["platform"],
                    "item_type": row["item_type"],
                    "thumbnail_url": thumbnail_url,
                    "duration": row["duration"],
                    "file_path": row["file_path"],
                    "createdAt": row["created_at"].isoformat() if row["created_at"] else None,  # Frontend expects camelCase
                    "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,  # Frontend expects camelCase
                    "tags": row["tags"]
                })
            
            # Get total count
            count_query = """
                SELECT COUNT(*)
                FROM items
                WHERE status = 'completed'
            """
            total_count = await conn.fetchval(count_query)
            
            # Frontend expects object with items array, total count, etc.
            return {
                "items": items,
                "total": total_count,
                "page": page,
                "pageSize": limit
            }
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve timeline: {e}")
