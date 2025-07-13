"""
Smart Categorization API endpoints
"""
from typing import Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_pool
from app.services.smart_categorization import smart_categorization

router = APIRouter()


class CategorizationRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None


class CategorizationResponse(BaseModel):
    category: str
    subcategory: str
    confidence: float
    suggested_tags: List[str]
    content_type: str
    reasoning: str


class BulkCategorizationResponse(BaseModel):
    processed: int
    total: int
    stats: Dict[str, int]
    message: str


class ItemConnectionResponse(BaseModel):
    id: str
    title: str
    similarity: float
    connection_type: str
    strength: str
    reason: str


@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_content(request: CategorizationRequest):
    """
    Categorize content using AI analysis
    """
    try:
        result = await smart_categorization.categorize_item(
            request.title,
            request.content,
            request.tags
        )
        return CategorizationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to categorize content: {str(e)}"
        )


@router.post("/categorize/bulk", response_model=BulkCategorizationResponse)
async def bulk_categorize(limit: int = 100):
    """
    Categorize multiple uncategorized items in bulk
    """
    try:
        result = await smart_categorization.bulk_categorize(limit)
        return BulkCategorizationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk categorization failed: {str(e)}"
        )


@router.get("/items/{item_id}/connections", response_model=List[ItemConnectionResponse])
async def get_item_connections(item_id: str, limit: int = 5):
    """
    Get suggested connections for an item based on content analysis
    """
    try:
        connections = await smart_categorization.suggest_item_connections(item_id, limit)
        return [ItemConnectionResponse(**conn) for conn in connections]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get item connections: {str(e)}"
        )


@router.post("/reorganize/clusters")
async def reorganize_by_clusters():
    """
    Reorganize content based on semantic clustering
    """
    try:
        result = await smart_categorization.reorganize_by_clusters()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorganize by clusters: {str(e)}"
        )


@router.get("/categories/stats")
async def get_category_statistics(db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """
    Get statistics about content categories
    """
    try:
        async with db_pool.acquire() as conn:
            # Get category counts
            category_stats = await conn.fetch("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    COUNT(DISTINCT tags) as unique_tags,
                    AVG(CASE WHEN metadata->>'ai_categorization' IS NOT NULL 
                        THEN (metadata->'ai_categorization'->>'confidence')::float 
                        ELSE 0 END) as avg_confidence
                FROM items
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            
            # Get uncategorized count
            uncategorized = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM items 
                WHERE category IS NULL OR category = 'general'
            """)
            
            return {
                "categories": [
                    {
                        "name": row['category'],
                        "count": row['count'],
                        "unique_tags": row['unique_tags'],
                        "avg_confidence": float(row['avg_confidence'] or 0)
                    }
                    for row in category_stats
                ],
                "uncategorized_count": uncategorized,
                "total_items": sum(row['count'] for row in category_stats) + uncategorized
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category statistics: {str(e)}"
        )