#!/usr/bin/env python3
"""
Add test videos to PRSNL database for testing video library and mini-course features
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

# Test videos - educational content for mini-course testing
TEST_VIDEOS = [
    {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "title": "Me at the zoo - First YouTube Video Ever",
        "tags": ["youtube", "history", "first-video", "zoo", "elephants"]
    },
    {
        "url": "https://www.youtube.com/watch?v=OPf0YbXqDm0",
        "title": "Mark Ronson - Uptown Funk ft. Bruno Mars",
        "tags": ["music", "funk", "dance", "bruno-mars", "mark-ronson"]
    },
    {
        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
        "tags": ["music", "latin", "spanish", "reggaeton", "dance"]
    },
    {
        "url": "https://www.youtube.com/watch?v=fRh_vgS2dFE",
        "title": "Justin Bieber - Sorry (PURPOSE : The Movement)",
        "tags": ["music", "pop", "dance", "justin-bieber", "choreography"]
    },
    {
        "url": "https://www.youtube.com/watch?v=7PCkvCPvDXk",
        "title": "Ed Sheeran - Shape of You [Official Video]",
        "tags": ["music", "pop", "ed-sheeran", "dance", "workout"]
    }
]

def add_video(video_data):
    """Add a single video through the capture API"""
    try:
        response = requests.post(
            f"{BASE_URL}/capture",
            json=video_data
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Added: {video_data['title']}")
            print(f"   ID: {result.get('id') or result.get('item_id')}")
            print(f"   Status: {result.get('status', 'pending')}")
            return True
        else:
            print(f"❌ Failed to add: {video_data['title']}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding video: {e}")
        return False

def main():
    """Add all test videos"""
    print("🎥 Adding test videos to PRSNL database...")
    print(f"   API endpoint: {BASE_URL}/capture")
    print()
    
    success_count = 0
    
    for i, video in enumerate(TEST_VIDEOS, 1):
        print(f"{i}/{len(TEST_VIDEOS)} Processing: {video['title']}")
        
        if add_video(video):
            success_count += 1
        
        # Small delay to avoid overwhelming the API
        if i < len(TEST_VIDEOS):
            time.sleep(2)
        
        print()
    
    print(f"\n📊 Summary: {success_count}/{len(TEST_VIDEOS)} videos added successfully")
    
    # Check current video count
    try:
        response = requests.get(f"{BASE_URL}/timeline?limit=100")
        if response.status_code == 200:
            data = response.json()
            videos = [item for item in data['items'] if item['item_type'] == 'video']
            print(f"📹 Total videos in database: {len(videos)}")
    except Exception as e:
        print(f"Could not fetch video count: {e}")

if __name__ == "__main__":
    main()