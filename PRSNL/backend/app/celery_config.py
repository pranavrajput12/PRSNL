#!/usr/bin/env python3
"""
Celery Configuration for PRSNL System
"""
import os
from celery.schedules import crontab
from datetime import timedelta

# Broker URL (Redis/DragonflyDB)
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

# Result backend
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Task serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

# Timezone
timezone = 'UTC'
enable_utc = True

# Task routing
task_routes = {
    'app.tasks_simple.cleanup_old_items': {'queue': 'maintenance'},
    'app.tasks_simple.update_search_vectors': {'queue': 'processing'},
    'app.tasks_simple.generate_weekly_analytics': {'queue': 'analytics'},
    'app.tasks_simple.health_check': {'queue': 'monitoring'},
    'app.tasks_simple.retry_failed_items': {'queue': 'processing'},
    'app.tasks_simple.optimize_database': {'queue': 'maintenance'},
    'app.tasks_simple.log_scraper_stats': {'queue': 'monitoring'}
}

# Worker configuration
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = False

# Task execution settings
task_soft_time_limit = 300  # 5 minutes
task_time_limit = 600  # 10 minutes
task_max_retries = 3
task_default_retry_delay = 60  # 1 minute

# Beat schedule (imported from celerybeat_schedule.py)
from celerybeat_schedule import CELERYBEAT_SCHEDULE
beat_schedule = CELERYBEAT_SCHEDULE
beat_scheduler = 'celery.beat:PersistentScheduler'

# Result expiration
result_expires = 3600  # 1 hour

# Concurrency
worker_concurrency = 4

# Monitoring
worker_send_task_events = True
task_send_sent_event = True

# Error handling
task_reject_on_worker_lost = True
task_ack_on_failure = True

# Queue configuration
task_default_queue = 'default'
task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
    'processing': {
        'exchange': 'processing',
        'routing_key': 'processing',
    },
    'analytics': {
        'exchange': 'analytics',
        'routing_key': 'analytics',
    },
    'monitoring': {
        'exchange': 'monitoring',
        'routing_key': 'monitoring',
    }
}

# Security
worker_hijack_root_logger = False
worker_log_color = False