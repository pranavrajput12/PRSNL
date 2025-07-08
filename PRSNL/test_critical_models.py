#!/usr/bin/env python3
"""
Quick test to verify critical Azure OpenAI models are working
Focuses on Vision and Embeddings which are the most important
"""

import asyncio
import aiohttp
import os
from datetime import datetime

API_BASE = "http://localhost:8000/api"

async def test_vision():
    """Test Vision model is working"""
    print("\n🔍 Testing Vision Model...")
    
    # Create a simple test image
    from PIL import Image, ImageDraw
    test_image = "/tmp/vision_test.png"
    
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "PRSNL Vision Test", fill='black')
    draw.text((50, 100), f"Time: {datetime.now()}", fill='gray')
    img.save(test_image)
    
    async with aiohttp.ClientSession() as session:
        with open(test_image, 'rb') as f:
            form_data = aiohttp.FormData()
            form_data.add_field('file', f, filename='test.png', content_type='image/png')
            form_data.add_field('save_to_db', 'false')  # Don't save to avoid clutter
            
            async with session.post(f"{API_BASE}/vision/analyze", data=form_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    data = result.get('data', {})
                    print(f"✅ Vision API working!")
                    print(f"   Description: {data.get('description', 'N/A')[:100]}...")
                    print(f"   Text extracted: {data.get('text', 'N/A')}")
                    return True
                else:
                    print(f"❌ Vision API failed: {resp.status}")
                    return False
    
    os.remove(test_image)

async def test_embeddings():
    """Test embedding generation and search"""
    print("\n🔍 Testing Embeddings Model...")
    
    # Create a test document
    test_doc = {
        "content": "This is a test document for Azure OpenAI embeddings",
        "title": f"Embedding Test {datetime.now().strftime('%H:%M:%S')}"
    }
    
    async with aiohttp.ClientSession() as session:
        # Create document
        async with session.post(
            f"{API_BASE}/capture",
            json=test_doc,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 201:
                result = await resp.json()
                item_id = result["id"]
                print(f"✅ Document created: {item_id}")
                
                # Wait for processing
                print("   Waiting for processing...")
                await asyncio.sleep(15)
                
                # Check if item was processed successfully
                async with session.get(f"{API_BASE}/items/{item_id}") as item_resp:
                    if item_resp.status == 200:
                        item = await item_resp.json()
                        if item['status'] == 'completed':
                            print(f"✅ Item processed successfully")
                            print(f"   Summary: {item.get('summary', 'N/A')[:100]}...")
                            
                            # Test search
                            async with session.get(
                                f"{API_BASE}/search",
                                params={"query": "Azure OpenAI", "semantic": "true"}
                            ) as search_resp:
                                if search_resp.status == 200:
                                    results = await search_resp.json()
                                    if results.get('items'):
                                        print(f"✅ Semantic search working! Found {len(results['items'])} results")
                                        return True
                                    else:
                                        print("⚠️  Search returned no results")
                                else:
                                    print(f"❌ Search failed: {search_resp.status}")
                        else:
                            print(f"❌ Item processing failed: {item['status']}")
                            if item.get('metadata', {}).get('error'):
                                print(f"   Error: {item['metadata']['error']}")
            else:
                print(f"❌ Failed to create document: {resp.status}")
    
    return False

async def main():
    print("🚀 Testing Critical Azure OpenAI Models")
    print("=" * 50)
    
    # Wait for backend
    print("Waiting for backend...")
    await asyncio.sleep(5)
    
    vision_ok = await test_vision()
    embeddings_ok = await test_embeddings()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"  Vision Model: {'✅ WORKING' if vision_ok else '❌ FAILED'}")
    print(f"  Embeddings Model: {'✅ WORKING' if embeddings_ok else '❌ FAILED'}")
    
    if vision_ok and embeddings_ok:
        print("\n🎉 All critical models are working!")
        print("The Azure OpenAI integration is successful.")
    else:
        print("\n⚠️  Some models need attention.")

if __name__ == "__main__":
    asyncio.run(main())