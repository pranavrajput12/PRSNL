#!/usr/bin/env python3
"""Test GitHub OAuth endpoint to debug the internal server error"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.github_service import GitHubService
from app.services.cache import cache_service

async def test_github_oauth():
    """Test the GitHub OAuth flow initialization"""
    
    print("🔍 Testing GitHub OAuth Configuration")
    print("=" * 50)
    
    # Check configuration
    print(f"✅ GITHUB_CLIENT_ID: {'***' + settings.GITHUB_CLIENT_ID[-4:] if settings.GITHUB_CLIENT_ID else 'NOT SET'}")
    print(f"✅ GITHUB_CLIENT_SECRET: {'***' + settings.GITHUB_CLIENT_SECRET[-4:] if settings.GITHUB_CLIENT_SECRET else 'NOT SET'}")
    print(f"✅ BACKEND_URL: {settings.BACKEND_URL}")
    print(f"✅ ENCRYPTION_KEY length: {len(settings.ENCRYPTION_KEY)} chars")
    
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        print("❌ GitHub OAuth credentials not configured!")
        return
    
    print("\n🔍 Testing GitHub Service")
    print("=" * 50)
    
    try:
        # Test cache connection
        print("Testing cache service...")
        await cache_service.connect()
        print("✅ Cache service connected")
        
        # Initialize GitHub service
        github_service = GitHubService()
        print("✅ GitHub service initialized")
        
        # Test OAuth flow
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        auth_url = await github_service.init_oauth_flow(user_id)
        
        print(f"\n✅ OAuth URL generated successfully!")
        print(f"   URL: {auth_url[:100]}...")
        
        # Verify state was stored in cache
        # Extract state from URL
        import urllib.parse
        parsed = urllib.parse.urlparse(auth_url)
        params = urllib.parse.parse_qs(parsed.query)
        state = params.get('state', [None])[0]
        
        if state:
            cached_user_id = await cache_service.get(f"github_oauth_state:{state}")
            print(f"\n✅ State stored in cache: {bool(cached_user_id)}")
            if cached_user_id:
                print(f"   Cached user_id: {cached_user_id}")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cache_service.disconnect()
        print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_github_oauth())