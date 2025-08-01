"""
Auto-Processing API endpoints
Provides endpoints for monitoring and controlling automatic AI processing
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_optional
from app.db.database import get_db_pool
from app.services.auto_processing_service import auto_processing_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auto-processing"])


# Request/Response Models
class ProcessItemRequest(BaseModel):
    item_id: UUID = Field(..., description="Item UUID to process")
    enable_ai_processing: bool = Field(default=True, description="Enable AI analysis")
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if already processed")


class BatchProcessRequest(BaseModel):
    item_ids: List[UUID] = Field(..., description="List of item UUIDs to process", max_items=50)
    enable_ai_processing: bool = Field(default=True, description="Enable AI analysis for all items")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="Maximum concurrent processing tasks")


class ProcessingStatusResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None


class ProcessingStatsResponse(BaseModel):
    total_items: int
    pending_items: int
    completed_items: int
    failed_items: int
    processing_items: int
    auto_processing_enabled: bool


@router.get("/status/{item_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    item_id: UUID,
    current_user=Depends(get_current_user_optional)
):
    """
    Get processing status for a specific item
    """
    try:
        status_data = await auto_processing_service.get_processing_status(item_id)
        
        return ProcessingStatusResponse(
            success=True,
            data=status_data,
            message="Processing status retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting processing status for {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.post("/process", response_model=ProcessingStatusResponse)
async def process_item(
    request: ProcessItemRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_optional)
):
    """
    Manually trigger processing for a specific item
    """
    try:
        # Check if item exists and get current status
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            item_data = await conn.fetchrow("""
                SELECT id, status, title, raw_content, url
                FROM items 
                WHERE id = $1
            """, request.item_id)
            
            if not item_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            
            # Check if already processed and not forcing reprocess
            if (item_data['status'] == 'completed' and 
                not request.force_reprocess):
                return ProcessingStatusResponse(
                    success=True,
                    data={
                        "item_id": str(request.item_id),
                        "status": "already_processed",
                        "message": "Item already processed. Use force_reprocess=true to reprocess."
                    }
                )
        
        # Trigger processing in background
        background_tasks.add_task(
            auto_processing_service.process_captured_item,
            request.item_id,
            item_data['raw_content'],
            item_data['url'],
            item_data['title'],
            request.enable_ai_processing
        )
        
        return ProcessingStatusResponse(
            success=True,
            data={
                "item_id": str(request.item_id),
                "status": "processing_started",
                "ai_processing_enabled": request.enable_ai_processing
            },
            message="Processing started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing item {request.item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process item: {str(e)}"
        )


@router.post("/batch-process", response_model=ProcessingStatusResponse)
async def batch_process_items(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_optional)
):
    """
    Process multiple items in batch
    """
    try:
        if len(request.item_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 items allowed per batch"
            )
        
        # Trigger batch processing in background
        background_tasks.add_task(
            auto_processing_service.batch_process_items,
            request.item_ids,
            request.max_concurrent
        )
        
        return ProcessingStatusResponse(
            success=True,
            data={
                "item_count": len(request.item_ids),
                "status": "batch_processing_started",
                "max_concurrent": request.max_concurrent,
                "ai_processing_enabled": request.enable_ai_processing
            },
            message=f"Batch processing started for {len(request.item_ids)} items"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch processing: {str(e)}"
        )


@router.get("/stats", response_model=ProcessingStatsResponse)
async def get_processing_stats(
    current_user=Depends(get_current_user_optional)
):
    """
    Get overall processing statistics
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get item counts by status
            status_counts = await conn.fetch("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM items
                GROUP BY status
            """)
            
            # Get count of items with auto-processing metadata
            auto_processed_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM items
                WHERE metadata ? 'auto_processing'
            """)
            
            # Convert to dict
            status_dict = {row['status']: row['count'] for row in status_counts}
            total_items = sum(status_dict.values())
            
            # Count currently processing items (approximation)
            processing_items = len(auto_processing_service.processing_queue)
            
            return ProcessingStatsResponse(
                total_items=total_items,
                pending_items=status_dict.get('pending', 0),
                completed_items=status_dict.get('completed', 0),
                failed_items=status_dict.get('failed', 0),
                processing_items=processing_items,
                auto_processing_enabled=bool(auto_processed_count > 0)
            )
            
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing statistics: {str(e)}"
        )


@router.get("/queue/status")
async def get_queue_status(
    current_user=Depends(get_current_user_optional)
):
    """
    Get current processing queue status
    """
    try:
        queue_items = list(auto_processing_service.processing_queue)
        
        return {
            "queue_size": len(queue_items),
            "currently_processing": queue_items,
            "queue_status": "active" if queue_items else "idle"
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )


@router.post("/bulk-process-unprocessed")
async def bulk_process_unprocessed(
    background_tasks: BackgroundTasks,
    limit: int = 100,
    enable_ai_processing: bool = True,
    current_user=Depends(get_current_user_optional)
):
    """
    Process all unprocessed items in bulk
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get unprocessed items
            unprocessed_items = await conn.fetch("""
                SELECT id
                FROM items
                WHERE status = 'pending' 
                   OR (metadata ? 'auto_processing') = false
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            if not unprocessed_items:
                return {
                    "message": "No unprocessed items found",
                    "count": 0
                }
            
            item_ids = [UUID(str(row['id'])) for row in unprocessed_items]
            
            # Trigger batch processing
            background_tasks.add_task(
                auto_processing_service.batch_process_items,
                item_ids,
                3  # max_concurrent
            )
            
            return {
                "message": f"Started processing {len(item_ids)} unprocessed items",
                "count": len(item_ids),
                "ai_processing_enabled": enable_ai_processing
            }
            
    except Exception as e:
        logger.error(f"Error processing unprocessed items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process unprocessed items: {str(e)}"
        )