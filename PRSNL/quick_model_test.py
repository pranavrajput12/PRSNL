#!/usr/bin/env python3
"""
Quick test script to verify each Azure OpenAI model individually
Run with: python quick_model_test.py [whisper|vision|embedding|all]
"""

import sys
import asyncio
import httpx
import json
import base64
from PIL import Image, ImageDraw
import io

API_BASE = "http://localhost:8000/api"

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def test_whisper():
    """Test Whisper transcription"""
    print(f"\n{BLUE}Testing Whisper (Video Transcription)...{RESET}")
    
    # Use a short video for testing
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo (19 seconds)
    
    async with httpx.AsyncClient() as client:
        # Capture the video
        print("1. Capturing video...")
        capture_data = {
            "url": video_url,
            "title": "Whisper Test - Me at the zoo"
        }
        
        try:
            resp = await client.post(f"{API_BASE}/capture", json=capture_data)
            if resp.status_code == 201:
                result = resp.json()
                    item_id = result['id']
                    print(f"{GREEN}✓ Video captured: {item_id}{RESET}")
                    
                    # Wait and check for transcription
                    print("2. Waiting for transcription (this may take 10-30 seconds)...")
                    for i in range(30):
                        await asyncio.sleep(1)
                        print(f"\r   Checking... {i+1}/30 seconds", end='', flush=True)
                        
                        item_resp = await client.get(f"{API_BASE}/items/{item_id}")
                        if item_resp.status_code == 200:
                            item = item_resp.json()
                                metadata = item.get('metadata', {})
                                
                                # Check multiple possible locations for transcription
                                transcription = None
                                if 'transcription' in metadata:
                                    transcription = metadata['transcription']
                                elif 'video_metadata' in metadata and 'transcription' in metadata['video_metadata']:
                                    transcription = metadata['video_metadata']['transcription']
                                elif 'ai_analysis' in metadata and 'transcription' in metadata['ai_analysis']:
                                    transcription = metadata['ai_analysis']['transcription']
                                
                                if transcription:
                                    print(f"\n{GREEN}✓ Transcription found!{RESET}")
                                    print(f"Transcription preview: {transcription[:200]}...")
                                    return True
                    
                    print(f"\n{YELLOW}⚠ No transcription found after 30 seconds{RESET}")
                    print("Possible issues:")
                    print("- Whisper model not deployed in Azure")
                    print("- AZURE_OPENAI_WHISPER_DEPLOYMENT not set in .env")
                    print("- Video still processing (check backend logs)")
                    return False
            else:
                error = resp.text()
                if "already exists" in error:
                    print(f"{YELLOW}Video already exists in database{RESET}")
                    return True
                else:
                    print(f"{RED}✗ Capture failed: {error}{RESET}")
                    return False
                        
        except Exception as e:
            print(f"{RED}✗ Error: {str(e)}{RESET}")
            return False


