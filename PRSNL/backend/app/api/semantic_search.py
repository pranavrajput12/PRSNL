import logging
from typing import List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.db.database import get_db_pool
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()

class SemanticSearchRequest(BaseModel):
    query: str
    full_text_query: Optional[str] = None
    limit: int = 10
    offset: int = 0

class SemanticSearchResult(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    url: Optional[str]
    similarity: float

@router.post("/search/semantic", response_model=List[SemanticSearchResult])
async def semantic_search(request: SemanticSearchRequest, db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """Performs a semantic search based on the query string, optionally combined with full-text search."""
    try:
        query_embedding = await embedding_service.get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Embedding service unavailable")
        
        async with db_pool.acquire() as conn:
            if request.full_text_query:
                # Hybrid search: combine semantic and full-text search
                # We'll use a CTE (Common Table Expression) to get semantic and full-text results separately
                # then combine and rank them.
                results = await conn.fetch("""
                    WITH semantic_results AS (
                        SELECT
                            id,
                            title,
                            summary,
                            url,
                            1 - (embedding <=> $1) AS semantic_similarity
                        FROM items
                        WHERE embedding IS NOT NULL
                    ),
                    full_text_results AS (
                        SELECT
                            id,
                            ts_rank_cd(search_vector, to_tsquery('english', $2)) AS full_text_rank
                        FROM items
                        WHERE search_vector @@ to_tsquery('english', $2)
                    )
                    SELECT
                        COALESCE(sr.id, ftr.id) AS id,
                        COALESCE(sr.title, i.title) AS title,
                        COALESCE(sr.summary, i.summary) AS summary,
                        COALESCE(sr.url, i.url) AS url,
                        COALESCE(sr.semantic_similarity, 0.0) AS semantic_similarity,
                        COALESCE(ftr.full_text_rank, 0.0) AS full_text_rank,
                        (COALESCE(sr.semantic_similarity, 0.0) * 0.7 + COALESCE(ftr.full_text_rank, 0.0) * 0.3) AS combined_score
                    FROM semantic_results sr
                    FULL OUTER JOIN full_text_results ftr ON sr.id = ftr.id
                    JOIN items i ON COALESCE(sr.id, ftr.id) = i.id
                    ORDER BY combined_score DESC
                    LIMIT $3 OFFSET $4
                """,
                    query_embedding,
                    request.full_text_query,
                    request.limit,
                    request.offset
                )
            else:
                # Pure semantic search
                results = await conn.fetch("""
                    SELECT id, title, summary, url, 1 - (embedding <=> $1) AS similarity
                    FROM items
                    WHERE embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT $2 OFFSET $3
                """,
                    query_embedding,
                    request.limit,
                    request.offset
                )
            
            return [
                SemanticSearchResult(
                    id=str(row['id']),
                    title=row['title'],
                    summary=row['summary'],
                    url=row['url'],
                    similarity=row['similarity'] if not request.full_text_query else row['combined_score']
                ) for row in results
            ]
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Semantic search failed: {e}")

@router.get("/search/similar/{item_id}", response_model=List[SemanticSearchResult])
async def find_similar_items(item_id: str, limit: int = 10, offset: int = 0, db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """Finds items semantically similar to a given item_id."""
    try:
        async with db_pool.acquire() as conn:
            # Fetch the embedding of the reference item
            reference_item = await conn.fetchrow("SELECT embedding FROM items WHERE id = $1", item_id)
            if not reference_item or not reference_item['embedding']:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or has no embedding.")
            
            reference_embedding = reference_item['embedding']
            
            # Perform cosine similarity search, excluding the item itself
            results = await conn.fetch(
                "SELECT id, title, summary, url, 1 - (embedding <=> $1) AS similarity FROM items WHERE id != $2 AND embedding IS NOT NULL ORDER BY similarity DESC LIMIT $3 OFFSET $4",
                reference_embedding,
                item_id,
                limit,
                offset
            )
            
            return [
                SemanticSearchResult(
                    id=str(row['id']),
                    title=row['title'],
                    summary=row['summary'],
                    url=row['url'],
                    similarity=row['similarity']
                ) for row in results
            ]
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error finding similar items for {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to find similar items: {e}")
