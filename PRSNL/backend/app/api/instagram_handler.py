"""Special handler for Instagram content that can't be downloaded"""
import json
import logging
from uuid import UUID

from app.db.database import get_db_pool
from app.services.embedding_service import embedding_service
from app.services.llm_processor import LLMProcessor
from app.services.scraper import WebScraper

logger = logging.getLogger(__name__)

async def process_instagram_bookmark(item_id: UUID, url: str):
    """Process Instagram URL as a bookmark with metadata extraction"""
    try:
        pool = await get_db_pool()
        scraper = WebScraper()
        llm_processor = LLMProcessor()
        
        # Try to scrape whatever metadata we can get
        logger.info(f"Attempting to scrape Instagram metadata from {url}")
        metadata = {}
        caption = ""
        
        try:
            # Scrape the page to get any available content
            scraped_data = await scraper.scrape(url)
            if scraped_data and scraped_data.content:
                # Extract caption/description from the scraped content
                caption = scraped_data.content[:500]  # First 500 chars
                metadata['scraped_title'] = scraped_data.title
                metadata['scraped_at'] = scraped_data.scraped_at
        except Exception as e:
            logger.warning(f"Could not scrape Instagram page: {e}")
        
        # Extract Instagram ID from URL
        instagram_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        
        # Build context for AI processing
        ai_context = f"""
Instagram Content Analysis:
URL: {url}
Instagram ID: {instagram_id}
Content Type: {'Reel' if '/reel/' in url else 'Post' if '/p/' in url else 'Unknown'}

Available Caption/Text:
{caption if caption else 'No caption available'}

Please analyze this Instagram content and provide:
1. A descriptive title based on the URL and any available context
2. Relevant tags for organization
3. A brief description of what this content might be about
"""
        
        # Process with AI to generate tags and description
        processed_content = await llm_processor.process(
            content=ai_context,
            url=url,
            title=f"Instagram {instagram_id}"
        )
        
        # Generate embedding for searchability
        embedding_text = f"{processed_content.title} {processed_content.summary} {' '.join(processed_content.tags)}"
        embedding_vector = await embedding_service.generate_embedding(embedding_text)
        # Convert to PostgreSQL array format
        embedding = f"[{','.join(map(str, embedding_vector))}]"
        
        # Update the item with processed information
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET
                    title = $2,
                    summary = $3,
                    status = 'bookmark',
                    platform = 'instagram',
                    metadata = $4::jsonb,
                    embedding = $5,
                    updated_at = NOW()
                WHERE id = $1
            """,
                item_id,
                processed_content.title,
                processed_content.summary,
                json.dumps({
                    'instagram_id': instagram_id,
                    'bookmark': True,
                    'caption': caption or "Instagram content - visit URL to view",
                    'ai_analysis': {
                        'tags': processed_content.tags,
                        'key_points': processed_content.key_points,
                        'entities': processed_content.entities,
                        'questions': processed_content.questions
                    },
                    **metadata
                }),
                embedding
            )
            
            # Add tags
            for tag_name in processed_content.tags:
                tag_id = await conn.fetchval("""
                    INSERT INTO tags (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, tag_name.lower())
                
                await conn.execute("""
                    INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, item_id, tag_id)
        
        logger.info(f"Successfully bookmarked Instagram content {item_id}")
        
    except Exception as e:
        logger.error(f"Failed to process Instagram bookmark {item_id}: {e}")
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET status = 'bookmark',
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{error}', to_jsonb($2::text)),
                    summary = 'Instagram content - saved as bookmark'
                WHERE id = $1
            """, item_id, str(e))