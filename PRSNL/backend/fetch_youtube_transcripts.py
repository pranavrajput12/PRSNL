#!/usr/bin/env python3
"""
Fetch YouTube transcripts directly without using Whisper API
This avoids rate limits and is much faster
"""

import asyncio
import asyncpg
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
from datetime import timedelta

# Database connection
DB_URL = "postgresql://postgres:postgres@db:5432/prsnl"

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"youtube\.com/embed/([a-zA-Z0-9_-]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_transcript(transcript_data):
    """Format transcript with timestamps"""
    full_text = ""
    key_moments = []
    
    for i, entry in enumerate(transcript_data):
        timestamp = str(timedelta(seconds=int(entry['start'])))
        text = entry['text'].strip()
        full_text += f"[{timestamp}] {text}\n"
        
        # Extract key moments (every 5th entry or important ones)
        if i % 5 == 0 or len(text) > 100:
            key_moments.append({
                "timestamp": timestamp,
                "text": text[:100] + "..." if len(text) > 100 else text
            })
    
    return full_text, key_moments[:10]  # Limit to 10 key moments

async def update_video_transcript(conn, video_id, transcript, key_moments, summary):
    """Update video with transcript and metadata"""
    # Update transcription field
    await conn.execute("""
        UPDATE items 
        SET transcription = $1,
            metadata = metadata || $2::jsonb
        WHERE id = $3
    """, transcript, json.dumps({
        "has_transcript": True,
        "key_moments": key_moments,
        "transcript_summary": summary
    }), video_id)

async def process_videos():
    """Process all YouTube videos without transcripts"""
    conn = await asyncpg.connect(DB_URL)
    
    # Get YouTube videos without transcripts
    rows = await conn.fetch("""
        SELECT id, title, url 
        FROM items 
        WHERE url LIKE '%youtube%' 
        AND (transcription IS NULL OR transcription = '')
        ORDER BY created_at DESC
    """)
    
    print(f"Found {len(rows)} YouTube videos without transcripts\n")
    
    success = 0
    failed = 0
    
    for row in rows:
        video_id = extract_video_id(row['url'])
        if not video_id:
            print(f"✗ Could not extract video ID from: {row['url']}")
            failed += 1
            continue
        
        try:
            print(f"Processing: {row['title'][:60]}...")
            
            # Get transcript from YouTube
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Format transcript
            transcript, key_moments = format_transcript(transcript_data)
            
            # Create summary from first few entries
            summary_entries = transcript_data[:5]
            summary = " ".join([entry['text'] for entry in summary_entries])[:500]
            
            # Update database
            await update_video_transcript(
                conn, 
                row['id'], 
                transcript, 
                key_moments,
                summary
            )
            
            print(f"✓ Success: {row['title'][:60]} ({len(transcript)} chars)")
            success += 1
            
        except Exception as e:
            print(f"✗ Failed: {row['title'][:60]} - {str(e)}")
            failed += 1
    
    await conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Total videos: {len(rows)}")
    print(f"Successfully processed: {success}")
    print(f"Failed: {failed}")
    
    # Verify results
    conn = await asyncpg.connect(DB_URL)
    count = await conn.fetchval("""
        SELECT COUNT(*) 
        FROM items 
        WHERE url LIKE '%youtube%' 
        AND transcription IS NOT NULL 
        AND transcription != ''
    """)
    await conn.close()
    
    print(f"Total videos with transcripts in DB: {count}")

if __name__ == "__main__":
    asyncio.run(process_videos())