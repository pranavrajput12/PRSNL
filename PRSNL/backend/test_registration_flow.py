#!/usr/bin/env python3
"""
Test the complete registration flow for PRSNL
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_registration_flow():
    print("🚀 Testing Complete Registration Flow")
    print("=" * 50)
    
    # Step 1: Register new user
    print("\n1️⃣ Registering new user...")
    registration_data = {
        "email": "slathiap@gmail.com",
        "password": "SecurePassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=registration_data
    )
    
    if response.status_code == 201 or response.status_code == 200:
        print("✅ Registration successful!")
        data = response.json()
        print(f"   User ID: {data['user']['id']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Verified: {data['user']['is_verified']}")
        print(f"   Access Token: {data['access_token'][:50]}...")
        
        user_id = data['user']['id']
        access_token = data['access_token']
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # Step 2: Check email logs
    print("\n2️⃣ Checking if verification email was sent...")
    time.sleep(2)  # Wait for email to be processed
    
    # We'll check this via database logs (you can check your email)
    print("   Note: Check your email for verification link")
    print("   Subject: 'Verify your email for PRSNL'")
    
    # Step 3: Test authenticated endpoint
    print("\n3️⃣ Testing authenticated access...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        print("✅ Authenticated access successful!")
        user_data = response.json()
        print(f"   Current user: {user_data['email']}")
        print(f"   Verification status: {user_data['is_verified']}")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
    
    # Step 4: Test login
    print("\n4️⃣ Testing login...")
    login_data = {
        "email": "slathiap@gmail.com",
        "password": "SecurePassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"   New access token received: {data['access_token'][:50]}...")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("✨ Registration flow test complete!")
    print("\n⚠️  Next steps:")
    print("1. Check your email for the verification link")
    print("2. Click the link to verify your email")
    print("3. Try logging in again - you should see is_verified = true")
    
if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/auth/health")
        if response.status_code == 200:
            print("✅ Backend is running\n")
            test_registration_flow()
        else:
            print("❌ Backend health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("   Make sure the backend is running!")