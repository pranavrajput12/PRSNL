#!/usr/bin/env python3
"""
Generate embeddings for items that don't have them
"""
import asyncio
import asyncpg
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after setting up environment
from app.services.unified_ai_service import UnifiedAIService

async def generate_embeddings():
    """Generate embeddings for items without them"""
    # Direct database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    ai_service = UnifiedAIService()
    
    try:
        # Get items with content but no embeddings
        items = await conn.fetch("""
            SELECT id, title, 
                   COALESCE(processed_content, raw_content) as content,
                   url
            FROM items 
            WHERE (processed_content IS NOT NULL OR raw_content IS NOT NULL)
            AND embedding IS NULL
            LIMIT 10
        """)
        
        print(f"Found {len(items)} items needing embeddings")
        
        if not items:
            print("No items need embeddings!")
            return
            
        success_count = 0
        
        for item in items:
            print(f"\nGenerating embedding for: {item['title'][:60]}...")
            
            # Prepare text for embedding
            text_to_embed = f"{item['title']} {item['content']}"
            
            try:
                # Generate embedding
                embeddings = await ai_service.generate_embeddings([text_to_embed])
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]
                    
                    # Convert embedding list to PostgreSQL array format
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    # Store in items table (legacy column)
                    await conn.execute("""
                        UPDATE items 
                        SET embedding = $2::vector,
                            updated_at = NOW()
                        WHERE id = $1
                    """, item['id'], embedding_str)
                    
                    # Also store in embeddings table
                    embedding_id = await conn.fetchval("""
                        INSERT INTO embeddings (
                            item_id, model_name, model_version, vector
                        ) VALUES ($1, $2, $3, $4::vector)
                        ON CONFLICT (item_id, model_name, model_version) 
                        DO UPDATE SET vector = $4::vector, updated_at = NOW()
                        RETURNING id
                    """, item['id'], 'text-embedding-ada-002', 'v1', embedding_str)
                    
                    # Update items table with embed_vector_id
                    await conn.execute("""
                        UPDATE items 
                        SET embed_vector_id = $2
                        WHERE id = $1
                    """, item['id'], embedding_id)
                    
                    print(f"  ✓ Generated embedding (dimension: {len(embedding)})")
                    success_count += 1
                else:
                    print(f"  ✗ Failed to generate embedding")
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                
        print(f"\nSuccessfully generated {success_count} embeddings!")
        
        # Check final state
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM items WHERE embedding IS NOT NULL
        """)
        print(f"Total items with embeddings: {count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(generate_embeddings())