#!/usr/bin/env python3
"""
Test script to emulate all Azure OpenAI models and verify data flow to frontend
Tests: Whisper (transcription), GPT-4.1 Vision (image analysis), text-embedding-ada-002 (semantic search)
"""

import asyncio
import aiohttp
import json
import base64
from datetime import datetime
from pathlib import Path
import sys

# API Base URL
API_BASE = "http://localhost:8000/api"

# Test data
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - First YouTube video
TEST_ARTICLE_URL = "https://www.theverge.com/2024/1/1/example-tech-article"
TEST_IMAGE_PATH = "/tmp/test_image.jpg"  # We'll create a test image
TEST_SEARCH_QUERY = "technology innovation"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print colored header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")


async def create_test_image():
    """Create a simple test image for vision testing"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print_error("PIL not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple test image with text
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    text = "PRSNL Test Image\nAI Vision Analysis\nTechnology & Innovation"
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        font = None
    
    draw.multiline_text((50, 50), text, fill='black', font=font, spacing=20)
    
    # Add some shapes
    draw.rectangle([50, 200, 350, 400], fill='red', outline='black', width=3)
    draw.ellipse([450, 200, 750, 400], fill='blue', outline='black', width=3)
    
    # Save the image
    img.save(TEST_IMAGE_PATH, 'JPEG')
    print_success(f"Created test image at {TEST_IMAGE_PATH}")
    return TEST_IMAGE_PATH


async def test_whisper_transcription(session):
    """Test 1: Whisper model for video transcription"""
    print_header("TEST 1: WHISPER - Video Transcription")
    
    # Step 1: Capture a video URL
    print_info("Capturing video URL to trigger transcription...")
    
    capture_data = {
        "url": TEST_VIDEO_URL,
        "title": "Test Video for Whisper Transcription"
    }
    
    try:
        async with session.post(f"{API_BASE}/capture", json=capture_data) as resp:
            if resp.status == 201:
                result = await resp.json()
                item_id = result['id']
                print_success(f"Video captured successfully. Item ID: {item_id}")
                
                # Check for duplicate info
                if 'duplicate_info' in result and result['duplicate_info']:
                    print_info("Duplicate detection info received:")
                    print(json.dumps(result['duplicate_info'], indent=2))
            else:
                error_text = await resp.text()
                print_error(f"Failed to capture video: {resp.status} - {error_text}")
                return
                
        # Step 2: Wait for processing and check transcription
        print_info("Waiting for video processing and transcription...")
        await asyncio.sleep(10)  # Give it time to process
        
        # Step 3: Retrieve the item to check transcription
        async with session.get(f"{API_BASE}/items/{item_id}") as resp:
            if resp.status == 200:
                item = await resp.json()
                
                # Check if transcription exists in metadata
                if 'metadata' in item and 'transcription' in item.get('metadata', {}):
                    print_success("Transcription found in item metadata!")
                    print(f"Transcription preview: {item['metadata']['transcription'][:200]}...")
                else:
                    print_info("Transcription not found in metadata. Checking video metadata...")
                    if 'metadata' in item and 'video_metadata' in item.get('metadata', {}):
                        video_meta = item['metadata']['video_metadata']
                        if 'transcription' in video_meta:
                            print_success("Transcription found in video metadata!")
                            print(f"Transcription: {video_meta['transcription'][:200]}...")
                        else:
                            print_error("No transcription found. Whisper may not be processing correctly.")
                            print_info("Video metadata keys: " + str(video_meta.keys()))
                
                # Show full item structure for debugging
                print_info("Full item structure:")
                print(json.dumps(item, indent=2, default=str))
            else:
                print_error(f"Failed to retrieve item: {resp.status}")
                
    except Exception as e:
        print_error(f"Error during Whisper test: {str(e)}")


async def test_vision_analysis(session):
    """Test 2: GPT-4.1 Vision for image analysis"""
    print_header("TEST 2: GPT-4.1 VISION - Image Analysis")
    
    # Create test image
    image_path = await create_test_image()
    
    # Step 1: Upload image for vision analysis
    print_info("Uploading image for vision analysis...")
    
    # Read image and convert to base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    vision_data = {
        "image_base64": image_base64,
        "image_path": "test_image.jpg"
    }
    
    try:
        async with session.post(f"{API_BASE}/vision/analyze", json=vision_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print_success("Vision analysis completed successfully!")
                
                print_info("Analysis Results:")
                print(f"- Extracted Text: {result.get('text', 'No text extracted')}")
                print(f"- Description: {result.get('description', 'No description')}")
                print(f"- Tags: {', '.join(result.get('tags', []))}")
                
                if 'objects' in result:
                    print(f"- Detected Objects: {', '.join(result['objects'])}")
                
                print_info("Full vision response:")
                print(json.dumps(result, indent=2))
            else:
                error_text = await resp.text()
                print_error(f"Vision analysis failed: {resp.status} - {error_text}")
                
    except Exception as e:
        print_error(f"Error during Vision test: {str(e)}")


async def test_embedding_search(session):
    """Test 3: text-embedding-ada-002 for semantic search"""
    print_header("TEST 3: TEXT-EMBEDDING-ADA-002 - Semantic Search")
    
    # First, let's add some test content to search through
    print_info("Adding test content for semantic search...")
    
    test_contents = [
        {
            "title": "The Future of Artificial Intelligence",
            "content": "AI is transforming how we work, live, and interact with technology. Machine learning and neural networks are advancing rapidly.",
            "tags": ["ai", "technology", "future"]
        },
        {
            "title": "Climate Change Solutions",
            "content": "Renewable energy, sustainable practices, and green technology are key to addressing climate change challenges.",
            "tags": ["climate", "environment", "sustainability"]
        },
        {
            "title": "Space Exploration Updates",
            "content": "NASA and SpaceX are pushing boundaries in space exploration with Mars missions and satellite technology.",
            "tags": ["space", "nasa", "technology"]
        }
    ]
    
    # Capture test content
    for content in test_contents:
        try:
            async with session.post(f"{API_BASE}/capture", json=content) as resp:
                if resp.status == 201:
                    print_success(f"Added: {content['title']}")
                else:
                    print_error(f"Failed to add: {content['title']}")
        except Exception as e:
            print_error(f"Error adding content: {str(e)}")
    
    # Wait for embedding generation
    print_info("Waiting for embeddings to be generated...")
    await asyncio.sleep(5)
    
    # Step 1: Test semantic search
    print_info(f"Performing semantic search for: '{TEST_SEARCH_QUERY}'")
    
    search_params = {
        "query": TEST_SEARCH_QUERY,
        "semantic": "true",  # Enable semantic search
        "limit": 10
    }
    
    try:
        async with session.get(f"{API_BASE}/search", params=search_params) as resp:
            if resp.status == 200:
                results = await resp.json()
                print_success(f"Semantic search completed! Found {len(results)} results")
                
                if results:
                    print_info("Search Results:")
                    for i, result in enumerate(results[:5], 1):
                        print(f"\n{i}. {result['title']}")
                        print(f"   Score: {result.get('score', 'N/A')}")
                        print(f"   Relevance: {result.get('relevance_score', 'N/A')}")
                        if 'highlight' in result:
                            print(f"   Highlight: {result['highlight']}")
                else:
                    print_info("No results found. Embeddings might not be generated yet.")
            else:
                error_text = await resp.text()
                print_error(f"Search failed: {resp.status} - {error_text}")
                
    except Exception as e:
        print_error(f"Error during semantic search test: {str(e)}")
    
    # Step 2: Test "Find Similar" functionality
    print_info("\nTesting 'Find Similar' functionality...")
    
    # Get one item to find similar items for
    try:
        async with session.get(f"{API_BASE}/items", params={"limit": 1}) as resp:
            if resp.status == 200:
                items = await resp.json()
                if items and 'items' in items and items['items']:
                    test_item_id = items['items'][0]['id']
                    
                    # Find similar items
                    async with session.get(f"{API_BASE}/items/{test_item_id}/similar") as resp:
                        if resp.status == 200:
                            similar_items = await resp.json()
                            print_success(f"Found {len(similar_items)} similar items!")
                            
                            for item in similar_items[:3]:
                                print(f"\n- {item['title']}")
                                print(f"  Similarity: {item.get('similarity', 'N/A')}")
                        else:
                            error_text = await resp.text()
                            print_error(f"Find similar failed: {resp.status} - {error_text}")
                            
    except Exception as e:
        print_error(f"Error during find similar test: {str(e)}")


async def test_data_flow_to_frontend(session):
    """Test 4: Verify data flow to frontend"""
    print_header("TEST 4: DATA FLOW TO FRONTEND")
    
    print_info("Testing WebSocket connection for real-time updates...")
    
    # This would typically involve WebSocket connection
    # For now, we'll test the REST API endpoints that frontend uses
    
    endpoints_to_test = [
        ("/timeline", "Timeline API"),
        ("/stats", "Statistics API"),
        ("/tags", "Tags API"),
        ("/ai/insights", "AI Insights API"),
    ]
    
    for endpoint, name in endpoints_to_test:
        try:
            async with session.get(f"{API_BASE}{endpoint}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success(f"{name} - OK (returned {len(str(data))} chars)")
                else:
                    print_error(f"{name} - Failed ({resp.status})")
        except Exception as e:
            print_error(f"{name} - Error: {str(e)}")


async def main():
    """Run all tests"""
    print_header("PRSNL v2.0 - Azure OpenAI Models Test Suite")
    print_info(f"Testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Backend API: {API_BASE}")
    
    # Create session with timeout
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Run tests in sequence
        await test_whisper_transcription(session)
        await test_vision_analysis(session)
        await test_embedding_search(session)
        await test_data_flow_to_frontend(session)
    
    print_header("TEST SUITE COMPLETED")
    print_info("Check the results above to verify all models are working correctly.")
    print_info("If any tests failed, check:")
    print_info("1. Azure OpenAI deployments are correctly configured")
    print_info("2. Environment variables are set properly")
    print_info("3. Backend logs for detailed error messages")


if __name__ == "__main__":
    asyncio.run(main())