"""Timeline API endpoints"""
from fastapi import APIRouter, Query, Depends
from app.models.schemas import TimelineResponse, TimelineItem
from app.db.database import get_db_connection
import asyncpg
from typing import List


router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/", response_model=TimelineResponse)
async def get_timeline(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get timeline of captured items
    """
    offset = (page - 1) * limit
    
    # Fetch items
    rows = await conn.fetch("""
        SELECT 
            i.id,
            i.title,
            i.url,
            i.summary,
            i.created_at,
            COALESCE(
                array_agg(t.name) FILTER (WHERE t.name IS NOT NULL), 
                '{}'::text[]
            ) as tags
        FROM items i
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.status = 'completed'
        GROUP BY i.id, i.title, i.url, i.summary, i.created_at
        ORDER BY i.created_at DESC
        LIMIT $1 OFFSET $2
    """, limit + 1, offset)
    
    # Check if there are more items
    has_more = len(rows) > limit
    items = rows[:limit] if has_more else rows
    
    # Convert to response
    timeline_items = [
        TimelineItem(
            id=row['id'],
            title=row['title'],
            url=row['url'],
            snippet=row['summary'] or '',
            tags=row['tags'],
            created_at=row['created_at']
        )
        for row in items
    ]
    
    return TimelineResponse(
        items=timeline_items,
        hasMore=has_more
    )