#!/usr/bin/env python3
"""
Test both Keycloak and FusionAuth authentication systems
"""

import requests
import json
from datetime import datetime

# Configuration
KEYCLOAK_URL = "http://localhost:8080"
FUSIONAUTH_URL = "http://localhost:9011"
FUSIONAUTH_API_KEY = "fs7t4gH-8k1cuE2uPEJq68uhGR3LFmZZ23Kwjd4Cz4PwejWIVvla3ZJC"

def test_keycloak():
    """Test Keycloak connectivity and health"""
    print("🔐 Testing Keycloak...")
    
    tests = {
        "Health Check": f"{KEYCLOAK_URL}/health",
        "Ready Check": f"{KEYCLOAK_URL}/health/ready",
        "Live Check": f"{KEYCLOAK_URL}/health/live",
        "Realm Info": f"{KEYCLOAK_URL}/realms/master",
    }
    
    for test_name, url in tests.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {test_name}: OK")
            else:
                print(f"  ⚠️  {test_name}: Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ {test_name}: {str(e)}")
    
    # Test admin console
    try:
        response = requests.get(f"{KEYCLOAK_URL}/admin/", timeout=5, allow_redirects=False)
        if response.status_code in [200, 302, 303]:
            print(f"  ✅ Admin Console: Accessible")
        else:
            print(f"  ⚠️  Admin Console: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Admin Console: {str(e)}")

def test_fusionauth():
    """Test FusionAuth connectivity and API"""
    print("\n🔐 Testing FusionAuth...")
    
    # Basic connectivity
    try:
        response = requests.get(f"{FUSIONAUTH_URL}/api/status", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ API Status: OK")
        else:
            print(f"  ⚠️  API Status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ API Status: {str(e)}")
    
    # Test API key
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user?email=prsnlfyi@gmail.com",
            headers={"Authorization": FUSIONAUTH_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            print(f"  ✅ API Key: Valid")
            user_data = response.json()
            if user_data.get('user'):
                print(f"  ✅ Admin User: Found (prsnlfyi@gmail.com)")
        else:
            print(f"  ❌ API Key: Invalid (Status {response.status_code})")
    except Exception as e:
        print(f"  ❌ API Key Test: {str(e)}")
    
    # Count users
    try:
        response = requests.post(
            f"{FUSIONAUTH_URL}/api/user/search",
            headers={
                "Authorization": FUSIONAUTH_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "search": {
                    "numberOfResults": 100,
                    "startRow": 0
                }
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            total_users = data.get('total', 0)
            print(f"  ✅ Total Users: {total_users}")
        else:
            print(f"  ⚠️  User Search: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ User Search: {str(e)}")
    
    # Check applications
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/application",
            headers={"Authorization": FUSIONAUTH_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            apps = response.json().get('applications', [])
            print(f"  ✅ Applications: {len(apps)} found")
            for app in apps:
                print(f"     - {app['name']} (ID: {app['id'][:8]}...)")
        else:
            print(f"  ⚠️  Applications: Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Applications: {str(e)}")

def test_oauth_flow():
    """Test OAuth configuration"""
    print("\n🔄 Testing OAuth Configuration...")
    
    # Get PRSNL application details
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/application",
            headers={"Authorization": FUSIONAUTH_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            apps = response.json().get('applications', [])
            prsnl_app = next((app for app in apps if app['name'] == 'PRSNL'), None)
            
            if prsnl_app:
                print(f"  ✅ PRSNL Application Found")
                oauth_config = prsnl_app.get('oauthConfiguration', {})
                print(f"     Client ID: {oauth_config.get('clientId', 'N/A')[:8]}...")
                print(f"     Redirect URLs: {len(oauth_config.get('authorizedRedirectURLs', []))} configured")
                print(f"     Enabled Grants: {', '.join(oauth_config.get('enabledGrants', []))}")
            else:
                print(f"  ❌ PRSNL Application not found")
    except Exception as e:
        print(f"  ❌ OAuth Config Test: {str(e)}")

def test_database_sync():
    """Check if users are properly synced"""
    print("\n📊 Testing Database Sync...")
    
    # Check specific users
    test_users = [
        "prsnlfyi@gmail.com",
        "slathiap@gmail.com",
        "shreyanshpunk@gmail.com"
    ]
    
    for email in test_users:
        try:
            response = requests.get(
                f"{FUSIONAUTH_URL}/api/user?email={email}",
                headers={"Authorization": FUSIONAUTH_API_KEY},
                timeout=5
            )
            if response.status_code == 200 and response.json().get('user'):
                user = response.json()['user']
                verified = "✅" if user.get('verified', False) else "❌"
                print(f"  {verified} {email}: Found in FusionAuth")
            else:
                print(f"  ❌ {email}: Not found in FusionAuth")
        except Exception as e:
            print(f"  ❌ {email}: Error - {str(e)}")

def main():
    print("🧪 Authentication Systems Test Suite")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test Keycloak
    test_keycloak()
    
    # Test FusionAuth
    test_fusionauth()
    
    # Test OAuth flow
    test_oauth_flow()
    
    # Test database sync
    test_database_sync()
    
    print("\n" + "=" * 50)
    print("✅ Test suite complete!")
    print("\n📋 Next Steps:")
    print("1. If any tests failed, check the respective service")
    print("2. Configure SMTP in FusionAuth for email delivery")
    print("3. Update frontend to use FusionAuth for authentication")
    print("4. Test actual login flow with a real user")

if __name__ == "__main__":
    main()