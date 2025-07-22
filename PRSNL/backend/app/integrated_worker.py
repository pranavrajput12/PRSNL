#!/usr/bin/env python3
"""
Integrated worker that handles all processing in one place
"""
import asyncio
import json
import logging
import os
from uuid import UUID
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

# Import services
from app.services.scraper import WebScraper
from app.services.unified_ai_service import UnifiedAIService
from app.services.embedding_manager import EmbeddingManager

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedWorker:
    def __init__(self):
        self.web_scraper = WebScraper()
        self.ai_service = UnifiedAIService()
        self.embedding_manager = None  # Will be initialized with DB connection
        
    async def listen_for_notifications(self):
        """
        Connects to PostgreSQL and listens for 'item_created' notifications.
        """
        db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
        conn = None
        try:
            conn = await asyncpg.connect(db_url)
            # Initialize embedding manager
            self.embedding_manager = EmbeddingManager()
            
            await conn.add_listener('item_created', lambda conn, pid, channel, payload: 
                                   asyncio.create_task(self.handle_notification(conn, pid, channel, payload)))
            logger.info("Integrated worker listening for 'item_created' notifications...")
            
            # Keep the worker alive
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in worker: {e}")
        finally:
            if conn:
                await conn.close()
                logger.info("Database connection closed.")

    async def handle_notification(self, connection, pid, channel, payload):
        """
        Handle incoming PostgreSQL notifications.
        """
        logger.info(f"Received notification on channel '{channel}': {payload}")
        try:
            item_id = UUID(payload)
            
            # Get item details
            row = await connection.fetchrow("""
                SELECT id, url, title, type, status, metadata, summary
                FROM items WHERE id = $1::uuid
            """, str(item_id))
            
            if row and row['status'] == 'pending':
                await self.process_item(connection, item_id, row)
            else:
                logger.info(f"Item {item_id} not found or already processed")
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}", exc_info=True)

    async def process_item(self, conn, item_id, row):
        """
        Process an item based on its type
        """
        try:
            logger.info(f"Processing item: {row['title']}")
            
            item_type = row['type']
            url = row['url']
            title = row['title']
            
            content = None
            
            # Fetch content based on type
            if item_type in ['website', 'article'] and url:
                logger.info(f"Fetching web content from: {url}")
                try:
                    # Use WebScraper
                    scraped_data = await self.web_scraper.scrape(url)
                    if scraped_data and scraped_data.content:
                        content = scraped_data.content
                        logger.info(f"Scraped {len(content)} characters from {url}")
                            
                except Exception as e:
                    logger.error(f"Error scraping URL: {e}")
                    
            elif item_type == 'pdf' and url:
                # TODO: Implement PDF processing
                logger.info(f"PDF processing not yet implemented for: {url}")
                content = f"PDF content placeholder for: {title}"
                
            elif item_type in ['video', 'youtube'] and url:
                # TODO: Implement video processing
                logger.info(f"Video processing not yet implemented for: {url}")
                content = f"Video content placeholder for: {title}"
                
            else:
                # For other types, use summary as content
                content = row.get('summary', f"Content for: {title}")
            
            if content:
                # Update item with content
                await conn.execute("""
                    UPDATE items 
                    SET 
                        status = 'processing',
                        processed_content = $2,
                        raw_content = $2,
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id), content[:100000])  # Limit to 100k chars
                
                logger.info(f"✓ Content saved for {item_id} ({len(content)} chars)")
                
                # Generate embedding
                try:
                    text_for_embedding = f"{title} {content[:2000]}"
                    embeddings = await self.ai_service.generate_embeddings([text_for_embedding])
                    
                    if embeddings and len(embeddings) > 0:
                        embedding = embeddings[0]
                        
                        # Convert to PostgreSQL format
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        # Store embedding
                        await conn.execute("""
                            UPDATE items 
                            SET embedding = $2::vector,
                                updated_at = NOW()
                            WHERE id = $1::uuid
                        """, str(item_id), embedding_str)
                        
                        # Also store in embeddings table
                        await conn.execute("""
                            INSERT INTO embeddings (
                                item_id, model_name, model_version, vector, embedding_type
                            ) VALUES ($1::uuid, $2, $3, $4::vector, $5)
                            ON CONFLICT (item_id, model_name, model_version, embedding_type) 
                            DO UPDATE SET vector = $4::vector, updated_at = NOW()
                        """, str(item_id), 'text-embedding-ada-002', 'v1', embedding_str, 'text')
                        
                        logger.info(f"✓ Embedding generated for {item_id}")
                        
                except Exception as e:
                    logger.error(f"Error generating embedding: {e}")
                
                # Update search vector
                await conn.execute("""
                    UPDATE items 
                    SET search_vector = to_tsvector('english', 
                        COALESCE(title, '') || ' ' || 
                        COALESCE(summary, '') || ' ' || 
                        COALESCE(processed_content, '') || ' ' ||
                        COALESCE(metadata->>'tags', '')
                    )
                    WHERE id = $1::uuid
                """, str(item_id))
                
                logger.info(f"✓ Search vector updated for {item_id}")
                
                # Mark as processed
                await conn.execute("""
                    UPDATE items 
                    SET 
                        status = 'processed',
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id))
                
                logger.info(f"✅ Item {item_id} fully processed!")
                
            else:
                # No content fetched
                await conn.execute("""
                    UPDATE items 
                    SET 
                        status = 'error',
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id))
                
                logger.warning(f"No content fetched for item {item_id}")
                
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}", exc_info=True)
            await conn.execute("""
                UPDATE items 
                SET 
                    status = 'error',
                    updated_at = NOW()
                WHERE id = $1::uuid
            """, str(item_id))

async def main():
    worker = IntegratedWorker()
    await worker.listen_for_notifications()

if __name__ == "__main__":
    asyncio.run(main())