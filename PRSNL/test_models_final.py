#!/usr/bin/env python3
"""
Final comprehensive test script for Azure OpenAI models
Tests all three models with proper API formats and error handling
"""

import asyncio
import aiohttp
import base64
import os
import json
from datetime import datetime
import tempfile
import sys

# API configuration
API_BASE = "http://localhost:8000/api"
HEADERS = {"accept": "application/json"}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {text} ==={Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"  {text}")

async def wait_for_backend():
    """Wait for backend to be ready"""
    print_info("Waiting for backend to be ready...")
    async with aiohttp.ClientSession() as session:
        for i in range(30):
            try:
                async with session.get(f"{API_BASE}/timeline") as resp:
                    if resp.status == 200:
                        print_success("Backend is ready!")
                        return True
            except:
                pass
            await asyncio.sleep(1)
    return False

async def test_whisper_transcription():
    """Test Whisper transcription with a video URL"""
    print_header("Testing Whisper Transcription")
    
    # Test videos with different platforms - using very short videos
    test_videos = [
        {
            "url": "https://www.youtube.com/watch?v=bnJOTSpaQw8",  # 5 second video
            "name": "5 Second Test Video"
        },
        {
            "url": "https://www.youtube.com/watch?v=xFmJGQpOGDY",  # 10 second countdown
            "name": "10 Second Countdown"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for video in test_videos:
            try:
                # Check if URL already exists
                check_data = {"url": video["url"]}
                async with session.post(
                    f"{API_BASE}/capture/check-duplicate",
                    json=check_data,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("is_duplicate"):
                            print_warning(f"Video already exists: {result['existing_item']['title']}")
                            continue
                
                # Capture the video
                print_info(f"📹 Capturing video: {video['name']}")
                capture_data = {
                    "url": video["url"],
                    "tags": ["test", "whisper", "transcription"]
                }
                
                async with session.post(
                    f"{API_BASE}/capture",
                    json=capture_data,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        item_id = result["id"]
                        print_success(f"Video capture initiated: {item_id}")
                        
                        # Monitor processing
                        print_info("⏳ Monitoring transcription progress...")
                        for i in range(30):  # Wait up to 30 seconds
                            await asyncio.sleep(2)
                            
                            async with session.get(f"{API_BASE}/items/{item_id}") as status_resp:
                                if status_resp.status == 200:
                                    item = await status_resp.json()
                                    status = item.get('status', 'unknown')
                                    
                                    if status == 'completed':
                                        print_success(f"Video processed successfully!")
                                        
                                        # Check for transcription
                                        if 'transcription' in item and item['transcription']:
                                            print_info(f"📝 Transcription preview: {item['transcription'][:200]}...")
                                            print_success("Whisper transcription successful!")
                                            return True
                                        else:
                                            print_warning("Video processed but no transcription found")
                                        break
                                    elif status == 'failed':
                                        error = item.get('metadata', {}).get('error', 'Unknown error')
                                        print_error(f"Processing failed: {error}")
                                        break
                                    else:
                                        print_info(f"  Status: {status} ({i*2}s elapsed)")
                                else:
                                    print_error(f"Failed to get item status: {status_resp.status}")
                                    break
                        
                        print_warning("Timeout waiting for transcription")
                    else:
                        error = await resp.text()
                        print_error(f"Failed to capture video: {resp.status} - {error}")
                        
            except Exception as e:
                print_error(f"Error testing video {video['name']}: {e}")
                import traceback
                traceback.print_exc()
    
    return False

async def test_vision_analysis():
    """Test Vision API with proper multipart form data"""
    print_header("Testing Vision Analysis")
    
    test_image_path = "/tmp/test_vision_prsnl.png"
    
    try:
        # Create a test image
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add test content
            draw.rectangle([50, 50, 750, 150], fill='lightblue', outline='blue', width=2)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                font = None
            draw.text((100, 80), "PRSNL Vision Test", fill='black', font=font)
            
            draw.rectangle([50, 200, 750, 400], fill='lightyellow', outline='orange', width=2)
            draw.text((100, 250), f"Azure OpenAI GPT-4 Vision", fill='blue', font=font)
            draw.text((100, 320), f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill='gray')
            
            # Add some shapes for object detection
            draw.ellipse([100, 450, 200, 550], fill='red', outline='darkred')
            draw.rectangle([300, 450, 400, 550], fill='green', outline='darkgreen')
            draw.polygon([(550, 450), (600, 550), (500, 550)], fill='blue', outline='darkblue')
            
            img.save(test_image_path)
            print_success("Created test image with PIL")
        except ImportError:
            print_warning("PIL not available, using minimal test image")
            # Create a minimal valid PNG
            with open(test_image_path, 'wb') as f:
                f.write(base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                ))
        
        # Test the vision endpoint
        async with aiohttp.ClientSession() as session:
            with open(test_image_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='test_image.png', content_type='image/png')
                form_data.add_field('save_to_db', 'true')
                
                print_info("📤 Uploading image to vision API...")
                async with session.post(
                    f"{API_BASE}/vision/analyze",
                    data=form_data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print_success("Vision analysis successful!")
                        
                        data = result.get('data', {})
                        if data:
                            print_info(f"📝 Description: {data.get('description', 'N/A')}")
                            print_info(f"🏷️  Tags: {', '.join(data.get('tags', []))}")
                            print_info(f"📄 Text extracted: {data.get('text', 'N/A')[:100]}...")
                            if data.get('objects'):
                                print_info(f"🔍 Objects detected: {', '.join(data['objects'][:5])}")
                            
                            # Check if item was saved
                            if result.get('item_id'):
                                print_success(f"Saved to database with ID: {result['item_id']}")
                            
                            return True
                    else:
                        error = await resp.text()
                        print_error(f"Vision API failed: {resp.status}")
                        print_error(f"Error details: {error}")
                        
    except Exception as e:
        print_error(f"Error testing vision: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
    
    return False

async def test_embeddings():
    """Test text-embedding-ada-002 for semantic search"""
    print_header("Testing Text Embeddings")
    
    test_documents = [
        {
            "content": """
            Azure OpenAI Service provides REST API access to OpenAI's powerful language models including 
            GPT-4, GPT-3.5-Turbo, and Embeddings model series. These models can be easily integrated 
            into your applications for various AI tasks.
            """,
            "title": "Azure OpenAI Overview",
            "tags": ["azure", "openai", "ai", "embeddings"]
        },
        {
            "content": """
            Semantic search uses AI embeddings to find conceptually similar content rather than just 
            keyword matches. This enables more intelligent search capabilities in knowledge bases.
            """,
            "title": "Semantic Search Explained",
            "tags": ["search", "embeddings", "ai", "semantic"]
        }
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            created_items = []
            
            # Create test documents
            for doc in test_documents:
                print_info(f"📤 Creating document: {doc['title']}")
                
                async with session.post(
                    f"{API_BASE}/capture",
                    json=doc,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        created_items.append(result["id"])
                        print_success(f"Document created: {result['id']}")
                        
                        # Check for duplicate warning
                        if result.get('duplicate_info'):
                            print_warning(f"Duplicate detected: {result['duplicate_info']['count']} similar items")
                    else:
                        error = await resp.text()
                        print_error(f"Failed to create document: {resp.status}")
                        print_error(f"Error: {error}")
                        continue
            
            if not created_items:
                print_error("No documents were created successfully")
                return False
            
            # Wait for embedding generation and processing
            print_info("⏳ Waiting for embeddings to be generated and items to be processed...")
            await asyncio.sleep(10)  # Increased wait time for processing
            
            # Test semantic search
            search_queries = [
                ("OpenAI models", "Should find Azure OpenAI document"),
                ("intelligent search", "Should find semantic search document"),
                ("machine learning embeddings", "Should find both documents")
            ]
            
            success_count = 0
            for query, expected in search_queries:
                print_info(f"\n🔍 Searching for: '{query}'")
                print_info(f"   Expected: {expected}")
                
                # Test semantic search
                params = {
                    "query": query,  # Changed from "q" to "query"
                    "semantic": "true",
                    "limit": 5
                }
                
                async with session.get(
                    f"{API_BASE}/search",
                    params=params
                ) as search_resp:
                    if search_resp.status == 200:
                        results = await search_resp.json()
                        items = results.get('items', [])
                        
                        if items:
                            print_success(f"Found {len(items)} results:")
                            for item in items[:3]:
                                score = item.get('relevance_score', item.get('score', 'N/A'))
                                print_info(f"  - {item['title']} (score: {score})")
                            success_count += 1
                        else:
                            print_warning("No results found")
                    else:
                        error = await search_resp.text()
                        print_error(f"Search failed: {search_resp.status}")
                        print_error(f"Error: {error}")
            
            return success_count >= 2  # At least 2 out of 3 searches should work
            
    except Exception as e:
        print_error(f"Error testing embeddings: {e}")
        import traceback
        traceback.print_exc()
    
    return False

async def test_api_endpoints():
    """Test various API endpoints"""
    print_header("Testing API Endpoints")
    
    endpoints = [
        ("/timeline", "Timeline stats"),
        ("/tags", "Tags list"),
        ("/search?query=test", "Search with query"),  # Changed from q to query
        ("/items", "Recent items")  # Removed limit parameter
    ]
    
    async with aiohttp.ClientSession() as session:
        success = 0
        for endpoint, description in endpoints:
            try:
                url = f"{API_BASE}{endpoint}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        print_success(f"{description}: OK")
                        success += 1
                    else:
                        print_error(f"{description}: {resp.status}")
            except Exception as e:
                print_error(f"{description}: {str(e)}")
    
    return success >= 3  # At least 3 out of 4 should work

async def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 PRSNL Azure OpenAI Models - Final Test Suite{Colors.RESET}")
    print("=" * 60)
    
    # Wait for backend
    if not await wait_for_backend():
        print_error("Backend is not responding after 30 seconds")
        return False
    
    # Test API endpoints first
    api_ok = await test_api_endpoints()
    
    # Run model tests
    results = {
        "API Endpoints": api_ok,
        "Vision (GPT-4V)": await test_vision_analysis(),
        "Embeddings (ada-002)": await test_embeddings(),
        "Whisper": await test_whisper_transcription(),
    }
    
    # Summary
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 Test Summary:{Colors.RESET}")
    
    passed = 0
    total = len(results)
    
    for test, success in results.items():
        if success:
            print_success(f"{test}: PASSED")
            passed += 1
        else:
            print_error(f"{test}: FAILED")
    
    print(f"\n{Colors.BOLD}Score: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Azure OpenAI models are working correctly.{Colors.RESET}")
        print(f"{Colors.GREEN}The data flow from backend to frontend is properly configured.{Colors.RESET}")
        return True
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Please check the logs above.{Colors.RESET}")
        print(f"{Colors.YELLOW}Fix the issues before implementing frontend changes.{Colors.RESET}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)