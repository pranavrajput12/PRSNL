#!/usr/bin/env python3
"""
Test script to debug GitHub preview generation
"""
import asyncio
import json
import os
import sys

# Add the backend app to the path
sys.path.append('/Users/pronav/Personal Knowledge Base/PRSNL/backend')

from app.services.preview_service import preview_service


async def test_preview():
    """Test GitHub preview generation"""
    test_urls = [
        "https://github.com/fastapi/fastapi",
        "https://github.com/sveltejs/svelte",
        "https://github.com/anthropics/claude-code"
    ]
    
    for url in test_urls:
        print(f"\n🧪 Testing preview for: {url}")
        try:
            result = await preview_service.generate_preview(url, 'development')
            print(f"✅ Preview generated successfully:")
            print(f"   Type: {result.get('type')}")
            print(f"   Platform: {result.get('platform')}")
            if result.get('repo'):
                print(f"   Repo: {result['repo'].get('full_name')}")
                print(f"   Description: {result['repo'].get('description', 'N/A')[:100]}...")
                print(f"   Stars: {result.get('stats', {}).get('stars', 0)}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_preview())