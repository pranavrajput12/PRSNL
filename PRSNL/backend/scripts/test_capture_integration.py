#!/usr/bin/env python3
"""
Test script to verify capture integration logic works correctly
"""

import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.slug_generator import SmartSlugGenerator
from app.db.models import Item

DATABASE_URL = 'postgresql+asyncpg://pronav@localhost:5433/prsnl'

async def test_capture_integration():
    print("🧪 Testing PRSNL Capture Integration Logic")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=test123",
            "content_type": "video",
            "expected_type": "video",
            "expected_section": "videos",
            "expected_category": "media"
        },
        {
            "name": "GitHub Repository", 
            "url": "https://github.com/user/repo",
            "content_type": "development",
            "expected_type": "development", 
            "expected_section": "code-cortex",
            "expected_category": "dev"
        },
        {
            "name": "Learning Article",
            "url": "https://example.com/learn-react-tutorial-advanced",
            "content_type": "article",
            "expected_type": "article",
            "expected_section": "timeline",
            "expected_category": "learn"
        },
        {
            "name": "Vimeo Video",
            "url": "https://vimeo.com/123456789",
            "content_type": "video", 
            "expected_type": "video",
            "expected_section": "videos",
            "expected_category": "media"
        },
        {
            "name": "Auto-detect GitHub",
            "url": "https://github.com/microsoft/vscode",
            "content_type": "auto",
            "expected_type": "development",
            "expected_section": "code-cortex", 
            "expected_category": "dev"
        }
    ]
    
    captured_items = []
    
    # Test each capture scenario
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Content Type: {test_case['content_type']}")
        
        try:
            # Send capture request
            async with aiohttp.ClientSession() as session:
                capture_data = {
                    "url": test_case['url'],
                    "content_type": test_case['content_type'],
                    "tags": ["integration-test"],
                    "enable_summarization": True  # Enable summarization to preserve content types
                }
                
                async with session.post(
                    "http://localhost:3004/api/capture",
                    json=capture_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        item_id = result.get('id')
                        captured_items.append({'id': item_id, 'test_case': test_case})
                        print(f"   ✅ Capture successful - ID: {item_id}")
                    elif response.status == 400:
                        # Might be duplicate
                        result = await response.json()
                        if "already exists" in result.get('detail', ''):
                            print(f"   ⚠️  URL already exists (expected for some tests)")
                        else:
                            print(f"   ❌ Capture failed: {result}")
                    else:
                        print(f"   ❌ Capture failed with status {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Capture error: {e}")
    
    # Wait for processing
    print(f"\n⏳ Waiting 10 seconds for processing...")
    await asyncio.sleep(10)
    
    # Generate permalinks for captured items
    print(f"\n🔗 Generating permalinks for captured items...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        for item_info in captured_items:
            item_id = item_info['id']
            try:
                # Get the item from database
                result = await session.execute(text("SELECT * FROM items WHERE id = :item_id"), {"item_id": item_id})
                item_row = result.fetchone()
                if item_row:
                    # Create a mock Item object for the slug generator
                    class MockItem:
                        def __init__(self, row):
                            for key, value in row._mapping.items():
                                setattr(self, key, value)
                    
                    item_obj = MockItem(item_row)
                    url_data = await SmartSlugGenerator.generate_slug_for_item(item_obj)
                    print(f"   🔗 Generated permalink for {item_id}: /{url_data['category']}/{url_data['slug']}")
            except Exception as e:
                print(f"   ❌ Failed to generate permalink for {item_id}: {e}")
    
        # Verify database state immediately after permalink generation
        print(f"\n🔍 Verifying Database State")
        print("=" * 40)
        for item_info in captured_items:
            item_id = item_info['id']
            test_case = item_info['test_case']
            
            print(f"\n📋 Checking: {test_case['name']}")
            
            # Get item details (refresh after permalink generation)
            result = await session.execute(text("""
                SELECT i.id, i.title, i.type, i.platform, i.video_url, i.url,
                       cu.category, cu.slug
                FROM items i
                LEFT JOIN content_urls cu ON cu.content_id = i.id
                WHERE i.id = :item_id
            """), {"item_id": item_id})
            
            item = result.fetchone()
            if not item:
                print(f"   ❌ Item not found in database!")
                continue
                
            # Check type
            if item.type == test_case['expected_type']:
                print(f"   ✅ Type: {item.type} (correct)")
            else:
                print(f"   ❌ Type: {item.type} (expected: {test_case['expected_type']})")
            
            # Check category
            if item.category == test_case['expected_category']:
                print(f"   ✅ Category: {item.category} (correct)")
            elif item.category is None:
                print(f"   ❌ Category: None (expected: {test_case['expected_category']})")
            else:
                print(f"   ❌ Category: {item.category} (expected: {test_case['expected_category']})")
            
            # Check video specifics
            if test_case['expected_type'] == 'video':
                if item.video_url:
                    print(f"   ✅ Video URL: {item.video_url}")
                else:
                    print(f"   ❌ Video URL: Missing")
                    
                if item.platform in ['youtube', 'vimeo']:
                    print(f"   ✅ Platform: {item.platform}")
                else:
                    print(f"   ❌ Platform: {item.platform} (expected youtube/vimeo)")
    
    await engine.dispose()
    
    # Test section visibility
    print(f"\n🎯 Testing Section Visibility")
    print("=" * 40)
    
    # Test videos endpoint
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/timeline?limit=100") as response:
                if response.status == 200:
                    data = await response.json()
                    video_items = [item for item in data['items'] if item.get('type') == 'video']
                    print(f"📺 Videos in timeline: {len(video_items)} items")
                    
                    # Check if our test videos appear
                    test_video_count = 0
                    for item in video_items:
                        if any(tag == 'integration-test' for tag in item.get('tags', [])):
                            test_video_count += 1
                    print(f"   📺 Test videos visible: {test_video_count}")
                else:
                    print(f"   ❌ Timeline API failed: {response.status}")
    except Exception as e:
        print(f"   ❌ Timeline test error: {e}")
    
    # Test development endpoint  
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/development/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    dev_count = data.get('total_items', 0)
                    print(f"💻 Development items: {dev_count} total")
                else:
                    print(f"   ❌ Development API failed: {response.status}")
    except Exception as e:
        print(f"   ❌ Development test error: {e}")
    
    print(f"\n" + "=" * 60)
    print("🏁 Integration Test Complete")
    print("Check the results above for any ❌ failures that need fixing")

if __name__ == "__main__":
    asyncio.run(test_capture_integration())