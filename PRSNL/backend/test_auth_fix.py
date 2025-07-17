#!/usr/bin/env python3
"""
Test the authentication fix
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_auth():
    """Test login and refresh"""
    
    email = "slathiap@gmail.com"
    password = "PSnama@13"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("1. Testing LOGIN...")
        login_resp = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        print(f"   Status: {login_resp.status_code}")
        
        if login_resp.status_code != 200:
            print(f"   Error: {login_resp.text}")
            return
            
        tokens = login_resp.json()
        print(f"   ✅ Got tokens")
        
        # 2. Test refresh immediately
        print("\n2. Testing REFRESH...")
        refresh_resp = await client.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        print(f"   Status: {refresh_resp.status_code}")
        
        if refresh_resp.status_code == 200:
            new_tokens = refresh_resp.json()
            print(f"   ✅ Refresh successful")
            
            # 3. Test refresh again with new token
            print("\n3. Testing SECOND REFRESH...")
            refresh2_resp = await client.post(
                f"{BASE_URL}/api/auth/refresh",
                json={"refresh_token": new_tokens["refresh_token"]}
            )
            print(f"   Status: {refresh2_resp.status_code}")
            
            if refresh2_resp.status_code == 200:
                print(f"   ✅ Second refresh successful")
            else:
                print(f"   ❌ Error: {refresh2_resp.text}")
        else:
            print(f"   ❌ Error: {refresh_resp.text}")

if __name__ == "__main__":
    asyncio.run(test_auth())