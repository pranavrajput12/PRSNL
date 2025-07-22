#!/usr/bin/env python3
"""
Test full automatic processing with real content
"""
import asyncio
import asyncpg
import os
from datetime import datetime
import uuid
import json

from dotenv import load_dotenv
load_dotenv()

async def test_full_processing():
    """Add a test item and verify full processing pipeline"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Testing Full Automatic Processing ===\n")
        
        # Create a test item with a real URL
        item_id = uuid.uuid4()
        test_url = "https://docs.anthropic.com/en/docs/build-with-claude"
        
        result = await conn.fetchrow("""
            INSERT INTO items (
                id, title, type, url, summary, status, user_id, 
                metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
            ) RETURNING id
        """, 
            str(item_id),
            "Building with Claude AI - Official Documentation",
            "website",
            test_url,
            "Official Anthropic documentation on building applications with Claude AI",
            "pending",
            str(uuid.uuid4()),  # dummy user_id
            json.dumps({"tags": ["claude", "ai", "chatbot", "documentation", "anthropic"]})
        )
        
        print(f"✓ Created test item: {result['id']}")
        print(f"  URL: {test_url}")
        print(f"  Title: Building with Claude AI - Official Documentation")
        print("\nWaiting for automatic processing...")
        
        # Monitor progress
        for i in range(30):  # Check for 30 seconds
            await asyncio.sleep(2)
            
            item = await conn.fetchrow("""
                SELECT 
                    id, title, status,
                    processed_content IS NOT NULL as has_content,
                    LENGTH(processed_content) as content_length,
                    embedding IS NOT NULL as has_embedding,
                    search_vector IS NOT NULL as has_search_vector,
                    embed_vector_id
                FROM items
                WHERE id = $1
            """, str(item_id))
            
            print(f"\r[{i*2}s] Status: {item['status']}", end="")
            print(f" | Content: {'✓' if item['has_content'] else '✗'}", end="")
            if item['content_length']:
                print(f" ({item['content_length']} chars)", end="")
            print(f" | Embedding: {'✓' if item['has_embedding'] else '✗'}", end="")
            print(f" | Search: {'✓' if item['has_search_vector'] else '✗'}", end="")
            
            if item['status'] == 'processed' and item['has_content']:
                print("\n\n✅ Success! Item was processed automatically!")
                
                # Show a snippet of the content
                content = await conn.fetchval("""
                    SELECT processed_content FROM items WHERE id = $1
                """, str(item_id))
                
                if content:
                    print(f"\nContent preview (first 200 chars):")
                    print(f"  {content[:200]}...")
                
                # Check embeddings table
                if item['embed_vector_id']:
                    embedding_info = await conn.fetchrow("""
                        SELECT model_name, vector_norm
                        FROM embeddings
                        WHERE id = $1
                    """, item['embed_vector_id'])
                    
                    if embedding_info:
                        print(f"\nEmbedding info:")
                        print(f"  Model: {embedding_info['model_name']}")
                        print(f"  Vector norm: {embedding_info['vector_norm']}")
                
                break
        else:
            print("\n\n⚠️  Item was not fully processed within 60 seconds")
            print("Check worker logs for issues")
            
        # Check worker logs
        print("\n=== Recent Worker Activity ===")
        import subprocess
        
        # Check PostgreSQL worker
        result = subprocess.run(['tail', '-10', 'simple_worker.log'], 
                              capture_output=True, text=True, cwd='/Users/pronav/Personal Knowledge Base/PRSNL/backend')
        print("\nPostgreSQL Worker Log:")
        print(result.stdout)
        
        # Check Celery worker
        result = subprocess.run(['tail', '-10', 'celery_worker.log'], 
                              capture_output=True, text=True, cwd='/Users/pronav/Personal Knowledge Base/PRSNL/backend')
        print("\nCelery Worker Log (last 10 lines):")
        for line in result.stdout.strip().split('\n')[-10:]:
            if line and not line.startswith('['):
                print(f"  {line}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_full_processing())