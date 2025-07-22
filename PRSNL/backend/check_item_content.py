#!/usr/bin/env python3
"""
Check what content is actually stored in items
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_content():
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    conn = await asyncpg.connect(db_url)
    
    try:
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        
        # Get all items with their content status
        items = await conn.fetch("""
            SELECT 
                id, 
                title, 
                url,
                type,
                status,
                raw_content IS NOT NULL as has_raw,
                processed_content IS NOT NULL as has_processed,
                summary IS NOT NULL as has_summary,
                search_vector IS NOT NULL as has_search_vector,
                LENGTH(COALESCE(raw_content, '')) as raw_length,
                LENGTH(COALESCE(processed_content, '')) as processed_length
            FROM items
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user_id)
        
        print(f"Total items: {len(items)}\n")
        
        for item in items:
            print(f"Title: {item['title'][:50]}...")
            print(f"  URL: {item['url']}")
            print(f"  Type: {item['type']}")
            print(f"  Status: {item['status']}")
            print(f"  Has raw content: {item['has_raw']} ({item['raw_length']} chars)")
            print(f"  Has processed content: {item['has_processed']} ({item['processed_length']} chars)")
            print(f"  Has summary: {item['has_summary']}")
            print(f"  Has search vector: {item['has_search_vector']}")
            print()
            
        # Count statistics
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN raw_content IS NOT NULL THEN 1 END) as with_raw,
                COUNT(CASE WHEN processed_content IS NOT NULL THEN 1 END) as with_processed,
                COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) as with_summary,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as with_vector,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM items
            WHERE user_id = $1
        """, user_id)
        
        print("=== Statistics ===")
        print(f"Total items: {stats['total']}")
        print(f"With raw content: {stats['with_raw']}")
        print(f"With processed content: {stats['with_processed']}")
        print(f"With summary: {stats['with_summary']}")
        print(f"With search vector: {stats['with_vector']}")
        print(f"Status - Completed: {stats['completed']}, Failed: {stats['failed']}, Pending: {stats['pending']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_content())