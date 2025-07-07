#!/usr/bin/env python3
"""Test script to verify capture flow and pending items display"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

async def test_capture_flow():
    """Test the complete capture flow"""
    async with httpx.AsyncClient() as client:
        print("🔍 Testing capture flow...")
        
        # 1. Test capture endpoint
        print("\n1️⃣  Testing capture endpoint...")
        capture_data = {
            "url": "https://example.com/test-article",
            "title": "Test Article - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tags": ["test", "automated"]
        }
        
        try:
            response = await client.post(f"{API_BASE}/capture", json=capture_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == 201:
                item_id = response.json()["id"]
                print(f"   ✅ Item created with ID: {item_id}")
            else:
                print(f"   ❌ Failed to capture item")
                return
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # 2. Test timeline endpoint
        print("\n2️⃣  Testing timeline endpoint...")
        try:
            response = await client.get(f"{API_BASE}/timeline?page=1&limit=10")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Total items: {data['total']}")
                print(f"   Items on page: {len(data['items'])}")
                
                # Look for our item
                found_item = None
                for item in data['items']:
                    if item['id'] == item_id:
                        found_item = item
                        break
                
                if found_item:
                    print(f"   ✅ Found captured item in timeline!")
                    print(f"      Title: {found_item['title']}")
                    print(f"      Status: {found_item.get('status', 'N/A')}")
                    print(f"      Tags: {found_item.get('tags', [])}")
                else:
                    print(f"   ⚠️  Captured item not found in timeline (might be filtering issue)")
                    
                # Show first few items
                print("\n   First 3 items in timeline:")
                for i, item in enumerate(data['items'][:3]):
                    print(f"   {i+1}. {item['title']} (status: {item.get('status', 'N/A')})")
                    
            else:
                print(f"   ❌ Failed to get timeline")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Test search endpoint
        print("\n3️⃣  Testing search endpoint...")
        try:
            response = await client.get(f"{API_BASE}/search?query=test")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Total results: {data.get('total', 0)}")
                print(f"   Items found: {len(data.get('items', []))}")
            else:
                print(f"   ❌ Search failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting capture flow test...")
    print(f"   API Base: {API_BASE}")
    print("   Make sure the backend is running on port 8000")
    print("-" * 50)
    
    asyncio.run(test_capture_flow())
    
    print("\n✨ Test complete!")