#!/usr/bin/env python3
"""
Simple reprocess script for bookmarks
"""
import asyncio
import asyncpg
import os
from datetime import datetime
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def process_bookmarks():
    """Process bookmarks and fetch their content"""
    # Direct database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get bookmarks without content
        bookmarks = await conn.fetch("""
            SELECT id, url, title
            FROM items 
            WHERE type = 'bookmark'
            AND (raw_content IS NULL OR processed_content IS NULL)
            LIMIT 5
        """)
        
        print(f"Found {len(bookmarks)} bookmarks to process")
        
        if not bookmarks:
            print("No bookmarks need processing!")
            return
            
        # For now, just add some sample content to test the system
        # In a real implementation, this would fetch actual content from URLs
        for bookmark in bookmarks:
            print(f"\nProcessing: {bookmark['title']}")
            print(f"  URL: {bookmark['url']}")
            
            # Sample content based on the bookmark
            sample_content = f"""
            Title: {bookmark['title']}
            URL: {bookmark['url']}
            
            This is sample content for testing knowledge base retrieval.
            The actual content would be fetched from the URL.
            
            Keywords: {bookmark['title'].lower().replace(' ', ', ')}
            Category: Technology, Web Development
            
            Description: This bookmark contains information about {bookmark['title']}.
            It was saved for future reference and contains valuable insights.
            """
            
            # Update the bookmark with sample content
            await conn.execute("""
                UPDATE items 
                SET 
                    raw_content = $2,
                    processed_content = $2,
                    status = 'processed',
                    updated_at = NOW()
                WHERE id = $1
            """, bookmark['id'], sample_content)
            
            print(f"  ✓ Added sample content")
            
        print("\nDone processing bookmarks!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(process_bookmarks())