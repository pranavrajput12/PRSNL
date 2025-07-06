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

@router.get("/search", response_model=List[SearchResult])
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
        
        # Map results to SearchResult model
        return [
            SearchResult(
                id=str(item.id),
                title=item.title,
                url=item.url,
                snippet=item.snippet
            ) for item in results
        ]
    except Exception as e:
        raise InternalServerError(f"Failed to perform search: {e}")
