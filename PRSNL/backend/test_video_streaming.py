"""
Test script for Video Streaming feature
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000/api"

# Test video URLs
TEST_VIDEOS = {
    "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
    "twitter": "https://twitter.com/elonmusk/status/1234567890",  # Example Twitter video
    "instagram": "https://www.instagram.com/p/ABC123/"  # Example Instagram video
}

async def test_video_streaming():
    async with aiohttp.ClientSession() as session:
        print("🎥 Testing Video Streaming Feature\n")
        
        # 1. Test URL checking
        print("1️⃣ Testing video URL detection...")
        
        for platform, url in TEST_VIDEOS.items():
            async with session.get(
                f"{API_BASE}/video-streaming/check-url",
                params={"url": url}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result["is_video"]:
                        print(f"   ✅ {platform}: Detected as video")
                        print(f"      Video ID: {result['data']['video_id']}")
                    else:
                        print(f"   ❌ {platform}: Not detected as video")
                else:
                    print(f"   ❌ {platform}: Check failed with status {resp.status}")
        
        # 2. First, let's capture a YouTube video
        print("\n2️⃣ Capturing a YouTube video...")
        
        # Capture the video first
        capture_data = {
            "url": TEST_VIDEOS["youtube"],
            "title": "Test Video",
            "tags": ["test", "video"]
        }
        
        video_item_id = None
        async with session.post(
            f"{API_BASE}/capture",
            json=capture_data
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                video_item_id = result.get("item_id")
                print(f"   ✅ Video captured with ID: {video_item_id}")
            else:
                print(f"   ❌ Capture failed: {resp.status}")
                return
        
        # 3. Process the video
        if video_item_id:
            print("\n3️⃣ Processing video (extracting metadata & transcript)...")
            
            async with session.post(
                f"{API_BASE}/video-streaming/process",
                json={"item_id": video_item_id}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    data = result["data"]
                    print(f"   ✅ Video processed successfully:")
                    print(f"      Platform: {data['platform']}")
                    print(f"      Has transcript: {data['has_transcript']}")
                    if data["metadata"].get("title"):
                        print(f"      Title: {data['metadata']['title']}")
                    if data["analysis"].get("summary"):
                        print(f"      Summary: {data['analysis']['summary'][:100]}...")
                    if data["analysis"].get("key_topics"):
                        print(f"      Topics: {', '.join(data['analysis']['key_topics'])}")
                else:
                    print(f"   ❌ Processing failed: {resp.status}")
        
        # 4. Test video timeline
        print("\n4️⃣ Testing video timeline...")
        
        async with session.get(
            f"{API_BASE}/video-streaming/timeline",
            params={"limit": 10}
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                timeline = result["data"]
                print(f"   ✅ Video timeline retrieved:")
                print(f"      Total videos: {timeline['total']}")
                print(f"      Showing: {len(timeline['videos'])}")
                for video in timeline["videos"][:3]:
                    print(f"      - {video['title']} ({video['platform']})")
            else:
                print(f"   ❌ Timeline failed: {resp.status}")
        
        # 5. Test related videos
        if video_item_id:
            print("\n5️⃣ Finding related videos...")
            
            async with session.post(
                f"{API_BASE}/video-streaming/related",
                json={
                    "item_id": video_item_id,
                    "limit": 5
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    related = result["data"]["related_videos"]
                    print(f"   ✅ Found {len(related)} related videos:")
                    for video in related:
                        print(f"      - {video['title']} (similarity: {video['similarity']:.2f})")
                else:
                    print(f"   ❌ Related videos failed: {resp.status}")
        
        # 6. Test mini-course creation
        print("\n6️⃣ Testing mini-course generation...")
        
        async with session.post(
            f"{API_BASE}/video-streaming/mini-course",
            json={
                "topic": "python",
                "skill_level": "beginner",
                "max_videos": 5
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                course = result["data"]
                if course.get("modules"):
                    print(f"   ✅ Mini-course created: {course.get('title', 'Python Course')}")
                    print(f"      Description: {course.get('description', 'N/A')}")
                    print(f"      Modules: {len(course.get('modules', []))}")
                    for module in course.get("modules", [])[:3]:
                        print(f"      {module['order']}. {module['title']}")
                        if module.get("why_this_order"):
                            print(f"         Reason: {module['why_this_order']}")
                else:
                    print(f"   ⚠️  No videos found for mini-course on 'python'")
            else:
                print(f"   ❌ Mini-course creation failed: {resp.status}")
        
        # 7. Test batch processing
        print("\n7️⃣ Testing batch video processing...")
        
        async with session.post(f"{API_BASE}/video-streaming/batch-process") as resp:
            if resp.status == 200:
                result = await resp.json()
                data = result["data"]
                print(f"   ✅ Batch processing complete:")
                print(f"      Processed: {data['processed_count']}")
                print(f"      Failed: {data['failed_count']}")
                if data["processed"]:
                    print(f"      Processed videos:")
                    for video in data["processed"][:3]:
                        print(f"      - {video['title']} ({video['platform']})")
            else:
                print(f"   ❌ Batch processing failed: {resp.status}")
        
        # 8. Test video stats
        print("\n8️⃣ Getting video statistics...")
        
        async with session.get(f"{API_BASE}/video-streaming/stats") as resp:
            if resp.status == 200:
                result = await resp.json()
                stats = result["data"]
                print(f"   ✅ Video statistics:")
                print(f"      Total videos: {stats['total_videos']}")
                print(f"      Videos with transcripts: {stats['videos_with_transcripts']} ({stats['transcript_percentage']:.1f}%)")
                print(f"      By platform:")
                for platform_stat in stats["videos_by_platform"]:
                    print(f"      - {platform_stat['platform']}: {platform_stat['count']}")
            else:
                print(f"   ❌ Stats failed: {resp.status}")
        
        print("\n✅ Video Streaming tests completed!")

if __name__ == "__main__":
    asyncio.run(test_video_streaming())