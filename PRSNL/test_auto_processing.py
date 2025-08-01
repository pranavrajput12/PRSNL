#!/usr/bin/env python3
"""
Test script for Auto-Processing System
Tests the complete AI processing pipeline
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime

import httpx

# Test configuration
BACKEND_URL = "http://localhost:8000/api"
TEST_CONTENT = """
Introducing React 18: The Future of User Interfaces

React 18 is the latest major release of the popular JavaScript library for building user interfaces. 
This release introduces several groundbreaking features that improve performance and developer experience.

Key Features:
1. Concurrent Rendering - Allows React to work on multiple tasks simultaneously
2. Automatic Batching - Groups multiple state updates for better performance  
3. Suspense for Server-Side Rendering - Improves loading states
4. New Hooks - useId, useDeferredValue, and useTransition

Performance Improvements:
React 18 shows significant performance gains in large applications. The concurrent rendering 
feature allows for better prioritization of user interactions, making apps feel more responsive.

Getting Started:
To upgrade to React 18, simply update your package.json and use the new createRoot API 
instead of ReactDOM.render. Most existing code will work without changes.

The React team has focused on backward compatibility while introducing these powerful new features.
This makes React 18 an exciting update for both new and existing projects.
"""

async def test_capture_with_auto_processing():
    """Test capturing content with auto-processing enabled"""
    print("🧪 Testing Capture with Auto-Processing...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test capture endpoint with AI processing enabled
        capture_data = {
            "url": "https://example.com/react-18-features",
            "title": "React 18 Features Guide",
            "content": TEST_CONTENT,
            "content_type": "article",
            "enable_summarization": True,  # This should trigger auto-processing
            "tags": ["react", "javascript", "frontend"]
        }
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/capture",
                json=capture_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                item_id = result["id"]
                print(f"✅ Capture successful! Item ID: {item_id}")
                print(f"   Status: {result['status']}")
                return item_id
            else:
                print(f"❌ Capture failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Capture error: {e}")
            return None

async def test_processing_status(item_id):
    """Test getting processing status"""
    print(f"\n🔍 Testing Processing Status for {item_id}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/auto-processing/status/{item_id}"
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Status retrieved successfully!")
                print(f"   Current status: {result['data']['status']}")
                print(f"   Currently processing: {result['data']['currently_processing']}")
                
                if result['data'].get('processing_results'):
                    processing_data = result['data']['processing_results']
                    print(f"   Steps completed: {processing_data.get('steps_completed', [])}")
                    print(f"   Success rate: {processing_data.get('success_rate', 0):.2%}")
                    if processing_data.get('errors'):
                        print(f"   Errors: {processing_data['errors']}")
                
                return result['data']
            else:
                print(f"❌ Status check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return None

async def test_processing_stats():
    """Test getting overall processing statistics"""
    print("\n📊 Testing Processing Statistics...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/auto-processing/stats")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Statistics retrieved successfully!")
                print(f"   Total items: {result['total_items']}")
                print(f"   Pending: {result['pending_items']}")
                print(f"   Completed: {result['completed_items']}")
                print(f"   Failed: {result['failed_items']}")
                print(f"   Currently processing: {result['processing_items']}")
                print(f"   Auto-processing enabled: {result['auto_processing_enabled']}")
                return result
            else:
                print(f"❌ Stats failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return None

async def test_manual_processing():
    """Test manual processing trigger"""
    print("\n🔧 Testing Manual Processing...")
    
    # Create a test item first without auto-processing
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Capture without AI processing
        capture_data = {
            "title": "Manual Processing Test",
            "content": "This is a test item for manual processing. It contains information about Python programming, web development, and data science.",
            "content_type": "note",
            "enable_summarization": False,  # Disable auto-processing
            "tags": ["test", "manual"]
        }
        
        try:
            # Capture item
            response = await client.post(
                f"{BACKEND_URL}/capture",
                json=capture_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 201:
                print(f"❌ Manual test capture failed: {response.status_code}")
                return None
                
            item_id = response.json()["id"]
            print(f"✅ Test item created: {item_id}")
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Trigger manual processing
            process_data = {
                "item_id": item_id,
                "enable_ai_processing": True,
                "force_reprocess": False
            }
            
            response = await client.post(
                f"{BACKEND_URL}/auto-processing/process",
                json=process_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Manual processing triggered!")
                print(f"   Status: {result['data']['status']}")
                return item_id
            else:
                print(f"❌ Manual processing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Manual processing error: {e}")
            return None

async def test_queue_status():
    """Test processing queue status"""
    print("\n⚡ Testing Queue Status...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/auto-processing/queue/status")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Queue status retrieved!")
                print(f"   Queue size: {result['queue_size']}")
                print(f"   Queue status: {result['queue_status']}")
                if result['currently_processing']:
                    print(f"   Processing items: {result['currently_processing']}")
                return result
            else:
                print(f"❌ Queue status failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Queue status error: {e}")
            return None

async def main():
    """Run all auto-processing tests"""
    print("🚀 PRSNL Auto-Processing System Test Suite")
    print("=" * 50)
    
    # Test 1: Capture with auto-processing
    item_id = await test_capture_with_auto_processing()
    
    if item_id:
        # Wait for processing to start
        print("\n⏳ Waiting 5 seconds for processing to begin...")
        await asyncio.sleep(5)
        
        # Test 2: Check processing status
        await test_processing_status(item_id)
        
        # Wait for processing to potentially complete
        print("\n⏳ Waiting 10 seconds for processing to complete...")
        await asyncio.sleep(10)
        
        # Check status again
        await test_processing_status(item_id)
    
    # Test 3: Processing statistics
    await test_processing_stats()
    
    # Test 4: Queue status
    await test_queue_status()
    
    # Test 5: Manual processing
    manual_item_id = await test_manual_processing()
    
    if manual_item_id:
        # Wait and check manual processing status
        print("\n⏳ Waiting 5 seconds for manual processing...")
        await asyncio.sleep(5)
        await test_processing_status(manual_item_id)
    
    print("\n🎉 Auto-Processing Test Suite Complete!")
    print("=" * 50)

if __name__ == "__main__":
    # Check if backend is running
    try:
        import requests
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running or unhealthy!")
            print("   Start with: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Start with: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
    
    # Run the async tests
    asyncio.run(main())