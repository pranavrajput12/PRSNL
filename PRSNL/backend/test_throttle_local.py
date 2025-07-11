#!/usr/bin/env python3
"""
Local test to verify FastAPI-Throttle functionality when properly installed
"""

import asyncio
import httpx

async def test_throttle():
    """Test throttling on capture endpoint"""
    print("🧪 Testing FastAPI-Throttle on capture endpoint (30 req/min limit)")
    print("Note: Backend must be rebuilt with fastapi-throttle installed")
    
    async with httpx.AsyncClient() as client:
        success = 0
        throttled = 0
        errors = 0
        
        # Make 35 rapid requests
        for i in range(35):
            try:
                response = await client.post(
                    "http://localhost:8000/api/capture",
                    json={
                        "url": f"https://example{i}.com",
                        "title": f"Test {i}",
                        "content_type": "auto"
                    },
                    timeout=2.0
                )
                
                if response.status_code == 429:
                    throttled += 1
                    print(f"✅ Request {i+1}: THROTTLED (429) - {response.text[:80]}...")
                elif response.status_code in [200, 201]:
                    success += 1
                    if i % 10 == 0:
                        print(f"✓ Request {i+1}: Success")
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                if i < 3:
                    print(f"❌ Request {i+1}: {str(e)[:50]}...")
                    
            await asyncio.sleep(0.01)  # 10ms between requests
    
    print(f"\n📊 Results: {success} success, {throttled} throttled, {errors} errors")
    
    if throttled > 0:
        print("✅ FastAPI-Throttle is WORKING!")
        return True
    else:
        print("❌ FastAPI-Throttle is NOT working (backend needs rebuild)")
        return False

async def test_search_throttle():
    """Test search endpoint throttling"""
    print("\n🧪 Testing search endpoint (50 req/min limit)")
    
    async with httpx.AsyncClient() as client:
        throttled = False
        
        for i in range(55):
            try:
                response = await client.post(
                    "http://localhost:8000/api/search/",
                    json={"query": f"test {i}", "search_type": "keyword"},
                    timeout=1.0
                )
                
                if response.status_code == 429:
                    print(f"✅ Search throttled at request {i+1}")
                    throttled = True
                    break
                    
            except:
                pass
                
        return throttled

async def main():
    print("FastAPI-Throttle Testing Suite")
    print("=" * 50)
    
    capture_working = await test_throttle()
    search_working = await test_search_throttle()
    
    print("\n" + "=" * 50)
    print("FINAL RESULT:")
    
    if capture_working or search_working:
        print("✅ FastAPI-Throttle is OPERATIONAL!")
    else:
        print("❌ FastAPI-Throttle needs backend rebuild with requirements.txt")
        print("\nTo fix:")
        print("1. docker-compose build --no-cache backend")
        print("2. docker-compose up -d backend")
        print("3. Wait for backend to start")
        print("4. Run this test again")

if __name__ == "__main__":
    asyncio.run(main())