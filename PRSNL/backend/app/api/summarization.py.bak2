"""
Content Summarization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field

from app.db.database import get_db_pool
from app.services.content_summarization import ContentSummarizationService
from app.core.auth import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summarization"])


# Request/Response Models
class ItemSummaryRequest(BaseModel):
    item_id: str
    summary_type: str = Field(
        default="brief",
        description="Type of summary: brief, detailed, or key_points"
    )


class DigestRequest(BaseModel):
    period: str = Field(
        default="daily",
        description="Period for digest: daily, weekly, or monthly"
    )
    user_id: Optional[str] = None


class TopicSummaryRequest(BaseModel):
    topic: str = Field(..., description="Topic to summarize")
    limit: int = Field(default=20, ge=1, le=100)


class CustomSummaryRequest(BaseModel):
    start_date: date
    end_date: date
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class BatchSummaryRequest(BaseModel):
    item_ids: List[str]
    summary_type: str = Field(default="brief")


class SummaryResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None


# Initialize service
summarization_service = ContentSummarizationService()


@router.post("/item", response_model=SummaryResponse)
async def summarize_item(
    request: ItemSummaryRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Generate a summary for a single item
    """
    try:
        result = await summarization_service.summarize_item(
            item_id=request.item_id,
            summary_type=request.summary_type
        )
        
        return SummaryResponse(
            success=True,
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error summarizing item: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.post("/digest", response_model=SummaryResponse)
async def generate_digest(
    request: DigestRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Generate a content digest for a specific period
    """
    try:
        result = await summarization_service.generate_digest(
            period=request.period,
            user_id=request.user_id or (current_user.id if current_user else None)
        )
        
        return SummaryResponse(
            success=True,
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate digest")


@router.post("/topic", response_model=SummaryResponse)
async def generate_topic_summary(
    request: TopicSummaryRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Generate a summary for a specific topic
    """
    try:
        result = await summarization_service.generate_topic_summary(
            topic=request.topic,
            limit=request.limit
        )
        
        return SummaryResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error generating topic summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate topic summary")


@router.post("/custom", response_model=SummaryResponse)
async def generate_custom_summary(
    request: CustomSummaryRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Generate a custom summary based on filters
    """
    try:
        # Convert date to datetime
        start_datetime = datetime.combine(request.start_date, datetime.min.time())
        end_datetime = datetime.combine(request.end_date, datetime.max.time())
        
        result = await summarization_service.generate_custom_summary(
            start_date=start_datetime,
            end_date=end_datetime,
            categories=request.categories,
            tags=request.tags
        )
        
        return SummaryResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error generating custom summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate custom summary")


@router.post("/batch", response_model=SummaryResponse)
async def batch_summarize(
    request: BatchSummaryRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Summarize multiple items in batch
    """
    try:
        if len(request.item_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 items allowed per batch"
            )
        
        results = await summarization_service.batch_summarize(
            item_ids=request.item_ids,
            summary_type=request.summary_type
        )
        
        return SummaryResponse(
            success=True,
            data={"summaries": results}
        )
    except Exception as e:
        logger.error(f"Error in batch summarization: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch summarize")


@router.get("/digest/preview")
async def preview_digest(
    period: str = Query(default="daily", description="Period: daily, weekly, monthly"),
    current_user = Depends(get_current_user_optional)
):
    """
    Preview what would be included in a digest without generating the full summary
    """
    try:
        # Calculate time range
        now = datetime.utcnow()
        if period == "daily":
            start_date = now - timedelta(days=1)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        # Query item count and categories
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get item count
            item_count = await conn.fetchval("""
                SELECT COUNT(*) FROM items
                WHERE created_at >= $1
            """, start_date)
            
            # Get category breakdown
            category_rows = await conn.fetch("""
                SELECT 
                    COALESCE(metadata->>'category', 'Uncategorized') as category,
                    COUNT(*) as count
                FROM items
                WHERE created_at >= $1
                GROUP BY metadata->>'category'
            """, start_date)
            
            categories = [
                {"category": row['category'], "count": row['count']}
                for row in category_rows
            ]
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "item_count": item_count,
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Error previewing digest: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview digest")


# Import datetime for the preview endpoint
from datetime import timedelta