import asyncio
import json
import logging
from uuid import UUID

import asyncpg

from app.core.capture_engine import CaptureEngine
from app.db.database import get_db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def listen_for_notifications(db_url: str):
    """
    Connects to PostgreSQL and listens for 'item_created' notifications.
    """
    conn = None
    try:
        conn = await asyncpg.connect(db_url)
        await conn.add_listener('item_created', handle_notification)
        logger.info("Listening for 'item_created' notifications...")
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
        capture_engine = CaptureEngine()
        
        # Get item details from database to process
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Add debug logging to see what database worker connects to
            logger.info(f"🔍 WORKER: Processing item {item_id}")
            try:
                # Test if the columns exist first
                test_columns = await conn.fetch("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'items' 
                    AND column_name IN ('content_type', 'enable_summarization')
                """)
                logger.info(f"🔍 WORKER: Available columns: {[r['column_name'] for r in test_columns]}")
                
                row = await conn.fetchrow("""
                    SELECT url, processed_content, raw_content, enable_summarization, content_type, status
                    FROM items WHERE id = $1
                """, item_id)
            except Exception as e:
                logger.error(f"🔍 WORKER ERROR: {e}")
                raise
            if row:
                # Only process if not already completed or failed
                if row['status'] in ['pending']:
                    url = row['url']
                    # Use raw_content (from form) if available, otherwise use processed_content
                    content = row['raw_content'] or row['processed_content']
                    enable_summarization = row['enable_summarization'] or False
                    content_type = row['content_type'] or 'auto'
                    
                    # Process item in background with all parameters
                    asyncio.create_task(capture_engine.process_item(
                        item_id, url, content, enable_summarization, content_type
                    ))
                else:
                    logger.info(f"Item {item_id} already processed (status: {row['status']})")
            else:
                logger.error(f"Item not found: {item_id}")
        
    except ValueError as e:
        logger.error(f"Invalid UUID payload: {payload} - {e}")
    except Exception as e:
        logger.error(f"Error handling notification: {e}")

# Example usage (for testing worker.py directly)
if __name__ == "__main__":
    # This should ideally come from environment variables or a config file
    # For local testing, ensure your DB is running and accessible
    DB_URL = "postgresql://user:password@localhost:5432/prsnl"
    asyncio.run(listen_for_notifications(DB_URL))
