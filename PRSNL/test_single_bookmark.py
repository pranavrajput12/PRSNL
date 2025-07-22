#!/usr/bin/env python3
"""
Test processing a single bookmark to verify the fix works
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/backend')

import asyncpg
from app.config import settings

async def test_single_bookmark():
    """Test with one bookmark"""
    # Use the database URL from settings
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgres://", 1)
    conn = await asyncpg.connect(database_url)
    
    try:
        # Get one bookmark
        item = await conn.fetchrow("""
            SELECT id, url, title, status
            FROM items 
            WHERE user_id = 'e03c9686-09b0-4a06-b236-d0839ac7f5df'
            AND type = 'bookmark'
            LIMIT 1
        """)
        
        if item:
            print(f"Found bookmark: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"Status: {item['status']}")
            print(f"ID: {item['id']}")
            
            # Initialize the database pool for the capture engine
            from app.db.database import init_db_pool
            await init_db_pool()
            
            # Now try to process it
            from app.core.capture_engine import CaptureEngine
            capture_engine = CaptureEngine()
            
            print("\nProcessing bookmark...")
            await capture_engine.process_item(
                item_id=item['id'],
                url=item['url'],
                enable_summarization=True,
                content_type='link'
            )
            
            # Check result
            result = await conn.fetchrow("""
                SELECT status, 
                       raw_content IS NOT NULL as has_raw,
                       processed_content IS NOT NULL as has_processed,
                       summary IS NOT NULL as has_summary,
                       search_vector IS NOT NULL as has_vector,
                       embedding IS NOT NULL as has_embedding
                FROM items WHERE id = $1
            """, item['id'])
            
            print("\nResults:")
            print(f"Status: {result['status']}")
            print(f"Has raw content: {result['has_raw']}")
            print(f"Has processed content: {result['has_processed']}")
            print(f"Has summary: {result['has_summary']}")
            print(f"Has search vector: {result['has_vector']}")
            print(f"Has embedding: {result['has_embedding']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_single_bookmark())