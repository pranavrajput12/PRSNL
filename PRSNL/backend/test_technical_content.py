#!/usr/bin/env python3
import asyncio
import asyncpg
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def test_content():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get the npm conversation
        conv = await conn.fetchrow("""
            SELECT technical_content
            FROM ai_conversation_imports
            WHERE title = 'npm Developmental Issues Fix'
        """)
        
        if conv and conv['technical_content']:
            tc = conv['technical_content']
            print("Technical Content Structure:")
            print(json.dumps(tc, indent=2))
            
            # Check the structure
            print("\nKeys in technical_content:")
            for key in tc.keys():
                print(f"  - {key}: {type(tc[key])}")
                if isinstance(tc[key], list) and len(tc[key]) > 0:
                    print(f"    First item type: {type(tc[key][0])}")
                    if isinstance(tc[key][0], dict):
                        print(f"    First item keys: {list(tc[key][0].keys())}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_content())