#!/usr/bin/env python3
"""
Simple Celery Beat Starter for PRSNL System
"""
import os
import sys
import logging
from celery import Celery

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_celery_beat():
    """Start Celery Beat scheduler using command line"""
    
    logger.info("🕰️ Starting Celery Beat scheduler...")
    
    # Set environment variables
    os.environ.setdefault('CELERY_CONFIG_MODULE', 'app.celery_config')
    
    # Start Celery Beat using os.system (simpler approach)
    beat_command = (
        "celery -A app.tasks_simple.celery_app beat "
        "--loglevel=INFO "
        "--logfile=celery_beat.log "
        "--pidfile=celery_beat.pid"
    )
    
    logger.info(f"Running command: {beat_command}")
    
    try:
        os.system(beat_command)
    except KeyboardInterrupt:
        logger.info("🛑 Celery Beat stopped by user")
    except Exception as e:
        logger.error(f"❌ Celery Beat error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_beat()