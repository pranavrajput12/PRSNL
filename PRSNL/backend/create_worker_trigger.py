#!/usr/bin/env python3
"""
Create the PostgreSQL trigger for item_created notifications
"""
import asyncio
import asyncpg
import os

from dotenv import load_dotenv
load_dotenv()

async def create_trigger():
    """Create the trigger for item notifications"""
    db_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("Creating item_created trigger...")
        
        # Create the trigger
        await conn.execute("""
            CREATE OR REPLACE TRIGGER notify_item_created
            AFTER INSERT ON items
            FOR EACH ROW
            EXECUTE FUNCTION notify_item_created();
        """)
        
        print("✓ Trigger created successfully!")
        
        # Verify it exists
        trigger = await conn.fetchrow("""
            SELECT * FROM pg_trigger 
            WHERE tgname = 'notify_item_created' 
            AND tgrelid = 'items'::regclass
        """)
        
        if trigger:
            print("✓ Trigger verified!")
        else:
            print("✗ Trigger creation failed!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_trigger())