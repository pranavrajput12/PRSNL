#!/usr/bin/env python3
"""
Test script to verify FastAPI-Throttle is working correctly.
Tests the rate limiting on embedding and capture endpoints.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000/api"

async def test_embedding_throttle():
    """Test embedding endpoint throttling (5 requests per 5 minutes)"""
    print("🧪 Testing embedding endpoint throttling...")
    
    async with httpx.AsyncClient() as client:
        success_count = 0
        throttled_count = 0
        
        # Try to make 7 requests quickly (should throttle after 5)
        for i in range(7):
            try:
                response = await client.post(f"{API_BASE}/embeddings/generate")
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ Request {i+1}: Success")
                elif response.status_code == 429:
                    throttled_count += 1
                    print(f"🚦 Request {i+1}: Throttled (429)")
                else:
                    print(f"❌ Request {i+1}: Unexpected status {response.status_code}")
            except Exception as e:
                print(f"❌ Request {i+1}: Error - {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    print(f"📊 Embedding test results: {success_count} success, {throttled_count} throttled")
    return success_count, throttled_count

async def test_capture_throttle():
    """Test capture endpoint throttling (30 requests per minute)"""
    print("\n🧪 Testing capture endpoint throttling...")
    
    async with httpx.AsyncClient() as client:
        success_count = 0
        throttled_count = 0
        
        # Try to make 35 requests quickly (should throttle after 30)
        test_payload = {
            "url": "https://example.com",
            "title": "Test capture",
            "content_type": "auto"
        }
        
        for i in range(35):
            try:
                response = await client.post(
                    f"{API_BASE}/capture", 
                    json=test_payload
                )
                if response.status_code in [200, 201]:
                    success_count += 1
                    if i < 5 or i % 10 == 0:  # Don't spam output
                        print(f"✅ Request {i+1}: Success")
                elif response.status_code == 429:
                    throttled_count += 1
                    print(f"🚦 Request {i+1}: Throttled (429)")
                else:
                    if i < 5:  # Only show first few errors
                        print(f"❌ Request {i+1}: Status {response.status_code}")
            except Exception as e:
                if i < 5:  # Only show first few errors
                    print(f"❌ Request {i+1}: Error - {e}")
            
            # Very small delay
            await asyncio.sleep(0.05)
    
    print(f"📊 Capture test results: {success_count} success, {throttled_count} throttled")
    return success_count, throttled_count

async def test_search_throttle():
    """Test search endpoint throttling (50 requests per minute)"""
    print("\n🧪 Testing search endpoint throttling...")
    
    async with httpx.AsyncClient() as client:
        success_count = 0
        throttled_count = 0
        
        # Try to make 55 requests quickly (should throttle after 50)
        test_payload = {
            "query": "test search",
            "search_type": "semantic",
            "limit": 10
        }
        
        for i in range(55):
            try:
                response = await client.post(
                    f"{API_BASE}/search/", 
                    json=test_payload
                )
                if response.status_code == 200:
                    success_count += 1
                    if i < 5 or i % 20 == 0:  # Don't spam output
                        print(f"✅ Request {i+1}: Success")
                elif response.status_code == 429:
                    throttled_count += 1
                    print(f"🚦 Request {i+1}: Throttled (429)")
                else:
                    if i < 5:  # Only show first few errors
                        print(f"❌ Request {i+1}: Status {response.status_code}")
            except Exception as e:
                if i < 5:  # Only show first few errors
                    print(f"❌ Request {i+1}: Error - {e}")
            
            await asyncio.sleep(0.02)
    
    print(f"📊 Search test results: {success_count} success, {throttled_count} throttled")
    return success_count, throttled_count

async def main():
    print("🚀 FastAPI-Throttle Test Suite")
    print("=" * 50)
    
    # Test different endpoints
    embedding_results = await test_embedding_throttle()
    capture_results = await test_capture_throttle() 
    search_results = await test_search_throttle()
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS")
    print("=" * 50)
    print(f"Embedding endpoint: {embedding_results[1]}/{embedding_results[0]+embedding_results[1]} requests throttled")
    print(f"Capture endpoint: {capture_results[1]}/{capture_results[0]+capture_results[1]} requests throttled") 
    print(f"Search endpoint: {search_results[1]}/{search_results[0]+search_results[1]} requests throttled")
    
    # Check if throttling is working
    if embedding_results[1] > 0 or capture_results[1] > 0 or search_results[1] > 0:
        print("\n✅ SUCCESS: FastAPI-Throttle is working! Some requests were throttled.")
    else:
        print("\n⚠️  WARNING: No requests were throttled. Check if throttling is properly configured.")

if __name__ == "__main__":
    asyncio.run(main())