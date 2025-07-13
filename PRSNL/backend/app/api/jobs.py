from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import InternalServerError
from app.models.schemas import Job, JobCancelResponse, JobQueueStatus, JobStatus
from app.services.job_scheduler import job_scheduler

router = APIRouter()

@router.get("/jobs/queue/status", response_model=JobQueueStatus)
async def get_job_queue_status():
    """
    Retrieves the current status of the job queues and scheduled jobs.
    """
    try:
        queue_size = job_scheduler.embedding_queue.qsize()
        scheduled_jobs = []
        for job in job_scheduler.scheduler.get_jobs():
            scheduled_jobs.append(Job(
                id=UUID(job.id),
                type=job.name, # Using job name as type for simplicity
                status=JobStatus.PENDING, # APScheduler jobs don't have a direct 'status' like our JobStatus enum
                created_at=job.next_run_time, # Approximation
                metadata={"trigger": str(job.trigger), "executor": job.executor}
            ))

        # For now, we'll just report on the embedding queue
        # In a real system, you'd track more detailed job states
        return JobQueueStatus(
            total_jobs=queue_size + len(scheduled_jobs),
            pending_jobs=queue_size,
            in_progress_jobs=0, # Not directly tracked here yet
            completed_jobs=0, # Not directly tracked here yet
            failed_jobs=0, # Not directly tracked here yet
            jobs=scheduled_jobs # Only scheduled jobs for now
        )
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve job queue status: {e}")

@router.post("/jobs/embedding/add")
async def add_embedding_job(item_id: UUID, priority: int = 5):
    """
    Adds an item to the embedding generation queue.
    """
    try:
        await job_scheduler.add_embedding_job(item_id, priority)
        return {"message": f"Embedding job for item {item_id} added to queue with priority {priority}."}
    except Exception as e:
        raise InternalServerError(f"Failed to add embedding job: {e}")

@router.post("/jobs/schedule_analytics")
async def schedule_analytics_job(job_id: str, interval_seconds: int = 3600):
    """
    Schedules a recurring analytics job.
    """
    try:
        # Example: schedule a dummy analytics job
        def dummy_analytics_task():
            print(f"Running scheduled analytics task: {job_id}")
            # In a real scenario, this would call analytics_service methods

        job_scheduler.schedule_analytics_job(job_id, dummy_analytics_task, interval_seconds)
        return {"message": f"Analytics job {job_id} scheduled to run every {interval_seconds} seconds."}
    except Exception as e:
        raise InternalServerError(f"Failed to schedule analytics job: {e}")

@router.delete("/jobs/{job_id}", response_model=JobCancelResponse)
async def cancel_job(job_id: UUID):
    """
    Cancels a job by its ID. This currently only supports cancelling scheduled APScheduler jobs.
    For queue jobs, a more complex mechanism would be needed.
    """
    try:
        job_scheduler.remove_job(str(job_id)) # APScheduler uses string IDs
        return JobCancelResponse(message=f"Job {job_id} cancelled successfully.", job_id=job_id, status=JobStatus.CANCELLED)
    except Exception as e:
        raise InternalServerError(f"Failed to cancel job {job_id}: {e}")
