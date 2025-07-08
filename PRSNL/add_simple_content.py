#!/usr/bin/env python3
"""
Add simple test content to PRSNL database directly
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
import uuid
import json
import random

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/prsnl"

# Simple test content
ITEMS = [
    # Videos
    {
        "title": "Introduction to Python Programming",
        "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
        "summary": "Learn Python basics in this comprehensive tutorial covering variables, functions, and basic programming concepts.",
        "item_type": "video",
        "tags": ["python", "programming", "tutorial", "beginner"],
        "platform": "youtube",
        "metadata": {"duration": 14400, "channel": "freeCodeCamp"}
    },
    {
        "title": "Machine Learning Crash Course",
        "url": "https://www.youtube.com/watch?v=N5E5YfP9gRs",
        "summary": "Google's fast-paced, practical introduction to machine learning featuring TensorFlow APIs.",
        "item_type": "video",
        "tags": ["machine-learning", "ai", "tensorflow", "google"],
        "platform": "youtube",
        "metadata": {"duration": 3600, "channel": "Google Developers"}
    },
    {
        "title": "React JS Full Course 2024",
        "url": "https://www.youtube.com/watch?v=b9eMGE7QtTk",
        "summary": "Complete React tutorial covering hooks, state management, and modern React patterns.",
        "item_type": "video",
        "tags": ["react", "javascript", "frontend", "web-development"],
        "platform": "youtube",
        "metadata": {"duration": 25200, "channel": "JavaScript Mastery"}
    },
    {
        "title": "Docker Tutorial for Beginners",
        "url": "https://www.youtube.com/watch?v=pTFZFxd4hOI",
        "summary": "Learn Docker containerization from scratch with practical examples.",
        "item_type": "video",
        "tags": ["docker", "devops", "containers", "tutorial"],
        "platform": "youtube",
        "metadata": {"duration": 10800, "channel": "Programming with Mosh"}
    },
    {
        "title": "AWS Certified Solutions Architect",
        "url": "https://www.youtube.com/watch?v=Ia-UEYYR44s",
        "summary": "Comprehensive guide to AWS services and preparation for certification exam.",
        "item_type": "video",
        "tags": ["aws", "cloud", "certification", "architecture"],
        "platform": "youtube",
        "metadata": {"duration": 36000, "channel": "freeCodeCamp"}
    },
    {
        "title": "Kubernetes Explained in 15 Minutes",
        "url": "https://www.youtube.com/watch?v=VnvRFRk_51k",
        "summary": "Quick introduction to Kubernetes container orchestration platform.",
        "item_type": "video",
        "tags": ["kubernetes", "k8s", "devops", "containers"],
        "platform": "youtube",
        "metadata": {"duration": 900, "channel": "TechWorld with Nana"}
    },
    
    # Tweets/Social
    {
        "title": "Paul Graham: Startups = Growth",
        "url": "https://twitter.com/paulg/status/1234567890",
        "summary": "If you want to understand startups, understand growth. Growth drives everything in a startup.",
        "item_type": "tweet",
        "tags": ["startups", "growth", "paulgraham", "advice"],
        "platform": "twitter",
        "metadata": {"author": "@paulg", "likes": 5420}
    },
    {
        "title": "Naval: How to Get Rich (without getting lucky)",
        "url": "https://twitter.com/naval/status/1002103360646823936",
        "summary": "Seek wealth, not money or status. Wealth is having assets that earn while you sleep.",
        "item_type": "tweet",
        "tags": ["wealth", "wisdom", "naval", "thread"],
        "platform": "twitter",
        "metadata": {"author": "@naval", "likes": 123000}
    },
    {
        "title": "Elon Musk on First Principles Thinking",
        "url": "https://twitter.com/elonmusk/status/9876543210",
        "summary": "Boil things down to their fundamental truths and reason up from there.",
        "item_type": "tweet",
        "tags": ["thinking", "innovation", "elon", "principles"],
        "platform": "twitter",  
        "metadata": {"author": "@elonmusk", "likes": 85000}
    },
    {
        "title": "Sam Altman: The Best Startup Ideas",
        "url": "https://twitter.com/sama/status/1357924680",
        "summary": "The best startup ideas are the ones that seem bad but are actually good.",
        "item_type": "tweet",
        "tags": ["startups", "ideas", "ycombinator", "advice"],
        "platform": "twitter",
        "metadata": {"author": "@sama", "likes": 12500}
    },
    
    # GitHub Repos
    {
        "title": "facebook/react - JavaScript UI Library",
        "url": "https://github.com/facebook/react",
        "summary": "A declarative, efficient, and flexible JavaScript library for building user interfaces.",
        "item_type": "github",
        "tags": ["react", "javascript", "frontend", "opensource"],
        "platform": "github",
        "metadata": {"stars": 215000, "language": "JavaScript"}
    },
    {
        "title": "torvalds/linux - Linux Kernel Source",
        "url": "https://github.com/torvalds/linux",
        "summary": "Linux kernel source tree maintained by Linus Torvalds.",
        "item_type": "github",
        "tags": ["linux", "kernel", "c", "opensource"],
        "platform": "github",
        "metadata": {"stars": 162000, "language": "C"}
    },
    {
        "title": "tensorflow/tensorflow - ML Framework",
        "url": "https://github.com/tensorflow/tensorflow",
        "summary": "An open source machine learning framework for everyone.",
        "item_type": "github",
        "tags": ["tensorflow", "machine-learning", "python", "google"],
        "platform": "github",
        "metadata": {"stars": 178000, "language": "Python"}
    },
    
    # Articles
    {
        "title": "How to Build a Personal Knowledge Management System",
        "url": "https://www.example.com/pkm-guide",
        "summary": "A comprehensive guide to building your own personal knowledge management system using modern tools.",
        "item_type": "article",
        "tags": ["pkm", "productivity", "knowledge", "guide"],
        "platform": "blog",
        "metadata": {"author": "Tech Writer", "read_time": 15}
    },
    {
        "title": "The Future of AI: GPT-4 and Beyond",
        "url": "https://www.example.com/future-of-ai",
        "summary": "Exploring the implications of large language models and their impact on society.",
        "item_type": "article",
        "tags": ["ai", "gpt4", "future", "technology"],
        "platform": "blog",
        "metadata": {"author": "AI Researcher", "read_time": 20}
    }
]

async def add_content():
    """Add content directly to database"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🚀 Adding test content to PRSNL database...\n")
        
        added_count = 0
        for idx, item in enumerate(ITEMS):
            try:
                # Generate timestamps with some variety
                created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                
                # Prepare item data
                item_id = str(uuid.uuid4())
                tags = item.get("tags", [])
                metadata = item.get("metadata", {})
                metadata["tags"] = ",".join(tags)
                metadata["category"] = tags[0] if tags else "uncategorized"
                metadata["item_type"] = item["item_type"]
                metadata["platform"] = item.get("platform", "web")
                
                # Insert into database
                await conn.execute("""
                    INSERT INTO items (
                        id, url, title, summary,
                        status, raw_content, processed_content,
                        search_vector, metadata, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7,
                        to_tsvector('english', $8), $9, $10
                    )
                """, 
                    item_id,
                    item["url"],
                    item["title"],
                    item.get("summary", ""),
                    "completed",
                    item.get("summary", ""),  # raw_content
                    item.get("summary", ""),  # processed_content
                    f"{item['title']} {item.get('summary', '')} {' '.join(tags)}",  # for search vector
                    json.dumps(metadata),
                    created_at
                )
                
                print(f"✅ Added: {item['title'][:50]}...")
                added_count += 1
                
            except Exception as e:
                print(f"❌ Failed to add {item['title']}: {e}")
        
        print(f"\n🎉 Successfully added {added_count}/{len(ITEMS)} items!")
        
        # Verify by counting items
        count = await conn.fetchval("SELECT COUNT(*) FROM items")
        print(f"📊 Total items in database: {count}")
        
        # Show breakdown by type
        type_counts = await conn.fetch("""
            SELECT metadata->>'item_type' as item_type, COUNT(*) as count 
            FROM items 
            GROUP BY metadata->>'item_type' 
            ORDER BY count DESC
        """)
        
        print("\n📈 Content breakdown:")
        for row in type_counts:
            print(f"   {row['item_type']}: {row['count']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_content())