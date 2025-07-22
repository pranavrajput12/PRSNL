#!/usr/bin/env python3
"""
Reset sample content from bookmarks
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def reset_sample_content():
    """Remove sample content and reset bookmarks to pending"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Resetting Sample Content ===")
        
        # Find bookmarks with sample content
        sample_bookmarks = await conn.fetch("""
            SELECT id, title 
            FROM items 
            WHERE type = 'bookmark'
            AND processed_content LIKE '%This is sample content for testing%'
        """)
        
        print(f"Found {len(sample_bookmarks)} bookmarks with sample content")
        
        if sample_bookmarks:
            # Reset these bookmarks
            updated = await conn.execute("""
                UPDATE items 
                SET 
                    raw_content = NULL,
                    processed_content = NULL,
                    summary = NULL,
                    embedding = NULL,
                    embed_vector_id = NULL,
                    status = 'pending',
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{reset_reason}', 
                        '"Removed sample content - needs real processing"'
                    )
                WHERE type = 'bookmark'
                AND processed_content LIKE '%This is sample content for testing%'
            """)
            
            print(f"Reset {len(sample_bookmarks)} bookmarks to pending state")
            
            # Delete their embeddings
            deleted = await conn.execute("""
                DELETE FROM embeddings 
                WHERE item_id IN (
                    SELECT id FROM items 
                    WHERE type = 'bookmark'
                    AND status = 'pending'
                )
            """)
            
            print(f"Deleted embeddings for reset bookmarks")
            
            # Show reset bookmarks
            print("\nReset bookmarks:")
            for bookmark in sample_bookmarks:
                print(f"  - {bookmark['title'][:60]}...")
        
        # Show current state
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_bookmarks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN processed_content IS NOT NULL THEN 1 END) as with_content,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding
            FROM items 
            WHERE type = 'bookmark'
        """)
        
        print(f"\nCurrent bookmark state:")
        print(f"  Total: {stats['total_bookmarks']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  With content: {stats['with_content']}")
        print(f"  With embeddings: {stats['with_embedding']}")
        
        print("\nBookmarks have been reset to pending state.")
        print("To fetch real content, use the frontend 'Capture' page to re-process them.")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_sample_content())