"""
Background Processing API

API endpoints for managing and monitoring Celery background tasks
for AI processing, file processing, and media processing.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_pool
from app.workers.ai_processing_tasks import (
    analyze_content_task,
    generate_embeddings_batch_task,
    process_with_llm_task,
    smart_categorization_task
)
from app.workers.file_processing_tasks import (
    process_document_task,
    extract_text_from_pdf_task,
    analyze_file_with_ai_task,
    batch_process_files_task
)
from app.workers.media_processing_tasks import (
    transcribe_audio_task,
    process_video_task,
    enhance_video_with_ai_task,
    batch_transcribe_videos_task
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/background", tags=["background_processing"])

# Request/Response Models
class AIProcessingRequest(BaseModel):
    content_id: str
    content: str
    options: Optional[Dict[str, Any]] = None

class BatchEmbeddingRequest(BaseModel):
    items: List[Dict[str, Any]]  # [{"id": str, "content": str, "type": str}]
    cache_prefix: Optional[str] = ""

class LLMProcessingRequest(BaseModel):
    content: str
    prompt_type: str  # summarize, analyze, categorize, extract_insights
    options: Optional[Dict[str, Any]] = None

class FileProcessingRequest(BaseModel):
    file_id: str
    file_path: str
    options: Optional[Dict[str, Any]] = None

class MediaProcessingRequest(BaseModel):
    media_file_path: str
    options: Optional[Dict[str, Any]] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# AI Processing Endpoints
@router.post("/ai/analyze-content")
async def start_content_analysis(
    request: AIProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Start AI-powered content analysis in background"""
    
    try:
        # Verify content ownership
        pool = await get_db_pool()
        async with pool.acquire() as db:
            content_exists = await db.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM items 
                    WHERE id = $1 AND user_id = $2
                )
            """, UUID(request.content_id), current_user.id)
            
            if not content_exists:
                raise HTTPException(status_code=404, detail="Content not found")
        
        # Start Celery task
        task = analyze_content_task.delay(
            content_id=request.content_id,
            content=request.content,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Content analysis started in background",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start content analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/generate-embeddings-batch")
async def start_batch_embedding_generation(
    request: BatchEmbeddingRequest,
    current_user = Depends(get_current_user)
):
    """Generate embeddings for multiple items in batch"""
    
    try:
        # Start Celery task
        task = generate_embeddings_batch_task.delay(
            items=request.items,
            cache_prefix=request.cache_prefix
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Batch embedding generation started for {len(request.items)} items",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start batch embedding generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/process-with-llm")
async def start_llm_processing(
    request: LLMProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Process content with LLM for specific tasks"""
    
    try:
        # Start Celery task
        task = process_with_llm_task.delay(
            content=request.content,
            prompt_type=request.prompt_type,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"LLM {request.prompt_type} processing started",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start LLM processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Processing Endpoints
@router.post("/files/process-document")
async def start_document_processing(
    request: FileProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Process uploaded document in background"""
    
    try:
        # Verify file ownership
        pool = await get_db_pool()
        async with pool.acquire() as db:
            file_exists = await db.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM attachments 
                    WHERE id = $1 AND user_id = $2
                )
            """, UUID(request.file_id), current_user.id)
            
            if not file_exists:
                raise HTTPException(status_code=404, detail="File not found")
        
        # Start Celery task
        task = process_document_task.delay(
            file_id=request.file_id,
            file_path=request.file_path,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Document processing started in background",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start document processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/extract-pdf-text")
async def start_pdf_text_extraction(
    request: FileProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Extract text from PDF with OCR fallback"""
    
    try:
        # Start Celery task
        task = extract_text_from_pdf_task.delay(
            file_id=request.file_id,
            file_path=request.file_path,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "PDF text extraction started",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start PDF text extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Media Processing Endpoints
@router.post("/media/transcribe-audio")
async def start_audio_transcription(
    request: MediaProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Transcribe audio file using hybrid approach"""
    
    try:
        # Start Celery task
        task = transcribe_audio_task.delay(
            audio_file_path=request.media_file_path,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Audio transcription started",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start audio transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/process-video")
async def start_video_processing(
    request: MediaProcessingRequest,
    current_user = Depends(get_current_user)
):
    """Process video: extract metadata, audio, and transcribe"""
    
    try:
        # Start Celery task
        task = process_video_task.delay(
            video_file_path=request.media_file_path,
            options=request.options or {}
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Video processing started",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task Monitoring Endpoints
@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status and progress of a background task"""
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Get task progress
            progress = await db.fetchrow("""
                SELECT * FROM task_progress 
                WHERE task_id = $1 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, task_id)
            
            # Get Celery task result
            task_result = await db.fetchrow("""
                SELECT * FROM celery_task_results 
                WHERE task_id = $1
            """, task_id)
            
            if not progress and not task_result:
                raise HTTPException(status_code=404, detail="Task not found")
            
            response = TaskStatusResponse(
                task_id=task_id,
                status=task_result["status"] if task_result else "unknown",
                progress={
                    "current": progress["current_value"] if progress else 0,
                    "total": progress["total_value"] if progress else None,
                    "percentage": (
                        round((progress["current_value"] / progress["total_value"]) * 100, 2)
                        if progress and progress["total_value"] and progress["total_value"] > 0
                        else 0
                    ),
                    "message": progress["message"] if progress else None,
                    "updated_at": progress["updated_at"].isoformat() if progress else None
                } if progress else None,
                result=task_result["result"] if task_result else None,
                error=task_result["error_message"] if task_result else None
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/active")
async def get_active_tasks(
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get list of currently active/running tasks"""
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as db:
            active_tasks = await db.fetch("""
                SELECT * FROM active_task_progress 
                ORDER BY updated_at DESC 
                LIMIT $1
            """, limit)
            
            return [dict(task) for task in active_tasks]
            
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/overview")
async def get_performance_overview(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user = Depends(get_current_user)
):
    """Get performance overview for task queues"""
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Get performance metrics
            performance_data = await db.fetch("""
                SELECT 
                    queue_name,
                    task_name,
                    total_tasks,
                    successful_tasks,
                    failed_tasks,
                    pending_tasks,
                    running_tasks,
                    avg_runtime_seconds,
                    max_runtime_seconds,
                    avg_retry_count
                FROM task_performance_overview
                WHERE latest_task_created >= NOW() - INTERVAL '%s hours'
                ORDER BY total_tasks DESC
            """, hours)
            
            return [dict(metric) for metric in performance_data]
            
    except Exception as e:
        logger.error(f"Failed to get performance overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints
@router.post("/ai/smart-categorization")
async def start_smart_categorization(
    content_items: List[Dict[str, Any]],
    current_user = Depends(get_current_user)
):
    """Start smart categorization for multiple content items"""
    
    try:
        # Start Celery task
        task = smart_categorization_task.delay(content_items=content_items)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Smart categorization started for {len(content_items)} items",
            "monitor_url": f"/api/background/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start smart categorization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Cancel a running background task"""
    
    try:
        from app.workers.celery_app import celery_app
        
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        # Update status in database
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE celery_task_results 
                SET status = 'revoked', completed_at = CURRENT_TIMESTAMP
                WHERE task_id = $1
            """, task_id)
            
            await db.execute("""
                UPDATE task_progress 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $1
            """, task_id)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))