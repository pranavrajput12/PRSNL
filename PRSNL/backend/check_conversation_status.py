#!/usr/bin/env python3
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_status():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get all conversations with their processing status
        convs = await conn.fetch("""
            SELECT id, title, platform, slug, processing_status,
                   summary, technical_content, actionable_insights
            FROM ai_conversation_imports
        """)
        
        print(f"Total conversations: {len(convs)}")
        for conv in convs:
            print(f"\nConversation: {conv['title']}")
            print(f"  ID: {conv['id']}")
            print(f"  Processing Status: {conv['processing_status']}")
            print(f"  Has Summary: {conv['summary'] is not None}")
            print(f"  Technical Content: {conv['technical_content']}")
            print(f"  Actionable Insights: {conv['actionable_insights']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_status())