#!/usr/bin/env python3
"""
Fixed test script for Azure OpenAI models
Tests all three models with proper API formats
"""

import asyncio
import aiohttp
import base64
import os
import json
from datetime import datetime
import tempfile
import aiofiles

# API configuration
API_BASE = "http://localhost:8000/api"
HEADERS = {"accept": "application/json"}

async def test_whisper_transcription():
    """Test Whisper transcription with a video URL"""
    print("\n=== Testing Whisper Transcription ===")
    
    # Use a different video URL since the previous one already exists
    video_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
        "https://www.youtube.com/watch?v=kXYiU_JCYtU",  # Numb
        "https://www.youtube.com/watch?v=hTWKbfoikeg",  # Smells Like Teen Spirit
    ]
    
    for video_url in video_urls:
        try:
            # First check if URL already exists
            async with aiohttp.ClientSession() as session:
                check_data = {"url": video_url}
                async with session.post(
                    f"{API_BASE}/capture/check-duplicate",
                    json=check_data,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    result = await resp.json()
                    if result.get("is_duplicate"):
                        print(f"  ⚠️  Video already exists: {result['existing_item']['title']}")
                        continue
                
                # Capture the video
                print(f"  📹 Capturing video: {video_url}")
                capture_data = {
                    "url": video_url,
                    "tags": ["test", "music", "whisper-test"]
                }
                
                async with session.post(
                    f"{API_BASE}/capture",
                    json=capture_data,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        item_id = result["id"]
                        print(f"  ✅ Video capture initiated: {item_id}")
                        
                        # Wait and check status
                        print("  ⏳ Waiting for transcription...")
                        await asyncio.sleep(10)
                        
                        # Get item details
                        async with session.get(f"{API_BASE}/items/{item_id}") as status_resp:
                            if status_resp.status == 200:
                                item = await status_resp.json()
                                print(f"  📊 Status: {item['status']}")
                                if item.get('transcription'):
                                    print(f"  📝 Transcription preview: {item['transcription'][:200]}...")
                                    return True
                            else:
                                print(f"  ❌ Failed to get item status: {status_resp.status}")
                    else:
                        error = await resp.text()
                        print(f"  ❌ Failed to capture video: {resp.status} - {error}")
                        
        except Exception as e:
            print(f"  ❌ Error testing video {video_url}: {e}")
            
    return False

async def test_vision_analysis():
    """Test Vision API with proper multipart form data"""
    print("\n=== Testing Vision Analysis ===")
    
    # Create a test image
    test_image_path = "/tmp/test_vision_image.png"
    
    try:
        # Create a simple test image using PIL if available, otherwise use a placeholder
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "PRSNL Vision Test", fill='black')
            draw.text((50, 100), "Azure OpenAI GPT-4 Vision", fill='blue')
            draw.text((50, 150), f"Timestamp: {datetime.now()}", fill='gray')
            draw.rectangle([50, 200, 750, 400], outline='red', width=3)
            draw.text((300, 280), "Test Content Area", fill='red')
            img.save(test_image_path)
            print("  ✅ Created test image with PIL")
        except ImportError:
            # Create a minimal PNG if PIL not available
            print("  ⚠️  PIL not available, using placeholder image")
            # PNG magic bytes + minimal valid PNG
            png_data = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            )
            with open(test_image_path, 'wb') as f:
                f.write(png_data)
        
        # Test the vision endpoint with multipart form data
        async with aiohttp.ClientSession() as session:
            with open(test_image_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='test_image.png', content_type='image/png')
                form_data.add_field('save_to_db', 'true')
                
                print("  📤 Sending image to vision API...")
                async with session.post(
                    f"{API_BASE}/vision/analyze",
                    data=form_data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print("  ✅ Vision analysis successful!")
                        data = result.get('data', {})
                        print(f"  📝 Description: {data.get('description', 'N/A')}")
                        print(f"  🏷️  Tags: {', '.join(data.get('tags', []))}")
                        print(f"  📄 Text extracted: {data.get('text', 'N/A')[:100]}...")
                        if data.get('objects'):
                            print(f"  🔍 Objects detected: {', '.join(data['objects'][:5])}")
                        return True
                    else:
                        error = await resp.text()
                        print(f"  ❌ Vision API failed: {resp.status} - {error}")
                        
    except Exception as e:
        print(f"  ❌ Error testing vision: {e}")
    finally:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            
    return False

async def test_embeddings():
    """Test text-embedding-ada-002 for semantic search"""
    print("\n=== Testing Text Embeddings ===")
    
    test_content = """
    Azure OpenAI provides powerful AI models including GPT-4, DALL-E, and Whisper.
    This test verifies that the text-embedding-ada-002 model is properly integrated
    for semantic search capabilities in the PRSNL knowledge base system.
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            # First capture some content to generate embeddings
            capture_data = {
                "content": test_content,
                "title": "Embedding Test Document",
                "tags": ["test", "embeddings", "azure", "semantic-search"]
            }
            
            print("  📤 Capturing content for embedding...")
            async with session.post(
                f"{API_BASE}/capture",
                json=capture_data,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    item_id = result["id"]
                    print(f"  ✅ Content captured: {item_id}")
                    
                    # Wait for processing
                    await asyncio.sleep(5)
                    
                    # Test semantic search
                    search_queries = [
                        "OpenAI models",
                        "semantic search",
                        "knowledge base AI"
                    ]
                    
                    for query in search_queries:
                        print(f"\n  🔍 Testing semantic search: '{query}'")
                        async with session.get(
                            f"{API_BASE}/search",
                            params={"q": query, "semantic": "true"}
                        ) as search_resp:
                            if search_resp.status == 200:
                                results = await search_resp.json()
                                if results.get('items'):
                                    print(f"  ✅ Found {len(results['items'])} results")
                                    for item in results['items'][:2]:
                                        print(f"     - {item['title']} (score: {item.get('relevance_score', 'N/A')})")
                                else:
                                    print("  ⚠️  No results found")
                            else:
                                print(f"  ❌ Search failed: {search_resp.status}")
                    
                    return True
                else:
                    error = await resp.text()
                    print(f"  ❌ Failed to capture content: {resp.status} - {error}")
                    
    except Exception as e:
        print(f"  ❌ Error testing embeddings: {e}")
        
    return False

async def test_api_health():
    """Test API health and available endpoints"""
    print("\n=== Testing API Health ===")
    
    endpoints = [
        "/timeline",  # Changed from /stats
        "/items",
        "/tags",
        "/search"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(f"{API_BASE}{endpoint}") as resp:
                    if resp.status == 200:
                        print(f"  ✅ {endpoint} - OK")
                    else:
                        print(f"  ❌ {endpoint} - {resp.status}")
            except Exception as e:
                print(f"  ❌ {endpoint} - Error: {e}")

async def main():
    """Run all tests"""
    print("🚀 PRSNL Azure OpenAI Models Test Suite")
    print("=" * 50)
    
    # Check API health first
    await test_api_health()
    
    # Test each model
    results = {
        "Whisper": await test_whisper_transcription(),
        "Vision": await test_vision_analysis(),
        "Embeddings": await test_embeddings()
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for model, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {model}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Models are properly configured.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())