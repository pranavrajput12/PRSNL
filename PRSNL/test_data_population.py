#!/usr/bin/env python3
"""
Test data population script for PRSNL
Adds various types of content to test all features
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000/api"

# Test data with various content types
TEST_ITEMS = [
    {
        "url": "https://github.com/mnfst/manifest",
        "title": "Manifest - Modern Backend Platform",
        "type": "article"
    },
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Classic YouTube Video",
        "type": "video"
    },
    {
        "url": "https://docs.anthropic.com/en/docs/intro",
        "title": "Claude Documentation",
        "type": "article"
    },
    {
        "url": "https://github.com/sveltejs/kit",
        "title": "SvelteKit - Web Framework",
        "type": "article"
    },
    {
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "title": "Tech Tutorial Video",
        "type": "video"
    },
    {
        "url": "https://fastapi.tiangolo.com/",
        "title": "FastAPI Documentation",
        "type": "article"
    },
    {
        "url": "https://redis.io/docs/latest/",
        "title": "Redis Documentation",
        "type": "article"
    },
    {
        "url": "https://www.postgresql.org/docs/",
        "title": "PostgreSQL Documentation",
        "type": "article"
    },
    {
        "url": "https://tailwindcss.com/docs/installation",
        "title": "Tailwind CSS Documentation",
        "type": "article"
    },
    {
        "url": "https://www.typescriptlang.org/docs/",
        "title": "TypeScript Handbook",
        "type": "article"
    }
]

# Manual notes to add
MANUAL_NOTES = [
    {
        "title": "Project Architecture Notes",
        "content": """# PRSNL Architecture Overview

## Backend Stack
- FastAPI for API framework
- PostgreSQL with pgvector for embeddings
- Redis for caching
- Azure OpenAI for all AI features

## Frontend Stack  
- SvelteKit with TypeScript
- Tailwind CSS for styling
- D3.js for visualizations

## Key Features
1. Universal capture from any URL
2. AI-powered metadata extraction
3. Semantic search with embeddings
4. Content organization with tags
5. Timeline view of all content
""",
        "tags": ["architecture", "documentation", "backend", "frontend"]
    },
    {
        "title": "AI Integration Strategy",
        "content": """# AI Integration in PRSNL

## Current Implementation
- Exclusive use of Azure OpenAI
- GPT-4 for content processing
- Ada-002 for embeddings
- Whisper for transcription

## Optimization Tips
1. Cache AI responses in Redis
2. Batch embedding generation
3. Use streaming for better UX
4. Implement retry logic

## Cost Management
- Monitor token usage
- Use appropriate models for tasks
- Implement request batching
""",
        "tags": ["ai", "azure", "optimization", "cost-management"]
    },
    {
        "title": "Development Workflow",
        "content": """# PRSNL Development Workflow

## Local Development
1. Start Docker containers: `docker compose up -d`
2. Backend: `cd backend && uvicorn app.main:app --reload`
3. Frontend: `cd frontend && npm run dev`

## Testing
- Backend: `pytest` in backend directory
- Frontend: `npm run test` in frontend directory

