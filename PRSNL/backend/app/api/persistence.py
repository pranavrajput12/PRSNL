"""
Unified Job Persistence API

This module provides API endpoints for the unified job persistence system.
It allows clients to save job results, check job status, and manage job lifecycle
through a consistent REST interface.

API Endpoints:
- POST /api/persistence/save - Save job results with jobId coordination
- GET /api/persistence/status/{jobId} - Get job status and results
- PUT /api/persistence/update - Update job status during processing
- GET /api/persistence/jobs - List jobs with filtering
- POST /api/persistence/retry/{jobId} - Retry a failed job
- DELETE /api/persistence/cancel/{jobId} - Cancel a pending/processing job
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.exceptions import InternalServerError
from app.db.database import get_db_connection
from app.models.schemas import (
    JobListRequest,
    JobListResponse,
    JobPersistenceRequest,
    JobResult,
    JobStatus,
    ProcessingJobCreate,
    ProcessingJobResponse,
    ProcessingJobUpdate
)
from app.services.job_persistence_service import JobPersistenceService

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_job_service():
    """Dependency to get job persistence service with database connection"""
    async for conn in get_db_connection():
        yield JobPersistenceService(conn)

@router.post("/save", response_model=Dict[str, Any])
async def save_job_result(
    request: JobPersistenceRequest,
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Save job results with jobId coordination.
    
    This is the main persistence endpoint that allows clients to save
    processing results in a coordinated manner. It's idempotent - calling
    it multiple times with the same job_id will update the existing record.
    
    Args:
        request: Job persistence request with job_id, result_data, and status
        
    Returns:
        Success confirmation with job details
        
    Raises:
        404: Job not found
        500: Internal server error
    """
    try:
        # Check if job exists
        job_status = await job_service.get_job_status(request.job_id)
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {request.job_id} not found"
            )
        
        # Save the results
        success = await job_service.save_job_result(
            job_id=request.job_id,
            result_data=request.result_data,
            status=request.status.value
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to save results for job {request.job_id}"
            )
        
        # Get updated job status
        updated_job = await job_service.get_job_status(request.job_id)
        
        logger.info(f"Successfully saved results for job {request.job_id}")
        
        return {
            "message": f"Results saved successfully for job {request.job_id}",
            "job_id": request.job_id,
            "status": updated_job['status'],
            "completed_at": updated_job['completed_at'].isoformat() if updated_job['completed_at'] else None,
            "result_size": len(str(request.result_data))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving job result for {request.job_id}: {e}")
        raise InternalServerError(f"Failed to save job result: {str(e)}")

@router.get("/status/{job_id}", response_model=ProcessingJobResponse)
async def get_job_status(
    job_id: str,
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Get job status and results.
    
    Returns comprehensive job information including current status,
    progress, results (if completed), and error details (if failed).
    
    Args:
        job_id: Job identifier
        
    Returns:
        Complete job information
        
    Raises:
        404: Job not found
        500: Internal server error
    """
    try:
        job_data = await job_service.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Convert to response model
        response = ProcessingJobResponse(
            job_id=job_data['job_id'],
            job_type=job_data['job_type'],
            status=JobStatus(job_data['status']),
            item_id=job_data['item_id'],
            progress_percentage=job_data['progress_percentage'] or 0,
            current_stage=job_data['current_stage'],
            stage_message=job_data['stage_message'],
            error_message=job_data['error_message'],
            result_data=job_data['result_data'],
            created_at=job_data['created_at'],
            started_at=job_data['started_at'],
            completed_at=job_data['completed_at'],
            last_updated=job_data['last_updated'],
            retry_count=job_data['retry_count'],
            tags=job_data['tags'] or []
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise InternalServerError(f"Failed to get job status: {str(e)}")

@router.put("/update", response_model=Dict[str, Any])
async def update_job_status(
    job_id: str = Query(..., description="Job identifier"),
    update: ProcessingJobUpdate = None,
    status: Optional[JobStatus] = Query(None, description="New job status"),
    progress: Optional[int] = Query(None, ge=0, le=100, description="Progress percentage"),
    stage: Optional[str] = Query(None, description="Current processing stage"),
    message: Optional[str] = Query(None, description="Stage message"),
    error: Optional[str] = Query(None, description="Error message"),
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Update job status during processing.
    
    This endpoint allows processing workers to update job status, progress,
    and other details during execution. Can be called via query parameters
    or request body.
    
    Args:
        job_id: Job identifier
        update: Job update object (from request body)
        status: New status (from query params)
        progress: Progress percentage (from query params)
        stage: Current stage (from query params)
        message: Stage message (from query params)
        error: Error message (from query params)
        
    Returns:
        Update confirmation
        
    Raises:
        404: Job not found
        500: Internal server error
    """
    try:
        # Merge query params with request body
        if update:
            status_value = update.status.value if update.status else status.value if status else None
            progress_value = update.progress_percentage if update.progress_percentage is not None else progress
            stage_value = update.current_stage if update.current_stage else stage
            message_value = update.stage_message if update.stage_message else message
            error_value = update.error_message if update.error_message else error
            error_details = update.error_details
        else:
            status_value = status.value if status else None
            progress_value = progress
            stage_value = stage
            message_value = message
            error_value = error
            error_details = None
        
        # Update job status
        success = await job_service.update_job_status(
            job_id=job_id,
            status=status_value,
            progress_percentage=progress_value,
            current_stage=stage_value,
            stage_message=message_value,
            error_message=error_value,
            error_details=error_details
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        logger.info(f"Updated job {job_id}: status={status_value}, progress={progress_value}%")
        
        return {
            "message": f"Job {job_id} updated successfully",
            "job_id": job_id,
            "status": status_value,
            "progress_percentage": progress_value,
            "updated_at": "now"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise InternalServerError(f"Failed to update job: {str(e)}")

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    item_id: Optional[UUID] = Query(None, description="Filter by associated item"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    List jobs with optional filtering.
    
    Provides paginated access to jobs with support for filtering by
    job type, status, and associated item. Useful for dashboards
    and monitoring interfaces.
    
    Args:
        job_type: Filter by job type
        status: Filter by status
        item_id: Filter by associated item
        limit: Maximum results per page
        offset: Pagination offset
        
    Returns:
        Paginated list of jobs
        
    Raises:
        500: Internal server error
    """
    try:
        # Get jobs list
        jobs_data = await job_service.list_jobs(
            job_type=job_type,
            status=status.value if status else None,
            item_id=item_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to response models
        jobs = []
        for job_data in jobs_data:
            job_response = ProcessingJobResponse(
                job_id=job_data['job_id'],
                job_type=job_data['job_type'],
                status=JobStatus(job_data['status']),
                item_id=job_data['item_id'],
                progress_percentage=job_data['progress_percentage'] or 0,
                current_stage=job_data['current_stage'],
                stage_message=job_data['stage_message'],
                error_message=job_data['error_message'],
                result_data=None,  # Don't include full results in list view
                created_at=job_data['created_at'],
                started_at=job_data['started_at'],
                completed_at=job_data['completed_at'],
                last_updated=job_data['last_updated'],
                retry_count=0,  # Not included in list query for performance
                tags=job_data['tags'] or []
            )
            jobs.append(job_response)
        
        # For total count, we'd need a separate query in a real implementation
        # For now, estimate based on limit/offset
        total = len(jobs_data)
        if len(jobs_data) == limit:
            total = offset + limit + 1  # Estimate there are more
        
        return JobListResponse(
            jobs=jobs,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise InternalServerError(f"Failed to list jobs: {str(e)}")

@router.post("/retry/{job_id}", response_model=Dict[str, Any])
async def retry_job(
    job_id: str,
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Retry a failed job.
    
    Marks a failed job for retry by resetting its status to pending
    and incrementing the retry count. Only works for jobs that haven't
    exceeded their maximum retry limit.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Retry confirmation
        
    Raises:
        404: Job not found
        400: Job cannot be retried
        500: Internal server error
    """
    try:
        success = await job_service.retry_job(job_id)
        
        if not success:
            # Check if job exists
            job_status = await job_service.get_job_status(job_id)
            if not job_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Job {job_id} cannot be retried (not failed or max retries exceeded)"
                )
        
        logger.info(f"Marked job {job_id} for retry")
        
        return {
            "message": f"Job {job_id} marked for retry",
            "job_id": job_id,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {e}")
        raise InternalServerError(f"Failed to retry job: {str(e)}")

@router.delete("/cancel/{job_id}", response_model=Dict[str, Any])
async def cancel_job(
    job_id: str,
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Cancel a pending or processing job.
    
    Marks a job as cancelled if it's currently pending or processing.
    Once cancelled, a job cannot be resumed or retried.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Cancellation confirmation
        
    Raises:
        404: Job not found
        400: Job cannot be cancelled
        500: Internal server error
    """
    try:
        success = await job_service.cancel_job(job_id)
        
        if not success:
            # Check if job exists
            job_status = await job_service.get_job_status(job_id)
            if not job_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job {job_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Job {job_id} cannot be cancelled (not pending or processing)"
                )
        
        logger.info(f"Cancelled job {job_id}")
        
        return {
            "message": f"Job {job_id} cancelled successfully",
            "job_id": job_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise InternalServerError(f"Failed to cancel job: {str(e)}")

@router.post("/create", response_model=Dict[str, Any])
async def create_job(
    request: ProcessingJobCreate,
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Create a new processing job.
    
    Creates a new job entry in the processing_jobs table with the specified
    parameters. This is typically called by processing services before
    starting work.
    
    Args:
        request: Job creation request
        
    Returns:
        Created job information
        
    Raises:
        500: Internal server error
    """
    try:
        job_id = await job_service.create_job(
            job_type=request.job_type,
            input_data=request.input_data,
            item_id=request.item_id,
            job_id=request.job_id,
            metadata=request.metadata,
            tags=request.tags
        )
        
        logger.info(f"Created job {job_id} of type {request.job_type}")
        
        return {
            "message": f"Job created successfully",
            "job_id": job_id,
            "job_type": request.job_type,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise InternalServerError(f"Failed to create job: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def persistence_health_check(
    job_service: JobPersistenceService = Depends(get_job_service)
):
    """
    Health check for persistence service.
    
    Verifies that the persistence service and database connection
    are working correctly.
    
    Returns:
        Health status information
    """
    try:
        # Test database connection by getting job stats
        stats = await job_service.list_jobs(limit=1)
        
        return {
            "status": "healthy",
            "service": "job_persistence",
            "database_connected": True,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"Persistence health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "job_persistence",
                "database_connected": False,
                "error": str(e),
                "timestamp": "now"
            }
        )