#!/usr/bin/env python3
import psycopg2
import sys
from datetime import datetime, timedelta

try:
    # Connect to the database - ARM64 PostgreSQL on port 5432
    conn = psycopg2.connect(
        host="localhost",
        database="prsnl",
        user="pronav",
        password="",
        port=5432  # PostgreSQL port
    )
    
    cur = conn.cursor()
    
    # Check recent items
    print("=== Recent Items (last 24 hours) ===")
    cur.execute("""
        SELECT id, title, type, status, user_id, created_at 
        FROM items 
        WHERE created_at > %s 
        ORDER BY created_at DESC 
        LIMIT 20
    """, (datetime.now() - timedelta(hours=24),))
    
    items = cur.fetchall()
    if items:
        for item in items:
            print(f"\nID: {item[0]}")
            print(f"Title: {item[1]}")
            print(f"Type: {item[2]}")
            print(f"Status: {item[3]}")
            print(f"User ID: {item[4]}")
            print(f"Created: {item[5]}")
    else:
        print("No items found in the last 24 hours")
    
    # Check total items by user
    print("\n=== Items by User ===")
    cur.execute("""
        SELECT user_id, COUNT(*) as count 
        FROM items 
        GROUP BY user_id 
        ORDER BY count DESC
    """)
    
    user_counts = cur.fetchall()
    for user_id, count in user_counts:
        print(f"User {user_id}: {count} items")
    
    # Check items with test user ID
    test_user_id = "00000000-0000-0000-0000-000000000001"
    cur.execute("""
        SELECT COUNT(*) 
        FROM items 
        WHERE user_id = %s
    """, (test_user_id,))
    
    test_count = cur.fetchone()[0]
    print(f"\n=== Test User Items ===")
    print(f"Items with test user ID ({test_user_id}): {test_count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)