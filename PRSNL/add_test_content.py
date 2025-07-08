#!/usr/bin/env python3
"""
Add test content to PRSNL using API endpoints
"""
import asyncio
import httpx
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000/api"

# Test content
VIDEOS = [
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "tags": ["music", "classic", "meme"],
        "notes": "The ultimate rickroll video"
    },
    {
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "title": "PSY - GANGNAM STYLE",
        "tags": ["music", "kpop", "viral"],
        "notes": "Most viewed video on YouTube for years"
    },
    {
        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
        "tags": ["music", "latin", "record-breaking"],
        "notes": "Broke all YouTube records"
    },
    {
        "url": "https://www.youtube.com/watch?v=JGwWNGJdvx8",
        "title": "Ed Sheeran - Shape of You",
        "tags": ["music", "pop", "ed-sheeran"],
        "notes": "One of the most streamed songs ever"
    },
    {
        "url": "https://www.youtube.com/watch?v=RgKAFK5djSk",
        "title": "Wiz Khalifa - See You Again ft. Charlie Puth",
        "tags": ["music", "tribute", "fast-furious"],
        "notes": "Tribute to Paul Walker"
    },
    {
        "url": "https://www.youtube.com/watch?v=fRh_vgS2dFE",
        "title": "Justin Bieber - Sorry",
        "tags": ["music", "pop", "justin-bieber"],
        "notes": "Part of Purpose album"
    },
    {
        "url": "https://www.youtube.com/watch?v=oyEuk8j8imI",
        "title": "Justin Bieber - Love Yourself",
        "tags": ["music", "pop", "ed-sheeran-written"],
        "notes": "Written by Ed Sheeran"
    }
]

TWEETS = [
    {
        "url": "https://twitter.com/elonmusk/status/1465347002012626947",
        "title": "Elon Musk on Twitter Blue",
        "tags": ["twitter", "elon", "social-media"],
        "notes": "Discussion about Twitter verification"
    },
    {
        "url": "https://twitter.com/naval/status/1002103360646823936",
        "title": "Naval - How to Get Rich Thread",
        "tags": ["wisdom", "wealth", "thread"],
        "notes": "Famous thread on building wealth"
    },
    {
        "url": "https://twitter.com/paulg/status/1436009229434626051",
        "title": "Paul Graham on Startups",
        "tags": ["startups", "ycombinator", "advice"],
        "notes": "Startup wisdom from YC founder"
    },
    {
        "url": "https://twitter.com/OpenAI/status/1598016004541321216",
        "title": "ChatGPT Launch Announcement",
        "tags": ["ai", "chatgpt", "openai"],
        "notes": "The tweet that changed everything"
    }
]

GITHUB_REPOS = [
    {
        "url": "https://github.com/facebook/react",
        "title": "React - A JavaScript library for building user interfaces",
        "tags": ["javascript", "frontend", "framework", "facebook"],
        "notes": "The library that revolutionized frontend development"
    },
    {
        "url": "https://github.com/tensorflow/tensorflow",
        "title": "TensorFlow - Machine Learning Framework",
        "tags": ["machine-learning", "ai", "google", "python"],
        "notes": "Google's open source ML framework"
    },
    {
        "url": "https://github.com/torvalds/linux",
        "title": "Linux Kernel Source",
        "tags": ["linux", "kernel", "operating-system"],
        "notes": "The kernel that powers most of the internet"
    },
    {
        "url": "https://github.com/microsoft/vscode",
        "title": "Visual Studio Code",
        "tags": ["editor", "ide", "microsoft", "typescript"],
        "notes": "Most popular code editor"
    },
    {
        "url": "https://github.com/rust-lang/rust",
        "title": "Rust Programming Language",
        "tags": ["rust", "systems-programming", "memory-safety"],
        "notes": "Memory safe systems programming language"
    }
]

