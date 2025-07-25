#!/usr/bin/env python3
"""
Celery Tasks for PRSNL System
Scheduled tasks for maintenance, analytics, and optimization
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from celery import Celery
from celery.utils.log import get_task_logger

from app.config import settings
import asyncpg
import os
from app.services.smart_scraper import smart_scraper
from app.services.embedding_manager import EmbeddingManager

logger = get_task_logger(__name__)

# Initialize Celery app
celery_app = Celery('prsnl_tasks')
celery_app.config_from_object('app.celery_config')

@celery_app.task(bind=True, max_retries=3)
async def cleanup_old_items(self):
    """Clean up old processed items older than 30 days"""
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = await asyncpg.connect(db_url)
        
        # Delete items older than 30 days with status 'processed'
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        result = conn.execute("""
            DELETE FROM items 
            WHERE status = 'processed' 
            AND updated_at < %s
            RETURNING id
        """, (cutoff_date,))
        
        deleted_count = len(result.fetchall())
        logger.info(f"Cleaned up {deleted_count} old items")
        
        await conn.close()
        
        return {"deleted_items": deleted_count, "cutoff_date": cutoff_date.isoformat()}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        self.retry(countdown=60 * 5)  # Retry after 5 minutes

@celery_app.task(bind=True, max_retries=2)
def update_search_vectors(self):
    """Update search vectors for items without embeddings"""
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = await asyncpg.connect(db_url)
        
        # Find items without embeddings
        result = conn.execute("""
            SELECT id, processed_content
            FROM items 
            WHERE embedding IS NULL 
            AND processed_content IS NOT NULL
            AND status = 'processed'
            LIMIT 50
        """)
        
        items = result.fetchall()
        embedding_manager = EmbeddingManager()
        updated_count = 0
        
        for item in items:
            try:
                # Generate embedding asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                embedding = loop.run_until_complete(
                    embedding_manager.generate_embedding(item['processed_content'])
                )
                
                # Update item with embedding
                await conn.execute("""
                    UPDATE items 
                    SET embedding = %s, updated_at = NOW()
                    WHERE id = %s
                """, (embedding, item['id']))
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for item {item['id']}: {e}")
                continue
        
        await conn.close()
        
        logger.info(f"Updated {updated_count} search vectors")
        return {"updated_vectors": updated_count}
        
    except Exception as e:
        logger.error(f"Update search vectors task failed: {e}")
        self.retry(countdown=60 * 10)  # Retry after 10 minutes

@celery_app.task
def generate_weekly_analytics():
    """Generate weekly analytics report"""
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = await asyncpg.connect(db_url)
        
        # Get stats for the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        stats = {}
        
        # Items created this week
        result = conn.execute("""
            SELECT COUNT(*) as count, type
            FROM items 
            WHERE created_at >= %s
            GROUP BY type
        """, (week_ago,))
        
        stats['items_by_type'] = dict(result.fetchall())
        
        # Processing success rate
        result = conn.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'processed') as processed,
                COUNT(*) FILTER (WHERE status = 'error') as errors,
                COUNT(*) as total
            FROM items
            WHERE created_at >= %s
        """, (week_ago,))
        
        row = result.fetchone()
        stats['processing'] = {
            'total': row['total'],
            'processed': row['processed'],
            'errors': row['errors'],
            'success_rate': (row['processed'] / row['total'] * 100) if row['total'] > 0 else 0
        }
        
        # Smart scraper stats
        scraper_stats = smart_scraper.get_stats()
        stats['scraper'] = scraper_stats
        
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
            'embedding_service': False
        }
        
        # Check database
        try:
            db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
            conn = await asyncpg.connect(db_url)
            result = conn.execute("SELECT 1")
            if result.fetchone():
                health_status['database'] = True
            conn.close()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
        
        # Check scraper services
        try:
            if smart_scraper.firecrawl.enabled or smart_scraper.jina.enabled:
                health_status['scraper'] = True
        except Exception as e:
            logger.error(f"Scraper health check failed: {e}")
        
        # Check embedding service
        try:
            embedding_manager = EmbeddingManager()
            # Simple test - generate embedding for short text
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            test_embedding = loop.run_until_complete(
                embedding_manager.generate_embedding("health check test")
            )
            if test_embedding:
                health_status['embedding_service'] = True
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
        
        # Overall health
        health_status['overall_healthy'] = all([
            health_status['database'],
            health_status['scraper'],
            health_status['embedding_service']
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
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = await asyncpg.connect(db_url)
        
        # Get failed items from the last 24 hours
        day_ago = datetime.utcnow() - timedelta(hours=24)
        
        result = conn.execute("""
            SELECT id, url, type
            FROM items 
            WHERE status = 'error' 
            AND updated_at >= %s
            AND retry_count < 3
            LIMIT 10
        """, (day_ago,))
        
        failed_items = result.fetchall()
        retry_count = 0
        
        for item in failed_items:
            try:
                # Reset status to pending and increment retry count
                await conn.execute("""
                    UPDATE items 
                    SET status = 'pending', 
                        retry_count = COALESCE(retry_count, 0) + 1,
                        updated_at = NOW()
                    WHERE id = %s
                """, (item['id'],))
                
                # Trigger notification for reprocessing
                await conn.execute("NOTIFY item_created, %s", (item['id'],))
                
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Failed to retry item {item['id']}: {e}")
                continue
        
        await conn.close()
        
        logger.info(f"Queued {retry_count} failed items for retry")
        return {"retried_items": retry_count}
        
    except Exception as e:
        logger.error(f"Retry failed items task failed: {e}")
        self.retry(countdown=60 * 15)  # Retry after 15 minutes

@celery_app.task
def optimize_database():
    """Optimize database performance"""
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = await asyncpg.connect(db_url)
        
        optimization_results = []
        
        # Vacuum and analyze main tables
        # Use a whitelist of valid table names to prevent SQL injection
        valid_tables = {'items', 'embeddings', 'conversations', 'bookmarks', 'tags', 'item_tags'}
        tables_to_optimize = ['items', 'embeddings', 'conversations', 'bookmarks']
        
        for table in tables_to_optimize:
            if table not in valid_tables:
                logger.error(f"Invalid table name for optimization: {table}")
                optimization_results.append(f"Skipped invalid table: {table}")
                continue
                
            try:
                # Table name is validated against whitelist, safe to use in query
                await conn.execute(f"VACUUM ANALYZE {table}")
                optimization_results.append(f"Optimized table: {table}")
            except Exception as e:
                logger.error(f"Failed to optimize table {table}: {e}")
                optimization_results.append(f"Failed to optimize {table}: {str(e)}")
        
        # Clean up old conversation data (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        result = conn.execute("""
            DELETE FROM conversations 
            WHERE created_at < %s
            RETURNING id
        """, (cutoff_date,))
        
        deleted_conversations = len(result.fetchall())
        optimization_results.append(f"Deleted {deleted_conversations} old conversations")
        
        await conn.close()
        
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
            if stats['total_requests'] > 100:  # Reset after significant usage
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