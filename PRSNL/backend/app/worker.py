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
        
        # Use the existing connection to get item details
        # (the pool may not be initialized in this context)
        conn = connection
        
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
                FROM items WHERE id = $1::uuid
            """, str(item_id))
        except Exception as e:
            logger.error(f"🔍 WORKER ERROR: {e}")
            raise
            
        if row:
            # Only process if not already completed or failed
            if row['status'] in ['pending']:
                url = row['url']
                # Use raw_content (from form) if available, otherwise use processed_content
                content = row['raw_content'] or row['processed_content']
                enable_summarization = row.get('enable_summarization', False)
                content_type = row.get('content_type', 'auto')
                
                # Initialize database pool for CaptureEngine
                try:
                    from app.db.database import create_db_pool
                    await create_db_pool()
                    logger.info(f"🔗 Database pool initialized for worker")
                except Exception as pool_error:
                    logger.error(f"❌ Failed to initialize database pool: {pool_error}")
                    return
                
                # Create capture engine and process item
                capture_engine = CaptureEngine()
                # Process item directly
                try:
                    await capture_engine.process_item(
                        item_id=item_id,
                        url=url,
                        content=content,
                        enable_summarization=enable_summarization,
                        content_type=content_type
                    )
                    logger.info(f"✅ Successfully processed item {item_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to process item {item_id}: {e}")
                    # Update item status to failed
                    try:
                        await conn.execute('UPDATE items SET status = $1 WHERE id = $2', 'failed', item_id)
                    except Exception as update_error:
                        logger.error(f"Failed to update item status: {update_error}")
            else:
                logger.info(f"Item {item_id} already processed (status: {row['status']}")
        else:
            logger.error(f"Item not found: {item_id}")
        
    except ValueError as e:
        logger.error(f"Invalid UUID payload: {payload} - {e}")
    except Exception as e:
        logger.error(f"Error handling notification: {e}")

# Example usage (for testing worker.py directly)
if __name__ == "__main__":
    # Get DB URL from environment or use default
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    DB_URL = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    asyncio.run(listen_for_notifications(DB_URL))
