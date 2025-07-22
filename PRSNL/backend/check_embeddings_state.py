#!/usr/bin/env python3
"""
Check the current state of embeddings in the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_embeddings_state():
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Checking Embeddings State ===\n")
        
        # Check if embeddings table exists
        embeddings_table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'embeddings'
            )
        """)
        
        print(f"1. Embeddings table exists: {embeddings_table_exists}")
        
        if embeddings_table_exists:
            # Count embeddings
            embeddings_count = await conn.fetchval("SELECT COUNT(*) FROM embeddings")
            print(f"   - Total embeddings: {embeddings_count}")
            
            # Check embedding models
            models = await conn.fetch("""
                SELECT model_name, model_version, COUNT(*) as count 
                FROM embeddings 
                GROUP BY model_name, model_version
            """)
            if models:
                print("   - Embedding models:")
                for model in models:
                    print(f"     * {model['model_name']} ({model['model_version']}): {model['count']} embeddings")
        
        # Check items table
        print("\n2. Items table state:")
        
        # Total items
        total_items = await conn.fetchval("SELECT COUNT(*) FROM items")
        print(f"   - Total items: {total_items}")
        
        # Items with embeddings in items.embedding column
        items_with_embedding = await conn.fetchval("""
            SELECT COUNT(*) FROM items WHERE embedding IS NOT NULL
        """)
        print(f"   - Items with embedding (legacy column): {items_with_embedding}")
        
        # Items with search vectors
        items_with_search_vector = await conn.fetchval("""
            SELECT COUNT(*) FROM items WHERE search_vector IS NOT NULL
        """)
        print(f"   - Items with search_vector: {items_with_search_vector}")
        
        # Items with content
        items_with_content = await conn.fetchval("""
            SELECT COUNT(*) FROM items 
            WHERE processed_content IS NOT NULL 
            OR raw_content IS NOT NULL
        """)
        print(f"   - Items with content: {items_with_content}")
        
        # Check pgvector extension
        print("\n3. pgvector extension:")
        pgvector_installed = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_extension WHERE extname = 'vector'
            )
        """)
        print(f"   - pgvector installed: {pgvector_installed}")
        
        if pgvector_installed:
            # Check vector version
            vector_version = await conn.fetchval("""
                SELECT extversion FROM pg_extension WHERE extname = 'vector'
            """)
            print(f"   - pgvector version: {vector_version}")
        
        # Sample items without embeddings
        print("\n4. Sample items without embeddings:")
        sample_items = await conn.fetch("""
            SELECT id, title, type, created_at,
                   CASE WHEN processed_content IS NOT NULL THEN 'Yes' ELSE 'No' END as has_content
            FROM items 
            WHERE embedding IS NULL
            LIMIT 5
        """)
        
        if sample_items:
            for item in sample_items:
                print(f"   - {item['title'][:50]}... (Type: {item['type']}, Has content: {item['has_content']})")
        else:
            print("   - All items have embeddings!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_embeddings_state())