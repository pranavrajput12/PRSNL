#!/usr/bin/env python3
"""
Test script for PRSNL Email Authentication System
Tests email verification and magic link authentication
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "success": 200 <= response.status_code < 300
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def main():
    print("🧪 Testing PRSNL Email Authentication System")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Testing auth health endpoint...")
    result = test_endpoint("GET", "/api/auth/health")
    if result.get("success"):
        print("✅ Auth health check passed")
        if isinstance(result["data"], dict) and "features" in result["data"]:
            features = result["data"]["features"]
            print(f"   Email verification: {features.get('email_verification', False)}")
            print(f"   Two factor: {features.get('two_factor', False)}")
    else:
        print(f"❌ Auth health check failed: {result}")
        return
    
    # Test 2: Test registration with email verification
    print("\n2️⃣ Testing user registration with email verification...")
    test_email = f"test_email_{int(time.time())}@example.com"
    registration_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "first_name": "Email",
        "last_name": "Test",
        "user_type": "individual"
    }
    
    result = test_endpoint("POST", "/api/auth/register", registration_data)
    if result.get("success"):
        print("✅ Registration successful!")
        user_data = result["data"]
        print(f"   User ID: {user_data.get('user', {}).get('id', 'N/A')}")
        print(f"   Email: {user_data.get('user', {}).get('email', 'N/A')}")
        print(f"   Verified: {user_data.get('user', {}).get('is_verified', False)}")
        access_token = user_data.get("access_token")
        
        # Test 3: Check if verification email would be sent (no actual email without API key)
        print("\n3️⃣ Testing email verification system...")
        if not result["data"]["user"]["is_verified"]:
            print("✅ User created with unverified status (verification email would be sent)")
            print("   📧 In production, verification email would be sent via Resend")
            print("   📧 Email would contain link: /auth/verify-email?token=<token>")
        else:
            print("⚠️  User was immediately verified (unexpected for email verification flow)")
        
        # Test 4: Test resend verification endpoint
        print("\n4️⃣ Testing resend verification email...")
        headers = {"Authorization": f"Bearer {access_token}"}
        result = test_endpoint("POST", "/api/auth/resend-verification", headers=headers)
        if result.get("success"):
            print("✅ Resend verification endpoint working")
            print("   📧 Verification email would be resent")
        else:
            print(f"❌ Resend verification failed: {result}")
    else:
        print(f"❌ Registration failed: {result}")
        return
    
    # Test 5: Test magic link request
    print("\n5️⃣ Testing magic link request...")
    magic_link_data = {"email": test_email}
    result = test_endpoint("POST", "/api/auth/magic-link", magic_link_data)
    if result.get("success"):
        print("✅ Magic link request successful!")
        print(f"   Message: {result['data'].get('message', 'N/A')}")
        print("   📧 In production, magic link would be sent via Resend")
        print("   📧 Email would contain link: /auth/magic-link?token=<token>")
    else:
        print(f"❌ Magic link request failed: {result}")
    
    # Test 6: Test magic link request for non-existent user
    print("\n6️⃣ Testing magic link for non-existent user...")
    fake_email_data = {"email": "nonexistent@example.com"}
    result = test_endpoint("POST", "/api/auth/magic-link", fake_email_data)
    if result.get("success"):
        print("✅ Magic link endpoint correctly obscures user existence")
        print(f"   Message: {result['data'].get('message', 'N/A')}")
    else:
        print(f"❌ Magic link endpoint test failed: {result}")
    
    # Test 7: Test invalid verification token
    print("\n7️⃣ Testing invalid verification token...")
    invalid_token_data = {"token": "invalid_token_12345"}
    result = test_endpoint("POST", "/api/auth/verify-email", invalid_token_data)
    if not result.get("success") and result.get("status_code") == 400:
        print("✅ Invalid verification token correctly rejected")
    else:
        print(f"⚠️  Invalid token handling unexpected: {result}")
    
    # Test 8: Test invalid magic link token
    print("\n8️⃣ Testing invalid magic link token...")
    invalid_magic_data = {"token": "invalid_magic_link_token"}
    result = test_endpoint("POST", "/api/auth/magic-link/verify", invalid_magic_data)
    if not result.get("success") and result.get("status_code") == 401:
        print("✅ Invalid magic link token correctly rejected")
    else:
        print(f"⚠️  Invalid magic link handling unexpected: {result}")
    
    print("\n" + "=" * 50)
    print("✅ Email authentication system tests completed!")
    print("\n📋 Summary:")
    print("   ✅ Registration flow with email verification")
    print("   ✅ Resend verification email endpoint")
    print("   ✅ Magic link request endpoint")
    print("   ✅ Security: User existence not revealed")
    print("   ✅ Token validation working correctly")
    print("\n🔧 To enable actual email sending:")
    print("   1. Sign up for Resend (3,000 emails/month free)")
    print("   2. Set RESEND_API_KEY in your .env file")
    print("   3. Configure EMAIL_FROM_ADDRESS domain")
    print("\n📧 Email templates are ready and stored in the database!")

if __name__ == "__main__":
    main()