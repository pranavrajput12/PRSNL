#!/usr/bin/env python3
"""
Test automatic embedding generation
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_auto_embedding():
    """Test if embeddings are generated automatically when creating items"""
    
    # Create a test item via API
    url = "http://localhost:8000/api/items"
    
    # Test data
    test_item = {
        "url": f"https://example.com/test-{datetime.now().timestamp()}",
        "title": "Test Article for Automatic Embedding Generation",
        "content_type": "article",
        "enable_ai": True,
        "metadata": {
            "tags": ["test", "embedding", "automatic"],
            "description": "This is a test article to verify automatic embedding generation works correctly"
        }
    }
    
    print("Creating test item via API...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Create item
            response = await client.post(url, json=test_item)
            
            if response.status_code == 200:
                item_data = response.json()
                item_id = item_data['id']
                print(f"✓ Created item: {item_id}")
                print(f"  Title: {item_data['title']}")
                print(f"  Status: {item_data['status']}")
                
                # Wait a bit for processing
                print("\nWaiting for processing...")
                await asyncio.sleep(5)
                
                # Check if item has embedding
                check_response = await client.get(f"http://localhost:8000/api/items/{item_id}")
                if check_response.status_code == 200:
                    updated_item = check_response.json()
                    
                    # Check direct database for embeddings
                    import asyncpg
                    db_url = "postgresql://pronav@localhost:5432/prsnl"
                    conn = await asyncpg.connect(db_url)
                    
                    try:
                        # Check items table
                        item_embedding = await conn.fetchval("""
                            SELECT embedding IS NOT NULL as has_embedding
                            FROM items WHERE id = $1
                        """, item_id)
                        
                        # Check embeddings table
                        embedding_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM embeddings WHERE item_id = $1
                        """, item_id)
                        
                        print(f"\nEmbedding Status:")
                        print(f"  Has embedding in items table: {item_embedding}")
                        print(f"  Embeddings in embeddings table: {embedding_count}")
                        
                        if embedding_count > 0:
                            embedding_info = await conn.fetchrow("""
                                SELECT model_name, model_version, embedding_type, 
                                       vector_norm, created_at
                                FROM embeddings WHERE item_id = $1
                            """, item_id)
                            print(f"  Model: {embedding_info['model_name']}")
                            print(f"  Type: {embedding_info['embedding_type']}")
                            print(f"  Created: {embedding_info['created_at']}")
                        
                    finally:
                        await conn.close()
                else:
                    print(f"✗ Failed to fetch item: {check_response.status_code}")
            else:
                print(f"✗ Failed to create item: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_auto_embedding())