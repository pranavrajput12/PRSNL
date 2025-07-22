#!/usr/bin/env python3
"""
Test Jina Reader service
"""
import asyncio
from app.services.jina_reader import JinaReaderService

async def test_jina():
    jina = JinaReaderService()
    
    print(f"Jina Reader enabled: {jina.enabled}")
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering"
    ]
    
    for url in test_urls:
        print(f"\n=== Testing: {url} ===")
        
        try:
            result = await jina.scrape_url(url)
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                data = result.get('data', {})
                content = data.get('content', '')
                print(f"Title: {data.get('title', 'N/A')}")
                print(f"Content length: {len(content)} chars")
                print(f"Content preview: {content[:300]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_jina())