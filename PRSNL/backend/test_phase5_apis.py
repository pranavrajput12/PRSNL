#!/usr/bin/env python3
"""
Phase 5 API Testing Script
==========================

Tests the new Phase 5 Advanced AI Features:
- Multi-modal AI Processing API
- Advanced Code Intelligence API  
- Natural Language Control API
"""

import asyncio
import json
import sys
import httpx
from datetime import datetime

# Test configurations
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0

class Phase5APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.results = []
        
    async def test_multimodal_capabilities(self):
        """Test multi-modal AI capabilities endpoint"""
        print("🧪 Testing Multi-modal AI Capabilities...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/multimodal/capabilities")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Multi-modal Capabilities: {len(data.get('supported_formats', {}))} format types")
                    print(f"   Analysis depths: {list(data.get('analysis_depths', {}).keys())}")
                    self.results.append({"test": "multimodal_capabilities", "status": "pass", "data": data})
                else:
                    print(f"❌ Multi-modal Capabilities: HTTP {response.status_code}")
                    self.results.append({"test": "multimodal_capabilities", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Multi-modal Capabilities: {e}")
            self.results.append({"test": "multimodal_capabilities", "status": "error", "error": str(e)})
    
    async def test_multimodal_health(self):
        """Test multi-modal AI health endpoint"""
        print("🧪 Testing Multi-modal AI Health...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/multimodal/health")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('overall_status', 'unknown')
                    print(f"✅ Multi-modal Health: {status}")
                    self.results.append({"test": "multimodal_health", "status": "pass", "health_status": status})
                else:
                    print(f"❌ Multi-modal Health: HTTP {response.status_code}")
                    self.results.append({"test": "multimodal_health", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Multi-modal Health: {e}")
            self.results.append({"test": "multimodal_health", "status": "error", "error": str(e)})
    
    async def test_code_intelligence_capabilities(self):
        """Test code intelligence capabilities endpoint"""
        print("🧪 Testing Code Intelligence Capabilities...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/code/capabilities")
                
                if response.status_code == 200:
                    data = response.json()
                    analysis_types = data.get('analysis_types', {})
                    languages = data.get('supported_languages', [])
                    print(f"✅ Code Intelligence: {len(analysis_types)} analysis types, {len(languages)} languages")
                    self.results.append({"test": "code_capabilities", "status": "pass", "data": data})
                else:
                    print(f"❌ Code Intelligence: HTTP {response.status_code}")
                    self.results.append({"test": "code_capabilities", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Code Intelligence: {e}")
            self.results.append({"test": "code_capabilities", "status": "error", "error": str(e)})
    
    async def test_code_intelligence_health(self):
        """Test code intelligence health endpoint"""
        print("🧪 Testing Code Intelligence Health...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/code/health")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    services = data.get('services', {})
                    print(f"✅ Code Intelligence Health: {status} ({len(services)} services)")
                    self.results.append({"test": "code_health", "status": "pass", "health_status": status})
                else:
                    print(f"❌ Code Intelligence Health: HTTP {response.status_code}")
                    self.results.append({"test": "code_health", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Code Intelligence Health: {e}")
            self.results.append({"test": "code_health", "status": "error", "error": str(e)})
    
    async def test_natural_language_capabilities(self):
        """Test natural language capabilities endpoint"""
        print("🧪 Testing Natural Language Capabilities...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/nl/capabilities")
                
                if response.status_code == 200:
                    data = response.json()
                    command_types = data.get('command_types', {})
                    entity_types = data.get('entity_types', [])
                    print(f"✅ Natural Language: {len(command_types)} command types, {len(entity_types)} entities")
                    self.results.append({"test": "nl_capabilities", "status": "pass", "data": data})
                else:
                    print(f"❌ Natural Language: HTTP {response.status_code}")
                    self.results.append({"test": "nl_capabilities", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Natural Language: {e}")
            self.results.append({"test": "nl_capabilities", "status": "error", "error": str(e)})
    
    async def test_natural_language_health(self):
        """Test natural language health endpoint"""
        print("🧪 Testing Natural Language Health...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/nl/health")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    services = data.get('services', {})
                    print(f"✅ Natural Language Health: {status} ({len(services)} services)")
                    self.results.append({"test": "nl_health", "status": "pass", "health_status": status})
                else:
                    print(f"❌ Natural Language Health: HTTP {response.status_code}")
                    self.results.append({"test": "nl_health", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Natural Language Health: {e}")
            self.results.append({"test": "nl_health", "status": "error", "error": str(e)})
    
    async def test_natural_language_examples(self):
        """Test natural language examples endpoint"""
        print("🧪 Testing Natural Language Examples...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/nl/examples")
                
                if response.status_code == 200:
                    data = response.json()
                    beginner_commands = len(data.get('beginner_commands', []))
                    advanced_commands = len(data.get('advanced_commands', []))
                    print(f"✅ Natural Language Examples: {beginner_commands} beginner, {advanced_commands} advanced")
                    self.results.append({"test": "nl_examples", "status": "pass", "data": data})
                else:
                    print(f"❌ Natural Language Examples: HTTP {response.status_code}")
                    self.results.append({"test": "nl_examples", "status": "fail", "error": response.status_code})
                    
        except Exception as e:
            print(f"❌ Natural Language Examples: {e}")
            self.results.append({"test": "nl_examples", "status": "error", "error": str(e)})
    
    async def run_all_tests(self):
        """Run all Phase 5 API tests"""
        print(f"🚀 Starting Phase 5 API Tests at {datetime.now()}")
        print(f"   Base URL: {self.base_url}")
        print("-" * 60)
        
        # Test all endpoints
        await self.test_multimodal_capabilities()
        await self.test_multimodal_health()
        await self.test_code_intelligence_capabilities()
        await self.test_code_intelligence_health()
        await self.test_natural_language_capabilities()
        await self.test_natural_language_health()
        await self.test_natural_language_examples()
        
        # Summary
        print("-" * 60)
        passed = len([r for r in self.results if r['status'] == 'pass'])
        failed = len([r for r in self.results if r['status'] == 'fail'])
        errors = len([r for r in self.results if r['status'] == 'error'])
        
        print(f"📊 Phase 5 API Test Results:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   🔥 Errors: {errors}")
        print(f"   📈 Success Rate: {(passed / len(self.results) * 100):.1f}%")
        
        if passed == len(self.results):
            print("\n🎉 All Phase 5 APIs are operational!")
            return True
        else:
            print(f"\n⚠️  {failed + errors} tests failed. Check server status.")
            return False

async def main():
    """Main test function"""
    tester = Phase5APITester()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())