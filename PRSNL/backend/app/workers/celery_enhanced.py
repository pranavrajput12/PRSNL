"""
Enhanced Celery Configuration with 5.5.3 Task Priorities
Implements priority queues and advanced task routing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import wraps

from celery import Celery, Task, group, chain, chord
from celery.signals import (
    task_prerun, task_postrun, task_failure, task_retry,
    worker_ready, worker_shutting_down
)
from kombu import Exchange, Queue
from celery.app.task import Task as BaseTask

from app.config import settings
from app.services.performance_monitoring import track_custom_metric

logger = logging.getLogger(__name__)


# Priority levels for tasks
class TaskPriority:
    CRITICAL = 10  # Highest priority
    HIGH = 7
    NORMAL = 5
    LOW = 3
    BACKGROUND = 1  # Lowest priority


# Define exchanges and queues with priority support
default_exchange = Exchange("default", type="direct")
priority_exchange = Exchange("priority", type="topic")

# Priority queues configuration
CELERY_QUEUES = [
    # Critical priority queue for urgent tasks
    Queue(
        "critical",
        exchange=priority_exchange,
        routing_key="priority.critical",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 300000  # 5 minutes TTL
        }
    ),
    # High priority queue for important tasks
    Queue(
        "high",
        exchange=priority_exchange,
        routing_key="priority.high",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 600000  # 10 minutes TTL
        }
    ),
    # Normal priority queue (default)
    Queue(
        "normal",
        exchange=default_exchange,
        routing_key="normal",
        queue_arguments={
            "x-max-priority": 10
        }
    ),
    # Low priority queue for background tasks
    Queue(
        "low",
        exchange=priority_exchange,
        routing_key="priority.low",
        queue_arguments={
            "x-max-priority": 10
        }
    ),
    # Specialized queues for different task types
    Queue("ai_processing", exchange=default_exchange, routing_key="ai"),
    Queue("document_processing", exchange=default_exchange, routing_key="document"),
    Queue("analytics", exchange=default_exchange, routing_key="analytics"),
]


class PriorityTask(BaseTask):
    """Base task class with priority support"""
    
    # Default priority
    priority = TaskPriority.NORMAL
    
    # Rate limiting
    rate_limit = None
    
    # Retry configuration
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def apply_async(self, args=None, kwargs=None, **options):
        """Override to add priority to task options"""
        # Set priority if not explicitly provided
        if "priority" not in options:
            options["priority"] = self.priority
        
        # Route to appropriate queue based on priority
        if "queue" not in options:
            if options["priority"] >= TaskPriority.CRITICAL:
                options["queue"] = "critical"
            elif options["priority"] >= TaskPriority.HIGH:
                options["queue"] = "high"
            elif options["priority"] <= TaskPriority.LOW:
                options["queue"] = "low"
            else:
                options["queue"] = "normal"
        
        return super().apply_async(args, kwargs, **options)


def create_enhanced_celery_app() -> Celery:
    """Create Celery app with enhanced configuration"""
    
    app = Celery(
        "prsnl_enhanced",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        task_cls=PriorityTask  # Use priority-aware task class
    )
    
    # Enhanced configuration
    app.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Queue configuration
        task_queues=CELERY_QUEUES,
        task_default_queue="normal",
        task_default_exchange="default",
        task_default_routing_key="normal",
        
        # Priority queue settings
        worker_prefetch_multiplier=1,  # Disable prefetching for priority to work
        task_acks_late=True,  # Acknowledge tasks after completion
        task_reject_on_worker_lost=True,
        
        # Task routing based on priority and type
        task_routes={
            # AI tasks go to specialized queue
            "*.ai_*": {"queue": "ai_processing"},
            "*.analyze_*": {"queue": "ai_processing"},
            
            # Document processing tasks
            "*.process_document*": {"queue": "document_processing"},
            "*.extract_*": {"queue": "document_processing"},
            
            # Analytics tasks
            "*.generate_report*": {"queue": "analytics"},
            "*.calculate_metrics*": {"queue": "analytics"},
        },
        
        # Result backend settings
        result_expires=3600,  # Results expire after 1 hour
        result_compression="gzip",  # Compress results
        
        # Worker settings
        worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
        worker_disable_rate_limits=False,
        
        # Task execution limits
        task_soft_time_limit=600,  # 10 minutes soft limit
        task_time_limit=900,  # 15 minutes hard limit
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
    
    return app


# Create the enhanced Celery instance
celery_app = create_enhanced_celery_app()


# Task decorators with priority support
def priority_task(
    priority: int = TaskPriority.NORMAL,
    rate_limit: Optional[str] = None,
    time_limit: Optional[int] = None,
    soft_time_limit: Optional[int] = None
):
    """
    Decorator for creating priority tasks
    
    Args:
        priority: Task priority (1-10, higher is more important)
        rate_limit: Rate limit string (e.g., "10/m" for 10 per minute)
        time_limit: Hard time limit in seconds
        soft_time_limit: Soft time limit in seconds
    """
    def decorator(func):
        @celery_app.task(
            base=PriorityTask,
            bind=True,
            priority=priority,
            rate_limit=rate_limit,
            time_limit=time_limit,
            soft_time_limit=soft_time_limit
        )
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Track task execution
            track_custom_metric(f"celery.task.{func.__name__}.started", 1)
            
            try:
                result = func(self, *args, **kwargs)
                track_custom_metric(f"celery.task.{func.__name__}.completed", 1)
                return result
            except Exception as e:
                track_custom_metric(f"celery.task.{func.__name__}.failed", 1)
                raise
        
        return wrapper
    return decorator


# Signal handlers for monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task start and track metrics"""
    logger.info(f"Task {task.name} [{task_id}] starting with priority {getattr(task, 'priority', 'unknown')}")
    track_custom_metric("celery.tasks.started", 1)


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, state=None, **kwargs):
    """Log task completion and track metrics"""
    logger.info(f"Task {task.name} [{task_id}] completed with state: {state}")
    track_custom_metric(f"celery.tasks.{state.lower()}", 1)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failures"""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")
    track_custom_metric("celery.tasks.failed", 1)


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **kwargs):
    """Log task retries"""
    logger.warning(f"Task {sender.name} [{task_id}] retrying: {reason}")
    track_custom_metric("celery.tasks.retried", 1)


# Example priority tasks
@priority_task(priority=TaskPriority.CRITICAL, rate_limit="100/m")
def process_urgent_document(self, document_id: str) -> Dict[str, Any]:
    """Process urgent documents with highest priority"""
    logger.info(f"Processing urgent document: {document_id}")
    # Implementation here
    return {"status": "processed", "document_id": document_id}


@priority_task(priority=TaskPriority.HIGH, soft_time_limit=300)
def analyze_complex_data(self, data_id: str) -> Dict[str, Any]:
    """Analyze complex data with high priority"""
    logger.info(f"Analyzing complex data: {data_id}")
    # Implementation here
    return {"status": "analyzed", "data_id": data_id}


@priority_task(priority=TaskPriority.LOW, rate_limit="10/h")
def generate_periodic_report(self) -> Dict[str, Any]:
    """Generate reports with low priority"""
    logger.info("Generating periodic report")
    # Implementation here
    return {"status": "generated", "timestamp": datetime.utcnow().isoformat()}


# Task workflow helpers
def create_priority_workflow(tasks: list, priority: int = TaskPriority.NORMAL):
    """Create a workflow with consistent priority"""
    for task in tasks:
        task.apply_async(priority=priority)
    return group(tasks)


def create_priority_chain(tasks: list, priority: int = TaskPriority.NORMAL):
    """Create a chain of tasks with consistent priority"""
    for task in tasks:
        task.apply_async(priority=priority)
    return chain(tasks)


# Worker command with priority queue support
def start_priority_worker(queues: list = None, concurrency: int = 4):
    """
    Start a Celery worker with priority queue support
    
    Usage:
        # High priority worker
        start_priority_worker(['critical', 'high'], concurrency=8)
        
        # Normal worker
        start_priority_worker(['normal'], concurrency=4)
        
        # Background worker
        start_priority_worker(['low'], concurrency=2)
    """
    if queues is None:
        queues = ['critical', 'high', 'normal', 'low']
    
    worker = celery_app.Worker(
        queues=queues,
        concurrency=concurrency,
        loglevel="INFO",
        optimization="fair"  # Fair scheduling for priority queues
    )
    worker.start()


# Export the enhanced app
__all__ = [
    'celery_app',
    'TaskPriority',
    'priority_task',
    'create_priority_workflow',
    'create_priority_chain',
    'start_priority_worker'
]