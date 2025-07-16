#!/usr/bin/env python3
"""
Test the complete login flow for slathiap@gmail.com
"""

import asyncio
import httpx
import json
from getpass import getpass
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

async def test_login_flow():
    """Test login, refresh, and logout flow"""
    
    email = "slathiap@gmail.com"
    print(f"Testing login flow for {email}")
    print("=" * 60)
    
    # Get password
    password = getpass(f"Enter password for {email}: ")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Login
        print("\n1. Testing LOGIN...")
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"   Error: {login_response.json()}")
            return
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        print(f"   ✅ Login successful")
        print(f"   Access Token: {access_token[:20]}...")
        print(f"   Refresh Token: {refresh_token[:20]}...")
        
        # Step 2: Test authenticated endpoint
        print("\n2. Testing AUTHENTICATED endpoint...")
        me_response = await client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"   Status: {me_response.status_code}")
        if me_response.status_code == 200:
            user_data = me_response.json()
            print(f"   ✅ Auth works - User: {user_data['email']}")
        else:
            print(f"   ❌ Auth failed: {me_response.json()}")
        
        # Step 3: Test refresh token
        print("\n3. Testing REFRESH token...")
        refresh_response = await client.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        print(f"   Status: {refresh_response.status_code}")
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            new_access_token = refresh_data["access_token"]
            new_refresh_token = refresh_data["refresh_token"]
            print(f"   ✅ Refresh successful")
            print(f"   New Access Token: {new_access_token[:20]}...")
            print(f"   New Refresh Token: {new_refresh_token[:20]}...")
            
            # Test new access token
            print("\n4. Testing NEW access token...")
            me2_response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            print(f"   Status: {me2_response.status_code}")
            if me2_response.status_code == 200:
                print(f"   ✅ New token works!")
            else:
                print(f"   ❌ New token failed: {me2_response.json()}")
        else:
            print(f"   ❌ Refresh failed: {refresh_response.json()}")
            
        # Step 5: Logout (optional)
        print("\n5. Testing LOGOUT...")
        logout_choice = input("   Do you want to test logout? (y/n): ").strip().lower()
        if logout_choice == 'y':
            logout_response = await client.post(
                f"{BASE_URL}/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            print(f"   Status: {logout_response.status_code}")
            if logout_response.status_code == 200:
                print(f"   ✅ Logout successful")
            else:
                print(f"   ❌ Logout failed: {logout_response.json()}")

if __name__ == "__main__":
    asyncio.run(test_login_flow())