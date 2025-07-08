#!/usr/bin/env python3
"""
Test script to add various content types through the PRSNL API
"""

import requests
import json
from datetime import datetime, timedelta
import random

API_BASE_URL = "http://localhost:8001/api"

# Test data
youtube_videos = [
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "description": "The official video for Rick Astley's classic hit",
        "tags": ["music", "classic", "80s"]
    },
    {
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "title": "PSY - GANGNAM STYLE",
        "description": "The viral K-pop sensation that took the world by storm",
        "tags": ["music", "kpop", "viral"]
    },
    {
        "url": "https://www.youtube.com/watch?v=fWNaR-rxAic",
        "title": "Carly Rae Jepsen - Call Me Maybe",
        "description": "The catchy pop hit from 2012",
        "tags": ["music", "pop", "2012"]
    },
    {
        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
        "description": "The Latin hit that broke YouTube records",
        "tags": ["music", "latin", "reggaeton"]
    },
    {
        "url": "https://www.youtube.com/watch?v=60ItHLz5WEA",
        "title": "Alan Walker - Faded",
        "description": "Electronic music hit with over 3 billion views",
        "tags": ["music", "electronic", "edm"]
    },
    {
        "url": "https://www.youtube.com/watch?v=7wtfhZwyrcc",
        "title": "Imagine Dragons - Believer",
        "description": "Rock anthem about pain and personal growth",
        "tags": ["music", "rock", "motivational"]
    }
]

articles = [
    {
        "url": "https://www.theverge.com/2025/1/8/ai-revolution",
        "title": "The AI Revolution: How Machine Learning is Changing Everything",
        "content": "Artificial intelligence has moved from science fiction to daily reality...",
        "tags": ["technology", "ai", "machine-learning"]
    },
    {
        "url": "https://techcrunch.com/2025/1/8/startup-funding",
        "title": "Startup Funding Reaches New Heights in 2025",
        "content": "Venture capital investments have surged to record levels...",
        "tags": ["business", "startups", "venture-capital"]
    },
    {
        "url": "https://www.wired.com/story/quantum-computing-breakthrough",
        "title": "Quantum Computing Finally Delivers on Its Promise",
        "content": "After years of hype, quantum computers are solving real problems...",
        "tags": ["technology", "quantum", "computing"]
    },
    {
        "url": "https://arstechnica.com/science/2025/01/mars-colony",
        "title": "First Mars Colony Reaches 100 Residents",
        "content": "The red planet's first permanent settlement celebrates a milestone...",
        "tags": ["space", "mars", "science"]
    }
]

tweets = [
    {
        "url": "https://twitter.com/elonmusk/status/1234567890",
        "title": "Elon Musk on Mars colonization",
        "content": "Making life multiplanetary is essential for the long-term survival of humanity. Mars is the next step.",
        "tags": ["space", "mars", "future"]
    },
    {
        "url": "https://twitter.com/satyanadella/status/1234567891",
        "title": "Satya Nadella on AI ethics",
        "content": "As we advance AI capabilities, we must ensure they augment human potential while preserving human agency and dignity.",
        "tags": ["ai", "ethics", "technology"]
    },
    {
        "url": "https://twitter.com/sundarpichai/status/1234567892",
        "title": "Sundar Pichai announces new AI features",
        "content": "Excited to announce our latest AI breakthroughs that will make technology more helpful for everyone.",
        "tags": ["ai", "google", "innovation"]
    },
    {
        "url": "https://twitter.com/timcook/status/1234567893",
        "title": "Tim Cook on privacy",
        "content": "Privacy is a fundamental human right. At Apple, it's also one of our core values.",
        "tags": ["privacy", "apple", "technology"]
    }
]

images = [
    {
        "url": "https://images.unsplash.com/photo-1518770660439-4636190af475",
        "title": "Modern Technology Workspace",
        "content": "A clean desk setup with multiple monitors and modern tech gadgets",
        "tags": ["workspace", "technology", "productivity"]
    },
    {
        "url": "https://images.unsplash.com/photo-1461988320302-91bde64fc8e4",
        "title": "AI and Machine Learning Visualization",
        "content": "Abstract representation of neural networks and AI concepts",
        "tags": ["ai", "visualization", "technology"]
    }
]

def capture_item(item_data):
    """Capture a single item through the API"""
    try:
        # Prepare the capture request
        capture_data = {
            "url": item_data["url"],
            "tags": item_data.get("tags", []),
            "notes": item_data.get("description") or item_data.get("content", "")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/capture",
            json=capture_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Captured: {item_data['title']}")
            return result
        else:
            print(f"❌ Failed to capture {item_data['title']}: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error capturing {item_data['title']}: {str(e)}")
        return None

def main():
    print("🚀 Starting PRSNL API content test...\n")
    
    # Test API health
    try:
        health_response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health")
        if health_response.status_code == 200:
            print("✅ API is healthy\n")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        return
    
    import time
    
    # Capture YouTube videos
    print("📹 Capturing YouTube videos...")
    for i, video in enumerate(youtube_videos):
        capture_item(video)
        if i < len(youtube_videos) - 1:
            time.sleep(6)  # Wait 6 seconds between captures to avoid rate limit
    
    print("\n📰 Capturing articles...")
    for i, article in enumerate(articles):
        capture_item(article)
        if i < len(articles) - 1:
            time.sleep(6)
    
    print("\n🐦 Capturing tweets...")
    for i, tweet in enumerate(tweets):
        capture_item(tweet)
        if i < len(tweets) - 1:
            time.sleep(6)
    
    print("\n🖼️ Capturing images...")
    for i, image in enumerate(images):
        capture_item(image)
        if i < len(images) - 1:
            time.sleep(6)
    
    # Get and display timeline
    print("\n📊 Fetching timeline...")
    try:
        timeline_response = requests.get(f"{API_BASE_URL}/timeline?limit=20")
        if timeline_response.status_code == 200:
            timeline = timeline_response.json()
            print(f"✅ Timeline has {len(timeline['items'])} items")
            
            # Count by type
            type_counts = {}
            for item in timeline['items']:
                item_type = item.get('item_type', 'unknown')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            print("\n📈 Content breakdown:")
            for item_type, count in type_counts.items():
                print(f"   - {item_type}: {count}")
                
        else:
            print(f"❌ Failed to fetch timeline: {timeline_response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching timeline: {str(e)}")
    
    # Test analytics
    print("\n📊 Testing analytics endpoints...")
    analytics_endpoints = [
        "/analytics/usage_patterns",
        "/analytics/trends?timeframe=7d",
        "/analytics/topics"
    ]
    
    for endpoint in analytics_endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint} working")
            else:
                print(f"❌ {endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} error: {str(e)}")
    
    print("\n✨ Test complete! Check http://localhost:3002 to see the content.")

if __name__ == "__main__":
    main()