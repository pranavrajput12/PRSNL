#!/usr/bin/env python3
"""
Reset bookmarks to pending status so they get reprocessed by the capture engine
"""
import psycopg2
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
    
    # Reset bookmarks that have placeholder content
    print("=== Resetting Bookmarks for Reprocessing ===")
    
    # Update bookmarks to pending status
    cur.execute("""
        UPDATE items 
        SET status = 'pending',
            raw_content = NULL,
            processed_content = NULL,
            search_vector = NULL,
            summary = NULL
        WHERE user_id = 'e03c9686-09b0-4a06-b236-d0839ac7f5df'
        AND type = 'bookmark'
        AND (
            summary LIKE 'Saved bookmark for%'
            OR summary IS NULL
            OR raw_content IS NULL
        )
        RETURNING id, title, url
    """)
    
    reset_items = cur.fetchall()
    
    print(f"Reset {len(reset_items)} bookmarks to pending status")
    
    for item_id, title, url in reset_items:
        print(f"\n- {title[:60]}...")
        print(f"  URL: {url}")
        print(f"  ID: {item_id}")
    
    conn.commit()
    
    print("\n✓ Bookmarks have been reset to pending status")
    print("  The capture engine should reprocess them automatically")
    print("  Check the backend logs to monitor progress")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")