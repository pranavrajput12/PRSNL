"""Core capture engine for processing items"""
import asyncio
import time
import json
from uuid import UUID
from app.services.scraper import WebScraper
from app.services.llm_processor import LLMProcessor
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_pool, update_item_embedding
from app.utils.content_fingerprint import generate_content_fingerprint, ContentFingerprintManager
import logging

logger = logging.getLogger(__name__)


class CaptureEngine:
    """Handles the capture and processing of items"""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.llm_processor = LLMProcessor()
        self.embedding_service = EmbeddingService()
    
    async def process_item(self, item_id: UUID, url: str = None, content: str = None, enable_summarization: bool = False, content_type: str = "auto"):
        """
        Process a captured item:
        1. Scrape content (if URL provided)
        2. Process with LLM (if enabled)
        3. Update database
        """
        try:
            pool = await get_db_pool()
            logger.info(f"Processing item {item_id} - URL: {url}, Content: {content[:100] if content else None}, Type: {content_type}")
            
            # If content is provided directly, use it; otherwise scrape the URL
            if content:
                logger.info(f"Using provided content for item {item_id}")
                
                # Extract a meaningful title from the content
                lines = content.strip().split('\n')
                first_line = lines[0].strip() if lines else ''
                
                # Use first line as title if it's reasonable length, otherwise truncate content
                if first_line and 10 <= len(first_line) <= 100:
                    extracted_title = first_line
                elif len(content) > 100:
                    # Extract first sentence or chunk
                    extracted_title = content[:80].strip()
                    if not extracted_title.endswith('.'):
                        extracted_title += '...'
                else:
                    extracted_title = content.strip() or 'Note'
                
                logger.info(f"Extracted title from content: {extracted_title}")
                
                scraped_data = type('ScrapedData', (), {
                    'content': content,
                    'title': extracted_title,
                    'html': content,
                    'author': None,
                    'published_date': None,
                    'scraped_at': None,
                    'images': []
                })()
            elif url:
                logger.info(f"Scraping URL: {url}")
                scraped_data = await self.scraper.scrape(url)
            else:
                raise ValueError("Either URL or content must be provided")
            
            if not scraped_data.content:
                logger.warning(f"No content extracted from {url}, using title as fallback")
                # Use title as fallback content to avoid complete failure
                if scraped_data.title:
                    scraped_data.content = f"Content from {url}: {scraped_data.title}"
                else:
                    scraped_data.content = f"Web page content from {url}"
            
            # Process with LLM (if enabled and not a link-only capture)
            if enable_summarization and content_type != "link":
                logger.info(f"Processing content with LLM for item {item_id}")
                processed = await self.llm_processor.process_content(
                    content=scraped_data.content,
                    url=url,
                    title=scraped_data.title
                )
            else:
                if content_type == "link":
                    logger.info(f"Link-only capture for item {item_id} - extracting meta only")
                else:
                    logger.info(f"Skipping LLM processing for item {item_id} (summarization disabled)")
                # Create a minimal processed object without AI analysis
                processed = type('ProcessedContent', (), {
                    'title': scraped_data.title,
                    'summary': None,
                    'content': scraped_data.content,
                    'tags': [],
                    'key_points': [],
                    'sentiment': None
                })()
            
            # First, fetch existing metadata to preserve it
            existing_metadata = {}
            async with pool.acquire() as conn:
                existing_row = await conn.fetchrow("""
                    SELECT metadata FROM items WHERE id = $1
                """, item_id)
                if existing_row and existing_row['metadata']:
                    # Handle both dict and string types
                    if isinstance(existing_row['metadata'], dict):
                        existing_metadata = existing_row['metadata']
                    elif isinstance(existing_row['metadata'], str):
                        try:
                            existing_metadata = json.loads(existing_row['metadata'])
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse existing metadata as JSON: {existing_row['metadata']}")
                            existing_metadata = {}
                    logger.info(f"🔍 Preserving existing metadata keys: {list(existing_metadata.keys())}")
            
            # Generate content fingerprint for deduplication
            content_fingerprint = generate_content_fingerprint(scraped_data.content)
            
            # Build metadata - merge with existing
            metadata = existing_metadata.copy()
            metadata.update({
                "author": scraped_data.author,
                "published_date": scraped_data.published_date,
                "word_count": len(processed.content.split()) if processed.content else 0,
                "scraped_at": scraped_data.scraped_at.isoformat() if scraped_data.scraped_at else None,
                "summarization_enabled": enable_summarization,
                "content_type": content_type,
                "content_fingerprint": content_fingerprint
            })
            
            # Only include ai_analysis if AI processing actually occurred
            if enable_summarization and content_type != "link":
                metadata["ai_analysis"] = {
                    "summary": processed.summary,
                    "tags": processed.tags,
                    "key_points": processed.key_points,
                    "sentiment": processed.sentiment,
                    "reading_time": getattr(processed, 'reading_time', None),
                    "entities": getattr(processed, 'entities', []),
                    "questions": getattr(processed, 'questions', []),
                    "processed_at": time.time()
                }

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
                        content_fingerprint = $7,
                        status = 'completed',
                        updated_at = NOW()
                    WHERE id = $1
                """, 
                    item_id,
                    processed.title or scraped_data.title or "Untitled",
                    processed.summary,
                    scraped_data.html,
                    processed.content,
                    json.dumps(metadata),
                    content_fingerprint
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
                
                # Save images as attachments
                if hasattr(scraped_data, 'images') and scraped_data.images:
                    for idx, img in enumerate(scraped_data.images[:5]):  # Limit to 5 images
                        try:
                            await conn.execute("""
                                INSERT INTO attachments (item_id, file_type, file_path, mime_type, metadata)
                                VALUES ($1, $2, $3, $4, $5)
                            """, 
                                item_id,
                                'image',
                                img['url'],  # Store URL as file_path
                                'image/jpeg',  # Default, could be improved by checking URL extension
                                json.dumps({
                                    'alt': img.get('alt', ''),
                                    'title': img.get('title', ''),
                                    'width': img.get('width', ''),
                                    'height': img.get('height', ''),
                                    'is_remote': True,
                                    'index': idx
                                })
                            )
                            logger.info(f"Saved image attachment {idx} for item {item_id}")
                        except Exception as e:
                            logger.warning(f"Failed to save image attachment: {e}")
                
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