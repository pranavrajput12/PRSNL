"""
Test script for Content Summarization feature
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api"

async def test_summarization():
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Content Summarization Feature\n")
        
        # 1. Test single item summarization
        print("1️⃣ Testing single item summarization...")
        
        # First, get an item ID from timeline
        async with session.get(f"{API_BASE}/timeline") as resp:
            if resp.status == 200:
                timeline_data = await resp.json()
                if timeline_data["items"]:
                    item_id = timeline_data["items"][0]["id"]
                    print(f"   Found item: {item_id}")
                    
                    # Test brief summary
                    async with session.post(
                        f"{API_BASE}/summarization/item",
                        json={
                            "item_id": item_id,
                            "summary_type": "brief"
                        }
                    ) as summary_resp:
                        if summary_resp.status == 200:
                            result = await summary_resp.json()
                            print(f"   ✅ Brief summary generated: {result['data']['summary'][:100]}...")
                        else:
                            print(f"   ❌ Failed: {summary_resp.status}")
                else:
                    print("   ⚠️  No items found to summarize")
            else:
                print(f"   ❌ Timeline fetch failed: {resp.status}")
        
        # 2. Test digest generation
        print("\n2️⃣ Testing digest generation...")
        
        # Test daily digest
        async with session.post(
            f"{API_BASE}/summarization/digest",
            json={
                "period": "daily"
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Daily digest generated:")
                print(f"      Items: {result['data']['item_count']}")
                print(f"      Executive Summary: {result['data'].get('executive_summary', 'N/A')[:200]}...")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 3. Test topic summary
        print("\n3️⃣ Testing topic summary...")
        
        async with session.post(
            f"{API_BASE}/summarization/topic",
            json={
                "topic": "technology",
                "limit": 10
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Topic summary for 'technology':")
                print(f"      Related items: {result['data']['item_count']}")
                print(f"      Summary: {result['data'].get('summary', 'N/A')[:200]}...")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 4. Test custom summary
        print("\n4️⃣ Testing custom summary...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        async with session.post(
            f"{API_BASE}/summarization/custom",
            json={
                "start_date": str(start_date),
                "end_date": str(end_date),
                "categories": ["tutorial", "reference"]
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Custom summary generated:")
                print(f"      Period: {start_date} to {end_date}")
                print(f"      Items: {result['data']['item_count']}")
                print(f"      Summary: {result['data'].get('summary', 'N/A')[:200]}...")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 5. Test digest preview
        print("\n5️⃣ Testing digest preview...")
        
        async with session.get(
            f"{API_BASE}/summarization/digest/preview?period=weekly"
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Weekly digest preview:")
                print(f"      Items: {result['item_count']}")
                print(f"      Categories: {json.dumps(result['categories'][:3], indent=2)}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        print("\n✅ Content Summarization tests completed!")

if __name__ == "__main__":
    asyncio.run(test_summarization())