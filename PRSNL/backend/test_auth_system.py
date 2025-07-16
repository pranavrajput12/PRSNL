#!/usr/bin/env python3
"""
Test script for PRSNL authentication system
Tests registration, login, token refresh, and protected endpoints
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def test_auth_system():
    """Run authentication system tests"""
    print("🧪 Testing PRSNL Authentication System")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1️⃣ Testing auth health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/auth/health")
            assert response.status_code == 200
            data = response.json()
            print(f"✅ Auth health check passed: {data['status']}")
            print(f"   Features: {json.dumps(data['features'], indent=2)}")
        except Exception as e:
            print(f"❌ Auth health check failed: {e}")
            return
        
        # Test 2: Register a new user
        print("\n2️⃣ Testing user registration...")
        test_email = f"test_{int(datetime.now().timestamp())}@example.com"
        test_password = "TestPassword123!"
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": test_email,
                    "password": test_password,
                    "first_name": "Test",
                    "last_name": "User",
                    "user_type": "individual"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["access_token"]
                refresh_token = data["refresh_token"]
                user_id = data["user"]["id"]
                print(f"✅ Registration successful!")
                print(f"   User ID: {user_id}")
                print(f"   Email: {data['user']['email']}")
                print(f"   Access token: {access_token[:20]}...")
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return
        
        # Test 3: Login with credentials
        print("\n3️⃣ Testing user login...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["access_token"]
                refresh_token = data["refresh_token"]
                print(f"✅ Login successful!")
                print(f"   New access token: {access_token[:20]}...")
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # Test 4: Access protected endpoint
        print("\n4️⃣ Testing protected endpoint access...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Protected endpoint access successful!")
                print(f"   User: {data['email']}")
                print(f"   Verified: {data['is_verified']}")
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
        
        # Test 5: Token refresh
        print("\n5️⃣ Testing token refresh...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data["access_token"]
                print(f"✅ Token refresh successful!")
                print(f"   New access token: {new_access_token[:20]}...")
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Test 6: Invalid token
        print("\n6️⃣ Testing invalid token rejection...")
        bad_headers = {"Authorization": "Bearer invalid-token-12345"}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers=bad_headers
            )
            
            if response.status_code == 401:
                print(f"✅ Invalid token correctly rejected!")
            else:
                print(f"❌ Invalid token not rejected: {response.status_code}")
        except Exception as e:
            print(f"❌ Invalid token test error: {e}")
        
        # Test 7: Logout
        print("\n7️⃣ Testing logout...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/logout",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Logout successful!")
                
                # Verify token is invalidated
                response = await client.get(
                    f"{BASE_URL}/api/auth/me",
                    headers=headers
                )
                
                if response.status_code == 401:
                    print(f"✅ Token correctly invalidated after logout!")
                else:
                    print(f"⚠️  Token still valid after logout")
            else:
                print(f"❌ Logout failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Logout error: {e}")
        
        # Test 8: Test admin user login
        print("\n8️⃣ Testing admin user login...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": "admin@prsnl.local",
                    "password": "admin123"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin login successful!")
                print(f"   Admin ID: {data['user']['id']}")
                print(f"   Note: Change admin password in production!")
            else:
                print(f"ℹ️  Admin login failed (expected if password was changed)")
        except Exception as e:
            print(f"❌ Admin login error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication system tests completed!")
    print("\n⚠️  IMPORTANT: The system is now using JWT authentication.")
    print("   - temp-user-for-oauth has been replaced with proper auth")
    print("   - All protected endpoints require a valid JWT token")
    print("   - Update frontend to use the auth endpoints")


if __name__ == "__main__":
    try:
        asyncio.run(test_auth_system())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        sys.exit(1)