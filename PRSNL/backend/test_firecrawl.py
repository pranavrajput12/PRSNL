#!/usr/bin/env python3
"""
Test Firecrawl API directly
"""
import asyncio
from app.services.firecrawl_service import FirecrawlService

async def test_firecrawl():
    firecrawl = FirecrawlService()
    
    print(f"Firecrawl enabled: {firecrawl.enabled}")
    print(f"API key: {firecrawl.api_key[:10]}...{firecrawl.api_key[-4:]}")
    print(f"Base URL: {firecrawl.base_url}")
    
    if firecrawl.enabled:
        try:
            # Test with a simple page
            test_url = "https://example.com"
            print(f"\nTesting with: {test_url}")
            
            result = await firecrawl.scrape_url(test_url)
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"Title: {data.get('title', 'N/A')}")
                content = data.get('markdown', '') or data.get('content', '')
                print(f"Content length: {len(content)} chars")
                print(f"Content preview: {content[:200]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Exception: {e}")
    else:
        print("Firecrawl not enabled")

if __name__ == "__main__":
    asyncio.run(test_firecrawl())