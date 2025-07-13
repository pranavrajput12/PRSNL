#!/usr/bin/env python3
"""
PRSNL Third-Party Integrations Test Script
Tests all integrated services and their API endpoints
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# Base configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class IntegrationTester:
    def __init__(self):
        self.results = {}
        self.session = None
    
    async def setup(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT))
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, name: str, method: str, url: str, data: dict = None) -> Dict[str, Any]:
        """Test a single endpoint"""
        start_time = time.time()
        try:
            if method.upper() == "GET":
                async with self.session.get(f"{BASE_URL}{url}") as response:
                    result = await response.json()
                    status = response.status
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(f"{BASE_URL}{url}", json=data, headers=headers) as response:
                    result = await response.json()
                    status = response.status
            else:
                return {"error": f"Unsupported method: {method}", "status": "failed"}
            
            response_time = time.time() - start_time
            
            return {
                "status": "success" if status < 400 else "error",
                "status_code": status,
                "response_time": round(response_time, 3),
                "response": result
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status": "failed",
                "error": str(e),
                "response_time": round(response_time, 3)
            }
    
    async def test_azure_openai(self):
        """Test Azure OpenAI integrations"""
        print("🤖 Testing Azure OpenAI integrations...")
        
        # Test LibreChat bridge
        librechat_result = await self.test_endpoint(
            "LibreChat Models",
            "GET", 
            "/api/ai/models"
        )
        self.results["azure_openai_librechat"] = librechat_result
        
        # Test AutoAgent status
        autoagent_result = await self.test_endpoint(
            "AutoAgent Status",
            "GET",
            "/api/autoagent/agent-status"
        )
        self.results["azure_openai_autoagent"] = autoagent_result
        
        print(f"  LibreChat: {librechat_result['status']} ({librechat_result['response_time']}s)")
        print(f"  AutoAgent: {autoagent_result['status']} ({autoagent_result['response_time']}s)")
    
    async def test_openclip(self):
        """Test OpenCLIP vision service"""
        print("👁️ Testing OpenCLIP vision service...")
        
        # Test health endpoint
        health_result = await self.test_endpoint(
            "OpenCLIP Health",
            "GET",
            "/api/openclip/health"
        )
        self.results["openclip_health"] = health_result
        
        # Test model info
        model_result = await self.test_endpoint(
            "OpenCLIP Model Info",
            "GET",
            "/api/openclip/model-info"
        )
        self.results["openclip_model"] = model_result
        
        print(f"  Health: {health_result['status']} ({health_result['response_time']}s)")
        print(f"  Model Info: {model_result['status']} ({model_result['response_time']}s)")
    
    async def test_firecrawl(self):
        """Test Firecrawl web scraping service"""
        print("🕷️ Testing Firecrawl web scraping...")
        
        # Test status endpoint (Firecrawl uses /status instead of /health)
        health_result = await self.test_endpoint(
            "Firecrawl Status",
            "GET",
            "/api/firecrawl/status"
        )
        self.results["firecrawl_health"] = health_result
        
        print(f"  Status: {health_result['status']} ({health_result['response_time']}s)")
    
    async def test_performance_stack(self):
        """Test performance infrastructure"""
        print("⚡ Testing performance infrastructure...")
        
        # Test main health endpoint (includes database, cache, etc.)
        health_result = await self.test_endpoint(
            "System Health",
            "GET",
            "/health"
        )
        self.results["system_health"] = health_result
        
        print(f"  System Health: {health_result['status']} ({health_result['response_time']}s)")
        
        if health_result['status'] == 'success':
            response = health_result['response']
            print(f"    Database: {response.get('database', {}).get('status', 'Unknown')}")
            print(f"    Azure OpenAI: {response.get('azure_openai', {}).get('status', 'Unknown')}")
            print(f"    Disk Space: {response.get('disk_space', {}).get('status', 'Unknown')}")
    
    async def test_api_endpoints(self):
        """Test core API functionality"""
        print("🔗 Testing core API endpoints...")
        
        # Test timeline endpoint
        timeline_result = await self.test_endpoint(
            "Timeline API",
            "GET",
            "/api/timeline?limit=5"
        )
        self.results["timeline_api"] = timeline_result
        
        # Test search endpoint (it's a GET request, not POST)
        search_result = await self.test_endpoint(
            "Search API",
            "GET",
            "/api/search?query=test&limit=5"
        )
        self.results["search_api"] = search_result
        
        print(f"  Timeline: {timeline_result['status']} ({timeline_result['response_time']}s)")
        print(f"  Search: {search_result['status']} ({search_result['response_time']}s)")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r['status'] == 'success')
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n🚨 FAILED TESTS:")
            for name, result in self.results.items():
                if result['status'] != 'success':
                    print(f"  - {name}: {result.get('error', 'Unknown error')}")
        
        print(f"\n🔧 SERVICE STATUS:")
        for name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            response_time = result.get('response_time', 0)
            print(f"  {status_icon} {name}: {response_time}s")
        
        print("\n" + "="*60)
        
        # Specific integration status
        print("📋 INTEGRATION STATUS:")
        
        # Azure OpenAI
        librechat_ok = self.results.get('azure_openai_librechat', {}).get('status') == 'success'
        autoagent_ok = self.results.get('azure_openai_autoagent', {}).get('status') == 'success'
        print(f"  🤖 Azure OpenAI: {'✅ OPERATIONAL' if librechat_ok and autoagent_ok else '⚠️ PARTIAL/ISSUES'}")
        
        # OpenCLIP
        openclip_ok = self.results.get('openclip_health', {}).get('status') == 'success'
        openclip_enabled = False
        if openclip_ok:
            response = self.results.get('openclip_health', {}).get('response', {})
            openclip_enabled = response.get('model_info', {}).get('enabled', False)
        print(f"  👁️ OpenCLIP: {'✅ READY' if openclip_enabled else '⚠️ API OK, SERVICE DISABLED'}")
        
        # Firecrawl
        firecrawl_ok = self.results.get('firecrawl_health', {}).get('status') == 'success'
        print(f"  🕷️ Firecrawl: {'✅ OPERATIONAL' if firecrawl_ok else '❌ ISSUES'}")
        
        # System Health
        system_ok = self.results.get('system_health', {}).get('status') == 'success'
        print(f"  ⚡ Performance Stack: {'✅ OPERATIONAL' if system_ok else '❌ ISSUES'}")
        
        print("\n💡 Next Steps:")
        if not openclip_enabled:
            print("  - Install open-clip-torch: pip install open-clip-torch")
        if not firecrawl_ok:
            print("  - Check Firecrawl API key configuration")
        if failed_tests == 0:
            print("  - All integrations are working! 🎉")

async def main():
    """Run all integration tests"""
    print("🚀 PRSNL Third-Party Integration Test Suite")
    print("=" * 60)
    
    tester = IntegrationTester()
    await tester.setup()
    
    try:
        # Run all tests
        await tester.test_azure_openai()
        await tester.test_openclip()
        await tester.test_firecrawl()
        await tester.test_performance_stack()
        await tester.test_api_endpoints()
        
        # Print summary
        tester.print_summary()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())