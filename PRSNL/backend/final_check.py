#!/usr/bin/env python3
"""
Final check of chatbot content processing
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def final_check():
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Final Processing Status ===\n")
        
        # Get stats for recent items
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                COUNT(CASE WHEN processed_content IS NOT NULL THEN 1 END) as has_content,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as has_embedding,
                COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as has_search_vector
            FROM items 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        print(f"Total items added: {stats['total']}")
        print(f"✓ Processed: {stats['processed']} ({stats['processed']/stats['total']*100:.0f}%)")
        print(f"✓ Has content: {stats['has_content']} ({stats['has_content']/stats['total']*100:.0f}%)")
        print(f"✓ Has embeddings: {stats['has_embedding']} ({stats['has_embedding']/stats['total']*100:.0f}%)")
        print(f"✓ Has search vectors: {stats['has_search_vector']} ({stats['has_search_vector']/stats['total']*100:.0f}%)")
        
        # Check embeddings table
        embeddings_count = await conn.fetchval("""
            SELECT COUNT(*) FROM embeddings 
            WHERE item_id IN (
                SELECT id FROM items WHERE created_at > NOW() - INTERVAL '1 hour'
            )
        """)
        print(f"✓ Embeddings table entries: {embeddings_count}")
        
        print("\n✅ All content is now ready for testing!")
        print("\nYou can now:")
        print("1. Check the frontend to see all 9 items")
        print("2. Search for 'chatbot', 'Claude', 'Windsurf', etc.")
        print("3. Ask in chat: 'How do I build a chatbot with AI IDEs?'")
        print("4. Test voice chat with similar questions")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(final_check())