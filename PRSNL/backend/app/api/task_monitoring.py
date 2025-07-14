"""
Task Monitoring API - Enterprise-grade task monitoring endpoints

Provides real-time monitoring of Celery tasks, workflows, and progress tracking.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_pool
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["task_monitoring"])

# Response Models
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict]
    progress: Optional[int]
    error: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
class WorkflowResponse(BaseModel):
    id: str
    job_id: str
    workflow_type: str
    status: str
    progress: int
    total_subtasks: int
    completed_subtasks: int
    main_task_id: str
    subtask_ids: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[dict]

class TaskProgressResponse(BaseModel):
    task_id: str
    job_id: Optional[str]
    progress_type: str
    current_value: int
    total_value: Optional[int]
    message: Optional[str]
    percentage: Optional[float]
    created_at: datetime

# Endpoints
@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Get the current status of a Celery task"""
    
    try:
        # Get task info from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        # Get additional info from database
        pool = await get_db_pool()
        async with pool.acquire() as db:
            task_meta = await db.fetchrow("""
                SELECT * FROM celery_task_meta 
                WHERE task_id = $1
            """, task_id)
            
            # Get workflow info if exists
            workflow = await db.fetchrow("""
                SELECT * FROM codemirror_task_workflows 
                WHERE main_task_id = $1 OR $1 = ANY(subtask_ids)
            """, task_id)
            
            # Get progress info
            progress_info = await db.fetchrow("""
                SELECT * FROM codemirror_task_progress 
                WHERE task_id = $1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, task_id)
        
        # Calculate progress percentage
        progress_percentage = None
        if progress_info:
            if progress_info['total_value'] and progress_info['total_value'] > 0:
                progress_percentage = (progress_info['current_value'] / progress_info['total_value']) * 100
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
            result=task_result.result if task_result.successful() else None,
            progress=workflow['progress'] if workflow else progress_percentage,
            error=str(task_result.result) if task_result.failed() else None,
            created_at=task_meta['created_at'] if task_meta else datetime.utcnow(),
            updated_at=task_meta['updated_at'] if task_meta else None
        )
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

@router.get("/workflow/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user = Depends(get_current_user)
):
    """Get the status of a complete workflow"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        workflow = await db.fetchrow("""
            SELECT * FROM codemirror_task_workflows 
            WHERE id = $1
        """, UUID(workflow_id))
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify user has access to this workflow
        job_access = await db.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM processing_jobs 
                WHERE job_id = $1 AND user_id = $2
            )
        """, workflow['job_id'], current_user.id)
        
        if not job_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return WorkflowResponse(
            id=str(workflow['id']),
            job_id=workflow['job_id'],
            workflow_type=workflow['workflow_type'],
            status=workflow['status'],
            progress=workflow['progress'],
            total_subtasks=workflow['total_subtasks'],
            completed_subtasks=workflow['completed_subtasks'],
            main_task_id=workflow['main_task_id'],
            subtask_ids=workflow['subtask_ids'] or [],
            started_at=workflow['started_at'],
            completed_at=workflow['completed_at'],
            error_message=workflow['error_message'],
            metadata=workflow['metadata']
        )

@router.get("/progress/{task_id}")
async def get_task_progress(
    task_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get progress updates for a task"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        progress_updates = await db.fetch("""
            SELECT * FROM codemirror_task_progress 
            WHERE task_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, task_id, limit)
        
        return [
            TaskProgressResponse(
                task_id=p['task_id'],
                job_id=p['job_id'],
                progress_type=p['progress_type'],
                current_value=p['current_value'],
                total_value=p['total_value'],
                message=p['message'],
                percentage=(p['current_value'] / p['total_value'] * 100) if p['total_value'] else None,
                created_at=p['created_at']
            )
            for p in progress_updates
        ]

