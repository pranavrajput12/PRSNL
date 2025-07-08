#!/usr/bin/env python3
"""
Process all YouTube videos to generate transcripts and summaries
Respects Whisper API rate limit of 3 calls per minute
"""

import asyncio
import httpx
import asyncpg
from datetime import datetime
import time

# Database connection
DB_URL = "postgresql://postgres:postgres@localhost:5432/prsnl"

async def get_unprocessed_videos():
    """Get all YouTube videos without transcripts"""
    conn = await asyncpg.connect(DB_URL)
    
    # Get YouTube videos without transcripts
    rows = await conn.fetch("""
        SELECT id, title, url 
        FROM items 
        WHERE url LIKE '%youtube%' 
        AND (transcription IS NULL OR transcription = '')
        AND status = 'completed'
        ORDER BY created_at DESC
    """)
    
    await conn.close()
    
    return [(row['id'], row['title'], row['url']) for row in rows]

async def process_video(video_id: str, title: str):
    """Process a single video through the API"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"Processing: {title[:60]}...")
            
            response = await client.post(
                "http://localhost:8000/api/video-streaming/process",
                json={"item_id": str(video_id)}
            )
            
            if response.status_code == 200:
                print(f"✓ Success: {title[:60]}")
                return True
            else:
                print(f"✗ Failed: {title[:60]} - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing {title[:60]}: {e}")
            return False

async def main():
    """Process all videos with rate limiting"""
    videos = await get_unprocessed_videos()
    print(f"\nFound {len(videos)} videos without transcripts\n")
    
    if not videos:
        print("No videos to process!")
        return
    
    # Process videos with rate limiting (3 per minute for Whisper)
    # We'll process in batches of 3 with 60 second delays
    batch_size = 3
    batch_delay = 61  # 61 seconds to be safe
    
    processed = 0
    failed = 0
    
    for i in range(0, len(videos), batch_size):
        batch = videos[i:i+batch_size]
        batch_start = time.time()
        
        print(f"\n--- Processing batch {i//batch_size + 1}/{(len(videos) + batch_size - 1)//batch_size} ---")
        
        # Process batch concurrently
        tasks = []
        for video_id, title, url in batch:
            tasks.append(process_video(video_id, title))
        
        results = await asyncio.gather(*tasks)
        
        # Count results
        for result in results:
            if result:
                processed += 1
            else:
                failed += 1
        
        # Wait if needed before next batch
        if i + batch_size < len(videos):
            elapsed = time.time() - batch_start
            if elapsed < batch_delay:
                wait_time = batch_delay - elapsed
                print(f"\nWaiting {wait_time:.0f} seconds for rate limit...")
                await asyncio.sleep(wait_time)
    
    print(f"\n=== Summary ===")
    print(f"Total videos: {len(videos)}")
    print(f"Successfully processed: {processed}")
    print(f"Failed: {failed}")
    
    # Check if transcripts were actually saved
    conn = await asyncpg.connect(DB_URL)
    transcript_count = await conn.fetchval("""
        SELECT COUNT(*) 
        FROM items 
        WHERE url LIKE '%youtube%' 
        AND transcription IS NOT NULL 
        AND transcription != ''
    """)
    await conn.close()
    
    print(f"Total videos with transcripts in DB: {transcript_count}")

if __name__ == "__main__":
    asyncio.run(main())