## Deployment
- Use Docker Compose for production
- Set proper environment variables
- Enable HTTPS with reverse proxy
""",
        "tags": ["development", "workflow", "docker", "deployment"]
    }
]

async def test_capture_endpoint(client: httpx.AsyncClient):
    """Test the capture endpoint with various URLs"""
    print("\n📥 Testing Capture Endpoint...")
    
    captured_items = []
    
    for item in TEST_ITEMS:
        try:
            # First get AI suggestions
            suggest_response = await client.post(
                f"{BASE_URL}/suggest",
                json={"url": item["url"]}
            )
            
            if suggest_response.status_code == 200:
                suggestions = suggest_response.json()
                print(f"✅ Got AI suggestions for {item['title']}")
                
                # Now capture with AI-generated metadata
                capture_data = {
                    "url": item["url"],
                    "title": suggestions.get("title", item["title"]),
                    "summary": suggestions.get("summary", ""),
                    "tags": suggestions.get("tags", []),
                    "category": suggestions.get("category", "general")
                }
                
                capture_response = await client.post(
                    f"{BASE_URL}/capture",
                    json=capture_data
                )
                
                if capture_response.status_code in [200, 201, 202]:
                    result = capture_response.json()
                    if result.get('status') == 'pending':
                        print(f"⏳ Capture pending: {capture_data['title']} (ID: {result.get('id')})")
                        captured_items.append(result.get('id'))
                    else:
                        print(f"✅ Captured: {capture_data['title']}")
                else:
                    print(f"❌ Failed to capture {item['url']}: {capture_response.text}")
            else:
                print(f"❌ Failed to get suggestions for {item['url']}: {suggest_response.text}")
                
        except Exception as e:
            print(f"❌ Error processing {item['url']}: {str(e)}")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    return captured_items

async def test_manual_notes(client: httpx.AsyncClient):
    """Test adding manual notes"""
    print("\n📝 Adding Manual Notes...")
    
    for note in MANUAL_NOTES:
        try:
            # Add manual note using capture endpoint with text content
            capture_data = {
                "title": note["title"],
                "content": note["content"],
                "tags": note["tags"],
                "category": "note"
            }
            
            response = await client.post(
                f"{BASE_URL}/capture",
                json=capture_data
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                if result.get('status') == 'pending':
                    print(f"⏳ Note capture pending: {note['title']} (ID: {result.get('id')})")
                else:
                    print(f"✅ Added note: {note['title']}")
            else:
                print(f"❌ Failed to add note {note['title']}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error adding note {note['title']}: {str(e)}")

async def check_capture_status(client: httpx.AsyncClient, capture_ids: list):
    """Check status of pending captures"""
    print("\n📊 Checking Capture Status...")
    
    completed = 0
    failed = 0
    
    for capture_id in capture_ids:
        try:
            response = await client.get(f"{BASE_URL}/capture/{capture_id}/status")
            if response.status_code == 200:
                status = response.json()
                if status.get('status') == 'completed':
                    completed += 1
                elif status.get('status') == 'failed':
                    failed += 1
        except:
            pass
    
    print(f"✅ Completed: {completed}, ❌ Failed: {failed}, ⏳ Pending: {len(capture_ids) - completed - failed}")

async def test_search_functionality(client: httpx.AsyncClient):
    """Test search functionality"""
    print("\n🔍 Testing Search...")
    
    search_queries = [
        "documentation",
        "AI",
        "backend",
        "video",
        "architecture"
    ]
    
    for query in search_queries:
        try:
            response = await client.get(
                f"{BASE_URL}/search",
                params={"query": query}
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Search '{query}': Found {len(results)} results")
            else:
                print(f"❌ Search failed for '{query}': {response.text}")
                
        except Exception as e:
            print(f"❌ Error searching '{query}': {str(e)}")

async def test_timeline_endpoint(client: httpx.AsyncClient):
    """Test timeline endpoint"""
    print("\n📅 Testing Timeline...")
    
    try:
        response = await client.get(
            f"{BASE_URL}/timeline",
            params={"limit": 20, "offset": 0}
        )
        
        if response.status_code == 200:
            items = response.json()
            
            # Handle both list and dict responses
            if isinstance(items, dict) and 'items' in items:
                items = items['items']
            
            if isinstance(items, list):
                print(f"✅ Timeline: Retrieved {len(items)} items")
                
                # Show item types
                item_types = {}
                for item in items:
                    if isinstance(item, dict):
                        item_type = item.get("item_type", "unknown")
                        item_types[item_type] = item_types.get(item_type, 0) + 1
                
                if item_types:
                    print(f"   Item types: {item_types}")
            else:
                print(f"✅ Timeline response: {type(items)}")
        else:
            print(f"❌ Timeline failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error fetching timeline: {str(e)}")

async def test_semantic_search(client: httpx.AsyncClient):
    """Test semantic search functionality"""
    print("\n🧠 Testing Semantic Search...")
    
    # First get an item to find similar ones
    try:
        timeline_response = await client.get(
            f"{BASE_URL}/timeline",
            params={"limit": 1}
        )
        
        if timeline_response.status_code == 200:
            items = timeline_response.json()
            
            # Handle both list and dict responses
            if isinstance(items, dict) and 'items' in items:
                items = items['items']
            
            if isinstance(items, list) and len(items) > 0:
                item = items[0]
                item_id = item.get("id")
                
                if item_id:
                    # Find similar items
                    similar_response = await client.get(
                        f"{BASE_URL}/items/{item_id}/similar"
                    )
                    
                    if similar_response.status_code == 200:
                        similar_items = similar_response.json()
                        print(f"✅ Found {len(similar_items)} similar items to '{item.get('title', 'Unknown')}'")
                    else:
                        print(f"❌ Similar items search failed: {similar_response.text}")
                else:
                    print("❌ No item ID found")
            else:
                print("❌ No items found for semantic search test")
        
    except Exception as e:
        print(f"❌ Error testing semantic search: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Starting PRSNL Test Data Population")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test capture with AI suggestions
        captured_ids = await test_capture_endpoint(client)
        
        # Add manual notes
        await test_manual_notes(client)
        
        # Wait a bit for processing
        print("\n⏳ Waiting for content processing...")
        await asyncio.sleep(5)
        
        # Check capture status
        if captured_ids:
            await check_capture_status(client, captured_ids)
        
        # Test search functionality
        await test_search_functionality(client)
        
        # Test timeline
        await test_timeline_endpoint(client)
        
        # Test semantic search
        await test_semantic_search(client)
    
    print("\n✅ Test data population complete!")
    print("You can now test the frontend at http://localhost:3002")

if __name__ == "__main__":
    asyncio.run(main())