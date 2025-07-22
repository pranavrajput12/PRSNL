#!/usr/bin/env python3
"""
Fix missing search vectors for all items in the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_search_vectors():
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        # Test user ID (from SECURITY BYPASS)
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        
        print("=== Fixing Search Vectors ===")
        
        # First, count items without search vectors
        count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM items
            WHERE user_id = $1
            AND (search_vector IS NULL OR processed_content IS NULL)
        """, user_id)
        
        print(f"Found {count} items without search vectors")
        
        if count == 0:
            print("All items already have search vectors!")
            return
            
        # Update search vectors for all items
        print("Updating search vectors...")
        
        # For items with processed_content, use that
        updated = await conn.execute("""
            UPDATE items 
            SET search_vector = to_tsvector('english', 
                COALESCE(title, '') || ' ' || 
                COALESCE(summary, '') || ' ' || 
                COALESCE(processed_content, '') || ' ' ||
                COALESCE(metadata->>'tags', '') || ' ' ||
                COALESCE(metadata->>'category', '')
            )
            WHERE user_id = $1
            AND processed_content IS NOT NULL
            AND search_vector IS NULL
        """, user_id)
        
        print(f"Updated {updated.split()[-1]} items with processed content")
        
        # For items without processed_content, use raw_content
        updated = await conn.execute("""
            UPDATE items 
            SET search_vector = to_tsvector('english', 
                COALESCE(title, '') || ' ' || 
                COALESCE(summary, '') || ' ' || 
                COALESCE(raw_content, '') || ' ' ||
                COALESCE(metadata->>'tags', '') || ' ' ||
                COALESCE(metadata->>'category', '')
            )
            WHERE user_id = $1
            AND processed_content IS NULL
            AND raw_content IS NOT NULL
            AND search_vector IS NULL
        """, user_id)
        
        print(f"Updated {updated.split()[-1]} items with raw content")
        
        # For items with neither, at least use title and metadata
        updated = await conn.execute("""
            UPDATE items 
            SET search_vector = to_tsvector('english', 
                COALESCE(title, '') || ' ' || 
                COALESCE(url, '') || ' ' ||
                COALESCE(metadata->>'tags', '') || ' ' ||
                COALESCE(metadata->>'category', '') || ' ' ||
                COALESCE(type, '')
            )
            WHERE user_id = $1
            AND processed_content IS NULL
            AND raw_content IS NULL
            AND search_vector IS NULL
        """, user_id)
        
        print(f"Updated {updated.split()[-1]} items with just metadata")
        
        # Test the search again
        print("\n=== Testing Search ===")
        
        search_terms = ["youtube", "video", "qubit", "bookmark"]
        
        for term in search_terms:
            results = await conn.fetch("""
                SELECT id, title, 
                       ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
                FROM items
                WHERE user_id = $2
                AND search_vector @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT 3
            """, term, user_id)
            
            print(f"\nSearch for '{term}': {len(results)} results")
            for row in results:
                print(f"  - {row['title'][:60]}... (rank: {row['rank']:.4f})")
        
        # Final check
        final_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM items
            WHERE user_id = $1
            AND search_vector IS NOT NULL
        """, user_id)
        
        print(f"\n=== Complete ===")
        print(f"Total items with search vectors: {final_count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_search_vectors())