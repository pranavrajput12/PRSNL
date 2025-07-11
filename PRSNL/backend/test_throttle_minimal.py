#!/usr/bin/env python3
"""
Minimal test to check if FastAPI-Throttle is active
"""

import httpx
import asyncio

async def test_single_endpoint():
    """Make just a few requests to test throttling"""
    print("Testing capture endpoint with 35 rapid requests...")
    
    async with httpx.AsyncClient(timeout=3.0) as client:
        for i in range(35):
            try:
                response = await client.post(
                    "http://localhost:8000/api/capture",
                    json={"url": f"https://test{i}.com", "title": f"Test {i}"}
                )
                
                if response.status_code == 429:
                    print(f"✅ THROTTLED at request {i+1}!")
                    print(f"Response: {response.text}")
                    return True
                elif i % 10 == 0:
                    print(f"Request {i+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error at {i+1}: {e}")
                
    print("❌ No throttling detected after 35 requests")
    return False

async def main():
    throttled = await test_single_endpoint()
    if throttled:
        print("\n✅ FastAPI-Throttle is WORKING!")
    else:
        print("\n❌ FastAPI-Throttle is NOT working - backend restart may be needed")

if __name__ == "__main__":
    asyncio.run(main())