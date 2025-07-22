#!/usr/bin/env python3
"""
Fix imported bookmarks that have no content by updating their status and adding basic content
"""
import psycopg2
import json
from datetime import datetime

try:
    # Connect to the database
    conn = psycopg2.connect(
        host="localhost",
        database="prsnl",
        user="pronav",
        password="",
        port=5432
    )
    
    cur = conn.cursor()
    
    # Update bookmarks with failed status to have basic content
    print("=== Fixing Bookmarks with Failed Status ===")
    
    # First, get all failed bookmarks
    cur.execute("""
        SELECT id, title, url, metadata
        FROM items 
        WHERE user_id = 'e03c9686-09b0-4a06-b236-d0839ac7f5df'
        AND type = 'bookmark'
        AND status = 'failed'
    """)
    
    failed_bookmarks = cur.fetchall()
    print(f"Found {len(failed_bookmarks)} failed bookmarks")
    
    for bookmark in failed_bookmarks:
        item_id, title, url, metadata = bookmark
        
        # Create basic content and summary
        content = f"Bookmark: {title}\nURL: {url}"
        summary = f"Saved bookmark for {title}"
        
        # Update the bookmark with basic content and change status
        cur.execute("""
            UPDATE items 
            SET status = 'completed',
                raw_content = %s,
                processed_content = %s,
                summary = %s,
                content = %s,
                search_vector = to_tsvector('english', %s)
            WHERE id = %s
        """, (content, content, summary, content, f"{title} {url}", item_id))
        
        print(f"Fixed: {title[:50]}...")
    
    conn.commit()
    print(f"\nSuccessfully updated {len(failed_bookmarks)} bookmarks")
    
    # Verify the update
    cur.execute("""
        SELECT COUNT(*), status 
        FROM items 
        WHERE user_id = 'e03c9686-09b0-4a06-b236-d0839ac7f5df'
        AND type = 'bookmark'
        GROUP BY status
    """)
    
    status_counts = cur.fetchall()
    print("\n=== Bookmark Status Summary ===")
    for count, status in status_counts:
        print(f"{status}: {count} bookmarks")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")