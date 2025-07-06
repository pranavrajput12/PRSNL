from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.core.exceptions import InvalidInput, InternalServerError
from app.core.search_engine import SearchEngine
from app.db.database import get_db_connection
import asyncpg

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None

@router.get("/search")
async def search_items(
    query: str,
    limit: int = 10,
    offset: int = 0,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Search for items by keyword or phrase."""
    if not query:
        raise InvalidInput("Search query cannot be empty.")
    try:
        search_engine = SearchEngine(db_connection)
        results = await search_engine.search(query, limit, offset)
        
        # Frontend expects object with items array
        return {
            "items": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "url": item.url,
                    "summary": item.snippet,
                    "tags": item.tags,
                    "createdAt": item.created_at.isoformat(),
                    "type": "article"  # TODO: Get actual type from DB
                } for item in results
            ],
            "total": len(results)
        }
    except Exception as e:
        raise InternalServerError(f"Failed to perform search: {e}")
