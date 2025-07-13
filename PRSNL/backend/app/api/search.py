import time
from datetime import timedelta
from typing import List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import InternalServerError, InvalidInput
from app.core.search_engine import SearchEngine
from app.db.database import find_similar_items_by_embedding, get_db_connection
from app.services.cache import cache_result, cache_service, CacheKeys
from app.services.embedding_service import EmbeddingService

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None

class SemanticSearchQuery(BaseModel):
    query: str

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
    
    # Try cache first
    cache_key = cache_service.make_key(CacheKeys.SEARCH, query, limit=limit, offset=offset)
    cached = await cache_service.get(cache_key)
    if cached:
        print(f"DEBUG: Returning cached response for key: {cache_key}")
        return cached
    else:
        print(f"DEBUG: No cache found for key: {cache_key}")
    
    try:
        # Start timing
        start_time = time.time()
        
        search_engine = SearchEngine(db_connection)
        # Pass parameters correctly with offset support
        results = await search_engine.search(query, limit=limit, offset=offset)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Frontend expects SearchResponse format with results array
        print(f"DEBUG: Found {len(results)} results from search engine")
        response = {
            "results": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "url": item.url,
                    "snippet": item.snippet,  # Frontend expects 'snippet' not 'summary'
                    "tags": item.tags,
                    "created_at": item.created_at.isoformat(),  # Frontend expects snake_case
                    "score": item.score if hasattr(item, 'score') else None
                } for item in results
            ],
            "total": len(results),
            "took_ms": execution_time_ms
        }
        
        # Cache the result
        await cache_service.set(cache_key, response, settings.CACHE_TTL_SEARCH)
        
        print(f"DEBUG: Returning response with keys: {list(response.keys())}")
        return response
    except Exception as e:
        raise InternalServerError(f"Failed to perform search: {e}")

from app.services.cache import cache_result, cache_service, CacheKeys


@router.get("/search/similar/{item_id}")
@cache_result(prefix=CacheKeys.SIMILAR, expire=timedelta(days=1))
async def find_similar_items(
    item_id: str,
    limit: int = 10,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Find items similar to the given item using embeddings"""
    try:
        item = await db_connection.fetchrow("SELECT embedding FROM items WHERE id = $1", item_id)
        if not item or not item["embedding"]:
            raise HTTPException(status_code=404, detail="Item not found or has no embedding")

        similar_items = await find_similar_items_by_embedding(
            db_connection, item["embedding"], limit, exclude_id=item_id
        )
        
        # Format the response
        response_items = [
            {
                "id": str(record["id"]),
                "title": record["title"],
                "url": record["url"],
                "summary": record.get("summary"), # Use .get for optional fields
                "createdAt": record["created_at"].isoformat() if record["created_at"] else None,
                "type": record.get("type", "article") # Get actual type from database
            }
            for record in similar_items
        ]
        return {"items": response_items}
    except HTTPException:
        raise # Re-raise HTTPException so FastAPI handles it
    except Exception as e:
        raise InternalServerError(f"Failed to find similar items: {e}")

@router.post("/search/semantic")
@cache_result(prefix=CacheKeys.SEARCH, expire=timedelta(days=1))
async def semantic_search(
    query_data: SemanticSearchQuery,
    limit: int = 20,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Search using semantic similarity"""
    embedding_service = EmbeddingService()
    try:
        query_embedding = await embedding_service.generate_embedding(query_data.query)
        if not query_embedding:
            raise InternalServerError("Failed to generate embedding for query.")

        similar_items = await find_similar_items_by_embedding(
            db_connection, query_embedding, limit
        )
        
        # Format the response
        response_items = [
            {
                "id": str(record["id"]),
                "title": record["title"],
                "url": record["url"],
                "summary": record.get("summary"),
                "createdAt": record["created_at"].isoformat() if record["created_at"] else None,
                "type": "article"
            }
            for record in similar_items
        ]
        return {"items": response_items}
    except Exception as e:
        raise InternalServerError(f"Failed to perform semantic search: {e}")
