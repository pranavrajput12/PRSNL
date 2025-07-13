import json
import time
from datetime import datetime, timedelta
from uuid import uuid4

import requests

BASE_URL = "http://localhost:8000/api"

def add_item(item_data):
    """Add a single item through the capture API"""
    try:
        response = requests.post(
            f"{BASE_URL}/capture",
            json=item_data
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Added: {item_data.get('title', 'Untitled')}")
            print(f"   ID: {result.get('id') or result.get('item_id')}")
            print(f"   Status: {result.get('status', 'pending')}")
            return True
        else:
            print(f"❌ Failed to add: {item_data.get('title', 'Untitled')}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding item: {e}")
        return False

def main():
    """Add various types of test data"""
    print("📊 Populating PRSNL database with test data...")
    print(f"   API endpoint: {BASE_URL}/capture")
    print()
    
    success_count = 0
    
    # Articles
    articles = [
        {
            "url": "http://example.com/article1",
            "title": "The Future of AI in Healthcare",
            "content": "AI is revolutionizing healthcare by improving diagnostics and personalized treatment plans.",
            "tags": ["AI", "healthcare", "future"]
        },
        {
            "url": "http://example.com/article2",
            "title": "Quantum Computing Explained",
            "content": "A beginner's guide to the complex world of quantum mechanics and computing.",
            "tags": ["quantum", "computing", "science"]
        },
    ]
    print("Adding articles...")
    for article in articles:
        if add_item(article):
            success_count += 1
        time.sleep(0.5)
    print()

    # Notes
    notes = [
        {
            "title": "Meeting Notes - Project Alpha",
            "content": "Discussed Q3 roadmap and resource allocation. Action items assigned.",
            "tags": ["meeting", "project-alpha", "roadmap"]
        },
        {
            "title": "Idea: Decentralized Knowledge Base",
            "content": "Concept for a blockchain-based personal knowledge management system.",
            "tags": ["idea", "blockchain", "PKM"]
        },
    ]
    print("Adding notes...")
    for note in notes:
        if add_item(note):
            success_count += 1
        time.sleep(0.5)
    print()

    # Videos (using existing add_test_videos.py content)
    from PRSNL.add_test_videos import TEST_VIDEOS
    print("Adding videos...")
    for video in TEST_VIDEOS:
        if add_item(video):
            success_count += 1
        time.sleep(0.5)
    print()

    print(f"\n📊 Summary: {success_count} items added successfully")
    
    # Optional: Verify total count
    try:
        response = requests.get(f"{BASE_URL}/timeline?limit=1")
        if response.status_code == 200:
            data = response.json()
            print(f"Total items in database (approx): {data.get('total', 'N/A')}")
    except Exception as e:
        print(f"Could not fetch total item count: {e}")

if __name__ == "__main__":
    main()
