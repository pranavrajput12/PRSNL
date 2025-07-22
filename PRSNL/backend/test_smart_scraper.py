#!/usr/bin/env python3
"""
Test Smart Scraper - Jina first with Firecrawl fallback
"""
import asyncio
from app.services.smart_scraper import SmartScraperService

async def test_smart_scraper():
    scraper = SmartScraperService()
    
    print("🧠 Testing Smart Scraper (Jina → Firecrawl fallback)")
    print(f"Firecrawl enabled: {scraper.firecrawl.enabled}")
    print()
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering",
        "https://httpbin.org/html",  # Should work with Jina
        "https://invalid-url-that-should-fail.com"  # Should fail both
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"{i}. Testing: {url}")
        
        try:
            result = await scraper.scrape_url(url)
            
            success = result.get('success', False)
            scraper_used = result.get('scraper_used', 'unknown')
            
            if success:
                data = result.get('data', {})
                content_length = len(data.get('content', ''))
                title = data.get('title', 'No title')[:50]
                
                emoji = "📖" if scraper_used == "jina" else "🔥"
                print(f"  {emoji} SUCCESS with {scraper_used}: {content_length} chars")
                print(f"  Title: {title}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"  ❌ FAILED ({scraper_used}): {error}")
                
        except Exception as e:
            print(f"  💥 EXCEPTION: {e}")
        
        print()
    
    # Show final statistics
    print("📊 Final Statistics:")
    stats = scraper.get_stats()
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Jina successes: {stats['jina_success']} ({stats['jina_success_rate']:.1f}%)")
    print(f"  Firecrawl successes: {stats['firecrawl_success']}")
    print(f"  💰 {stats['cost_savings']}")

if __name__ == "__main__":
    asyncio.run(test_smart_scraper())