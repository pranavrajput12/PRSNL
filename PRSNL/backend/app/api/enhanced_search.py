"""
Enhanced Search API endpoints using new embedding architecture
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import logging

from app.services.enhanced_search_service import enhanced_search_service
from app.services.embedding_manager import embedding_manager
from app.utils.fingerprint import calculate_content_fingerprint
from app.core.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Enhanced Search"])


class SearchRequest(BaseModel):
    """Request model for enhanced search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    search_type: Literal["semantic", "keyword", "hybrid"] = Field(default="hybrid", description="Type of search to perform")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_duplicates: bool = Field(default=False, description="Whether to include duplicate content")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class DuplicateSearchRequest(BaseModel):
    """Request model for duplicate detection."""
    content: str = Field(..., min_length=1, max_length=10000, description="Content to check for duplicates")
    exclude_id: Optional[str] = Field(default=None, description="Item ID to exclude from results")


class SimilarItemsRequest(BaseModel):
    """Request model for finding similar items."""
    item_id: str = Field(..., description="ID of the item to find similar items for")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of similar items")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")


@router.post("/")
async def enhanced_search(
    request: SearchRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Perform enhanced search with the new embedding architecture.
    
    Supports semantic, keyword, and hybrid search modes with automatic
    deduplication based on content fingerprints.
    """
    try:
        user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Enhanced search request from user {user_id}: '{request.query}' ({request.search_type})")
        
        # Choose search method based on type
        if request.search_type == "semantic":
            results = await enhanced_search_service.semantic_search(
                query=request.query,
                limit=request.limit,
                threshold=request.threshold,
                filter_by=request.filters
            )
        elif request.search_type == "keyword":
            results = await enhanced_search_service.keyword_search(
                query=request.query,
                limit=request.limit,
                filter_by=request.filters
            )
        else:  # hybrid
            results = await enhanced_search_service.hybrid_search(
                query=request.query,
                limit=request.limit
            )
        
        # Apply deduplication if requested
        if not request.include_duplicates:
            results = await enhanced_search_service.search_with_deduplication(
                query=request.query,
                search_type=request.search_type,
                limit=request.limit
            )
        
        # Add search metadata
        results["user_id"] = user_id
        results["request_params"] = {
            "search_type": request.search_type,
            "limit": request.limit,
            "threshold": request.threshold,
            "include_duplicates": request.include_duplicates
        }
        
        logger.info(f"Search completed: {len(results.get('results', []))} results for '{request.query}'")
        return results
        
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/semantic")
async def semantic_search_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    GET endpoint for semantic search (convenience method).
    """
    try:
        results = await enhanced_search_service.semantic_search(
            query=q,
            limit=limit,
            threshold=threshold
        )
        return results
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keyword")
async def keyword_search_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    GET endpoint for keyword search (convenience method).
    """
    try:
        results = await enhanced_search_service.keyword_search(
            query=q,
            limit=limit
        )
        return results
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/duplicates")
async def find_duplicates(
    request: DuplicateSearchRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Find duplicate content using content fingerprint.
    """
    try:
        duplicates = await enhanced_search_service.find_duplicates_by_fingerprint(
            content=request.content,
            exclude_id=request.exclude_id
        )
        
        return {
            "duplicates": duplicates,
            "total": len(duplicates),
            "content_fingerprint": calculate_content_fingerprint(request.content),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Duplicate search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar_items(
    request: SimilarItemsRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Find items similar to a given item using embedding similarity.
    """
    try:
        # Get the item's embedding
        item_embedding = await embedding_manager.get_embedding(request.item_id)
        
        if item_embedding is None:
            raise HTTPException(
                status_code=404,
                detail="Item not found or has no embedding"
            )
        
        # Search for similar items
        similar_items = await embedding_manager.search_similar(
            query_embedding=item_embedding.tolist(),
            limit=request.limit + 1,  # +1 because we'll exclude the original item
            threshold=request.threshold
        )
        
        # Remove the original item from results
        filtered_items = [
            item for item in similar_items 
            if item["id"] != request.item_id
        ][:request.limit]
        
        return {
            "similar_items": filtered_items,
            "total": len(filtered_items),
            "reference_item_id": request.item_id,
            "threshold": request.threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar items search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_search_stats(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Get statistics about the search system.
    """
    try:
        from app.db.database import get_db_pool
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get basic statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(content_fingerprint) as items_with_fingerprint,
                    COUNT(embed_vector_id) as items_with_embedding,
                    COUNT(embedding) as items_with_legacy_embedding
                FROM items
            """)
            
            # Get embeddings table stats
            embedding_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_embeddings,
                    COUNT(DISTINCT model_name) as unique_models,
                    COUNT(DISTINCT item_id) as items_with_embeddings
                FROM embeddings
            """)
            
            return {
                "items": {
                    "total": stats["total_items"],
                    "with_fingerprint": stats["items_with_fingerprint"],
                    "with_embedding": stats["items_with_embedding"],
                    "with_legacy_embedding": stats["items_with_legacy_embedding"]
                },
                "embeddings": {
                    "total": embedding_stats["total_embeddings"],
                    "unique_models": embedding_stats["unique_models"],
                    "items_covered": embedding_stats["items_with_embeddings"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate-embeddings")
async def migrate_legacy_embeddings(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Migrate legacy embeddings from items.embedding to embeddings table.
    """
    try:
        result = await embedding_manager.migrate_legacy_embeddings()
        
        return {
            "migration_result": result,
            "message": f"Migrated {result['migrated']} embeddings, {result['failed']} failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Embedding migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-embeddings")
async def update_all_embeddings(
    model_name: Optional[str] = Query(None, description="Embedding model to use"),
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Update embeddings for all items using content fingerprint change detection.
    """
    try:
        result = await embedding_manager.update_all_embeddings(model_name=model_name)
        
        return {
            "update_result": result,
            "message": f"Updated {result['updated']} embeddings, {result['unchanged']} unchanged, {result['failed']} failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Embedding update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))