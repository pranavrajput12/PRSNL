#!/usr/bin/env python3
"""
Simple Celery Tasks for PRSNL System
Non-async version for compatibility
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery import Celery
from celery.utils.log import get_task_logger
import psycopg2
import os

from app.services.smart_scraper import smart_scraper

logger = get_task_logger(__name__)

# Initialize Celery app
celery_app = Celery('prsnl_tasks')
celery_app.config_from_object('app.celery_config')

def get_db_connection():
    """Get synchronous database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    # Convert asyncpg URL to psycopg2 format
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "")
        parts = db_url.split("/")
        if len(parts) >= 2:
            connection_part = parts[0]
            db_name = parts[1]
            if "@" in connection_part:
                user, host_port = connection_part.split("@")
                if ":" in host_port:
                    host, port = host_port.split(":")
                else:
                    host, port = host_port, "5432"
            else:
                user, host, port = "postgres", connection_part, "5432"
            
            return psycopg2.connect(
                host=host,
                port=port,
                user=user,
                database=db_name
            )
    
    # Fallback
    return psycopg2.connect(
        host="localhost",
        port="5432", 
        user="pronav",
        database="prsnl"
    )

@celery_app.task(bind=True, max_retries=3)
def cleanup_old_items(self):
    """Clean up old processed items older than 30 days"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete items older than 30 days with status 'processed'
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        cursor.execute("""
            DELETE FROM items 
            WHERE status = 'processed' 
            AND updated_at < %s
            RETURNING id
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        logger.info(f"Cleaned up {deleted_count} old items")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"deleted_items": deleted_count, "cutoff_date": cutoff_date.isoformat()}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        self.retry(countdown=60 * 5)  # Retry after 5 minutes

@celery_app.task(bind=True, max_retries=2)
def update_search_vectors(self):
    """Update search vectors for items without embeddings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find items without embeddings
        cursor.execute("""
            SELECT id, processed_content
            FROM items 
            WHERE embedding IS NULL 
            AND processed_content IS NOT NULL
            AND status = 'processed'
            LIMIT 10
        """)
        
        items = cursor.fetchall()
        updated_count = 0
        
        for item_id, content in items:
            try:
                # For now, just mark as having some processing
                cursor.execute("""
                    UPDATE items 
                    SET updated_at = NOW()
                    WHERE id = %s
                """, (item_id,))
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update item {item_id}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Updated {updated_count} items")
        return {"updated_items": updated_count}
        
    except Exception as e:
        logger.error(f"Update search vectors task failed: {e}")
        self.retry(countdown=60 * 10)  # Retry after 10 minutes

@celery_app.task
def generate_weekly_analytics():
    """Generate weekly analytics report"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get stats for the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        stats = {}
        
        # Items created this week
        cursor.execute("""
            SELECT COUNT(*) as count, type
            FROM items 
            WHERE created_at >= %s
            GROUP BY type
        """, (week_ago,))
        
        stats['items_by_type'] = dict(cursor.fetchall())
        
        # Processing success rate
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                COUNT(*) as total
            FROM items
            WHERE created_at >= %s
        """, (week_ago,))
        
        row = cursor.fetchone()
        stats['processing'] = {
            'total': row[2],
            'processed': row[0],
            'errors': row[1],
            'success_rate': (row[0] / row[2] * 100) if row[2] > 0 else 0
        }
        
        # Smart scraper stats
        scraper_stats = smart_scraper.get_stats()
        stats['scraper'] = scraper_stats
        
        cursor.close()
        conn.close()
        
        logger.info(f"Weekly analytics generated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Weekly analytics task failed: {e}")
        return {"error": str(e)}

@celery_app.task
def health_check():
    """System health check"""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': False,
            'scraper': False,
        }
        
        # Check database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            if cursor.fetchone():
                health_status['database'] = True
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
        
        # Check scraper services
        try:
            if smart_scraper.firecrawl.enabled or smart_scraper.jina.enabled:
                health_status['scraper'] = True
        except Exception as e:
            logger.error(f"Scraper health check failed: {e}")
        
        # Overall health
        health_status['overall_healthy'] = all([
            health_status['database'],
            health_status['scraper']
        ])
        
        if not health_status['overall_healthy']:
            logger.warning(f"System health issues detected: {health_status}")
        else:
            logger.info("System health check passed")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        return {"error": str(e), "overall_healthy": False}

@celery_app.task(bind=True, max_retries=3)
def retry_failed_items(self):
    """Retry processing failed items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get failed items from the last 24 hours
        day_ago = datetime.utcnow() - timedelta(hours=24)
        
        cursor.execute("""
            SELECT id, url, type
            FROM items 
            WHERE status = 'error' 
            AND updated_at >= %s
            AND COALESCE(CAST(metadata->>'retry_count' AS INTEGER), 0) < 3
            LIMIT 5
        """, (day_ago,))
        
        failed_items = cursor.fetchall()
        retry_count = 0
        
        for item_id, url, item_type in failed_items:
            try:
                # Reset status to pending and increment retry count
                cursor.execute("""
                    UPDATE items 
                    SET status = 'pending', 
                        metadata = COALESCE(metadata, '{}')::jsonb || '{"retry_count": 1}'::jsonb,
                        updated_at = NOW()
                    WHERE id = %s
                """, (item_id,))
                
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Failed to retry item {item_id}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Queued {retry_count} failed items for retry")
        return {"retried_items": retry_count}
        
    except Exception as e:
        logger.error(f"Retry failed items task failed: {e}")
        self.retry(countdown=60 * 15)  # Retry after 15 minutes

@celery_app.task
def optimize_database():
    """Optimize database performance"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        optimization_results = []
        
        # Vacuum and analyze main tables
        tables_to_optimize = ['items', 'conversations', 'bookmarks']
        
        for table in tables_to_optimize:
            try:
                cursor.execute(f"VACUUM ANALYZE {table}")
                optimization_results.append(f"Optimized table: {table}")
            except Exception as e:
                logger.error(f"Failed to optimize table {table}: {e}")
                optimization_results.append(f"Failed to optimize {table}: {str(e)}")
        
        # Clean up old conversation data (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        cursor.execute("""
            DELETE FROM conversations 
            WHERE created_at < %s
        """, (cutoff_date,))
        
        deleted_conversations = cursor.rowcount
        optimization_results.append(f"Deleted {deleted_conversations} old conversations")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Database optimization completed: {optimization_results}")
        return {"optimization_results": optimization_results}
        
    except Exception as e:
        logger.error(f"Database optimization task failed: {e}")
        return {"error": str(e)}

@celery_app.task
def log_scraper_stats():
    """Log smart scraper statistics"""
    try:
        stats = smart_scraper.get_stats()
        
        if stats['total_requests'] > 0:
            smart_scraper.log_stats()
            
            # Reset stats every 24 hours (daily stats)
            if stats['total_requests'] > 50:  # Reset after moderate usage
                # Store final stats
                logger.info(f"Daily scraper stats - Credits saved: {stats['credits_saved']}")
                
                # Reset counters for new day
                smart_scraper.stats = {
                    'jina_success': 0,
                    'jina_failure': 0,
                    'firecrawl_success': 0,
                    'firecrawl_failure': 0,
                    'total_requests': 0,
                    'credits_saved': 0
                }
        
        return stats
        
    except Exception as e:
        logger.error(f"Log scraper stats task failed: {e}")
        return {"error": str(e)}