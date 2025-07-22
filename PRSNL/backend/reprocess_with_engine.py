#!/usr/bin/env python3
"""
Reprocess bookmarks using the actual capture engine
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncpg
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import after path setup
from app.core.capture_engine import CaptureEngine

async def reprocess_bookmarks():
    """Reprocess bookmarks to fetch real content"""
    # Direct database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    capture_engine = CaptureEngine()
    
    try:
        # Reset the bookmarks that have sample content
        print("Resetting bookmarks with sample content...")
        await conn.execute("""
            UPDATE items 
            SET 
                raw_content = NULL,
                processed_content = NULL,
                embedding = NULL,
                embed_vector_id = NULL,
                status = 'pending'
            WHERE type = 'bookmark'
            AND processed_content LIKE '%This is sample content for testing%'
        """)
        
        # Also delete their embeddings
        await conn.execute("""
            DELETE FROM embeddings 
            WHERE item_id IN (
                SELECT id FROM items 
                WHERE type = 'bookmark'
            )
        """)
        
        # Get bookmarks to process
        bookmarks = await conn.fetch("""
            SELECT id, url, title
            FROM items 
            WHERE type = 'bookmark'
            AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        print(f"\nFound {len(bookmarks)} bookmarks to process with real content")
        
        if not bookmarks:
            print("No bookmarks need processing!")
            return
            
        success_count = 0
        fail_count = 0
        
        for bookmark in bookmarks:
            print(f"\nProcessing: {bookmark['title'][:60]}...")
            print(f"  URL: {bookmark['url']}")
            
            try:
                # Use the actual capture engine to process the item
                await capture_engine.process_item(
                    item_id=bookmark['id'],
                    url=bookmark['url'],
                    enable_summarization=True,
                    content_type='auto'
                )
                
                # Check if it was processed successfully
                result = await conn.fetchrow("""
                    SELECT status, processed_content IS NOT NULL as has_content,
                           embedding IS NOT NULL as has_embedding
                    FROM items WHERE id = $1
                """, bookmark['id'])
                
                if result['status'] == 'processed':
                    print(f"  ✓ Successfully processed")
                    print(f"    - Has content: {result['has_content']}")
                    print(f"    - Has embedding: {result['has_embedding']}")
                    success_count += 1
                else:
                    print(f"  ⚠ Status: {result['status']}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                fail_count += 1
                
            # Small delay between requests
            await asyncio.sleep(2)
        
        print(f"\n=== Summary ===")
        print(f"Successfully processed: {success_count}")
        print(f"Failed: {fail_count}")
        
        # Show final state
        final_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_bookmarks,
                COUNT(CASE WHEN processed_content IS NOT NULL THEN 1 END) as with_content,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding
            FROM items WHERE type = 'bookmark'
        """)
        
        print(f"\nFinal bookmark state:")
        print(f"  Total bookmarks: {final_stats['total_bookmarks']}")
        print(f"  With content: {final_stats['with_content']}")
        print(f"  With embeddings: {final_stats['with_embedding']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    # Set minimal environment to avoid Pydantic validation issues
    os.environ['AZURE_OPENAI_API_KEY'] = os.getenv('AZURE_OPENAI_API_KEY', '')
    os.environ['AZURE_OPENAI_ENDPOINT'] = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    os.environ['POSTGRES_HOST'] = 'localhost'
    os.environ['POSTGRES_PORT'] = '5432'
    os.environ['POSTGRES_USER'] = 'pronav'
    os.environ['POSTGRES_PASSWORD'] = ''
    os.environ['POSTGRES_DB'] = 'prsnl'
    
    asyncio.run(reprocess_bookmarks())