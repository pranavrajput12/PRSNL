#!/usr/bin/env python3
"""
Reprocess failed bookmarks with the fixed capture engine
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/backend')

import asyncpg
from app.core.capture_engine import CaptureEngine
from app.config import settings


async def reprocess_failed_bookmarks():
    """Find and reprocess all failed bookmarks"""
    # Create direct connection
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB
    )
    
    capture_engine = CaptureEngine()
    
    try:
        # Get all failed bookmarks
        failed_items = await conn.fetch("""
            SELECT id, url, title, metadata
            FROM items 
            WHERE user_id = 'e03c9686-09b0-4a06-b236-d0839ac7f5df'
            AND type = 'bookmark'
            AND (status = 'failed' OR status = 'completed')
            ORDER BY created_at DESC
        """)
        
        print(f"Found {len(failed_items)} bookmarks to reprocess")
        
        success_count = 0
        fail_count = 0
        
        for item in failed_items:
            print(f"\nProcessing: {item['title'][:60]}...")
            print(f"  URL: {item['url']}")
            
            try:
                # Reset status to pending so it gets processed
                await conn.execute("""
                    UPDATE items 
                    SET status = 'pending',
                        raw_content = NULL,
                        processed_content = NULL,
                        search_vector = NULL
                    WHERE id = $1
                """, item['id'])
                
                # Process with auto-fetch and AI summarization enabled
                await capture_engine.process_item(
                    item_id=item['id'],
                    url=item['url'],
                    enable_summarization=True,
                    content_type='link'
                )
                
                # Check the result
                result = await conn.fetchrow("""
                    SELECT status, processed_content IS NOT NULL as has_content
                    FROM items WHERE id = $1
                """, item['id'])
                
                if result['status'] == 'completed' and result['has_content']:
                    print(f"  ✓ Success! Content fetched and processed")
                    success_count += 1
                else:
                    print(f"  ✗ Failed with status: {result['status']}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                fail_count += 1
                # Mark as failed
                await conn.execute("""
                    UPDATE items 
                    SET status = 'failed',
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'::jsonb),
                            '{error}',
                            $2::jsonb
                        )
                    WHERE id = $1
                """, item['id'], json.dumps(str(e)))
    
    print(f"\n=== Reprocessing Complete ===")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {len(failed_items)}")


    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(reprocess_failed_bookmarks())