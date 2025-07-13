from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.exceptions import InternalServerError
from app.db.database import get_db_pool

router = APIRouter()

class Tag(BaseModel):
    name: str
    count: int

@router.get("/tags", response_model=List[Tag])
async def get_tags():
    """Get all tags with usage count."""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            query = """
                SELECT t.name, COUNT(it.item_id) as count
                FROM tags t
                LEFT JOIN item_tags it ON t.id = it.tag_id
                GROUP BY t.id, t.name
                ORDER BY count DESC, t.name ASC
            """
            
            rows = await conn.fetch(query)
            
            return [{"name": row["name"], "count": row["count"]} for row in rows]
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve tags: {e}")

@router.get("/tags/recent", response_model=List[str])
async def get_recent_tags():
    """Get recently used tags (last 10 unique tags)."""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            query = """
                SELECT t.name, MAX(i.created_at) as last_used
                FROM tags t
                JOIN item_tags it ON t.id = it.tag_id
                JOIN items i ON it.item_id = i.id
                GROUP BY t.id, t.name
                ORDER BY last_used DESC
                LIMIT 10
            """
            
            rows = await conn.fetch(query)
            
            return [row["name"] for row in rows]
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve recent tags: {e}")