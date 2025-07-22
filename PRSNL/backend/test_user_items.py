#!/usr/bin/env python3
"""
Test script to check if user has items in database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_user_items():
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5433/prsnl")
    
    # Connect to database
    conn = await asyncpg.connect(db_url)
    
    try:
        # Test user ID (from SECURITY BYPASS)
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        
        # Count items for this user
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM items WHERE user_id = $1",
            user_id
        )
        print(f"User {user_id} has {count} items in the database")
        
        # Get a few sample items
        items = await conn.fetch(
            """
            SELECT id, title, type, created_at 
            FROM items 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
            """,
            user_id
        )
        
        if items:
            print("\nRecent items:")
            for item in items:
                print(f"- {item['title']} ({item['type']}) - {item['created_at']}")
        else:
            print("\nNo items found for this user!")
            
            # Check if there are any items in the database at all
            total_count = await conn.fetchval("SELECT COUNT(*) FROM items")
            print(f"\nTotal items in database: {total_count}")
            
            # Get some user IDs that have items
            user_counts = await conn.fetch(
                """
                SELECT user_id, COUNT(*) as count 
                FROM items 
                GROUP BY user_id 
                ORDER BY count DESC 
                LIMIT 5
                """
            )
            
            if user_counts:
                print("\nUsers with items:")
                for row in user_counts:
                    print(f"- User {row['user_id']}: {row['count']} items")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_user_items())