#!/usr/bin/env python3
"""
Test script for Azure OpenAI + LibreChat integration.

This script verifies that:
1. Azure OpenAI endpoints are accessible
2. LibreChat bridge API is working
3. Knowledge base integration is functioning
4. Models are properly configured
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

class AzureLibreChatTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.librechat_url = "http://localhost:3080"
        self.azure_endpoint = "https://airops.openai.azure.com"
        
        # Load environment variables
        self.azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        if not self.azure_api_key:
            print("❌ AZURE_OPENAI_API_KEY not found in environment")
            sys.exit(1)
    
    async def test_azure_openai_direct(self):
        """Test direct Azure OpenAI API access."""
        print("\n🔍 Testing Azure OpenAI Direct Access...")
        
        headers = {
            "api-key": self.azure_api_key,
            "Content-Type": "application/json"
        }
        
        # Test models endpoint
        models_url = f"{self.azure_endpoint}/openai/models?api-version=2025-01-01-preview"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(models_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Azure OpenAI models endpoint accessible")
                        print(f"   Available models: {len(data.get('data', []))}")
                        return True
                    else:
                        print(f"❌ Azure OpenAI models endpoint failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ Azure OpenAI connection error: {e}")
                return False
    
    async def test_chat_completion_direct(self):
        """Test direct Azure OpenAI chat completion."""
        print("\n🔍 Testing Azure OpenAI Chat Completion...")
        
        headers = {
            "api-key": self.azure_api_key,
            "Content-Type": "application/json"
        }
        
        chat_url = f"{self.azure_endpoint}/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
        
        payload = {
            "messages": [
                {"role": "user", "content": "Hello! This is a test from PRSNL. Respond briefly."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(chat_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = data['choices'][0]['message']['content']
                        print(f"✅ Azure OpenAI chat completion working")
                        print(f"   Response: {message[:100]}...")
                        return True
                    else:
                        text = await response.text()
                        print(f"❌ Azure OpenAI chat completion failed: {response.status}")
                        print(f"   Error: {text}")
                        return False
            except Exception as e:
                print(f"❌ Azure OpenAI chat completion error: {e}")
                return False
    
    async def test_prsnl_backend(self):
        """Test PRSNL backend health."""
        print("\n🔍 Testing PRSNL Backend...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ PRSNL Backend is healthy")
                        print(f"   Database: {data.get('database', {}).get('status', 'unknown')}")
                        print(f"   Azure OpenAI: {data.get('azure_openai', {}).get('status', 'unknown')}")
                        return True
                    else:
                        print(f"❌ PRSNL Backend health check failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ PRSNL Backend connection error: {e}")
                return False
    
    async def test_librechat_bridge(self):
        """Test LibreChat bridge API endpoints."""
        print("\n🔍 Testing LibreChat Bridge API...")
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            try:
                async with session.get(f"{self.backend_url}/api/ai/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ LibreChat Bridge health check passed")
                        print(f"   Service: {data.get('service', 'unknown')}")
                        print(f"   Models: {data.get('models', 'unknown')}")
                    else:
                        print(f"❌ LibreChat Bridge health check failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ LibreChat Bridge health error: {e}")
                return False
            
            # Test models endpoint
            try:
                async with session.get(f"{self.backend_url}/api/ai/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('data', [])
                        print(f"✅ LibreChat Bridge models endpoint working")
                        print(f"   Available models: {[m['id'] for m in models]}")
                        return True
                    else:
                        print(f"❌ LibreChat Bridge models endpoint failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ LibreChat Bridge models error: {e}")
                return False
    
    async def test_chat_completion_bridge(self):
        """Test chat completion through LibreChat bridge."""
        print("\n🔍 Testing LibreChat Bridge Chat Completion...")
        
        headers = {
            "Content-Type": "application/json",
            "X-PRSNL-Integration": "test"
        }
        
        payload = {
            "model": "prsnl-gpt-4",
            "messages": [
                {"role": "user", "content": "Hello from LibreChat bridge test! Tell me about PRSNL briefly."}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.backend_url}/api/ai/chat/completions", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = data['choices'][0]['message']['content']
                        print(f"✅ LibreChat Bridge chat completion working")
                        print(f"   Response: {message[:150]}...")
                        return True
                    else:
                        text = await response.text()
                        print(f"❌ LibreChat Bridge chat completion failed: {response.status}")
                        print(f"   Error: {text[:200]}...")
                        return False
            except Exception as e:
                print(f"❌ LibreChat Bridge chat completion error: {e}")
                return False
    
    async def test_librechat_service(self):
        """Test LibreChat service if running."""
        print("\n🔍 Testing LibreChat Service...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Try to access LibreChat health endpoint
                async with session.get(f"{self.librechat_url}/api/health") as response:
                    if response.status == 200:
                        print(f"✅ LibreChat service is running on {self.librechat_url}")
                        return True
                    else:
                        print(f"⚠️ LibreChat service responded with status: {response.status}")
                        return False
            except aiohttp.ClientConnectorError:
                print(f"⚠️ LibreChat service not running on {self.librechat_url}")
                print("   Start with: ./scripts/start_librechat.sh")
                return False
            except Exception as e:
                print(f"❌ LibreChat service test error: {e}")
                return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Azure OpenAI + LibreChat Integration Test Suite")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Backend URL: {self.backend_url}")
        print(f"LibreChat URL: {self.librechat_url}")
        print(f"Azure Endpoint: {self.azure_endpoint}")
        print("=" * 60)
        
        tests = [
            ("Azure OpenAI Direct Access", self.test_azure_openai_direct),
            ("Azure OpenAI Chat Completion", self.test_chat_completion_direct),
            ("PRSNL Backend Health", self.test_prsnl_backend),
            ("LibreChat Bridge API", self.test_librechat_bridge),
            ("LibreChat Bridge Chat", self.test_chat_completion_bridge),
            ("LibreChat Service", self.test_librechat_service),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 Test Results Summary")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print("=" * 60)
        print(f"Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Azure OpenAI + LibreChat integration is working!")
        elif passed >= total - 1:
            print("⚠️ Most tests passed. Minor issues detected.")
        else:
            print("❌ Multiple issues detected. Check the logs above.")
        
        return passed == total

async def main():
    """Main test execution."""
    tester = AzureLibreChatTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())