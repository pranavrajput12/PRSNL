import asyncio
import json
import logging
import os
from uuid import UUID

import asyncpg
from dotenv import load_dotenv

# Import the actual services
from app.core.capture_engine import CaptureEngine
from app.services.embedding_manager import embedding_manager
from app.workers.celery_app import celery_app
from app.workers.ai_processing_tasks import analyze_content_task
from app.workers.media_processing_tasks import process_video_task

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def listen_for_notifications():
    """
    Connects to PostgreSQL and listens for 'item_created' notifications.
    """
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        await conn.add_listener('item_created', handle_notification)
        logger.info("Enhanced worker listening for 'item_created' notifications...")
        while True:
            await asyncio.sleep(1) # Keep the listener alive
    except Exception as e:
        logger.error(f"Error in worker: {e}")
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")

async def handle_notification(connection, pid, channel, payload):
    """
    Callback function to handle incoming PostgreSQL notifications.
    """
    logger.info(f"Received notification on channel '{channel}': {payload}")
    try:
        # Payload should be the item ID
        item_id = UUID(payload)
        
        # Get item details
        row = await connection.fetchrow("""
            SELECT id, url, title, type, status, metadata
            FROM items WHERE id = $1::uuid
        """, str(item_id))
        
        if row and row['status'] == 'pending':
            logger.info(f"Processing item: {row['title']}")
            
            # Determine the processing type
            item_type = row['type']
            url = row['url']
            
            if item_type in ['video', 'youtube'] and url:
                # Process video through Celery
                logger.info(f"Dispatching video processing task for: {url}")
                process_video_task.delay(str(item_id), url)
                
            elif item_type in ['website', 'article', 'pdf'] and url:
                # Use capture engine for web content
                logger.info(f"Fetching content for: {url}")
                capture_engine = CaptureEngine()
                
                # Process item directly with capture engine
                asyncio.create_task(capture_engine.process_item(
                    item_id, url, None, False, item_type
                ))
                
            else:
                # For other types, just mark as processed with basic content
                await connection.execute("""
                    UPDATE items 
                    SET 
                        status = 'processed',
                        processed_content = $2,
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id), f"Content for: {row['title']}")
                
                logger.info(f"✓ Item {item_id} processed with basic content")
        else:
            logger.info(f"Item {item_id} not found or already processed")
            
    except Exception as e:
        logger.error(f"Error handling notification: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(listen_for_notifications())