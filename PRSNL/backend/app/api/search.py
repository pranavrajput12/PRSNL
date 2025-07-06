from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from app.core.exceptions import InvalidInput, InternalServerError

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    content_snippet: Optional[str] = None

@router.get("/search", response_model=List[SearchResult])
async def search_items(query: str, limit: int = 10, offset: int = 0):
    """Search for items by keyword or phrase."""
    if not query:
        raise InvalidInput("Search query cannot be empty.")
    try:
        # Simulate search logic
        results = [
            {"id": "1", "title": "Sample Result 1", "url": "http://example.com/1", "content_snippet": "...snippet 1..."},
            {"id": "2", "title": "Sample Result 2", "url": "http://example.com/2", "content_snippet": "...snippet 2..."},
        ]
        return results
    except Exception as e:
        raise InternalServerError(f"Failed to perform search: {e}")
