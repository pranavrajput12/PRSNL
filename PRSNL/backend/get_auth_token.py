#!/usr/bin/env python3
"""
Script to get an auth token for a specific user by logging in.
This token can be used to call protected API endpoints like resend-verification.
"""

import asyncio
import httpx
import json
import sys
from getpass import getpass

BASE_URL = "http://localhost:8000"

async def login_and_get_token(email: str, password: str):
    """Login with email and password to get auth tokens"""
    print(f"\n🔐 Logging in as: {email}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["access_token"]
                refresh_token = data["refresh_token"]
                user = data["user"]
                
                print(f"\n✅ Login successful!")
                print(f"User ID: {user['id']}")
                print(f"Email: {user['email']}")
                print(f"Verified: {user['is_verified']}")
                print(f"\n📋 Access Token (copy this for API calls):")
                print(f"{access_token}")
                print(f"\n📋 Refresh Token:")
                print(f"{refresh_token}")
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user
                }
            else:
                print(f"\n❌ Login failed: {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"\n❌ Login error: {e}")
            return None

async def test_token(token: str):
    """Test if the token works by calling a protected endpoint"""
    print(f"\n🧪 Testing token...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                print(f"✅ Token is valid!")
                return True
            else:
                print(f"❌ Token test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Token test error: {e}")
            return False

async def call_resend_verification(token: str):
    """Call the resend-verification endpoint with the token"""
    print(f"\n📧 Calling resend-verification endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/resend-verification",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if response.status_code == 200:
                print(f"\n✅ Verification email sent successfully!")
            else:
                print(f"\n❌ Failed to send verification email")
                
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ API call error: {e}")
            return False

async def main():
    print("🔑 PRSNL Auth Token Generator")
    print("=============================")
    
    # Check if email was provided as argument
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter email (or press Enter for slathiap@gmail.com): ").strip()
        if not email:
            email = "slathiap@gmail.com"
    
    # Get password
    password = getpass(f"Enter password for {email}: ")
    
    # Login and get token
    result = await login_and_get_token(email, password)
    
    if result:
        # Test the token
        await test_token(result["access_token"])
        
        # Ask if user wants to call resend-verification
        if not result["user"]["is_verified"]:
            print(f"\n⚠️  User is not verified!")
            call_api = input("Do you want to call resend-verification API? (y/n): ").strip().lower()
            if call_api == 'y':
                await call_resend_verification(result["access_token"])
        else:
            print(f"\n✅ User is already verified!")
            call_api = input("Do you want to call resend-verification API anyway? (y/n): ").strip().lower()
            if call_api == 'y':
                await call_resend_verification(result["access_token"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)