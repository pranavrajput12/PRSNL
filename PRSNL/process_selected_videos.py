#!/usr/bin/env python3
"""
Process selected YouTube videos to generate transcripts
Videos to process:
1. Justin Bieber - Love Yourself (d3e82f53-0944-46d8-b365-6c7235a7eea0)
4. Ed Sheeran - Shape of You (dc469a4b-b01f-4d41-823b-70d4b7a38fb6)
"""

import asyncio
import asyncpg
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
from datetime import timedelta

# Database connection
DB_URL = "postgresql://postgres:postgres@localhost:5432/prsnl"

# Video IDs to process - Let's try technical videos instead
VIDEO_IDS_TO_PROCESS = [
    "dc507430-62b3-4025-bc84-47dabf4444f7",  # AWS Certified Solutions Architect
    "c0c08c41-3b32-4e83-8181-cd756d078c60"   # Machine Learning Crash Course
]

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
        
        # Extract key moments (every 30 seconds or important ones)
        if i % 30 == 0 or len(text) > 100 or i < 5:
            key_moments.append({
                "timestamp": timestamp,
                "text": text[:100] + "..." if len(text) > 100 else text
            })
    
    return full_text, key_moments[:15]  # Limit to 15 key moments

async def update_video_transcript(conn, video_id, transcript, key_moments, summary):
    """Update video with transcript and metadata"""
    # Update transcription field and metadata
    await conn.execute("""
        UPDATE items 
        SET transcription = $1,
            metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb,
            summary = CASE 
                WHEN summary IS NULL OR summary = '' THEN $3
                ELSE summary
            END
        WHERE id = $4
    """, transcript, json.dumps({
        "has_transcript": True,
        "key_moments": key_moments,
        "transcript_summary": summary,
        "transcript_generated_at": str(timedelta(seconds=0))
    }), summary, video_id)

async def process_videos():
    """Process selected YouTube videos"""
    conn = await asyncpg.connect(DB_URL)
    
    # Get the selected videos
    rows = await conn.fetch("""
        SELECT id, title, url, summary
        FROM items 
        WHERE id = ANY($1::uuid[])
        ORDER BY created_at DESC
    """, VIDEO_IDS_TO_PROCESS)
    
    print(f"Processing {len(rows)} selected videos\n")
    
    success = 0
    failed = 0
    
    for row in rows:
        video_id = extract_video_id(row['url'])
        if not video_id:
            print(f"✗ Could not extract video ID from: {row['url']}")
            failed += 1
            continue
        
        try:
            print(f"Processing: {row['title']}")
            
            # Get transcript from YouTube
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Format transcript
            transcript, key_moments = format_transcript(transcript_data)
            
            # Create summary from first few entries if none exists
            if not row['summary'] or row['summary'] == '':
                summary_entries = transcript_data[:10]
                summary = "Song lyrics: " + " ".join([entry['text'] for entry in summary_entries])[:300] + "..."
            else:
                summary = row['summary']
            
            # Update database
            await update_video_transcript(
                conn, 
                row['id'], 
                transcript, 
                key_moments,
                summary
            )
            
            print(f"✓ Success: {row['title']} - Transcript length: {len(transcript)} chars")
            print(f"  Key moments extracted: {len(key_moments)}")
            success += 1
            
        except Exception as e:
            print(f"✗ Failed: {row['title']} - {str(e)}")
            failed += 1
    
    await conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Total videos processed: {len(rows)}")
    print(f"Successfully processed: {success}")
    print(f"Failed: {failed}")
    
    # Verify results
    conn = await asyncpg.connect(DB_URL)
    
    # Check which videos now have transcripts
    verified = await conn.fetch("""
        SELECT id, title, 
               LENGTH(transcription) as transcript_length,
               metadata->>'has_transcript' as has_transcript
        FROM items 
        WHERE id = ANY($1::uuid[])
    """, VIDEO_IDS_TO_PROCESS)
    
    print(f"\n=== Verification ===")
    for v in verified:
        print(f"- {v['title']}: {v['transcript_length'] or 0} chars, has_transcript={v['has_transcript']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(process_videos())