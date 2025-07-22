#!/usr/bin/env python3
"""
Test script to debug search functionality
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_search():
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        # Test user ID (from SECURITY BYPASS)
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        
        # Test searches
        search_terms = ["youtube", "video", "qubit", "bookmark"]
        
        for term in search_terms:
            print(f"\n=== Searching for: {term} ===")
            
            # Full-text search
            results = await conn.fetch(
                """
                SELECT id, title, url, type, 
                       ts_rank(search_vector, plainto_tsquery('english', $1)) as rank_score
                FROM items
                WHERE user_id = $2
                AND (
                    search_vector @@ plainto_tsquery('english', $1)
                    OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                    OR title ILIKE '%' || $1 || '%'
                    OR url ILIKE '%' || $1 || '%'
                )
                ORDER BY rank_score DESC
                LIMIT 5
                """,
                term, user_id
            )
            
            if results:
                print(f"Found {len(results)} results:")
                for row in results:
                    score = row['rank_score'] if row['rank_score'] is not None else 0.0
                    print(f"  - {row['title'][:60]}... (score: {score:.4f})")
            else:
                print("No results found")
                
                # Try a simpler search
                simple_results = await conn.fetch(
                    """
                    SELECT id, title, url
                    FROM items
                    WHERE user_id = $1
                    AND (title ILIKE '%' || $2 || '%' OR url ILIKE '%' || $2 || '%')
                    LIMIT 5
                    """,
                    user_id, term
                )
                
                if simple_results:
                    print(f"Simple search found {len(simple_results)} results:")
                    for row in simple_results:
                        print(f"  - {row['title'][:60]}...")
        
        # Check if search_vector column exists and has data
        print("\n=== Checking search_vector column ===")
        vector_info = await conn.fetchrow(
            """
            SELECT COUNT(*) as total_items,
                   COUNT(search_vector) as items_with_vector,
                   COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as non_null_vectors
            FROM items
            WHERE user_id = $1
            """,
            user_id
        )
        print(f"Total items: {vector_info['total_items']}")
        print(f"Items with search_vector: {vector_info['items_with_vector']}")
        print(f"Non-null search vectors: {vector_info['non_null_vectors']}")
        
        # Check one item in detail
        sample = await conn.fetchrow(
            """
            SELECT title, url, search_vector IS NOT NULL as has_vector,
                   processed_content IS NOT NULL as has_processed_content
            FROM items
            WHERE user_id = $1
            AND title ILIKE '%qubit%'
            LIMIT 1
            """,
            user_id
        )
        
        if sample:
            print(f"\nSample item matching 'qubit':")
            print(f"  Title: {sample['title']}")
            print(f"  URL: {sample['url']}")
            print(f"  Has search vector: {sample['has_vector']}")
            print(f"  Has processed content: {sample['has_processed_content']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_search())