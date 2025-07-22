#!/usr/bin/env python3
"""
Generate embeddings for chatbot content items
"""
import asyncio
import asyncpg
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import after environment setup
from app.services.unified_ai_service import UnifiedAIService

async def generate_embeddings():
    """Generate embeddings for recently added items"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    ai_service = UnifiedAIService()
    
    try:
        print("=== Generating Embeddings for Chatbot Content ===\n")
        
        # Get items that need embeddings
        items = await conn.fetch("""
            SELECT id, title, 
                   COALESCE(processed_content, raw_content, summary) as content
            FROM items 
            WHERE embedding IS NULL
            AND created_at > NOW() - INTERVAL '1 hour'
            AND (processed_content IS NOT NULL OR raw_content IS NOT NULL OR summary IS NOT NULL)
            ORDER BY created_at DESC
        """)
        
        print(f"Found {len(items)} items needing embeddings\n")
        
        success_count = 0
        
        for idx, item in enumerate(items, 1):
            print(f"{idx}. Generating embedding for: {item['title'][:60]}...")
            
            try:
                # Prepare text for embedding
                text_to_embed = f"{item['title']} {item['content'] or ''}"
                
                # Generate embedding
                embeddings = await ai_service.generate_embeddings([text_to_embed[:2000]])
                
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]
                    
                    # Convert to PostgreSQL format
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    # Store in items table
                    await conn.execute("""
                        UPDATE items 
                        SET embedding = $2::vector,
                            updated_at = NOW()
                        WHERE id = $1
                    """, item['id'], embedding_str)
                    
                    # Also store in embeddings table
                    embedding_id = await conn.fetchval("""
                        INSERT INTO embeddings (
                            item_id, model_name, model_version, vector, embedding_type
                        ) VALUES ($1, $2, $3, $4::vector, $5)
                        ON CONFLICT (item_id, model_name, model_version, embedding_type) 
                        DO UPDATE SET vector = $4::vector, updated_at = NOW()
                        RETURNING id
                    """, item['id'], 'text-embedding-ada-002', 'v1', embedding_str, 'text')
                    
                    # Update embed_vector_id
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
                
        print(f"\n✓ Successfully generated {success_count} embeddings!")
        
        # Final check
        final_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as searchable
            FROM items 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        print(f"\nFinal Status:")
        print(f"  Total recent items: {final_stats['total_items']}")
        print(f"  With embeddings: {final_stats['with_embeddings']}")
        print(f"  Searchable: {final_stats['searchable']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(generate_embeddings())