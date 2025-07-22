#!/usr/bin/env python3
"""
Debug Firecrawl API calls
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_firecrawl_direct():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    print(f"API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Test with simple request
    request_data = {
        "url": "https://example.com",
        "formats": ["markdown"]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"Request data: {request_data}")
    print(f"Headers: {dict(headers)}")
    
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0)
    ) as client:
        try:
            print("\nMaking request to Firecrawl...")
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                json=request_data,
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            try:
                result = response.json()
                print(f"Response JSON: {result}")
            except:
                print(f"Response text: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_firecrawl_direct())