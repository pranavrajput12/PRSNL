#!/usr/bin/env python3
"""
Test API endpoints with a fresh token
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """Test various API endpoints with authentication"""
    
    email = "slathiap@gmail.com"
    password = "PSnama@13"
    
    async with httpx.AsyncClient() as client:
        # First, login to get a fresh token
        print("1. Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
            
        tokens = login_response.json()
        access_token = tokens["access_token"]
        print(f"✅ Login successful, got token: {access_token[:20]}...")
        
        # Now test various endpoints
        headers = {"Authorization": f"Bearer {access_token}"}
        
        endpoints = [
            "/api/tags",
            "/api/content-types",
            "/api/timeline?page=1"
        ]
        
        for endpoint in endpoints:
            print(f"\n2. Testing {endpoint}...")
            try:
                response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   ✅ Success - Got {len(data)} items")
                    else:
                        print(f"   ✅ Success - Got response")
                else:
                    print(f"   ❌ Failed: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())