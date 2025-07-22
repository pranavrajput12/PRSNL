#!/usr/bin/env python3
"""
Start Celery Beat for PRSNL System
Runs scheduled tasks defined in celerybeat_schedule.py
"""
import os
import sys
import logging
from celery import Celery
from celery.bin import beat

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_celery_beat():
    """Start Celery Beat scheduler"""
    
    # Create Celery app
    app = Celery('prsnl_beat')
    
    # Load configuration
    app.config_from_object('app.celery_config')
    
    # Import tasks to register them
    app.autodiscover_tasks(['app'])
    
    logger.info("🕰️ Starting Celery Beat scheduler...")
    logger.info("📋 Scheduled tasks:")
    
    # Log scheduled tasks
    schedule = app.conf.beat_schedule
    for task_name, config in schedule.items():
        schedule_info = config['schedule']
        if hasattr(schedule_info, 'human_readable'):
            schedule_str = schedule_info.human_readable
        else:
            schedule_str = str(schedule_info)
        logger.info(f"  - {task_name}: {schedule_str}")
    
    # Create beat application
    beat_app = beat.beat(app=app)
    
    # Beat options
    options = {
        'loglevel': 'INFO',
        'logfile': 'celery_beat.log',
        'pidfile': 'celery_beat.pid',
    }
    
    try:
        logger.info("🚀 Celery Beat started successfully!")
        beat_app.run(**options)
    except KeyboardInterrupt:
        logger.info("🛑 Celery Beat stopped by user")
    except Exception as e:
        logger.error(f"❌ Celery Beat error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_beat()