"""Search API endpoints"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from app.models.schemas import SearchResponse, SearchResult
from app.core.search_engine import SearchEngine
from app.db.database import get_db_connection
import asyncpg
import time


router = APIRouter(prefix="/search", tags=["search"])


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    date: Optional[str] = Query("all", description="Date filter"),
    type: Optional[str] = Query("all", description="Type filter"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(20, le=100),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Full-text search with PostgreSQL
    """
    start_time = time.time()
    
    # Build search query
    search_engine = SearchEngine(conn)
    
    # Parse tags
    tag_list = tags.split(",") if tags else []
    
    # Perform search
    results = await search_engine.search(
        query=q,
        date_filter=date,
        type_filter=type,
        tags=tag_list,
        limit=limit
    )
    
    # Count total results
    total = await search_engine.count_results(
        query=q,
        date_filter=date,
        type_filter=type,
        tags=tag_list
    )
    
    # Calculate timing
    took_ms = int((time.time() - start_time) * 1000)
    
    return SearchResponse(
        results=results,
        total=total,
        took_ms=took_ms
    )