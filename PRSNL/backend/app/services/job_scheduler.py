import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable, Dict, Any
from uuid import UUID

from app.core.websocket_manager import manager
from app.models.schemas import ProcessingProgressUpdate

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.embedding_queue = asyncio.Queue() # Priority queue for embeddings
        self.running_jobs = {}

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started.")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler shut down.")

    async def send_progress_update(self, item_id: UUID, stage: str, progress: float, message: str, is_complete: bool = False):
        update = ProcessingProgressUpdate(
            item_id=item_id,
            stage=stage,
            progress=progress,
            message=message,
            is_complete=is_complete
        )
        # Broadcast to all connected clients for now, can be refined to specific clients later
        await manager.broadcast(update.model_dump_json())

    async def add_embedding_job(self, item_id: UUID, priority: int = 5):
        """
        Adds an embedding generation job to the priority queue.
        Higher priority (e.g., 1) means it gets processed sooner.
        """
        await self.embedding_queue.put((priority, item_id)) # Store as (priority, item_id)
        logger.info(f"Added embedding job for item {item_id} with priority {priority}.")
        await self.send_progress_update(item_id, "queued", 0.0, "Item added to processing queue.")

    async def process_embedding_queue(self):
        """
        Processes embedding jobs from the priority queue.
        This method should be run as a background task.
        """
        while True:
            try:
                priority, item_id = await self.embedding_queue.get() # Get job from queue
                logger.info(f"Processing embedding job for item {item_id} (Priority: {priority})...")
                await self.send_progress_update(item_id, "processing", 0.1, "Starting embedding generation.")
                
                # Implement actual embedding generation logic
                try:
                    # Get database session
                    from app.db.database import get_db
                    from app.services.embedding_service import EmbeddingService
                    
                    async for db in get_db():
                        # Fetch item content
                        result = await db.execute(
                            "SELECT title, summary, processed_content FROM items WHERE id = $1",
                            item_id
                        )
                        item = result.fetchone()
                        
                        if not item:
                            raise ValueError(f"Item {item_id} not found")
                        
                        await self.send_progress_update(item_id, "processing", 0.3, "Fetching item content...")
                        
                        # Prepare content for embedding
                        content_parts = []
                        if item.title:
                            content_parts.append(f"Title: {item.title}")
                        if item.summary:
                            content_parts.append(f"Summary: {item.summary}")
                        if item.processed_content:
                            content_parts.append(f"Content: {item.processed_content[:5000]}")  # Limit content length
                        
                        content_text = "\n".join(content_parts)
                        
                        await self.send_progress_update(item_id, "processing", 0.5, "Generating embeddings...")
                        
                        # Generate embedding
                        embedding_service = EmbeddingService()
                        embedding = await embedding_service.generate_embedding(content_text)
                        
                        await self.send_progress_update(item_id, "processing", 0.8, "Saving embeddings to database...")
                        
                        # Update database with embedding
                        await db.execute(
                            "UPDATE items SET embedding = $1 WHERE id = $2",
                            embedding,
                            item_id
                        )
                        await db.commit()
                        
                        break  # Exit the async generator
                        
                except Exception as e:
                    logger.error(f"Error generating embedding for item {item_id}: {e}")
                    raise

                logger.info(f"Finished embedding job for item {item_id}.")
                await self.send_progress_update(item_id, "completed", 1.0, "Embedding generation completed.", is_complete=True)
                self.embedding_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Embedding queue processing cancelled.")
                break
            except Exception as e:
                logger.error(f"Error processing embedding job for item {item_id}: {e}")
                await self.send_progress_update(item_id, "failed", 0.0, f"Embedding generation failed: {e}", is_complete=True)
                # Depending on error, might re-queue or log for manual intervention

    def schedule_analytics_job(self, job_id: str, func: Callable, interval_seconds: int, **kwargs):
        """
        Schedules a recurring analytics job.
        """
        if job_id in self.running_jobs:
            logger.warning(f"Job {job_id} already scheduled. Skipping.")
            return

        self.scheduler.add_job(
            func,
            IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            name=job_id,
            args=kwargs.get('args', []),
            kwargs=kwargs.get('kwargs', {})
        )
        self.running_jobs[job_id] = True
        logger.info(f"Scheduled analytics job '{job_id}' to run every {interval_seconds} seconds.")

    def remove_job(self, job_id: str):
        """
        Removes a scheduled job.
        """
        if job_id in self.running_jobs:
            self.scheduler.remove_job(job_id)
            del self.running_jobs[job_id]
            logger.info(f"Removed job '{job_id}'.")
        else:
            logger.warning(f"Job '{job_id}' not found.")

# Global scheduler instance
job_scheduler = JobScheduler()
