#!/usr/bin/env python3
"""
Test FusionAuth API Key
"""

import requests
import json

API_KEY = "fs7tdgH-8k1cuEZuPEJq68uhQR3LFmZZ23Kwjd4Cz4PwejWiVvla3ZJC"
BASE_URL = "http://localhost:9011"

print("🔍 Testing FusionAuth API Key\n")

# Test different endpoints
endpoints = [
    ("/api/system-configuration", "System Configuration"),
    ("/api/user", "Users"),
    ("/api/application", "Applications"),
    ("/api/tenant", "Tenants"),
]

for endpoint, name in endpoints:
    print(f"Testing {name}...")
    
    # Try with different header formats
    headers_options = [
        {"Authorization": API_KEY},
        {"Authorization": f"Bearer {API_KEY}"},
        {"X-FusionAuth-API-Key": API_KEY},
        {"API-Key": API_KEY}
    ]
    
    for i, headers in enumerate(headers_options):
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={**headers, "Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"  ✅ Success with header format {i+1}: {list(headers.keys())[0]}")
                print(f"     Response preview: {str(response.text)[:100]}...")
                break
            else:
                print(f"  ❌ Failed with format {i+1}: Status {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error with format {i+1}: {e}")
    
    print()

# Also check if the key might need URL encoding
print("\n🔐 API Key Details:")
print(f"Length: {len(API_KEY)} characters")
special_chars = '!@#$%^&*()+={}[]|\\:;<>?,/'
print(f"Contains special characters: {any(c in API_KEY for c in special_chars)}")
print(f"First 10 chars: {API_KEY[:10]}...")
print(f"Last 10 chars: ...{API_KEY[-10:]}")

# Check FusionAuth version
print("\n📋 Checking FusionAuth status without auth:")
try:
    response = requests.get(f"{BASE_URL}/api/status", timeout=5)
    if response.status_code == 200:
        print(f"✅ FusionAuth is running")
        data = response.json()
        print(f"   Version: {data.get('version', 'Unknown')}")
except Exception as e:
    print(f"❌ Could not check status: {e}")