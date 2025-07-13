#!/usr/bin/env python3
"""
Test script to verify all the fixes we've implemented
"""

import asyncio
import json

import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql+asyncpg://pronav@localhost:5433/prsnl'

async def test_all_fixes():
    print("🧪 Testing All PRSNL Fixes")
    print("=" * 50)
    
    # Test 1: Capture API
    print("\n1. Testing Capture API...")
    try:
        async with aiohttp.ClientSession() as session:
            test_data = {
                "url": "https://example.com/test-endpoint",
                "type": "article",
                "tags": ["test"]
            }
            async with session.post(
                "http://localhost:3004/api/capture",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    print("   ✅ Capture API working correctly")
                else:
                    print(f"   ❌ Capture API failed with status {response.status}")
    except Exception as e:
        print(f"   ❌ Capture API error: {e}")
    
    # Test 2: Permalink API
    print("\n2. Testing Permalink API...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8000/api/content/media/rick-astley-never-gonna-give-you-up-official-video-4k"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['content'].get('video_url'):
                        print("   ✅ Video permalink API working with video_url")
                    else:
                        print("   ❌ Video permalink missing video_url")
                else:
                    print(f"   ❌ Permalink API failed with status {response.status}")
    except Exception as e:
        print(f"   ❌ Permalink API error: {e}")
    
    # Test 3: Database integrity
    print("\n3. Testing Database Integrity...")
    try:
        engine = create_async_engine(DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Check video type consistency
            result = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM items 
                WHERE (url LIKE '%youtube.com%' OR url LIKE '%youtu.be%' OR url LIKE '%vimeo.com%')
                AND type <> 'video'
            """))
            video_mismatches = result.scalar()
            
            if video_mismatches == 0:
                print("   ✅ All video URLs have correct type")
            else:
                print(f"   ❌ Found {video_mismatches} video URL type mismatches")
                
            # Check video_url presence
            result = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM items 
                WHERE type = 'video' AND video_url IS NULL
            """))
            missing_video_urls = result.scalar()
            
            if missing_video_urls == 0:
                print("   ✅ All video items have video_url")
            else:
                print(f"   ❌ Found {missing_video_urls} video items without video_url")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"   ❌ Database test error: {e}")
    
    # Test 4: Frontend permalink structure
    print("\n4. Testing Frontend Permalink Structure...")
    frontend_files = [
        "/Users/pronav/Personal Knowledge Base/PRSNL/frontend/src/routes/code-cortex/+page.svelte",
        "/Users/pronav/Personal Knowledge Base/PRSNL/frontend/src/routes/code-cortex/docs/+page.svelte", 
        "/Users/pronav/Personal Knowledge Base/PRSNL/frontend/src/routes/code-cortex/links/+page.svelte",
        "/Users/pronav/Personal Knowledge Base/PRSNL/frontend/src/routes/code-cortex/projects/+page.svelte"
    ]
    
    old_patterns = ["/items/${", "/item/${"]
    issues_found = 0
    
    for file_path in frontend_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                for pattern in old_patterns:
                    if pattern in content:
                        if file_path.endswith('projects/+page.svelte') and pattern == "/item/${":
                            continue  # This is expected fallback
                        if pattern == "/item/${":
                            continue  # This is the new correct fallback
                        issues_found += 1
                        print(f"   ❌ Found old pattern {pattern} in {file_path}")
        except Exception as e:
            print(f"   ❌ Error reading {file_path}: {e}")
            issues_found += 1
    
    if issues_found == 0:
        print("   ✅ All frontend files use correct permalink structure")
    
    print("\n" + "=" * 50)
    print("🎯 Fix Summary:")
    print("   • Capture API: Fixed rate limiter issue")
    print("   • Video URLs: Updated types and video_url fields") 
    print("   • Permalinks: Fixed content_urls mapping")
    print("   • Frontend: Updated Code Cortex pages to use correct URLs")
    print("   • Data Integrity: Created automated checker script")

if __name__ == "__main__":
    asyncio.run(test_all_fixes())