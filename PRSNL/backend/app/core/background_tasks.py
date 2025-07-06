from typing import Callable, Coroutine, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class BackgroundTasks:
    def __init__(self):
        self._tasks = set()

    def add_task(self, task_func: Callable[..., Coroutine[Any, Any, None]], *args, **kwargs):
        """Adds a coroutine function as a background task."""
        task = asyncio.create_task(task_func(*args, **kwargs))
        self._tasks.add(task)
        task.add_done_callback(self._remove_task)
        logger.info(f"Background task '{task_func.__name__}' added.")

    def _remove_task(self, task: asyncio.Task):
        """Removes a task from the set when it's done."""
        self._tasks.discard(task)
        if task.exception():
            logger.error(f"Background task '{task.get_name()}' failed: {task.exception()}", exc_info=True)
        else:
            logger.info(f"Background task '{task.get_name()}' completed.")

    async def shutdown(self):
        """Cancels all running background tasks."""
        if not self._tasks:
            return
        
        logger.info(f"Shutting down {len(self._tasks)} background tasks...")
        for task in list(self._tasks): # Iterate over a copy as tasks will be removed
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("All background tasks shut down.")

background_tasks = BackgroundTasks()