ARTICLES = [
    {
        "url": "https://www.paulgraham.com/ds.html",
        "title": "Do Things that Don't Scale",
        "tags": ["startups", "advice", "paulgraham"],
        "notes": "Classic PG essay on early stage startups"
    },
    {
        "url": "https://waitbutwhy.com/2015/01/artificial-intelligence-revolution-1.html",
        "title": "The AI Revolution: The Road to Superintelligence",
        "tags": ["ai", "future", "long-read"],
        "notes": "Tim Urban's comprehensive take on AI"
    },
    {
        "url": "https://stratechery.com/2020/the-end-of-the-beginning/",
        "title": "The End of the Beginning",
        "tags": ["tech", "analysis", "ben-thompson"],
        "notes": "Ben Thompson on the tech industry maturation"
    }
]

async def capture_item(client: httpx.AsyncClient, item_data: dict, item_type: str):
    """Capture a single item using the API"""
    try:
        # First, get AI suggestions for better metadata
        try:
            suggest_response = await client.post(
                f"{API_BASE}/suggest",
                json={"url": item_data["url"]},
                timeout=30.0
            )
            if suggest_response.status_code == 200:
                suggestions = suggest_response.json()
                # Merge AI suggestions with our data
                if "summary" in suggestions:
                    item_data["summary"] = suggestions["summary"]
                if "tags" in suggestions and len(suggestions["tags"]) > 0:
                    # Combine our tags with AI tags
                    all_tags = list(set(item_data.get("tags", []) + suggestions["tags"]))
                    item_data["tags"] = all_tags[:6]  # Limit to 6 tags
        except Exception as e:
            print(f"Could not get AI suggestions for {item_data['url']}: {e}")
        
        # Prepare capture request
        capture_data = {
            "url": item_data["url"],
            "title": item_data["title"],
            "tags": item_data.get("tags", []),
            "notes": item_data.get("notes", ""),
            "item_type": item_type
        }
        
        if "summary" in item_data:
            capture_data["summary"] = item_data["summary"]
        
        # Capture the item
        response = await client.post(
            f"{API_BASE}/capture",
            json=capture_data,
            timeout=60.0  # Longer timeout for video processing
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Captured: {item_data['title']}")
            return result
        else:
            print(f"✗ Failed to capture {item_data['title']}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error capturing {item_data['title']}: {e}")
        return None

async def main():
    """Add all test content"""
    async with httpx.AsyncClient() as client:
        print("Adding test content to PRSNL...\n")
        
        # Capture videos
        print("📹 Adding YouTube videos...")
        for video in VIDEOS:
            await capture_item(client, video, "video")
            await asyncio.sleep(1)  # Small delay between requests
        
        print("\n🐦 Adding tweets...")
        for tweet in TWEETS:
            await capture_item(client, tweet, "tweet")
            await asyncio.sleep(1)
        
        print("\n🐙 Adding GitHub repositories...")
        for repo in GITHUB_REPOS:
            await capture_item(client, repo, "github")
            await asyncio.sleep(1)
        
        print("\n📄 Adding articles...")
        for article in ARTICLES:
            await capture_item(client, article, "article")
            await asyncio.sleep(1)
        
        # Test search to verify content
        print("\n🔍 Testing search...")
        search_response = await client.get(f"{API_BASE}/search?query=music&limit=5")
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"Found {len(results.get('results', []))} music-related items")
        
        # Get timeline to show all items
        print("\n📊 Checking timeline...")
        timeline_response = await client.get(f"{API_BASE}/timeline?limit=50")
        if timeline_response.status_code == 200:
            timeline = timeline_response.json()
            print(f"Total items in timeline: {len(timeline.get('items', []))}")
            
            # Count by type
            type_counts = {}
            for item in timeline.get('items', []):
                item_type = item.get('item_type', 'unknown')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            print("\nContent breakdown:")
            for item_type, count in type_counts.items():
                print(f"  {item_type}: {count}")

if __name__ == "__main__":
    asyncio.run(main())