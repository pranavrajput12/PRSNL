#!/usr/bin/env python3
"""
Clean up old sessions
"""

import asyncio
import asyncpg
from app.config import settings

async def clean_sessions():
    """Clean up old sessions"""
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    # Delete all sessions for this user
    user_id = "5706f717-fe9f-4b15-aa50-a0bdd2032369"
    
    result = await db.execute("""
        DELETE FROM user_sessions 
        WHERE user_id = $1
    """, user_id)
    
    print(f"Deleted {result} sessions")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(clean_sessions())