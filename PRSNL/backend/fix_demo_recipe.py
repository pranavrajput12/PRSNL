#!/usr/bin/env python3
"""
Fix the demo recipe database entry to have consistent content types
"""
import asyncio
import sys
sys.path.append('.')

import asyncpg
from app.config import settings


async def fix_demo_recipe():
    """Fix the demo recipe database entry"""
    
    item_id = "50fd6178-0f14-4060-a860-6004e5204b4a"
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Update the recipe item to have consistent types, user_id, and recent timestamp
        result = await conn.execute("""
            UPDATE items 
            SET type = 'recipe', content_type = 'recipe', user_id = 'f92d9270-2416-4ddb-a1d2-a72fe3e43296', 
                created_at = NOW(), updated_at = NOW()
            WHERE id = $1
        """, item_id)
        
        # Verify the update
        recipe = await conn.fetchrow("""
            SELECT id, title, type, content_type, status
            FROM items 
            WHERE id = $1
        """, item_id)
        
        await conn.close()
        
        if recipe:
            print(f"✅ Demo recipe updated successfully!")
            print(f"📋 Item ID: {recipe['id']}")
            print(f"🍽️ Title: {recipe['title']}")
            print(f"📄 Type: {recipe['type']}")
            print(f"🔖 Content Type: {recipe['content_type']}")
            print(f"📊 Status: {recipe['status']}")
            print()
            print(f"🌐 Test URL: http://localhost:3004/recipe/{item_id}")
        else:
            print(f"❌ Recipe with ID {item_id} not found!")
        
    except Exception as e:
        print(f"❌ Error fixing demo recipe: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(fix_demo_recipe())