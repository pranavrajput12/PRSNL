#!/usr/bin/env python3
"""
Quick test to add content through direct database insertion
"""

import psycopg2
import json
from datetime import datetime
from uuid import uuid4

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="prsnl",
    user="prsnl",
    password="prsnl123"
)
cur = conn.cursor()

# Test data
items = [
    # YouTube videos
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "summary": "The official video for Rick Astley's classic hit from the 80s",
        "metadata": {"type": "video", "platform": "youtube", "duration": 213}
    },
    {
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "title": "PSY - GANGNAM STYLE",
        "summary": "The viral K-pop sensation that took the world by storm",
        "metadata": {"type": "video", "platform": "youtube", "duration": 252}
    },
    {
        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
        "summary": "The Latin hit that broke YouTube records",
        "metadata": {"type": "video", "platform": "youtube", "duration": 282}
    },
    {
        "url": "https://www.youtube.com/watch?v=60ItHLz5WEA",
        "title": "Alan Walker - Faded",
        "summary": "Electronic music hit with over 3 billion views",
        "metadata": {"type": "video", "platform": "youtube", "duration": 212}
    },
    {
        "url": "https://www.youtube.com/watch?v=7wtfhZwyrcc",
        "title": "Imagine Dragons - Believer",
        "summary": "Rock anthem about pain and personal growth",
        "metadata": {"type": "video", "platform": "youtube", "duration": 204}
    },
    {
        "url": "https://www.youtube.com/watch?v=fWNaR-rxAic",
        "title": "Carly Rae Jepsen - Call Me Maybe",
        "summary": "The catchy pop hit from 2012",
        "metadata": {"type": "video", "platform": "youtube", "duration": 193}
    },
    # Articles
    {
        "url": "https://www.theverge.com/2025/1/8/ai-revolution",
        "title": "The AI Revolution: How Machine Learning is Changing Everything",
        "summary": "Artificial intelligence has moved from science fiction to daily reality",
        "metadata": {"type": "article", "source": "The Verge"}
    },
    {
        "url": "https://techcrunch.com/2025/1/8/startup-funding",
        "title": "Startup Funding Reaches New Heights in 2025",
        "summary": "Venture capital investments have surged to record levels",
        "metadata": {"type": "article", "source": "TechCrunch"}
    },
    {
        "url": "https://www.wired.com/story/quantum-computing-breakthrough",
        "title": "Quantum Computing Finally Delivers on Its Promise",
        "summary": "After years of hype, quantum computers are solving real problems",
        "metadata": {"type": "article", "source": "Wired"}
    },
    {
        "url": "https://arstechnica.com/science/2025/01/mars-colony",
        "title": "First Mars Colony Reaches 100 Residents",
        "summary": "The red planet's first permanent settlement celebrates a milestone",
        "metadata": {"type": "article", "source": "Ars Technica"}
    },
    # Tweets
    {
        "url": "https://twitter.com/elonmusk/status/1234567890",
        "title": "Elon Musk on Mars colonization",
        "summary": "Making life multiplanetary is essential for the long-term survival of humanity",
        "metadata": {"type": "tweet", "platform": "twitter", "author": "@elonmusk"}
    },
    {
        "url": "https://twitter.com/satyanadella/status/1234567891",
        "title": "Satya Nadella on AI ethics",
        "summary": "As we advance AI capabilities, we must ensure they augment human potential",
        "metadata": {"type": "tweet", "platform": "twitter", "author": "@satyanadella"}
    },
    {
        "url": "https://twitter.com/sundarpichai/status/1234567892",
        "title": "Sundar Pichai announces new AI features",
        "summary": "Excited to announce our latest AI breakthroughs",
        "metadata": {"type": "tweet", "platform": "twitter", "author": "@sundarpichai"}
    },
    {
        "url": "https://twitter.com/timcook/status/1234567893",
        "title": "Tim Cook on privacy",
        "summary": "Privacy is a fundamental human right",
        "metadata": {"type": "tweet", "platform": "twitter", "author": "@timcook"}
    },
    # Images
    {
        "url": "https://images.unsplash.com/photo-1518770660439-4636190af475",
        "title": "Modern Technology Workspace",
        "summary": "A clean desk setup with multiple monitors",
        "metadata": {"type": "image", "source": "Unsplash"}
    },
    {
        "url": "https://images.unsplash.com/photo-1461988320302-91bde64fc8e4",
        "title": "AI and Machine Learning Visualization",
        "summary": "Abstract representation of neural networks",
        "metadata": {"type": "image", "source": "Unsplash"}
    }
]

# Tags for items
tags_map = {
    "video": ["entertainment", "music", "viral"],
    "article": ["technology", "news", "innovation"],
    "tweet": ["social", "tech-leaders", "insights"],
    "image": ["visual", "design", "tech"]
}

print("🚀 Adding content to PRSNL database...\n")

# First, create tags
tag_ids = {}
for tag_type, tag_names in tags_map.items():
    for tag_name in tag_names:
        cur.execute(
            "INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            (tag_name,)
        )
        tag_ids[tag_name] = cur.fetchone()[0]

# Insert items
for item in items:
    item_id = str(uuid4())
    
    # Insert item
    cur.execute(
        """
        INSERT INTO items (id, url, title, summary, status, metadata, created_at, updated_at, accessed_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        """,
        (item_id, item["url"], item["title"], item["summary"], "completed", json.dumps(item["metadata"]))
    )
    
    # Add tags based on type
    item_type = item["metadata"]["type"]
    if item_type in tags_map:
        for tag_name in tags_map[item_type]:
            if tag_name in tag_ids:
                cur.execute(
                    "INSERT INTO item_tags (item_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (item_id, tag_ids[tag_name])
                )
    
    print(f"✅ Added: {item['title']}")

# Commit all changes
conn.commit()

# Get count
cur.execute("SELECT COUNT(*) FROM items")
total = cur.fetchone()[0]

# Get type breakdown
cur.execute("""
    SELECT 
        metadata->>'type' as item_type,
        COUNT(*) as count
    FROM items
    GROUP BY metadata->>'type'
    ORDER BY count DESC
""")

print(f"\n📊 Summary:")
print(f"Total items: {total}")
print("\nBreakdown by type:")
for row in cur.fetchall():
    print(f"  - {row[0]}: {row[1]}")

cur.close()
conn.close()

print("\n✨ Done! Check http://localhost:3002 to see the content.")