"""
Unified Job Persistence Service

This service provides a centralized system for managing job lifecycle and persistence.
It coordinates with the processing_jobs table to track all types of processing operations
and provides idempotent persistence operations.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import asyncpg
from app.models.schemas import JobResult, JobStatus, ProcessingJobCreate, ProcessingJobUpdate

logger = logging.getLogger(__name__)

class JobPersistenceService:
    """
    Manages job lifecycle and result persistence across all processing types.
    
    Key Features:
    - Unified job tracking across media, AI, and other processing types
    - Idempotent operations (safe to call multiple times)
    - Progress tracking and error handling
    - Result storage and retrieval
    - Job coordination for multi-step workflows
    """
    
    def __init__(self, connection: asyncpg.Connection):
        self.conn = connection
    
    async def generate_job_id(self, job_type: str, item_id: Optional[UUID] = None) -> str:
        """
        Generate a unique job ID for tracking.
        
        Format: {job_type}_{timestamp}_{uuid_short}
        Example: media_image_20250713_abc123
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uuid_short = str(uuid.uuid4())[:8]
        
        if item_id:
            return f"{job_type}_{timestamp}_{item_id}_{uuid_short}"
        else:
            return f"{job_type}_{timestamp}_{uuid_short}"
    
    async def create_job(
        self,
        job_type: str,
        input_data: Dict[str, Any],
        item_id: Optional[UUID] = None,
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a new processing job entry.
        
        Args:
            job_type: Type of job (media_image, media_video, etc.)
            input_data: Original input parameters
            item_id: Associated item ID (optional)
            job_id: Custom job ID (generated if not provided)
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            job_id: The unique job identifier
        """
        if not job_id:
            job_id = await self.generate_job_id(job_type, item_id)
        
        try:
            query = """
                INSERT INTO processing_jobs (
                    job_id, job_type, item_id, input_data, metadata, tags, status
                ) VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                ON CONFLICT (job_id) 
                DO UPDATE SET 
                    input_data = EXCLUDED.input_data,
                    metadata = EXCLUDED.metadata,
                    tags = EXCLUDED.tags,
                    last_updated = NOW()
                RETURNING job_id
            """
            
            result = await self.conn.fetchrow(
                query,
                job_id,
                job_type,
                item_id,
                json.dumps(input_data),
                json.dumps(metadata or {}),
                tags or []
            )
            
            logger.info(f"Created job: {job_id} (type: {job_type})")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job {job_id}: {e}")
            raise
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress_percentage: Optional[int] = None,
        current_stage: Optional[str] = None,
        stage_message: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update job status and progress.
        
        Args:
            job_id: Job identifier
            status: New status (pending, processing, completed, failed, etc.)
            progress_percentage: Progress (0-100)
            current_stage: Current processing stage
            stage_message: Human-readable stage description
            error_message: Error message if failed
            error_details: Detailed error information
            
        Returns:
            bool: True if job was updated, False if not found
        """
        try:
            # Build dynamic query based on provided parameters
            set_clauses = ["status = $2", "last_updated = NOW()"]
            params = [job_id, status]
            param_count = 2
            
            if progress_percentage is not None:
                param_count += 1
                set_clauses.append(f"progress_percentage = ${param_count}")
                params.append(progress_percentage)
            
            if current_stage is not None:
                param_count += 1
                set_clauses.append(f"current_stage = ${param_count}")
                params.append(current_stage)
            
            if stage_message is not None:
                param_count += 1
                set_clauses.append(f"stage_message = ${param_count}")
                params.append(stage_message)
            
            if error_message is not None:
                param_count += 1
                set_clauses.append(f"error_message = ${param_count}")
                params.append(error_message)
            
            if error_details is not None:
                param_count += 1
                set_clauses.append(f"error_details = ${param_count}")
                params.append(json.dumps(error_details))
            
            query = f"""
                UPDATE processing_jobs 
                SET {', '.join(set_clauses)}
                WHERE job_id = $1
                RETURNING job_id
            """
            
            result = await self.conn.fetchrow(query, *params)
            
            if result:
                logger.info(f"Updated job {job_id}: status={status}, progress={progress_percentage}%")
                return True
            else:
                logger.warning(f"Job {job_id} not found for status update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def save_job_result(
        self,
        job_id: str,
        result_data: Dict[str, Any],
        status: str = "completed"
    ) -> bool:
        """
        Save job results and mark as completed.
        
        Args:
            job_id: Job identifier
            result_data: Processing results
            status: Final status (completed or failed)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            query = """
                UPDATE processing_jobs 
                SET 
                    result_data = $2,
                    status = $3,
                    progress_percentage = 100,
                    last_updated = NOW()
                WHERE job_id = $1
                RETURNING job_id
            """
            
            result = await self.conn.fetchrow(
                query,
                job_id,
                json.dumps(result_data),
                status
            )
            
            if result:
                logger.info(f"Saved results for job {job_id} with status {status}")
                return True
            else:
                logger.warning(f"Job {job_id} not found for result save")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save results for job {job_id}: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current job status and details.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict with job details or None if not found
        """
        try:
            query = """
                SELECT 
                    job_id,
                    job_type,
                    status,
                    item_id,
                    input_data,
                    result_data,
                    progress_percentage,
                    current_stage,
                    stage_message,
                    error_message,
                    error_details,
                    retry_count,
                    created_at,
                    started_at,
                    completed_at,
                    last_updated,
                    metadata,
                    tags
                FROM processing_jobs 
                WHERE job_id = $1
            """
            
            result = await self.conn.fetchrow(query, job_id)
            
            if result:
                # Convert to dict and parse JSON fields
                job_data = dict(result)
                job_data['input_data'] = json.loads(job_data['input_data']) if job_data['input_data'] else {}
                job_data['result_data'] = json.loads(job_data['result_data']) if job_data['result_data'] else {}
                job_data['metadata'] = json.loads(job_data['metadata']) if job_data['metadata'] else {}
                job_data['error_details'] = json.loads(job_data['error_details']) if job_data['error_details'] else {}
                
                return job_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            raise
    
    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job results (convenience method).
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict with result data or None if not found/incomplete
        """
        job_status = await self.get_job_status(job_id)
        
        if job_status and job_status['status'] == 'completed':
            return job_status['result_data']
        else:
            return None
    
    async def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        item_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering.
        
        Args:
            job_type: Filter by job type
            status: Filter by status
            item_id: Filter by associated item
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of job dictionaries
        """
        try:
            # Build dynamic WHERE clause
            where_clauses = []
            params = []
            param_count = 0
            
            if job_type:
                param_count += 1
                where_clauses.append(f"job_type = ${param_count}")
                params.append(job_type)
            
            if status:
                param_count += 1
                where_clauses.append(f"status = ${param_count}")
                params.append(status)
            
            if item_id:
                param_count += 1
                where_clauses.append(f"item_id = ${param_count}")
                params.append(item_id)
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            param_count += 1
            limit_param = f"${param_count}"
            params.append(limit)
            
            param_count += 1
            offset_param = f"${param_count}"
            params.append(offset)
            
            query = f"""
                SELECT 
                    job_id, job_type, status, item_id, progress_percentage,
                    current_stage, stage_message, error_message,
                    created_at, started_at, completed_at, last_updated,
                    tags
                FROM processing_jobs 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """
            
            results = await self.conn.fetch(query, *params)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise
    
    async def retry_job(self, job_id: str) -> bool:
        """
        Mark a failed job for retry.
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if job was marked for retry
        """
        try:
            query = """
                UPDATE processing_jobs 
                SET 
                    status = 'pending',
                    retry_count = retry_count + 1,
                    error_message = NULL,
                    error_details = '{}',
                    progress_percentage = 0,
                    current_stage = NULL,
                    stage_message = NULL,
                    last_updated = NOW()
                WHERE job_id = $1 
                AND status = 'failed'
                AND retry_count < max_retries
                RETURNING job_id
            """
            
            result = await self.conn.fetchrow(query, job_id)
            
            if result:
                logger.info(f"Marked job {job_id} for retry")
                return True
            else:
                logger.warning(f"Job {job_id} cannot be retried (not failed or max retries exceeded)")
                return False
                
        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {e}")
            raise
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or processing job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if job was cancelled
        """
        try:
            query = """
                UPDATE processing_jobs 
                SET 
                    status = 'cancelled',
                    last_updated = NOW()
                WHERE job_id = $1 
                AND status IN ('pending', 'processing')
                RETURNING job_id
            """
            
            result = await self.conn.fetchrow(query, job_id)
            
            if result:
                logger.info(f"Cancelled job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} cannot be cancelled (not pending/processing)")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            raise
    
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """
        Clean up old completed/failed jobs.
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            int: Number of jobs deleted
        """
        try:
            query = """
                DELETE FROM processing_jobs 
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND completed_at < NOW() - INTERVAL '%s days'
            """
            
            result = await self.conn.execute(query, days_old)
            deleted_count = result.split()[-1]  # Extract count from "DELETE {count}"
            
            logger.info(f"Cleaned up {deleted_count} old jobs (older than {days_old} days)")
            return int(deleted_count)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            raise


# Note: JobPersistenceService requires a database connection
# Use get_job_persistence_service() function to get an instance with connection