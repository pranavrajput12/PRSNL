#!/usr/bin/env python3
"""
Test Smart Scraper in production with real item processing
"""
import asyncio
import asyncpg
import os
from datetime import datetime
import uuid
import json

from dotenv import load_dotenv
load_dotenv()

async def test_smart_scraper_production():
    """Test smart scraper with real item processing"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    test_items = [
        {
            "title": "Example Domain (should use Jina)",
            "type": "website",
            "url": "https://example.com",
            "summary": "Simple example domain that should work with Jina"
        },
        {
            "title": "Anthropic Docs (should use Jina and save credit!)",
            "type": "website", 
            "url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering",
            "summary": "Complex site that should work with Jina first"
        },
        {
            "title": "HTTPBin HTML Test (should use Jina)",
            "type": "website",
            "url": "https://httpbin.org/html",
            "summary": "Test HTML page for scraping"
        }
    ]
    
    try:
        print("=== Testing Smart Scraper in Production ===\n")
        
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
                json.dumps({"tags": ["smart-scraper-test", "cost-saving"]})
            )
            
            created_items.append((item_id, test_item["type"], test_item["title"]))
            print(f"✓ Created item {i}: {result['id']}")
        
        print(f"\nWaiting for smart processing...")
        
        # Monitor processing
        for check_round in range(10):  # Check for 30 seconds
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
                        metadata
                    FROM items
                    WHERE id = $1::uuid
                """, str(item_id))
                
                status_emoji = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'processed': '✅',
                    'error': '❌'
                }.get(item['status'], '❓')
                
                print(f"  {status_emoji} {item['status']}", end="")
                if item['content_length']:
                    print(f" | {item['content_length']} chars", end="")
                
                # Check which scraper was used
                if item['metadata']:
                    try:
                        metadata = json.loads(item['metadata']) if isinstance(item['metadata'], str) else item['metadata']
                        scraper_method = metadata.get('scraping_method', 'unknown')
                        emoji = "📖" if scraper_method == "jina" else "🔥" if scraper_method == "firecrawl" else "❓"
                        print(f" | {emoji} {scraper_method}", end="")
                    except:
                        pass
                
                print(f" | {title[:40]}...")
                
                if item['status'] not in ['processed', 'error']:
                    all_processed = False
            
            if all_processed:
                print(f"\n🎉 All items processed!")
                break
        
        # Show final results
        print(f"\n=== Final Results ===")
        for item_id, item_type, title in created_items:
            item = await conn.fetchrow("""
                SELECT title, status, LENGTH(processed_content) as content_length, metadata
                FROM items WHERE id = $1::uuid
            """, str(item_id))
            
            if item and item['metadata']:
                try:
                    metadata = json.loads(item['metadata']) if isinstance(item['metadata'], str) else item['metadata']
                    scraper_method = metadata.get('scraping_method', 'unknown')
                    emoji = "📖" if scraper_method == "jina" else "🔥" if scraper_method == "firecrawl" else "❓"
                    
                    credit_saved = "💰 CREDIT SAVED!" if scraper_method == "jina" else "💳 Used credit"
                    
                    print(f"{emoji} {scraper_method.upper()}: {item['content_length']} chars - {credit_saved}")
                    print(f"   {item['title'][:60]}...")
                except Exception as e:
                    print(f"❓ {item['title']}: {item['status']} (metadata parse error)")
        
        print(f"\n📊 Check worker logs for cost savings stats!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_smart_scraper_production())