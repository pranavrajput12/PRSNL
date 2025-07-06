from typing import Callable, Coroutine, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class BackgroundTasks:
    """Manages background tasks for asynchronous processing."""

    def __init__(self):
        self._tasks = set()

    def add_task(self, task_func: Callable[..., Coroutine[Any, Any, None]], *args, **kwargs):
        """Adds a new coroutine task to be run in the background."""
        task = asyncio.create_task(self._run_task(task_func, *args, **kwargs))
        self._tasks.add(task)
        task.add_done_callback(self._remove_task)
        logger.info(f"Background task '{task_func.__name__}' added.")

    async def _run_task(self, task_func: Callable[..., Coroutine[Any, Any, None]], *args, **kwargs):
        """Executes the task function and handles exceptions."""
        try:
            await task_func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.warning(f"Background task '{task_func.__name__}' was cancelled.")
        except Exception as e:
            logger.error(f"Background task '{task_func.__name__}' failed: {e}", exc_info=True)

    def _remove_task(self, task: asyncio.Task):
        """Removes a completed task from the set."""
        self._tasks.discard(task)
        logger.info(f"Background task '{task.get_name()}' completed or was removed.")

    async def shutdown(self):
        """Cancels all running background tasks and waits for them to finish."""
        if not self._tasks:
            return

        logger.info(f"Shutting down {len(self._tasks)} background tasks...")
        for task in list(self._tasks): # Iterate over a copy to allow modification
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True) # Wait for tasks to finish, ignore exceptions
        logger.info("All background tasks shut down.")

background_tasks = BackgroundTasks()
