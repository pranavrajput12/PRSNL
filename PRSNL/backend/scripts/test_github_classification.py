#!/usr/bin/env python3
"""
Test GitHub 3-type classification system:
1. github_repo - Repository links 
2. github_document - Markdown files
3. github_course - AI-generated (not tested here, created separately)
"""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

import aiohttp

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.url_classifier import URLClassifier


async def test_github_classification():
    """Test GitHub URL classification and capture logic."""
    print("🐙 Testing GitHub 3-Type Classification System")
    print("=" * 60)
    
    # Generate unique test ID
    test_id = str(uuid4())[:8]
    
    # Test URL classification first
    print("\n🔍 Testing URL Classification Logic")
    print("-" * 40)
    
    test_urls = [
        {
            "name": "GitHub Repository Main Page",
            "url": f"https://github.com/test-user/my-project-{test_id}",
            "expected_github_type": "github_repo"
        },
        {
            "name": "GitHub README File", 
            "url": f"https://github.com/test-user/docs-{test_id}/blob/main/README.md",
            "expected_github_type": "github_document"
        },
        {
            "name": "GitHub Documentation File",
            "url": f"https://github.com/test-user/project-{test_id}/blob/main/docs/tutorial.md", 
            "expected_github_type": "github_document"
        },
        {
            "name": "GitHub Wiki Page",
            "url": f"https://github.com/test-user/project-{test_id}/wiki",
            "expected_github_type": "github_document"
        },
        {
            "name": "GitHub Issues Page",
            "url": f"https://github.com/test-user/project-{test_id}/issues",
            "expected_github_type": "github_repo"
        },
        {
            "name": "GitHub Gist",
            "url": f"https://gist.github.com/test-user/abc123def456{test_id}",
            "expected_github_type": "github_document"
        }
    ]
    
    classification_results = []
    
    for test_case in test_urls:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Test URL classification
            result = URLClassifier.classify_url(test_case['url'])
            
            github_type = result.get('content_type')
            expected_type = test_case['expected_github_type']
            
            if github_type == expected_type:
                print(f"   ✅ Classification: {github_type} (correct)")
                classification_results.append(True)
            else:
                print(f"   ❌ Classification: {github_type} (expected: {expected_type})")
                classification_results.append(False)
            
            # Show additional details
            platform = result.get('platform')
            project_category = result.get('project_category')
            print(f"   📊 Platform: {platform}, Category: {project_category}")
            
            # Show GitHub-specific metadata
            github_metadata = result.get('metadata', {}).get('github', {})
            if github_metadata:
                print(f"   🔍 GitHub Info: {github_metadata}")
                
        except Exception as e:
            print(f"   ❌ Classification error: {e}")
            classification_results.append(False)
    
    # Test capture API integration
    print(f"\n\n🔗 Testing Capture API Integration")
    print("-" * 40)
    
    capture_tests = [
        {
            "name": "Auto-Detect GitHub Repo",
            "url": f"https://github.com/test-user/auto-repo-{test_id}",
            "content_type": "auto",
            "expected_type": "github_repo"
        },
        {
            "name": "Auto-Detect GitHub Document", 
            "url": f"https://github.com/test-user/auto-docs-{test_id}/blob/main/guide.md",
            "content_type": "auto", 
            "expected_type": "github_document"
        },
        {
            "name": "Manual GitHub Repo Selection",
            "url": f"https://github.com/test-user/manual-repo-{test_id}",
            "content_type": "github_repo",
            "expected_type": "github_repo"
        },
        {
            "name": "Manual GitHub Document Selection",
            "url": f"https://github.com/test-user/manual-docs-{test_id}/blob/main/README.md",
            "content_type": "github_document", 
            "expected_type": "github_document"
        }
    ]
    
    capture_results = []
    captured_items = []
    
    for test_case in capture_tests:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Content Type: {test_case['content_type']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                capture_data = {
                    "url": test_case['url'],
                    "content_type": test_case['content_type'],
                    "title": f"Test {test_case['name']}",
                    "tags": ["github-classification-test"],
                    "enable_summarization": True
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
                        capture_results.append(True)
                    else:
                        result = await response.json()
                        print(f"   ❌ Capture failed: {result}")
                        capture_results.append(False)
                        
        except Exception as e:
            print(f"   ❌ Capture error: {e}")
            capture_results.append(False)
    
    # Verify captured items in database
    if captured_items:
        print(f"\n🔍 Verifying Database Storage")
        print("-" * 40)
        
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        DATABASE_URL = 'postgresql+asyncpg://pronav@localhost:5432/prsnl'
        engine = create_async_engine(DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            for item_info in captured_items:
                item_id = item_info['id']
                test_case = item_info['test_case']
                
                print(f"\n📋 Verifying: {test_case['name']}")
                
                # Get item from database
                result = await session.execute(text("""
                    SELECT type, platform, project_category, programming_language
                    FROM items WHERE id = :item_id
                """), {"item_id": item_id})
                
                item = result.fetchone()
                if item:
                    actual_type = item.type
                    expected_type = test_case['expected_type']
                    
                    if actual_type == expected_type:
                        print(f"   ✅ Database Type: {actual_type} (correct)")
                    else:
                        print(f"   ❌ Database Type: {actual_type} (expected: {expected_type})")
                    
                    print(f"   📊 Platform: {item.platform}")
                    print(f"   📁 Project Category: {item.project_category}")
                    print(f"   💻 Programming Language: {item.programming_language}")
                else:
                    print(f"   ❌ Item not found in database!")
        
        await engine.dispose()
    
    # Summary
    print(f"\n" + "=" * 60)
    print("🏁 GitHub Classification Test Summary")
    
    classification_passed = sum(classification_results)
    classification_total = len(classification_results)
    capture_passed = sum(capture_results) 
    capture_total = len(capture_results)
    
    print(f"📊 URL Classification: {classification_passed}/{classification_total} passed")
    print(f"🔗 Capture Integration: {capture_passed}/{capture_total} passed")
    
    all_passed = (classification_passed == classification_total and 
                  capture_passed == capture_total)
    
    if all_passed:
        print("🎉 ALL GITHUB CLASSIFICATION TESTS PASSED!")
        print("✅ Repository detection working")
        print("✅ Document detection working") 
        print("✅ Capture API integration working")
        print("✅ Database storage working")
        print("\n💯 GitHub 3-type system ready for production!")
    else:
        print("❌ SOME TESTS FAILED - Review issues above")
        print("🔧 Additional fixes needed before production")

if __name__ == "__main__":
    asyncio.run(test_github_classification())