#!/usr/bin/env python3
"""
Production Worker - Complete processing with all services
Uses Firecrawl for web scraping, YouTube processing, and PDF extraction
"""
import asyncio
import json
import logging
import os
from uuid import UUID
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

# Import all processing services
from app.services.smart_scraper import smart_scraper
from app.services.platforms.youtube import YouTubeProcessor
from app.services.document_processor import DocumentProcessor
from app.services.video_processor import VideoProcessor
from app.services.unified_ai_service import UnifiedAIService
from app.services.embedding_manager import EmbeddingManager

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionWorker:
    def __init__(self):
        self.smart_scraper = smart_scraper
        self.youtube_processor = YouTubeProcessor()
        self.document_processor = DocumentProcessor()
        self.video_processor = VideoProcessor()
        self.ai_service = UnifiedAIService()
        self.embedding_manager = None  # Will be initialized
        
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
            logger.info("🚀 Production worker listening with smart scraping enabled!")
            logger.info("Services:")
            logger.info(f"  - Smart Scraper: ✓ (Jina + Firecrawl fallback)")
            logger.info(f"  - Firecrawl fallback: {'✓' if self.smart_scraper.firecrawl.enabled else '✗'}")
            logger.info(f"  - YouTube: ✓")
            logger.info(f"  - Documents: ✓")
            logger.info(f"  - Video: ✓")
            
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
        logger.info(f"📨 Received notification: {payload}")
        try:
            item_id = UUID(payload)
            
            # Create a new connection for processing to avoid conflicts
            db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
            proc_conn = await asyncpg.connect(db_url)
            
            try:
                # Get item details
                row = await proc_conn.fetchrow("""
                    SELECT id, url, title, type, status, metadata, summary
                    FROM items WHERE id = $1::uuid
                """, str(item_id))
                
                if row and row['status'] == 'pending':
                    await self.process_item(proc_conn, item_id, row)
                else:
                    logger.info(f"Item {item_id} not found or already processed")
            finally:
                await proc_conn.close()
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}", exc_info=True)

    async def process_item(self, conn, item_id, row):
        """
        Process an item using appropriate service based on type
        """
        try:
            logger.info(f"🔄 Processing: {row['title']}")
            
            item_type = row['type']
            url = row['url']
            title = row['title']
            
            content = None
            metadata = {}
            
            # Update status to processing
            await conn.execute("""
                UPDATE items 
                SET status = 'processing', updated_at = NOW()
                WHERE id = $1::uuid
            """, str(item_id))
            
            # Process based on type
            if item_type in ['website', 'article'] and url:
                logger.info(f"🌐 Smart scraping: {url}")
                try:
                    # Use smart scraper (Jina first, Firecrawl fallback)
                    result = await self.smart_scraper.scrape_url(url)
                    
                    if result and result.get('success'):
                        data = result.get('data', {})
                        content = data.get('markdown', '') or data.get('content', '')
                        
                        scraper_used = data.get('scraper_used', result.get('scraper_used', 'unknown'))
                        
                        metadata.update({
                            'title': data.get('title', title),
                            'description': data.get('description', ''),
                            'language': data.get('language', 'en'),
                            'source_url': data.get('sourceURL', url),
                            'scraping_method': scraper_used
                        })
                        
                        # Log success with scraper info
                        emoji = "📖" if scraper_used == "jina" else "🔥"
                        logger.info(f"✓ {emoji} {scraper_used.title()} scraped {len(content)} chars")
                        
                        # Log stats periodically
                        if self.smart_scraper.stats['total_requests'] % 5 == 0:
                            self.smart_scraper.log_stats()
                            
                    else:
                        logger.warning(f"Smart scraping failed: {result.get('error', 'Unknown error')}")
                        content = f"Content extraction failed for: {title}"
                        
                except Exception as e:
                    logger.error(f"Error in web scraping: {e}")
                    content = f"Error processing web content: {title}"
                    
            elif item_type in ['video', 'youtube'] and url:
                logger.info(f"📺 Video processing: {url}")
                try:
                    # Extract video metadata and transcript
                    video_info = await self.youtube_processor.get_info(url)
                    if video_info:
                        content = f"Title: {video_info.get('title', title)}\n\n"
                        content += f"Description: {video_info.get('description', '')}\n\n"
                        
                        # Try to get transcript if available
                        try:
                            transcript = await self.youtube_processor.get_transcript(url)
                            if transcript:
                                content += f"Transcript:\n{transcript}"
                                logger.info(f"✓ Video transcript extracted ({len(transcript)} chars)")
                        except Exception as e:
                            logger.warning(f"Transcript extraction failed: {e}")
                            content += "Transcript: Not available"
                        
                        metadata.update({
                            'duration': video_info.get('duration'),
                            'view_count': video_info.get('view_count'),
                            'upload_date': video_info.get('upload_date'),
                            'uploader': video_info.get('uploader'),
                            'platform': 'youtube',
                            'processing_method': 'youtube_processor'
                        })
                        logger.info(f"✓ Video processed: {video_info.get('title', title)}")
                    else:
                        logger.warning("Video processing failed")
                        content = f"Video processing failed for: {title}"
                        
                except Exception as e:
                    logger.error(f"Error in video processing: {e}")
                    content = f"Error processing video: {title}"
                    
            elif item_type == 'pdf' and url:
                logger.info(f"📄 PDF processing: {url}")
                try:
                    # Download PDF and extract text
                    import httpx
                    import tempfile
                    import os
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        
                        # Save to temp file and extract
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                            tmp.write(response.content)
                            tmp.flush()
                            
                            # Extract text from PDF
                            result = await self.document_processor.extract_text(tmp.name)
                            content = result.get('text', '')
                            os.unlink(tmp.name)  # Clean up temp file
                    
                    if content:
                        metadata.update({
                            'document_type': 'pdf',
                            'processing_method': 'document_processor',
                            'source_url': url
                        })
                        logger.info(f"✓ PDF extracted ({len(content)} chars)")
                    else:
                        logger.warning("PDF extraction failed")
                        content = f"PDF extraction failed for: {title}"
                        
                except Exception as e:
                    logger.error(f"Error in PDF processing: {e}")
                    content = f"Error processing PDF: {title}"
                    
            else:
                # For other types, use summary as content
                content = row.get('summary', f"Content for: {title}")
                metadata = {'processing_method': 'fallback'}
            
            if content:
                # Update item with content and metadata
                existing_metadata = row.get('metadata', {})
                if isinstance(existing_metadata, str):
                    existing_metadata = json.loads(existing_metadata)
                existing_metadata.update(metadata)
                
                await conn.execute("""
                    UPDATE items 
                    SET 
                        processed_content = $2,
                        raw_content = $2,
                        metadata = $3,
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id), content[:100000], json.dumps(existing_metadata))
                
                logger.info(f"✓ Content saved ({len(content)} chars)")
                
                # Generate embedding
                try:
                    text_for_embedding = f"{title} {content[:2000]}"
                    embeddings = await self.ai_service.generate_embeddings([text_for_embedding])
                    
                    if embeddings and len(embeddings) > 0:
                        embedding = embeddings[0]
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        # Store embedding
                        await conn.execute("""
                            UPDATE items 
                            SET embedding = $2::vector
                            WHERE id = $1::uuid
                        """, str(item_id), embedding_str)
                        
                        # Store in embeddings table
                        await conn.execute("""
                            INSERT INTO embeddings (
                                item_id, model_name, model_version, vector, embedding_type
                            ) VALUES ($1::uuid, $2, $3, $4::vector, $5)
                            ON CONFLICT (item_id, model_name, model_version, embedding_type) 
                            DO UPDATE SET vector = $4::vector, updated_at = NOW()
                        """, str(item_id), 'text-embedding-ada-002', 'v1', embedding_str, 'text')
                        
                        logger.info(f"✓ Embedding generated")
                        
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
                
                logger.info(f"✓ Search vector updated")
                
                # Mark as processed
                await conn.execute("""
                    UPDATE items 
                    SET status = 'processed', updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id))
                
                logger.info(f"✅ Item {item_id} fully processed!")
                
            else:
                # Processing failed
                await conn.execute("""
                    UPDATE items 
                    SET status = 'error', updated_at = NOW()
                    WHERE id = $1::uuid
                """, str(item_id))
                
                logger.error(f"❌ Processing failed for item {item_id}")
                
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}", exc_info=True)
            await conn.execute("""
                UPDATE items 
                SET status = 'error', updated_at = NOW()
                WHERE id = $1::uuid
            """, str(item_id))

async def main():
    worker = ProductionWorker()
    await worker.listen_for_notifications()

if __name__ == "__main__":
    asyncio.run(main())