#!/usr/bin/env python3
"""
Phase 2 API Testing: Verify dual endpoint support (ID + slug)
Tests that both old ID-based and new slug-based APIs work
"""

import asyncio
import json
from typing import Any, Dict

import aiohttp

API_BASE = "http://localhost:8000"


async def make_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make an HTTP request and return the response."""
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            return {
                "status": response.status,
                "data": await response.json() if response.content_type == 'application/json' else None,
                "text": await response.text() if response.content_type != 'application/json' else None
            }


async def test_content_urls_api():
    """Test the new content URL endpoints."""
    print("🔗 Testing Content URL APIs")
    print("=" * 60)
    
    tests = [
        # Test category content listing
        {
            "name": "List dev category content",
            "method": "GET",
            "url": f"{API_BASE}/api/content/category/dev",
            "expected_status": 200
        },
        {
            "name": "List media category content", 
            "method": "GET",
            "url": f"{API_BASE}/api/content/category/media",
            "expected_status": 200
        },
        # Test specific content by slug
        {
            "name": "Get content by category/slug",
            "method": "GET", 
            "url": f"{API_BASE}/api/content/dev/untitled",
            "expected_status": [200, 404]  # Might not exist
        },
        # Test popular content
        {
            "name": "Get popular content",
            "method": "GET",
            "url": f"{API_BASE}/api/content/popular",
            "expected_status": 200
        },
        # Test search
        {
            "name": "Search content",
            "method": "GET",
            "url": f"{API_BASE}/api/content/search?q=test",
            "expected_status": 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await make_request(test["method"], test["url"])
            expected = test["expected_status"]
            expected_list = expected if isinstance(expected, list) else [expected]
            
            if result["status"] in expected_list:
                print(f"✅ {test['name']}: {result['status']}")
                if result["data"] and "results" in result["data"]:
                    print(f"   Found {len(result['data']['results'])} items")
                passed += 1
            else:
                print(f"❌ {test['name']}: Expected {expected}, got {result['status']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test['name']}: Error - {str(e)}")
            failed += 1
    
    print(f"\n📊 Content URL API Results: {passed} passed, {failed} failed")
    return passed, failed


async def test_legacy_api_compatibility():
    """Test that old ID-based APIs still work."""
    print("\n🔄 Testing Legacy API Compatibility")
    print("=" * 60)
    
    # First, get an item to test with
    search_result = await make_request("GET", f"{API_BASE}/api/search?query=test&limit=1")
    
    if search_result["status"] != 200 or not search_result["data"]["results"]:
        print("⚠️  No items found to test legacy APIs")
        return 0, 0
    
    item_id = search_result["data"]["results"][0]["id"]
    print(f"📝 Testing with item ID: {item_id}")
    
    tests = [
        # Test item detail endpoint
        {
            "name": "Get item by ID",
            "method": "GET",
            "url": f"{API_BASE}/api/items/{item_id}",
            "expected_status": 200
        },
        # Test legacy redirect endpoint
        {
            "name": "Get legacy redirect",
            "method": "GET",
            "url": f"{API_BASE}/api/legacy-redirect/items/{item_id}",
            "expected_status": 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await make_request(test["method"], test["url"])
            
            if result["status"] == test["expected_status"]:
                print(f"✅ {test['name']}: {result['status']}")
                if test["name"] == "Get legacy redirect" and result["data"]:
                    print(f"   Redirects to: {result['data'].get('newUrl', 'N/A')}")
                passed += 1
            else:
                print(f"❌ {test['name']}: Expected {test['expected_status']}, got {result['status']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test['name']}: Error - {str(e)}")
            failed += 1
    
    print(f"\n📊 Legacy API Results: {passed} passed, {failed} failed")
    return passed, failed


async def test_admin_endpoints():
    """Test admin endpoints for content URL management."""
    print("\n🔧 Testing Admin Endpoints")
    print("=" * 60)
    
    tests = [
        {
            "name": "Get content URL stats",
            "method": "GET",
            "url": f"{API_BASE}/api/admin/content-urls/stats",
            "expected_status": 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await make_request(test["method"], test["url"])
            
            if result["status"] == test["expected_status"]:
                print(f"✅ {test['name']}: {result['status']}")
                if result["data"]:
                    stats = result["data"]
                    print(f"   Total URLs: {stats.get('total_urls', 'N/A')}")
                    print(f"   Categories: {stats.get('categories', 'N/A')}")
                passed += 1
            else:
                print(f"❌ {test['name']}: Expected {test['expected_status']}, got {result['status']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test['name']}: Error - {str(e)}")
            failed += 1
    
    print(f"\n📊 Admin API Results: {passed} passed, {failed} failed")
    return passed, failed


async def main():
    """Run all Phase 2 API tests."""
    print("🧪 Phase 2 API Testing Suite")
    print("=" * 60)
    
    # Check if backend is running
    try:
        health = await make_request("GET", f"{API_BASE}/api/health")
        if health["status"] != 200:
            print("❌ Backend is not running on http://localhost:8000")
            print("   Please start the backend first")
            return
    except Exception:
        print("❌ Cannot connect to backend on http://localhost:8000")
        print("   Please start the backend first")
        return
    
    print("✅ Backend is running\n")
    
    # Run all test suites
    total_passed = 0
    total_failed = 0
    
    # Test new content URL APIs
    passed, failed = await test_content_urls_api()
    total_passed += passed
    total_failed += failed
    
    # Test legacy API compatibility
    passed, failed = await test_legacy_api_compatibility()
    total_passed += passed
    total_failed += failed
    
    # Test admin endpoints
    passed, failed = await test_admin_endpoints()
    total_passed += passed
    total_failed += failed
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 All Phase 2 API tests passed!")
        print("✅ Backend is ready for Phase 3: Frontend route implementation")
    else:
        print(f"\n⚠️  {total_failed} tests failed. Fix these before proceeding to Phase 3")


if __name__ == "__main__":
    asyncio.run(main())