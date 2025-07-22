#!/usr/bin/env python3
"""
Check the processing status of recently added chatbot content
"""
import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
import json

from dotenv import load_dotenv

load_dotenv()

async def check_content_processing():
    """Check if content has been processed with embeddings, vectors, etc."""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Checking Content Processing Status ===\n")
        
        # Get recently added items (last hour)
        recent_items = await conn.fetch("""
            SELECT 
                i.id, 
                i.title, 
                i.type,
                i.status,
                i.url,
                i.created_at,
                i.processed_content IS NOT NULL as has_processed_content,
                i.raw_content IS NOT NULL as has_raw_content,
                i.summary IS NOT NULL as has_summary,
                i.embedding IS NOT NULL as has_embedding,
                i.search_vector IS NOT NULL as has_search_vector,
                i.embed_vector_id IS NOT NULL as has_embed_vector_id,
                i.metadata
            FROM items i
            WHERE i.created_at > NOW() - INTERVAL '1 hour'
            ORDER BY i.created_at DESC
        """)
        
        print(f"Found {len(recent_items)} recently added items\n")
        
        # Summary statistics
        stats = {
            'total': len(recent_items),
            'processed': 0,
            'has_content': 0,
            'has_embedding': 0,
            'has_search_vector': 0,
            'has_embeddings_table_entry': 0
        }
        
        # Check each item
        for idx, item in enumerate(recent_items, 1):
            print(f"{idx}. {item['title'][:60]}...")
            print(f"   Type: {item['type']}")
            print(f"   Status: {item['status']}")
            print(f"   URL: {item['url'][:50]}...")
            print(f"   Created: {item['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check processing status
            print(f"   Processing Status:")
            print(f"     - Has raw content: {'✓' if item['has_raw_content'] else '✗'}")
            print(f"     - Has processed content: {'✓' if item['has_processed_content'] else '✗'}")
            print(f"     - Has summary: {'✓' if item['has_summary'] else '✗'}")
            print(f"     - Has embedding (legacy): {'✓' if item['has_embedding'] else '✗'}")
            print(f"     - Has search vector: {'✓' if item['has_search_vector'] else '✗'}")
            print(f"     - Has embed_vector_id: {'✓' if item['has_embed_vector_id'] else '✗'}")
            
            # Update stats
            if item['status'] == 'processed':
                stats['processed'] += 1
            if item['has_processed_content'] or item['has_raw_content']:
                stats['has_content'] += 1
            if item['has_embedding']:
                stats['has_embedding'] += 1
            if item['has_search_vector']:
                stats['has_search_vector'] += 1
                
            # Check embeddings table
            if item['has_embed_vector_id']:
                embedding_info = await conn.fetchrow("""
                    SELECT 
                        e.model_name,
                        e.model_version,
                        e.embedding_type,
                        e.vector_norm,
                        e.created_at,
                        ARRAY_LENGTH(e.vector, 1) as vector_dimensions
                    FROM embeddings e
                    WHERE e.id = $1
                """, item['embed_vector_id'])
                
                if embedding_info:
                    stats['has_embeddings_table_entry'] += 1
                    print(f"     - Embeddings table entry: ✓")
                    print(f"       Model: {embedding_info['model_name']}")
                    print(f"       Type: {embedding_info['embedding_type']}")
                    print(f"       Dimensions: {embedding_info['vector_dimensions']}")
            
            # Check metadata
            metadata = item['metadata']
            if metadata:
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                if isinstance(metadata, dict) and 'tags' in metadata and isinstance(metadata['tags'], list):
                    print(f"     - Tags: {', '.join(metadata['tags'][:5])}")
            
            print()
        
        # Overall summary
        print("=== Summary Statistics ===")
        print(f"Total items: {stats['total']}")
        print(f"Processed status: {stats['processed']} ({stats['processed']/stats['total']*100:.1f}%)")
        print(f"Has content: {stats['has_content']} ({stats['has_content']/stats['total']*100:.1f}%)")
        print(f"Has embeddings: {stats['has_embedding']} ({stats['has_embedding']/stats['total']*100:.1f}%)")
        print(f"Has search vectors: {stats['has_search_vector']} ({stats['has_search_vector']/stats['total']*100:.1f}%)")
        print(f"Has embeddings table entries: {stats['has_embeddings_table_entry']} ({stats['has_embeddings_table_entry']/stats['total']*100:.1f}%)")
        
        # Check if capture engine is needed
        if stats['has_content'] < stats['total']:
            print(f"\n⚠️  {stats['total'] - stats['has_content']} items need content fetching")
            print("   The capture engine should process these automatically")
            print("   Or you can trigger processing through the frontend")
            
        if stats['has_embedding'] < stats['has_content']:
            print(f"\n⚠️  {stats['has_content'] - stats['has_embedding']} items with content need embeddings")
            
        # Check overall embedding statistics
        print("\n=== Overall Embedding Statistics ===")
        embedding_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_embeddings,
                COUNT(DISTINCT item_id) as unique_items,
                COUNT(DISTINCT model_name) as models_used
            FROM embeddings
        """)
        
        print(f"Total embeddings in system: {embedding_stats['total_embeddings']}")
        print(f"Unique items with embeddings: {embedding_stats['unique_items']}")
        print(f"Different models used: {embedding_stats['models_used']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_content_processing())