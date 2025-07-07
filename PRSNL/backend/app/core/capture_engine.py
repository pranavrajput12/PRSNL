"""Core capture engine for processing items"""
import asyncio
import time
import json
from uuid import UUID
from app.services.scraper import WebScraper
from app.services.llm_processor import LLMProcessor
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_pool, update_item_embedding
import logging

logger = logging.getLogger(__name__)


class CaptureEngine:
    """Handles the capture and processing of items"""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.llm_processor = LLMProcessor()
        self.embedding_service = EmbeddingService()
    
    async def process_item(self, item_id: UUID, url: str = None, content: str = None):
        """
        Process a captured item:
        1. Scrape content (if URL provided)
        2. Process with LLM
        3. Update database
        """
        try:
            pool = await get_db_pool()
            
            # If content is provided directly, use it; otherwise scrape the URL
            if content:
                logger.info(f"Using provided content for item {item_id}")
                scraped_data = type('ScrapedData', (), {
                    'content': content,
                    'title': 'User Note',
                    'html': content,
                    'author': None,
                    'published_date': None,
                    'scraped_at': None
                })()
            elif url:
                logger.info(f"Scraping URL: {url}")
                scraped_data = await self.scraper.scrape(url)
            else:
                raise ValueError("Either URL or content must be provided")
            
            if not scraped_data.content:
                logger.error(f"Failed to scrape content from {url}")
                async with pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE items 
                        SET status = 'failed', 
                            metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', '"Failed to scrape content"')
                        WHERE id = $1
                    """, item_id)
                return
            
            # Process with LLM
            logger.info(f"Processing content with LLM for item {item_id}")
            processed = await self.llm_processor.process(
                content=scraped_data.content,
                url=url,
                title=scraped_data.title
            )
            
            # Update the item in database
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE items 
                    SET 
                        title = $2,
                        summary = $3,
                        raw_content = $4,
                        processed_content = $5,
                        search_vector = to_tsvector('english', $2 || ' ' || COALESCE($3, '') || ' ' || COALESCE($5, '')),
                        metadata = $6::jsonb,
                        status = 'completed',
                        updated_at = NOW()
                    WHERE id = $1
                """, 
                    item_id,
                    processed.title or scraped_data.title,
                    processed.summary,
                    scraped_data.html,
                    processed.content,
                    json.dumps({
                        "author": scraped_data.author,
                        "published_date": scraped_data.published_date,
                        "word_count": len(processed.content.split()) if processed.content else 0,
                        "scraped_at": scraped_data.scraped_at.isoformat() if scraped_data.scraped_at else None,
                        "ai_analysis": {
                            "summary": processed.summary,
                            "tags": processed.tags,
                            "key_points": processed.key_points,
                            "sentiment": processed.sentiment,
                            "reading_time": processed.reading_time,
                            "entities": processed.entities,
                            "questions": processed.questions,
                            "processed_at": time.time()
                        }
                    })
                )
                
                # Add auto-generated tags
                if processed.tags:
                    for tag in processed.tags:
                        # Insert tag if not exists
                        await conn.execute("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO NOTHING
                        """, tag)
                        
                        # Link tag to item
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id)
                            SELECT $1, id FROM tags WHERE name = $2
                            ON CONFLICT DO NOTHING
                        """, item_id, tag)
                
                # Generate and store embedding
                if processed.summary:
                    embedding = await self.embedding_service.generate_embedding(processed.summary)
                    if embedding:
                        await update_item_embedding(str(item_id), embedding)
                        logger.info(f"Generated and stored embedding for item {item_id}")
            
            logger.info(f"Successfully processed item {item_id}")
            
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {str(e)}")
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE items 
                    SET status = 'failed',
                        metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text))
                    WHERE id = $1
                """, item_id, str(e))