async def test_vision():
    """Test GPT-4.1 Vision"""
    print(f"\n{BLUE}Testing GPT-4.1 Vision (Image Analysis)...{RESET}")
    
    # Create a test image
    print("1. Creating test image...")
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "PRSNL Vision Test", fill='black')
    draw.rectangle([50, 100, 350, 200], fill='red', outline='black')
    draw.text((100, 130), "AI Analysis", fill='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    async with httpx.AsyncClient() as client:
        print("2. Sending image for analysis...")
        vision_data = {
            "image_base64": img_base64,
            "image_path": "test_vision.png"
        }
        
        try:
            resp = await client.post(f"{API_BASE}/vision/analyze", json=vision_data)
            if resp.status_code == 200:
                result = resp.json()
                    print(f"{GREEN}✓ Vision analysis successful!{RESET}")
                    
                    print("\nAnalysis Results:")
                    print(f"- Text extracted: {result.get('text', 'None')}")
                    print(f"- Description: {result.get('description', 'None')[:100]}...")
                    print(f"- Tags: {', '.join(result.get('tags', [])[:5])}")
                    
                    if result.get('objects'):
                        print(f"- Objects detected: {', '.join(result['objects'][:5])}")
                    
                    return True
            else:
                error = resp.text()
                print(f"{RED}✗ Vision analysis failed: {error}{RESET}")
                    print("Possible issues:")
                    print("- GPT-4.1 deployment doesn't support vision")
                    print("- Check AZURE_OPENAI_DEPLOYMENT in .env")
                    return False
                    
        except Exception as e:
            print(f"{RED}✗ Error: {str(e)}{RESET}")
            return False


async def test_embedding():
    """Test text-embedding-ada-002"""
    print(f"\n{BLUE}Testing text-embedding-ada-002 (Semantic Search)...{RESET}")
    
    async with httpx.AsyncClient() as client:
        # First, add some test content
        print("1. Adding test content...")
        test_content = {
            "content": "Artificial intelligence and machine learning are transforming technology. "
                      "Neural networks and deep learning enable computers to learn from data.",
            "title": "AI and Machine Learning Overview",
            "tags": ["ai", "ml", "technology"]
        }
        
        try:
            resp = await client.post(f"{API_BASE}/capture", json=test_content)
            if resp.status_code == 201:
                print(f"{GREEN}✓ Test content added{RESET}")
            elif resp.status_code == 400:
                print(f"{YELLOW}Test content might already exist{RESET}")
                    
            # Wait for embedding generation
            await asyncio.sleep(2)
            
            # Test semantic search
            print("2. Testing semantic search...")
            search_params = {
                "query": "deep learning neural networks",
                "semantic": "true",
                "limit": 5
            }
            
            resp = await client.get(f"{API_BASE}/search", params=search_params)
            if resp.status_code == 200:
                results = resp.json()
                    
                    if results and len(results) > 0:
                        print(f"{GREEN}✓ Semantic search working! Found {len(results)} results{RESET}")
                        
                        # Check for semantic features
                        first_result = results[0]
                        if 'relevance_score' in first_result:
                            print(f"- Relevance scoring: {GREEN}✓ Active{RESET}")
                        else:
                            print(f"- Relevance scoring: {YELLOW}⚠ Not found{RESET}")
                        
                        print(f"\nTop result: {first_result['title']}")
                        if 'score' in first_result:
                            print(f"Score: {first_result['score']}")
                        
                        return True
                    else:
                        print(f"{YELLOW}⚠ No search results found{RESET}")
                        print("Embeddings might not be generated yet")
                        return False
            else:
                error = resp.text()
                print(f"{RED}✗ Search failed: {error}{RESET}")
                return False
                    
        except Exception as e:
            print(f"{RED}✗ Error: {str(e)}{RESET}")
            return False


async def check_backend_health():
    """Check if backend is running"""
    print(f"{BLUE}Checking backend health...{RESET}")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/timeline?limit=1")
            if resp.status_code == 200:
                print(f"{GREEN}✓ Backend is running{RESET}")
                return True
            else:
                print(f"{RED}✗ Backend returned status {resp.status_code}{RESET}")
                return False
    except Exception as e:
        print(f"{RED}✗ Backend is not accessible: {str(e)}{RESET}")
        print(f"Make sure backend is running on {API_BASE}")
        return False


async def main():
    """Run tests based on command line argument"""
    if not await check_backend_health():
        print("\nPlease start the backend first:")
        print("cd PRSNL && docker-compose up -d")
        return
    
    # Get test to run
    test_name = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print(f"\n{BLUE}PRSNL v2.0 - Azure OpenAI Model Quick Test{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    
    results = {}
    
    if test_name in ["whisper", "all"]:
        results["whisper"] = await test_whisper()
    
    if test_name in ["vision", "all"]:
        results["vision"] = await test_vision()
    
    if test_name in ["embedding", "all"]:
        results["embedding"] = await test_embedding()
    
    # Summary
    if len(results) > 0:
        print(f"\n{BLUE}{'='*50}{RESET}")
        print(f"{BLUE}Test Summary:{RESET}")
        for model, success in results.items():
            status = f"{GREEN}✓ Working{RESET}" if success else f"{RED}✗ Not Working{RESET}"
            print(f"  {model.upper()}: {status}")
        
        # Overall status
        all_working = all(results.values())
        if all_working:
            print(f"\n{GREEN}All tested models are working correctly!{RESET}")
        else:
            print(f"\n{YELLOW}Some models need attention. Check the errors above.{RESET}")
            print("\nCommon fixes:")
            print("1. Check Azure OpenAI deployments in Azure Portal")
            print("2. Verify deployment names in .env file")
            print("3. Check backend logs: docker logs prsnl_backend -f")
    else:
        print("\nUsage: python quick_model_test.py [whisper|vision|embedding|all]")


if __name__ == "__main__":
    asyncio.run(main())