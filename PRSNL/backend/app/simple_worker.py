import asyncio
import json
import logging
from uuid import UUID

import asyncpg
import os
from dotenv import load_dotenv

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
        
        # Get item details
        row = await connection.fetchrow("""
            SELECT id, url, title, status
            FROM items WHERE id = $1::uuid
        """, str(item_id))
        
        if row and row['status'] == 'pending':
            logger.info(f"Processing item: {row['title']}")
            
            # For now, just update status and add some dummy content
            await connection.execute("""
                UPDATE items 
                SET 
                    status = 'processed',
                    processed_content = $2,
                    updated_at = NOW()
                WHERE id = $1::uuid
            """, str(item_id), f"Processed content for: {row['title']}")
            
            logger.info(f"✓ Item {item_id} marked as processed")
            
            # TODO: In the real system, this would:
            # 1. Use capture engine to fetch content
            # 2. Generate embeddings
            # 3. Update search vectors
            # 4. etc.
        else:
            logger.info(f"Item {item_id} not found or already processed")
            
    except Exception as e:
        logger.error(f"Error handling notification: {e}")

if __name__ == "__main__":
    asyncio.run(listen_for_notifications())