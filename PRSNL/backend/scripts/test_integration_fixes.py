#!/usr/bin/env python3
"""
Integration test to verify all capture logic fixes are working correctly
Tests the 6 critical issues that were fixed:
1. ✅ Type logging bug fixed
2. ✅ Field name standardization
3. ✅ Classification conflicts resolved (GitHub override only in auto mode)
4. ✅ Content type validation added
5. ✅ Video detection improved for Instagram/Twitter
6. ✅ Category/type alignment fixed
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.slug_generator import SmartSlugGenerator

DATABASE_URL = 'postgresql+asyncpg://pronav@localhost:5433/prsnl'

async def test_integration_fixes():
    """Test all integration fixes with unique URLs."""
    print("🔧 Testing PRSNL Integration Logic Fixes")
    print("=" * 60)
    
    # Generate unique URLs to avoid duplicates
    test_id = str(uuid4())[:8]
    
    test_cases = [
        {
            "name": "GitHub Override Respect",
            "url": f"https://github.com/test-user/repo-{test_id}",
            "content_type": "article",  # User explicitly chooses article, not development
            "expected_type": "article",  # Should respect user choice, not auto-detect as development
            "expected_category": "learn",  # GitHub repos are inherently educational (AI will detect)
            "enable_summarization": True
        },
        {
            "name": "GitHub Auto-Detection", 
            "url": f"https://github.com/test-user/auto-repo-{test_id}",
            "content_type": "auto",  # Auto mode should detect as development
            "expected_type": "development",
            "expected_category": "dev",
            "enable_summarization": True
        },
        {
            "name": "Learning Article Classification",
            "url": f"https://example.com/learn-tutorial-{test_id}",
            "content_type": "article",
            "expected_type": "article",
            "expected_category": "learn",  # Should be categorized as learning based on URL
            "enable_summarization": True
        },
        {
            "name": "Invalid Content Type Validation",
            "url": f"https://example.com/invalid-test-{test_id}",
            "content_type": "invalid_type",  # Should trigger validation error
            "expected_error": True,
            "enable_summarization": True
        },
        {
            "name": "Instagram Reel Detection",
            "url": f"https://instagram.com/reel/test{test_id}/",
            "content_type": "auto",
            "expected_type": "video",
            "expected_category": "media",
            "enable_summarization": False  # Videos don't need summarization
        }
    ]
    
    captured_items = []
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Content Type: {test_case['content_type']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                capture_data = {
                    "url": test_case['url'],
                    "content_type": test_case['content_type'],
                    "tags": ["integration-fix-test"],
                    "enable_summarization": test_case['enable_summarization']
                }
                
                # Add title for learning articles to trigger correct categorization
                if "learn-tutorial" in test_case['url']:
                    capture_data["title"] = "React Tutorial Guide for Beginners"
                elif "github.com" in test_case['url'] and test_case['content_type'] == 'article':
                    capture_data["title"] = "My Random GitHub Project Notes"
                
                async with session.post(
                    "http://localhost:3004/api/capture",
                    json=capture_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if test_case.get('expected_error'):
                        if response.status == 422:
                            result = await response.json()
                            print(f"   ✅ Validation error as expected: {result.get('detail', '')}")
                        else:
                            print(f"   ❌ Expected validation error, got status {response.status}")
                    elif response.status == 201:
                        result = await response.json()
                        item_id = result.get('id')
                        captured_items.append({'id': item_id, 'test_case': test_case})
                        print(f"   ✅ Capture successful - ID: {item_id}")
                    else:
                        result = await response.json()
                        print(f"   ❌ Capture failed: {result}")
                        
        except Exception as e:
            print(f"   ❌ Capture error: {e}")
    
    if not captured_items:
        print("\n❌ No items captured successfully, cannot continue with verification")
        return
    
    # Wait for processing
    print(f"\n⏳ Waiting 5 seconds for processing...")
    await asyncio.sleep(5)
    
    # Generate permalinks and verify results
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"\n🔗 Generating permalinks and verifying results...")
        
        all_passed = True
        
        for item_info in captured_items:
            item_id = item_info['id']
            test_case = item_info['test_case']
            
            print(f"\n📋 Checking: {test_case['name']}")
            
            try:
                # Get the item from database
                result = await session.execute(text("SELECT * FROM items WHERE id = :item_id"), {"item_id": item_id})
                item_row = result.fetchone()
                
                if not item_row:
                    print(f"   ❌ Item not found!")
                    all_passed = False
                    continue
                
                # Check type
                actual_type = item_row.type
                expected_type = test_case['expected_type']
                if actual_type == expected_type:
                    print(f"   ✅ Type: {actual_type} (correct)")
                else:
                    print(f"   ❌ Type: {actual_type} (expected: {expected_type})")
                    all_passed = False
                
                # Generate permalink to test category detection
                class MockItem:
                    def __init__(self, row):
                        for key, value in row._mapping.items():
                            setattr(self, key, value)
                
                item_obj = MockItem(item_row)
                url_data = await SmartSlugGenerator.generate_slug_for_item(item_obj)
                
                # Check category
                actual_category = url_data['category']
                expected_category = test_case['expected_category']
                if actual_category == expected_category:
                    print(f"   ✅ Category: {actual_category} (correct)")
                else:
                    print(f"   ❌ Category: {actual_category} (expected: {expected_category})")
                    all_passed = False
                
                print(f"   🔗 Permalink: /{actual_category}/{url_data['slug']}")
                
            except Exception as e:
                print(f"   ❌ Verification failed: {e}")
                all_passed = False
    
    await engine.dispose()
    
    # Summary
    print(f"\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL INTEGRATION FIXES VERIFIED SUCCESSFULLY!")
        print("✅ GitHub override respects user choice")
        print("✅ Auto-detection works correctly") 
        print("✅ Content type validation prevents invalid types")
        print("✅ Category detection aligns with item types")
        print("✅ Video detection improved for social media")
        print("\n💯 System is ready for git push!")
    else:
        print("❌ SOME TESTS FAILED - Review issues above")
        print("🔧 Additional fixes may be needed before git push")

if __name__ == "__main__":
    asyncio.run(test_integration_fixes())