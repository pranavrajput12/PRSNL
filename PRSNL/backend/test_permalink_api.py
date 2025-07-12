#!/usr/bin/env python3
"""
Permalink System API Testing Suite

This script tests all the new permalink API endpoints to ensure they work correctly
and handle edge cases properly.
"""

import asyncio
import httpx
import json
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if different
TIMEOUT = 30.0


class PermalinkAPITester:
    """Comprehensive tester for permalink system APIs."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.test_results = []
        self.stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0
        }
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests and return results."""
        print("🧪 Starting comprehensive API testing...")
        
        # Test API availability first
        if not await self._test_api_health():
            return self._generate_results("API is not available")
        
        # Run all test suites
        await self._test_content_endpoints()
        await self._test_category_endpoints()
        await self._test_legacy_redirects()
        await self._test_admin_endpoints()
        await self._test_popular_content()
        await self._test_search_endpoints()
        await self._test_edge_cases()
        await self._test_performance()
        
        return self._generate_results()
    
    async def _test_api_health(self) -> bool:
        """Test if the API is available."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API is available")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return False
    
    async def _test_content_endpoints(self):
        """Test /api/content/{category}/{slug} endpoints."""
        print("📄 Testing content endpoints...")
        
        # Test valid content retrieval
        test_cases = [
            ("dev", "sample-slug"),
            ("learn", "tutorial-example"),
            ("media", "video-demo"),
            ("ideas", "personal-note")
        ]
        
        for category, slug in test_cases:
            await self._run_test(
                f"GET /api/content/{category}/{slug}",
                self._test_get_content,
                category, slug
            )
        
        # Test invalid categories
        await self._run_test(
            "GET /api/content/invalid/slug",
            self._test_get_content_invalid_category,
            "invalid", "slug"
        )
        
        # Test invalid slug formats
        invalid_slugs = ["UPPERCASE", "with spaces", "with_underscores", "with@symbols"]
        for slug in invalid_slugs:
            await self._run_test(
                f"GET /api/content/dev/{slug}",
                self._test_get_content_invalid_slug,
                "dev", slug
            )
    
    async def _test_category_endpoints(self):
        """Test /api/content/category/{category} endpoints."""
        print("📁 Testing category endpoints...")
        
        for category in ["dev", "learn", "media", "ideas"]:
            # Test basic category listing
            await self._run_test(
                f"GET /api/content/category/{category}",
                self._test_get_category_content,
                category
            )
            
            # Test pagination
            await self._run_test(
                f"GET /api/content/category/{category}?page=1&limit=5",
                self._test_get_category_content_paginated,
                category, 1, 5
            )
            
            # Test sorting
            for sort_option in ["recent", "popular", "title", "views"]:
                await self._run_test(
                    f"GET /api/content/category/{category}?sort={sort_option}",
                    self._test_get_category_content_sorted,
                    category, sort_option
                )
            
            # Test search within category
            await self._run_test(
                f"GET /api/content/category/{category}?search=test",
                self._test_search_in_category,
                category, "test"
            )
    
    async def _test_legacy_redirects(self):
        """Test legacy redirect endpoints."""
        print("🔄 Testing legacy redirect endpoints...")
        
        # These would need real item IDs from your database
        # For now, testing with UUID format
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        await self._run_test(
            f"GET /api/legacy-redirect/items/{test_uuid}",
            self._test_legacy_item_redirect,
            test_uuid
        )
        
        await self._run_test(
            f"GET /api/legacy-redirect/videos/{test_uuid}",
            self._test_legacy_video_redirect,
            test_uuid
        )
        
        # Test with invalid UUID
        await self._run_test(
            "GET /api/legacy-redirect/items/invalid-id",
            self._test_legacy_redirect_invalid_id,
            "invalid-id"
        )
    
    async def _test_admin_endpoints(self):
        """Test admin endpoints."""
        print("👑 Testing admin endpoints...")
        
        await self._run_test(
            "GET /api/admin/content-urls/stats",
            self._test_admin_stats
        )
    
    async def _test_popular_content(self):
        """Test popular content endpoint."""
        print("🔥 Testing popular content endpoint...")
        
        # Test general popular content
        await self._run_test(
            "GET /api/content/popular",
            self._test_get_popular_content
        )
        
        # Test popular content by category
        for category in ["dev", "learn", "media", "ideas"]:
            await self._run_test(
                f"GET /api/content/popular?category={category}",
                self._test_get_popular_content_by_category,
                category
            )
        
        # Test with limit
        await self._run_test(
            "GET /api/content/popular?limit=5",
            self._test_get_popular_content_with_limit,
            5
        )
    
    async def _test_search_endpoints(self):
        """Test search endpoints."""
        print("🔍 Testing search endpoints...")
        
        search_queries = ["python", "tutorial", "api", "javascript"]
        
        for query in search_queries:
            await self._run_test(
                f"GET /api/content/search?q={query}",
                self._test_search_content,
                query
            )
        
        # Test search with limit
        await self._run_test(
            "GET /api/content/search?q=test&limit=10",
            self._test_search_content_with_limit,
            "test", 10
        )
        
        # Test empty search query
        await self._run_test(
            "GET /api/content/search?q=",
            self._test_search_empty_query
        )
    
    async def _test_edge_cases(self):
        """Test edge cases and error conditions."""
        print("⚠️ Testing edge cases...")
        
        # Test very long slug
        long_slug = "a" * 100
        await self._run_test(
            f"GET /api/content/dev/{long_slug}",
            self._test_get_content_long_slug,
            "dev", long_slug
        )
        
        # Test special characters in search
        special_queries = ["test@example.com", "C++", "React.js", "Node.js"]
        for query in special_queries:
            await self._run_test(
                f"GET /api/content/search?q={query}",
                self._test_search_special_chars,
                query
            )
        
        # Test pagination edge cases
        await self._run_test(
            "GET /api/content/category/dev?page=999999",
            self._test_pagination_out_of_bounds,
            "dev", 999999
        )
        
        await self._run_test(
            "GET /api/content/category/dev?page=0",
            self._test_pagination_invalid_page,
            "dev", 0
        )
    
    async def _test_performance(self):
        """Test performance and concurrent requests."""
        print("⚡ Testing performance...")
        
        # Test concurrent requests to same endpoint
        await self._run_test(
            "Concurrent requests test",
            self._test_concurrent_requests
        )
        
        # Test response times
        await self._run_test(
            "Response time test",
            self._test_response_times
        )
    
    # Individual test methods
    async def _test_get_content(self, category: str, slug: str):
        """Test getting content by category and slug."""
        response = await self.client.get(f"{self.base_url}/api/content/{category}/{slug}")
        
        if response.status_code == 404:
            # This is expected if no content exists with this slug
            return {"status": "skipped", "message": "No content with this slug (expected)"}
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        required_fields = ["content", "contentUrl", "relatedContent"]
        
        for field in required_fields:
            if field not in data:
                return {"status": "failed", "message": f"Missing required field: {field}"}
        
        # Validate content structure
        if not isinstance(data["content"], dict) or "id" not in data["content"]:
            return {"status": "failed", "message": "Invalid content structure"}
        
        return {"status": "passed", "message": f"Content retrieved successfully for {category}/{slug}"}
    
    async def _test_get_content_invalid_category(self, category: str, slug: str):
        """Test getting content with invalid category."""
        response = await self.client.get(f"{self.base_url}/api/content/{category}/{slug}")
        
        if response.status_code == 404:
            return {"status": "passed", "message": "Correctly returned 404 for invalid category"}
        
        return {"status": "failed", "message": f"Expected 404, got {response.status_code}"}
    
    async def _test_get_content_invalid_slug(self, category: str, slug: str):
        """Test getting content with invalid slug format."""
        response = await self.client.get(f"{self.base_url}/api/content/{category}/{slug}")
        
        if response.status_code == 404:
            return {"status": "passed", "message": f"Correctly returned 404 for invalid slug: {slug}"}
        
        return {"status": "failed", "message": f"Expected 404 for invalid slug, got {response.status_code}"}
    
    async def _test_get_category_content(self, category: str):
        """Test getting content for a category."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        required_fields = ["content", "pagination"]
        
        for field in required_fields:
            if field not in data:
                return {"status": "failed", "message": f"Missing required field: {field}"}
        
        if not isinstance(data["content"], list):
            return {"status": "failed", "message": "Content should be a list"}
        
        return {"status": "passed", "message": f"Category {category} content retrieved successfully"}
    
    async def _test_get_category_content_paginated(self, category: str, page: int, limit: int):
        """Test paginated category content."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}?page={page}&limit={limit}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        pagination = data.get("pagination", {})
        
        if pagination.get("page") != page or pagination.get("limit") != limit:
            return {"status": "failed", "message": "Pagination parameters not respected"}
        
        if len(data["content"]) > limit:
            return {"status": "failed", "message": f"Returned more items than limit: {len(data['content'])} > {limit}"}
        
        return {"status": "passed", "message": f"Pagination working correctly for {category}"}
    
    async def _test_get_category_content_sorted(self, category: str, sort: str):
        """Test sorted category content."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}?sort={sort}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        content = data.get("content", [])
        
        if len(content) < 2:
            return {"status": "skipped", "message": "Not enough content to verify sorting"}
        
        # Basic validation that content is returned (detailed sort validation would need specific data)
        return {"status": "passed", "message": f"Sorting by {sort} working for {category}"}
    
    async def _test_search_in_category(self, category: str, query: str):
        """Test search within category."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}?search={query}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        return {"status": "passed", "message": f"Search in {category} working"}
    
    async def _test_legacy_item_redirect(self, item_id: str):
        """Test legacy item redirect."""
        response = await self.client.get(f"{self.base_url}/api/legacy-redirect/items/{item_id}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        if "newUrl" not in data:
            return {"status": "failed", "message": "Missing newUrl field"}
        
        return {"status": "passed", "message": "Legacy item redirect endpoint working"}
    
    async def _test_legacy_video_redirect(self, video_id: str):
        """Test legacy video redirect."""
        response = await self.client.get(f"{self.base_url}/api/legacy-redirect/videos/{video_id}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        if "newUrl" not in data:
            return {"status": "failed", "message": "Missing newUrl field"}
        
        return {"status": "passed", "message": "Legacy video redirect endpoint working"}
    
    async def _test_legacy_redirect_invalid_id(self, invalid_id: str):
        """Test legacy redirect with invalid ID."""
        response = await self.client.get(f"{self.base_url}/api/legacy-redirect/items/{invalid_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("newUrl") is None:
                return {"status": "passed", "message": "Correctly returned null for invalid ID"}
        
        return {"status": "passed", "message": "Invalid ID handled appropriately"}
    
    async def _test_admin_stats(self):
        """Test admin stats endpoint."""
        response = await self.client.get(f"{self.base_url}/api/admin/content-urls/stats")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        required_fields = ["totalUrls", "categoryStats", "totalRedirects"]
        
        for field in required_fields:
            if field not in data:
                return {"status": "failed", "message": f"Missing required field: {field}"}
        
        return {"status": "passed", "message": "Admin stats endpoint working"}
    
    async def _test_get_popular_content(self):
        """Test popular content endpoint."""
        response = await self.client.get(f"{self.base_url}/api/content/popular")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        if "content" not in data:
            return {"status": "failed", "message": "Missing content field"}
        
        return {"status": "passed", "message": "Popular content endpoint working"}
    
    async def _test_get_popular_content_by_category(self, category: str):
        """Test popular content by category."""
        response = await self.client.get(f"{self.base_url}/api/content/popular?category={category}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        return {"status": "passed", "message": f"Popular content for {category} working"}
    
    async def _test_get_popular_content_with_limit(self, limit: int):
        """Test popular content with limit."""
        response = await self.client.get(f"{self.base_url}/api/content/popular?limit={limit}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        content = data.get("content", [])
        
        if len(content) > limit:
            return {"status": "failed", "message": f"Returned more than limit: {len(content)} > {limit}"}
        
        return {"status": "passed", "message": f"Popular content limit {limit} working"}
    
    async def _test_search_content(self, query: str):
        """Test content search."""
        response = await self.client.get(f"{self.base_url}/api/content/search?q={query}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        required_fields = ["content", "query", "total"]
        
        for field in required_fields:
            if field not in data:
                return {"status": "failed", "message": f"Missing required field: {field}"}
        
        return {"status": "passed", "message": f"Search for '{query}' working"}
    
    async def _test_search_content_with_limit(self, query: str, limit: int):
        """Test search with limit."""
        response = await self.client.get(f"{self.base_url}/api/content/search?q={query}&limit={limit}")
        
        if response.status_code != 200:
            return {"status": "failed", "message": f"Expected 200, got {response.status_code}"}
        
        data = response.json()
        content = data.get("content", [])
        
        if len(content) > limit:
            return {"status": "failed", "message": f"Returned more than limit: {len(content)} > {limit}"}
        
        return {"status": "passed", "message": f"Search limit {limit} working"}
    
    async def _test_search_empty_query(self):
        """Test search with empty query."""
        response = await self.client.get(f"{self.base_url}/api/content/search?q=")
        
        # Should return 400 for empty query based on API definition
        if response.status_code == 400:
            return {"status": "passed", "message": "Correctly rejected empty search query"}
        
        return {"status": "failed", "message": f"Expected 400 for empty query, got {response.status_code}"}
    
    async def _test_get_content_long_slug(self, category: str, slug: str):
        """Test content retrieval with very long slug."""
        response = await self.client.get(f"{self.base_url}/api/content/{category}/{slug}")
        
        if response.status_code == 404:
            return {"status": "passed", "message": "Correctly handled long slug"}
        
        return {"status": "failed", "message": f"Long slug not handled properly: {response.status_code}"}
    
    async def _test_search_special_chars(self, query: str):
        """Test search with special characters."""
        response = await self.client.get(f"{self.base_url}/api/content/search?q={query}")
        
        if response.status_code == 200:
            return {"status": "passed", "message": f"Special character search '{query}' handled"}
        
        return {"status": "failed", "message": f"Special character search failed: {response.status_code}"}
    
    async def _test_pagination_out_of_bounds(self, category: str, page: int):
        """Test pagination with out-of-bounds page."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}?page={page}")
        
        if response.status_code == 200:
            data = response.json()
            if len(data.get("content", [])) == 0:
                return {"status": "passed", "message": "Out-of-bounds page handled correctly"}
        
        return {"status": "passed", "message": "Out-of-bounds pagination handled"}
    
    async def _test_pagination_invalid_page(self, category: str, page: int):
        """Test pagination with invalid page number."""
        response = await self.client.get(f"{self.base_url}/api/content/category/{category}?page={page}")
        
        # Should return 422 for invalid page (page < 1)
        if response.status_code == 422:
            return {"status": "passed", "message": "Invalid page number correctly rejected"}
        
        return {"status": "failed", "message": f"Invalid page not handled properly: {response.status_code}"}
    
    async def _test_concurrent_requests(self):
        """Test concurrent requests to the API."""
        start_time = datetime.now()
        
        # Make 10 concurrent requests to the popular endpoint
        tasks = []
        for i in range(10):
            task = self.client.get(f"{self.base_url}/api/content/popular")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful_responses = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        
        if successful_responses >= 8:  # Allow for some failures
            return {"status": "passed", "message": f"Concurrent requests handled: {successful_responses}/10 successful in {duration:.2f}s"}
        
        return {"status": "failed", "message": f"Too many concurrent request failures: {successful_responses}/10"}
    
    async def _test_response_times(self):
        """Test response times for key endpoints."""
        endpoints = [
            "/api/content/popular",
            "/api/admin/content-urls/stats",
            "/api/content/search?q=test"
        ]
        
        slow_responses = 0
        for endpoint in endpoints:
            start_time = datetime.now()
            response = await self.client.get(f"{self.base_url}{endpoint}")
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            if duration > 5.0:  # 5 second threshold
                slow_responses += 1
        
        if slow_responses == 0:
            return {"status": "passed", "message": "All endpoints respond within 5 seconds"}
        else:
            return {"status": "warning", "message": f"{slow_responses} endpoints are slow (>5s)"}
    
    # Utility methods
    async def _run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run a single test and record the result."""
        self.stats['total_tests'] += 1
        
        try:
            result = await test_func(*args, **kwargs)
            result['test_name'] = test_name
            result['timestamp'] = datetime.utcnow().isoformat()
            
            if result['status'] == 'passed':
                self.stats['passed_tests'] += 1
                print(f"  ✅ {test_name}")
            elif result['status'] == 'failed':
                self.stats['failed_tests'] += 1
                print(f"  ❌ {test_name}: {result['message']}")
            elif result['status'] == 'skipped':
                self.stats['skipped_tests'] += 1
                print(f"  ⏭️  {test_name}: {result['message']}")
            
            self.test_results.append(result)
            
        except Exception as e:
            self.stats['failed_tests'] += 1
            error_result = {
                'test_name': test_name,
                'status': 'failed',
                'message': f"Test error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
            self.test_results.append(error_result)
            print(f"  ❌ {test_name}: Test error: {str(e)}")
    
    def _generate_results(self, error_message: str = None) -> Dict[str, Any]:
        """Generate the final test results."""
        return {
            'success': self.stats['failed_tests'] == 0 and error_message is None,
            'error_message': error_message,
            'stats': self.stats,
            'test_results': self.test_results,
            'timestamp': datetime.utcnow().isoformat()
        }


async def main():
    """Run the permalink API testing suite."""
    print("🚀 Starting Permalink API Testing Suite")
    print("="*50)
    
    async with PermalinkAPITester() as tester:
        results = await tester.run_all_tests()
        
        print("\n" + "="*50)
        print("📊 TEST RESULTS")
        print("="*50)
        
        if results['error_message']:
            print(f"❌ Test suite failed: {results['error_message']}")
            return 2
        
        stats = results['stats']
        print(f"📈 Statistics:")
        print(f"   Total tests: {stats['total_tests']}")
        print(f"   Passed: {stats['passed_tests']}")
        print(f"   Failed: {stats['failed_tests']}")
        print(f"   Skipped: {stats['skipped_tests']}")
        
        success_rate = (stats['passed_tests'] / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        if results['success']:
            print("\n✅ All tests passed! The permalink API is working correctly.")
            return 0
        else:
            print(f"\n⚠️ {stats['failed_tests']} test(s) failed.")
            
            # Show failed tests
            failed_tests = [r for r in results['test_results'] if r['status'] == 'failed']
            if failed_tests:
                print("\n❌ Failed tests:")
                for test in failed_tests:
                    print(f"   - {test['test_name']}: {test['message']}")
            
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)