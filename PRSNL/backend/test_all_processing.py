#!/usr/bin/env python3
"""
Test all processing types: Website, YouTube, PDF
"""
import asyncio
import asyncpg
import os
from datetime import datetime
import uuid
import json

from dotenv import load_dotenv
load_dotenv()

async def test_processing_types():
    """Test all processing types"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    test_items = [
        {
            "title": "Claude AI Documentation - Advanced Features",
            "type": "website",
            "url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering",
            "summary": "Complete guide to prompt engineering with Claude"
        },
        {
            "title": "Building AI Applications Tutorial",
            "type": "youtube", 
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Example YouTube URL
            "summary": "YouTube tutorial on building AI applications"
        },
        {
            "title": "AI Research Paper Sample",
            "type": "pdf",
            "url": "https://arxiv.org/pdf/1706.03762.pdf",  # Attention is All You Need paper
            "summary": "Transformer architecture research paper"
        }
    ]
    
    try:
        print("=== Testing All Processing Types ===\n")
        
        created_items = []
        
        for i, test_item in enumerate(test_items, 1):
            item_id = uuid.uuid4()
            
            result = await conn.fetchrow("""
                INSERT INTO items (
                    id, title, type, url, summary, status, user_id, 
                    metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
                ) RETURNING id
            """, 
                str(item_id),
                test_item["title"],
                test_item["type"],
                test_item["url"],
                test_item["summary"],
                "pending",
                str(uuid.uuid4()),  # dummy user_id
                json.dumps({"tags": ["test", "processing", test_item["type"]]})
            )
            
            created_items.append((item_id, test_item["type"], test_item["title"]))
            print(f"✓ Created {test_item['type']} item: {result['id']}")
            print(f"  URL: {test_item['url']}")
        
        print(f"\nWaiting for processing... (checking every 3 seconds)")
        
        # Monitor all items
        for check_round in range(20):  # Check for 60 seconds
            await asyncio.sleep(3)
            
            print(f"\n[Round {check_round + 1}] Processing Status:")
            all_processed = True
            
            for item_id, item_type, title in created_items:
                item = await conn.fetchrow("""
                    SELECT 
                        id, title, status,
                        processed_content IS NOT NULL as has_content,
                        LENGTH(processed_content) as content_length,
                        embedding IS NOT NULL as has_embedding,
                        search_vector IS NOT NULL as has_search_vector
                    FROM items
                    WHERE id = $1::uuid
                """, str(item_id))
                
                status_emoji = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'processed': '✅',
                    'error': '❌'
                }.get(item['status'], '❓')
                
                print(f"  {status_emoji} {item_type.upper()}: {item['status']}", end="")
                if item['content_length']:
                    print(f" | {item['content_length']} chars", end="")
                print(f" | Embed: {'✓' if item['has_embedding'] else '✗'}")
                
                if item['status'] not in ['processed', 'error']:
                    all_processed = False
                    
                # Show content preview for processed items
                if item['status'] == 'processed' and item['content_length'] and item['content_length'] > 50:
                    content = await conn.fetchval("""
                        SELECT processed_content FROM items WHERE id = $1::uuid
                    """, str(item_id))
                    print(f"    Preview: {content[:100]}...")
            
            if all_processed:
                print(f"\n🎉 All items processed!")
                break
        else:
            print(f"\n⚠️  Some items still processing after 60 seconds")
        
        # Check worker activity
        print(f"\n=== Worker Activity ===")
        import subprocess
        result = subprocess.run(['tail', '-20', 'production_worker.log'], 
                              capture_output=True, text=True,
                              cwd='/Users/pronav/Personal Knowledge Base/PRSNL/backend')
        
        recent_logs = result.stdout.strip().split('\n')[-10:]  # Last 10 lines
        for log_line in recent_logs:
            if any(keyword in log_line for keyword in ['Processing:', '✓', '❌', 'Error']):
                print(f"  {log_line}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_processing_types())