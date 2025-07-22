#!/usr/bin/env python3
"""
Test automatic item processing with PostgreSQL notifications
"""
import asyncio
import asyncpg
import os
from datetime import datetime
import uuid

from dotenv import load_dotenv
load_dotenv()

async def test_automatic_processing():
    """Add a test item and see if it gets processed automatically"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("=== Testing Automatic Processing ===\n")
        
        # Create a test item
        item_id = uuid.uuid4()
        
        result = await conn.fetchrow("""
            INSERT INTO items (
                id, title, type, url, summary, status, user_id, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, NOW(), NOW()
            ) RETURNING id
        """, 
            str(item_id),
            "Test Automatic Processing - Building AI Chatbots",
            "website",
            "https://example.com/ai-chatbot-guide",
            "A comprehensive guide on building AI chatbots with modern tools",
            "pending",
            str(uuid.uuid4())  # dummy user_id
        )
        
        print(f"Created test item: {result['id']}")
        print("Worker should pick this up automatically...\n")
        
        # Wait a bit for processing
        print("Waiting 5 seconds for automatic processing...")
        await asyncio.sleep(5)
        
        # Check the status
        item = await conn.fetchrow("""
            SELECT 
                id, title, status,
                processed_content IS NOT NULL as has_content,
                embedding IS NOT NULL as has_embedding,
                search_vector IS NOT NULL as has_search_vector
            FROM items
            WHERE id = $1
        """, str(item_id))
        
        print(f"\nItem Status After Processing:")
        print(f"  Status: {item['status']}")
        print(f"  Has content: {item['has_content']}")
        print(f"  Has embedding: {item['has_embedding']}")
        print(f"  Has search vector: {item['has_search_vector']}")
        
        # Check worker log
        print("\nChecking worker log...")
        import subprocess
        result = subprocess.run(['tail', '-20', 'worker.log'], 
                              capture_output=True, text=True)
        print("Recent worker activity:")
        print(result.stdout)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_automatic_processing())