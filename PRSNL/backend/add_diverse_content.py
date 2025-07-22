import json
import random
import uuid
from datetime import datetime, timedelta

import psycopg2

# Database connection
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='prsnl',
    user='prsnl',
    password='prsnl123'
)
cur = conn.cursor()

# Articles
articles = [
    {
        'title': 'The Complete Guide to Python Async Programming',
        'url': 'https://realpython.com/async-io-python/',
        'summary': 'Learn async programming in Python with asyncio, including coroutines, tasks, and event loops.',
        'platform': 'web'
    },
    {
        'title': 'Understanding React Hooks: A Deep Dive',
        'url': 'https://blog.logrocket.com/react-hooks-complete-guide/',
        'summary': 'Comprehensive guide to React Hooks including useState, useEffect, and custom hooks.',
        'platform': 'web'
    },
    {
        'title': 'Building Scalable Microservices with Kubernetes',
        'url': 'https://kubernetes.io/docs/tutorials/microservices/',
        'summary': 'Learn how to design, deploy, and manage microservices architecture using Kubernetes.',
        'platform': 'web'
    },
    {
        'title': 'The State of AI in 2025: Trends and Predictions',
        'url': 'https://techcrunch.com/2025/01/ai-trends/',
        'summary': 'Analysis of current AI trends, breakthrough technologies, and future predictions.',
        'platform': 'web'
    }
]

# Tweets
tweets = [
    {
        'title': 'Elon Musk on Mars Mission Update',
        'url': 'https://x.com/elonmusk/status/1234567890',
        'content': 'Starship static fire test complete. We are go for orbital launch attempt next week. Mars, here we come! 🚀',
        'platform': 'twitter'
    },
    {
        'title': 'OpenAI announces GPT-5 capabilities',
        'url': 'https://x.com/openai/status/2345678901',
        'content': 'Introducing GPT-5: Our most capable model yet. Features include improved reasoning, multimodal understanding, and 10x faster inference.',
        'platform': 'twitter'
    },
    {
        'title': 'Google unveils quantum breakthrough',
        'url': 'https://x.com/sundarpichai/status/3456789012',
        'content': 'Proud to announce Willow, our new quantum computing chip. 5 minutes to solve problems that would take classical computers 10 septillion years.',
        'platform': 'twitter'
    },
    {
        'title': 'Apple Vision Pro 2 leak',
        'url': 'https://x.com/mingchikuo/status/4567890123',
        'content': 'Supply chain sources confirm: Vision Pro 2 will feature 4K per-eye displays, 50% lighter design, and all-day battery life. Launch Q2 2025.',
        'platform': 'twitter'
    }
]

# Insert articles
print("Adding articles...")
for article in articles:
    item_id = str(uuid.uuid4())
    created_at = datetime.now() - timedelta(days=random.randint(1, 30))
    metadata = {
        'source': article['platform'],
        'read_time': f"{random.randint(3, 15)} min",
        'author': 'Various Authors',
        'tags': ['technology', 'programming', 'tutorial']
    }
    
    cur.execute("""
        INSERT INTO items (
            id, title, url, type, platform,
            summary, status, created_at, metadata
        ) VALUES (
            %s, %s, %s, 'article', %s,
            %s, 'completed', %s, %s
        )
    """, (
        item_id,
        article['title'],
        article['url'],
        article['platform'],
        article['summary'],
        created_at,
        json.dumps(metadata)
    ))
    print(f"✓ Added article: {article['title']}")

# Insert tweets
print("\nAdding tweets...")
for tweet in tweets:
    item_id = str(uuid.uuid4())
    created_at = datetime.now() - timedelta(hours=random.randint(1, 72))
    metadata = {
        'tweet': {
            'author': tweet['url'].split('/')[3],
            'likes': random.randint(1000, 50000),
            'retweets': random.randint(100, 5000),
            'replies': random.randint(50, 1000)
        }
    }
    
    cur.execute("""
        INSERT INTO items (
            id, title, url, type, platform,
            processed_content, status, created_at, metadata
        ) VALUES (
            %s, %s, %s, 'tweet', %s,
            %s, 'completed', %s, %s
        )
    """, (
        item_id,
        tweet['title'],
        tweet['url'],
        tweet['platform'],
        tweet['content'],
        created_at,
        json.dumps(metadata)
    ))
    print(f"✓ Added tweet: {tweet['title']}")

# Add some images/screenshots
print("\nAdding images...")
images = [
    {
        'title': 'System Architecture Diagram',
        'url': 'https://example.com/architecture.png',
        'summary': 'High-level overview of microservices architecture'
    },
    {
        'title': 'UI/UX Mockup for Dashboard',
        'url': 'https://example.com/dashboard-mockup.png',
        'summary': 'New dashboard design with dark mode support'
    }
]

for image in images:
    item_id = str(uuid.uuid4())
    created_at = datetime.now() - timedelta(days=random.randint(1, 7))
    metadata = {
        'image': {
            'width': 1920,
            'height': 1080,
            'format': 'png',
            'size_kb': random.randint(100, 500)
        }
    }
    
    cur.execute("""
        INSERT INTO items (
            id, title, url, type, platform,
            summary, status, created_at, metadata
        ) VALUES (
            %s, %s, %s, 'image', 'web',
            %s, 'completed', %s, %s
        )
    """, (
        item_id,
        image['title'],
        image['url'],
        image['summary'],
        created_at,
        json.dumps(metadata)
    ))
    print(f"✓ Added image: {image['title']}")

conn.commit()
cur.close()
conn.close()

print(f"\n✅ Successfully added:")
print(f"   - {len(articles)} articles")
print(f"   - {len(tweets)} tweets")
print(f"   - {len(images)} images")
print(f"\nTotal items in database now...")