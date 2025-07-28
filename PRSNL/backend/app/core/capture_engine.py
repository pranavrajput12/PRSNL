"""Core capture engine for processing items"""
import asyncio
import json
import logging
import time
from uuid import UUID

from app.db.database import get_db_pool, update_item_embedding
from app.services.embedding_manager import embedding_manager
from app.services.embedding_service import EmbeddingService
from app.services.llm_processor import LLMProcessor
from app.services.smart_scraper import SmartScraperService
from app.services.unified_ai_service import unified_ai_service
from app.utils.content_fingerprint import (
    ContentFingerprintManager,
    generate_content_fingerprint,
)
from app.utils.fingerprint import calculate_content_fingerprint

logger = logging.getLogger(__name__)


class CaptureEngine:
    """Handles the capture and processing of items"""
    
    def __init__(self):
        self.scraper = SmartScraperService()
        self.llm_processor = LLMProcessor()
        self.embedding_service = EmbeddingService()
    
    def _is_recipe_content(self, url: str, content: str) -> bool:
        """Check if content appears to be a recipe"""
        if not url and not content:
            return False
            
        # Check URL patterns
        if url:
            recipe_indicators = [
                'recipe', 'recipes', 'cooking', 'food', 'ingredients',
                'allrecipes', 'foodnetwork', 'epicurious', 'bonappetit'
            ]
            url_lower = url.lower()
            if any(indicator in url_lower for indicator in recipe_indicators):
                return True
        
        # Check content patterns
        if content:
            content_lower = content.lower()
            recipe_keywords = [
                'ingredients', 'instructions', 'directions', 'prep time',
                'cook time', 'servings', 'serves', 'tablespoon', 'teaspoon',
                'cup', 'ounce', 'pound', 'grams', 'preheat', 'bake', 'sauté'
            ]
            keyword_count = sum(1 for keyword in recipe_keywords if keyword in content_lower)
            # If we find 3 or more recipe keywords, likely a recipe
            return keyword_count >= 3
        
        return False
    
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
                # Detect YouTube URLs and use specialized processor
                if "youtube.com" in url or "youtu.be" in url:
                    logger.info(f"Processing YouTube video: {url}")
                    try:
                        from app.services.platforms.youtube import YouTubeProcessor
                        youtube_processor = YouTubeProcessor()
                        
                        # Get video info and transcript
                        video_info = await youtube_processor.get_info(url)
                        if video_info:
                            # Extract transcript if available
                            transcript_content = ""
                            key_moments = []
                            
                            try:
                                from app.services.youtube_transcript_service import youtube_transcript_service
                                
                                logger.info(f"Extracting transcript for YouTube video: {url}")
                                transcript_content, key_moments = await youtube_transcript_service.extract_transcript(url)
                                
                                if transcript_content:
                                    logger.info(f"Successfully extracted transcript: {len(transcript_content)} characters, {len(key_moments)} key moments")
                                else:
                                    logger.warning(f"No transcript available for video: {url}")
                                    
                            except Exception as transcript_error:
                                logger.error(f"Transcript extraction error: {transcript_error}")
                                transcript_content = ""
                                key_moments = []
                            
                            # Use transcript as content, or fall back to description
                            content = transcript_content or video_info.get('description', '') or f"YouTube video: {video_info.get('title', 'Unknown')}"
                            
                            scraped_data = type('ScrapedData', (), {
                                'content': content,
                                'title': video_info.get('title', ''),
                                'html': content,
                                'author': video_info.get('uploader', ''),
                                'published_date': video_info.get('upload_date'),
                                'scraped_at': None,
                                'images': [],
                                'transcript': transcript_content,  # Store transcript separately
                                'duration': video_info.get('duration'),
                                'view_count': video_info.get('view_count'),
                                'platform': 'youtube',
                                'key_moments': key_moments  # Store key moments for Visual Cortex
                            })()
                            logger.info(f"YouTube processing complete: {video_info.get('title')} ({len(content)} chars)")
                        else:
                            logger.error(f"Failed to get YouTube video info for {url}")
                            raise Exception("Failed to extract YouTube video information")
                            
                    except Exception as youtube_error:
                        logger.error(f"YouTube processing failed: {youtube_error}")
                        # Fallback to SmartScraper for YouTube URLs as last resort
                        logger.info(f"Falling back to SmartScraper for: {url}")
                        scraper_result = await self.scraper.scrape_url(url)
                        
                        if scraper_result.get('success') and 'data' in scraper_result:
                            data = scraper_result['data']
                            scraped_data = type('ScrapedData', (), {
                                'content': data.get('content', ''),
                                'title': data.get('title', ''),
                                'html': data.get('content', ''),
                                'author': data.get('author'),
                                'published_date': data.get('published_date'),
                                'scraped_at': None,
                                'images': data.get('images', [])
                            })()
                        else:
                            raise Exception(f"Both YouTube processor and SmartScraper failed for {url}")
                else:
                    # Use SmartScraper for non-YouTube URLs
                    logger.info(f"Scraping URL with SmartScraper: {url}")
                    scraper_result = await self.scraper.scrape_url(url)
                    
                    # Extract data from SmartScraper response format
                    if scraper_result.get('success') and 'data' in scraper_result:
                        data = scraper_result['data']
                        logger.info(f"SmartScraper success with {scraper_result.get('scraper_used', 'unknown')} scraper")
                    else:
                        logger.warning(f"SmartScraper failed: {scraper_result.get('error', 'Unknown error')}")
                        data = {}
                    
                    # Convert SmartScraper result to ScrapedData format
                    scraped_data = type('ScrapedData', (), {
                        'content': data.get('content', ''),
                        'title': data.get('title', ''),
                        'html': data.get('content', ''),  # SmartScraper doesn't provide raw HTML, use content
                        'author': data.get('author'),
                        'published_date': data.get('published_date'),
                        'scraped_at': None,  # SmartScraper doesn't provide this
                        'images': data.get('images', [])
                    })()
            else:
                raise ValueError("Either URL or content must be provided")
            
            if not scraped_data.content:
                logger.warning(f"No content extracted from {url}, using title as fallback")
                # Use title as fallback content to avoid complete failure
                if scraped_data.title:
                    scraped_data.content = f"Content from {url}: {scraped_data.title}"
                else:
                    scraped_data.content = f"Web page content from {url}"
            
            # Clean the content using ContentCleanerAgent
            logger.info(f"Cleaning content for item {item_id}")
            cleaned_result = await unified_ai_service.clean_content(
                content=scraped_data.content,
                content_type=content_type,
                preserve_structure=True,
                aggressive_cleaning=False
            )
            
            # Use cleaned content if successful
            if cleaned_result and cleaned_result.get('content'):
                scraped_data.content = cleaned_result['content']
                logger.info(f"Content cleaned successfully. Stats: {cleaned_result.get('cleaning_stats', {})}")
            
            # Check if this is a recipe URL and extract recipe data
            recipe_data = None
            if content_type == "recipe" or self._is_recipe_content(url, scraped_data.content):
                logger.info(f"Extracting recipe data for item {item_id}")
                try:
                    recipe_data = await unified_ai_service.extract_recipe_data(
                        content=scraped_data.content,
                        url=url,
                        title=scraped_data.title
                    )
                    logger.info(f"Recipe extraction successful: {recipe_data.get('title', 'Unknown Recipe')}")
                except Exception as e:
                    logger.error(f"Recipe extraction failed: {e}")
                    recipe_data = None

            # Process with LLM (if enabled and not a link-only capture)
            if enable_summarization and content_type != "link":
                logger.info(f"Processing content with LLM and extracting actionable insights for item {item_id}")
                
                # Extract actionable insights
                insights_result = await unified_ai_service.extract_actionable_insights(
                    content=scraped_data.content,
                    content_type=content_type,
                    url=url,
                    title=scraped_data.title
                )
                
                # Generate actionable summary
                actionable_summary = await unified_ai_service.generate_actionable_summary(
                    content=scraped_data.content,
                    content_type=content_type,
                    max_length=500
                )
                
                # Also get regular analysis for backward compatibility
                processed = await self.llm_processor.process_content(
                    content=scraped_data.content,
                    url=url,
                    title=scraped_data.title
                )
                
                # Override summary with actionable summary
                processed.summary = actionable_summary
                
                # Store insights in processed object
                processed.actionable_insights = insights_result
                
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
                    'sentiment': None,
                    'actionable_insights': None
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
            
            # Generate content fingerprint for deduplication (use unified method)
            content_fingerprint = calculate_content_fingerprint(scraped_data.content)
            
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
            
            # Add YouTube-specific metadata if available
            if hasattr(scraped_data, 'platform') and scraped_data.platform == 'youtube':
                metadata.update({
                    "platform": "youtube",
                    "duration": getattr(scraped_data, 'duration', None),
                    "view_count": getattr(scraped_data, 'view_count', None),
                    "transcript_length": len(getattr(scraped_data, 'transcript', '') or ''),
                    "key_moments": getattr(scraped_data, 'key_moments', [])
                })
            
            # Only include ai_analysis if AI processing actually occurred
            if enable_summarization:
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
                
                # Add actionable insights if available
                if hasattr(processed, 'actionable_insights') and processed.actionable_insights:
                    metadata["actionable_insights"] = processed.actionable_insights
            
            # Add recipe data if available
            if recipe_data:
                metadata["recipe_data"] = recipe_data

            # Update the item in database
            async with pool.acquire() as conn:
                # Store transcript separately for video content
                transcript_content = getattr(scraped_data, 'transcript', '') or ''
                
                await conn.execute("""
                    UPDATE items 
                    SET 
                        title = $2::text,
                        summary = $3::text,
                        raw_content = $4::text,
                        processed_content = $5::text,
                        transcription = $6::text,
                        search_vector = to_tsvector('english', $2::text || ' ' || COALESCE($3::text, '') || ' ' || COALESCE($5::text, '') || ' ' || COALESCE($6::text, '')),
                        metadata = $7::jsonb,
                        content_fingerprint = $8::varchar(64),
                        status = 'completed'::varchar(20),
                        updated_at = NOW()
                    WHERE id = $1
                """, 
                    item_id,
                    str(processed.title or scraped_data.title or "Untitled")[:255],  # Limit to 255 chars for varchar column
                    str(processed.summary) if processed.summary else None,
                    str(scraped_data.html) if scraped_data.html else None,
                    str(processed.content) if processed.content else None,
                    transcript_content,  # Store transcript in transcription field
                    json.dumps(metadata),
                    str(content_fingerprint)[:64] if content_fingerprint else None  # Limit to 64 chars
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
                
                # Create embedding using the new embedding manager
                embed_content = f"{processed.title or scraped_data.title} {processed.content or scraped_data.content}"
                embedding_result = await embedding_manager.create_embedding(
                    str(item_id),
                    embed_content[:2000],  # Limit content length for embedding
                    update_item=True
                )
                if embedding_result:
                    logger.info(f"Created embedding {embedding_result['embedding_id']} for item {item_id}")
                else:
                    logger.warning(f"Failed to create embedding for item {item_id}")
                
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
                
                # Legacy embedding generation (keeping for backward compatibility)
                if processed.summary:
                    embedding = await self.embedding_service.generate_embedding(processed.summary)
                    if embedding:
                        await update_item_embedding(str(item_id), embedding)
                        logger.info(f"Generated and stored legacy embedding for item {item_id}")
            
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