@router.get("/active")
async def get_active_tasks(
    workflow_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get active tasks for the current user"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        query = """
            SELECT * FROM codemirror_active_tasks 
            WHERE user_id = $1
        """
        params = [current_user.id]
        
        if workflow_type:
            query += " AND workflow_type = $2"
            params.append(workflow_type)
        
        query += " ORDER BY started_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        active_tasks = await db.fetch(query, *params)
        
        return [
            {
                "workflow_id": str(task['workflow_id']),
                "job_id": task['job_id'],
                "workflow_type": task['workflow_type'],
                "status": task['workflow_status'],
                "progress": task['progress'],
                "total_subtasks": task['total_subtasks'],
                "completed_subtasks": task['completed_subtasks'],
                "started_at": task['started_at'],
                "repo_id": task['repo_id'],
                "analysis_depth": task['analysis_depth']
            }
            for task in active_tasks
        ]

@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Cancel a running task"""
    
    try:
        # Revoke the task in Celery
        celery_app.control.revoke(task_id, terminate=True)
        
        # Update database status
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE celery_task_meta 
                SET status = 'REVOKED', updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $1
            """, task_id)
            
            await db.execute("""
                UPDATE codemirror_task_workflows 
                SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP
                WHERE main_task_id = $1 OR $1 = ANY(subtask_ids)
            """, task_id)
        
        return {"message": "Task cancelled successfully", "task_id": task_id}
        
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")

@router.get("/stats")
async def get_task_stats(
    days: int = Query(7, ge=1, le=30),
    current_user = Depends(get_current_user)
):
    """Get task execution statistics"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get workflow stats
        workflow_stats = await db.fetchrow("""
            SELECT 
                COUNT(*) as total_workflows,
                COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'FAILURE' THEN 1 END) as failed,
                COUNT(CASE WHEN status IN ('PENDING', 'STARTED') THEN 1 END) as active,
                AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
            FROM codemirror_task_workflows w
            JOIN processing_jobs j ON w.job_id = j.job_id
            WHERE j.user_id = $1 AND w.created_at >= $2
        """, current_user.id, since_date)
        
        # Get task type distribution
        task_types = await db.fetch("""
            SELECT 
                workflow_type,
                COUNT(*) as count
            FROM codemirror_task_workflows w
            JOIN processing_jobs j ON w.job_id = j.job_id
            WHERE j.user_id = $1 AND w.created_at >= $2
            GROUP BY workflow_type
            ORDER BY count DESC
        """, current_user.id, since_date)
        
        return {
            "period_days": days,
            "total_workflows": workflow_stats['total_workflows'],
            "successful": workflow_stats['successful'],
            "failed": workflow_stats['failed'],
            "active": workflow_stats['active'],
            "success_rate": (workflow_stats['successful'] / workflow_stats['total_workflows'] * 100) if workflow_stats['total_workflows'] > 0 else 0,
            "avg_duration_seconds": workflow_stats['avg_duration_seconds'],
            "task_type_distribution": [
                {"type": task['workflow_type'], "count": task['count']}
                for task in task_types
            ]
        }

@router.websocket("/ws/progress/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str
):
    """WebSocket endpoint for real-time task progress updates"""
    
    await websocket.accept()
    
    try:
        while True:
            # Get current progress
            pool = await get_db_pool()
            async with pool.acquire() as db:
                progress = await db.fetchrow("""
                    SELECT * FROM codemirror_task_progress 
                    WHERE task_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, task_id)
                
                if progress:
                    await websocket.send_json({
                        "task_id": task_id,
                        "progress_type": progress['progress_type'],
                        "current_value": progress['current_value'],
                        "total_value": progress['total_value'],
                        "message": progress['message'],
                        "percentage": (progress['current_value'] / progress['total_value'] * 100) if progress['total_value'] else None,
                        "timestamp": progress['created_at'].isoformat()
                    })
            
            # Check if task is complete
            task_result = celery_app.AsyncResult(task_id)
            if task_result.ready():
                await websocket.send_json({
                    "task_id": task_id,
                    "status": "completed",
                    "final_status": task_result.status,
                    "result": task_result.result if task_result.successful() else None,
                    "error": str(task_result.result) if task_result.failed() else None
                })
                break
            
            # Wait before next update
            await websocket.receive_text()  # Wait for client ping
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

@router.get("/health")
async def get_celery_health():
    """Get Celery worker health status"""
    
    try:
        # Check if Celery is responding
        inspect = celery_app.control.inspect()
        
        # Get worker stats
        stats = inspect.stats()
        active_tasks = inspect.active()
        registered_tasks = inspect.registered()
        
        if not stats:
            return {"status": "unhealthy", "message": "No Celery workers available"}
        
        worker_info = []
        for worker_name, worker_stats in stats.items():
            worker_info.append({
                "name": worker_name,
                "status": "healthy",
                "pool": worker_stats.get('pool', {}),
                "total_tasks": worker_stats.get('total', {}),
                "active_tasks": len(active_tasks.get(worker_name, [])),
                "registered_tasks": len(registered_tasks.get(worker_name, []))
            })
        
        return {
            "status": "healthy",
            "workers": worker_info,
            "total_workers": len(stats),
            "broker_url": celery_app.conf.broker_url,
            "result_backend": celery_app.conf.result_backend
        }
        
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }