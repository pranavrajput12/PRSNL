#!/usr/bin/env python3
"""
Simple test to verify FastAPI-Throttle is working on available endpoints.
"""

import asyncio
import httpx
import time

async def test_search_throttling():
    """Test search endpoint with aggressive requests"""
    print("🧪 Testing search endpoint throttling (50 requests/minute limit)...")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        throttled = False
        
        # Make 60 rapid requests to trigger throttling
        for i in range(60):
            try:
                response = await client.post(
                    "http://localhost:8000/api/search/",
                    json={
                        "query": f"test query {i}",
                        "search_type": "keyword",
                        "limit": 5
                    }
                )
                
                if response.status_code == 429:
                    throttled = True
                    print(f"✅ SUCCESS! Request {i+1} was throttled (HTTP 429)")
                    print(f"   Response: {response.text[:100]}...")
                    break
                elif response.status_code == 200:
                    if i % 10 == 0:
                        print(f"✓ Request {i+1}: Success (200)")
                else:
                    print(f"⚠️  Request {i+1}: Unexpected status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request {i+1}: Error - {e}")
            
            # No delay - hammer the endpoint
            await asyncio.sleep(0.001)
        
        return throttled

async def test_capture_throttling():
    """Test capture endpoint with rapid requests"""
    print("\n🧪 Testing capture endpoint throttling (30 requests/minute limit)...")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        throttled = False
        
        # Make 40 rapid requests
        for i in range(40):
            try:
                response = await client.post(
                    "http://localhost:8000/api/capture",
                    json={
                        "url": f"https://example.com/test{i}",
                        "title": f"Test {i}",
                        "content_type": "auto"
                    }
                )
                
                if response.status_code == 429:
                    throttled = True
                    print(f"✅ SUCCESS! Request {i+1} was throttled (HTTP 429)")
                    print(f"   Response: {response.text[:100]}...")
                    break
                elif response.status_code in [200, 201]:
                    if i % 10 == 0:
                        print(f"✓ Request {i+1}: Success")
                elif response.status_code == 400:
                    # Expected for duplicate URLs
                    pass
                else:
                    if i < 5:
                        print(f"⚠️  Request {i+1}: Status {response.status_code}")
                    
            except Exception as e:
                if i < 3:
                    print(f"❌ Request {i+1}: Error - {e}")
            
            await asyncio.sleep(0.001)
        
        return throttled

async def test_file_upload_throttling():
    """Test file upload endpoint"""
    print("\n🧪 Testing file upload endpoint throttling (15 files/5 minutes limit)...")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        throttled = False
        
        # Make 20 rapid requests
        for i in range(20):
            try:
                # Create a small test file
                files = {
                    'files': (f'test{i}.txt', f'Test content {i}', 'text/plain')
                }
                data = {
                    'title': f'Test upload {i}'
                }
                
                response = await client.post(
                    "http://localhost:8000/api/file/upload",
                    files=files,
                    data=data
                )
                
                if response.status_code == 429:
                    throttled = True
                    print(f"✅ SUCCESS! Request {i+1} was throttled (HTTP 429)")
                    print(f"   Response: {response.text[:100]}...")
                    break
                elif response.status_code in [200, 201]:
                    if i % 5 == 0:
                        print(f"✓ Request {i+1}: Success")
                else:
                    if i < 3:
                        print(f"⚠️  Request {i+1}: Status {response.status_code}")
                    
            except Exception as e:
                if i < 3:
                    print(f"❌ Request {i+1}: Error - {e}")
            
            await asyncio.sleep(0.001)
        
        return throttled

async def main():
    print("🚀 FastAPI-Throttle Simple Test")
    print("=" * 50)
    
    search_throttled = await test_search_throttling()
    capture_throttled = await test_capture_throttling()
    file_throttled = await test_file_upload_throttling()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    if search_throttled:
        print("✅ Search endpoint throttling: WORKING")
    else:
        print("❌ Search endpoint throttling: NOT WORKING")
        
    if capture_throttled:
        print("✅ Capture endpoint throttling: WORKING")
    else:
        print("❌ Capture endpoint throttling: NOT WORKING")
        
    if file_throttled:
        print("✅ File upload throttling: WORKING")
    else:
        print("❌ File upload throttling: NOT WORKING")
    
    if search_throttled or capture_throttled or file_throttled:
        print("\n✅ FastAPI-Throttle is partially working!")
        print("⚠️  Note: Some endpoints may not be throttled due to missing imports or configuration.")
    else:
        print("\n❌ FastAPI-Throttle is NOT working on any endpoint!")
        print("💡 Possible issues:")
        print("   - Backend needs restart after adding throttle middleware")
        print("   - FastAPI-Throttle not properly installed")
        print("   - Syntax errors in throttle configuration")

if __name__ == "__main__":
    asyncio.run(main())