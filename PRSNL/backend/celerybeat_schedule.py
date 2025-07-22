#!/usr/bin/env python3
"""
Celery Beat Schedule Configuration
Defines periodic tasks for the PRSNL system
"""
from celery.schedules import crontab
from datetime import timedelta

# Celery Beat Schedule
beat_schedule = {
    # Clean up old processed items every day at 2 AM
    'cleanup-old-items': {
        'task': 'app.tasks_simple.cleanup_old_items',
        'schedule': crontab(hour=2, minute=0),
        'options': {'expires': 300}  # Expire after 5 minutes if not run
    },
    
    # Update search vectors every 6 hours
    'update-search-vectors': {
        'task': 'app.tasks_simple.update_search_vectors',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {'expires': 1800}  # Expire after 30 minutes
    },
    
    # Generate weekly analytics report every Monday at 9 AM
    'weekly-analytics': {
        'task': 'app.tasks_simple.generate_weekly_analytics',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
        'options': {'expires': 3600}  # Expire after 1 hour
    },
    
    # Health check every 5 minutes
    'health-check': {
        'task': 'app.tasks_simple.health_check',
        'schedule': timedelta(minutes=5),
        'options': {'expires': 60}  # Expire after 1 minute
    },
    
    # Reprocess failed items every hour
    'retry-failed-items': {
        'task': 'app.tasks_simple.retry_failed_items',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'expires': 300}
    },
    
    # Optimize database performance every Sunday at 3 AM
    'optimize-database': {
        'task': 'app.tasks_simple.optimize_database',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'options': {'expires': 7200}  # Expire after 2 hours
    },
    
    # Update smart scraper stats every 15 minutes
    'scraper-stats': {
        'task': 'app.tasks_simple.log_scraper_stats',
        'schedule': timedelta(minutes=15),
        'options': {'expires': 60}
    }
}

# Celery Beat Configuration
CELERYBEAT_SCHEDULE = beat_schedule

# Time zone for scheduling
CELERY_TIMEZONE = 'UTC'

# Beat scheduler backend
CELERYBEAT_SCHEDULER = 'celery.beat:PersistentScheduler'