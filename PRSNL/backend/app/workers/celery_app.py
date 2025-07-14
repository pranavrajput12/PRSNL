"""
Celery Application Configuration

Enterprise-grade distributed task queue using Celery with DragonflyDB backend.
Provides scalable, fault-tolerant processing for CodeMirror analysis tasks.
"""

import os
import logging
from typing import Dict, Any

from celery import Celery, Task
from celery.signals import worker_ready, task_prerun, task_postrun, task_failure
from kombu import Exchange, Queue

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Celery with DragonflyDB as broker and backend
celery_app = Celery(
    "prsnl_codemirror",
    broker=settings.CELERY_BROKER_URL,  # redis://localhost:6379/0
    backend=settings.CELERY_RESULT_BACKEND,  # redis://localhost:6379/0
    include=[
        "app.workers.codemirror_tasks",
        "app.workers.analysis_tasks",
        "app.workers.insight_tasks",
        "app.workers.package_intelligence_tasks",
        "app.workers.ai_processing_tasks",
        "app.workers.file_processing_tasks",
        "app.workers.media_processing_tasks",
        "app.workers.conversation_intelligence_tasks",
        "app.workers.knowledge_graph_tasks",
        "app.workers.agent_coordination_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing (Phase 2: Agent-specific routing)
    task_routes={
        "app.workers.codemirror_tasks.*": {"queue": "codemirror"},
        "app.workers.analysis_tasks.*": {"queue": "analysis"},
        "app.workers.insight_tasks.*": {"queue": "insights"},
        "app.workers.package_intelligence_tasks.*": {"queue": "packages"},
        "app.workers.ai_processing_tasks.*": {"queue": "ai_processing"},
        "app.workers.file_processing_tasks.*": {"queue": "file_processing"},
        "app.workers.media_processing_tasks.*": {"queue": "media_processing"},
        "app.workers.conversation_intelligence_tasks.*": {"queue": "conversation_intelligence"},
        "app.workers.knowledge_graph_tasks.*": {"queue": "knowledge_graph"},
        "app.workers.agent_coordination_tasks.*": {"queue": "agent_coordination"},
        # Phase 2: Agent-specific routing
        "conversation.technical_extraction": {"queue": "ai_analysis"},
        "conversation.learning_analysis": {"queue": "ai_analysis"},
        "conversation.insights_extraction": {"queue": "ai_analysis"},
        "conversation.gap_identification": {"queue": "ai_analysis"},
        "conversation.contextual_analysis": {"queue": "ai_analysis"},
        "conversation.pattern_recognition": {"queue": "ai_analysis"},
        "conversation.sentiment_progression": {"queue": "ai_analysis"},
        "conversation.topic_evolution": {"queue": "ai_analysis"},
        "conversation.synthesis": {"queue": "ai_synthesis"},
        # Knowledge graph routing
        "knowledge_graph.extract_relationships": {"queue": "ai_analysis"},
        "knowledge_graph.semantic_search": {"queue": "ai_analysis"},
        "knowledge_graph.entity_linking": {"queue": "ai_analysis"},
        "knowledge_graph.assemble_graph": {"queue": "ai_synthesis"},
        # Agent coordination routing
        "agent_coordination.advanced_content_analysis": {"queue": "ai_analysis"},
        "agent_coordination.advanced_pattern_detection": {"queue": "ai_analysis"},
        "agent_coordination.advanced_sentiment_analysis": {"queue": "ai_analysis"},
        "agent_coordination.advanced_entity_extraction": {"queue": "ai_analysis"},
        "agent_coordination.intelligent_synthesis": {"queue": "ai_synthesis"},
        "agent_coordination.decision_aggregation": {"queue": "ai_synthesis"},
        "agent_coordination.hierarchical_synthesis": {"queue": "ai_synthesis"},
    },
    
    # Queue configuration (Phase 2: Enhanced with agent-specific queues)
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("codemirror", Exchange("codemirror"), routing_key="codemirror", priority=5),
        Queue("analysis", Exchange("analysis"), routing_key="analysis", priority=3),
        Queue("insights", Exchange("insights"), routing_key="insights", priority=1),
        Queue("packages", Exchange("packages"), routing_key="packages", priority=4),
        # Phase 1 Critical Performance Queues
        Queue("ai_processing", Exchange("ai_processing"), routing_key="ai_processing", priority=8),
        Queue("file_processing", Exchange("file_processing"), routing_key="file_processing", priority=7),
        Queue("media_processing", Exchange("media_processing"), routing_key="media_processing", priority=6),
        # Phase 2 Agent-Specific Queues
        Queue("conversation_intelligence", Exchange("conversation_intelligence"), routing_key="conversation_intelligence", priority=7),
        Queue("knowledge_graph", Exchange("knowledge_graph"), routing_key="knowledge_graph", priority=6),
        Queue("agent_coordination", Exchange("agent_coordination"), routing_key="agent_coordination", priority=8),
        Queue("ai_analysis", Exchange("ai_analysis"), routing_key="ai_analysis", priority=8),
        Queue("ai_synthesis", Exchange("ai_synthesis"), routing_key="ai_synthesis", priority=9),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task execution limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    task_acks_late=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    result_compression="gzip",
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-analyses": {
            "task": "app.workers.codemirror_tasks.cleanup_old_analyses",
            "schedule": 3600.0,  # Every hour
        },
        "sync-pending-cli-results": {
            "task": "app.workers.codemirror_tasks.sync_pending_cli_results",
            "schedule": 300.0,  # Every 5 minutes
        },
        "generate-analysis-reports": {
            "task": "app.workers.analysis_tasks.generate_daily_reports",
            "schedule": 86400.0,  # Every 24 hours
        },
    },
    
    # Monitoring and metrics
    worker_send_task_events=True,
    task_send_sent_event=True,
)


class BaseTask(Task):
    """Base task with automatic retries and error handling."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(
            f"Task {self.name}[{task_id}] failed: {exc}",
            exc_info=True,
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
            }
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            f"Task {self.name}[{task_id}] retrying: {exc}",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "retry_count": self.request.retries,
            }
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(
            f"Task {self.name}[{task_id}] succeeded",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "duration": self.request.runtime,
            }
        )


# Set default task base
celery_app.Task = BaseTask


# Signal handlers for monitoring
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready event."""
    logger.info(f"Celery worker ready: {sender}")


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Handle task pre-run event."""
    logger.debug(
        f"Task starting: {task.name}[{task_id}]",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": args,
            "kwargs": kwargs,
        }
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kw):
    """Handle task post-run event."""
    logger.debug(
        f"Task completed: {task.name}[{task_id}] - State: {state}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "state": state,
            "runtime": getattr(task.request, "runtime", None),
        }
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, 
                        kwargs=None, traceback=None, einfo=None, **kw):
    """Handle task failure event."""
    logger.error(
        f"Task failed: {sender.name}[{task_id}] - {exception}",
        exc_info=True,
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "args": args,
            "kwargs": kwargs,
        }
    )


# Health check task
@celery_app.task(name="health_check")
def health_check():
    """Simple health check task."""
    return {"status": "healthy", "worker": celery_app.current_worker_task.request.hostname}


if __name__ == "__main__":
    # Start worker if run directly
    celery_app.start()