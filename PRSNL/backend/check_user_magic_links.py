#!/usr/bin/env python3
"""Check magic links for user in PRSNL database"""
import asyncio
import os
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_magic_links(email: str):
    """Check magic links for user"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5433/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Checking magic links for: {email}")
    print("-" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # First get user ID
        user_query = "SELECT id FROM users WHERE email = $1"
        user = await conn.fetchrow(user_query, email)
        
        if not user:
            print(f"❌ User not found with email: {email}")
            return
        
        user_id = user['id']
        print(f"User ID: {user_id}")
        print()
        
        # Check magic links
        magic_links_query = """
        SELECT 
            id,
            token,
            expires_at,
            used_at,
            created_at
        FROM magic_links 
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        links = await conn.fetch(magic_links_query, user_id)
        
        if links:
            print(f"🔗 MAGIC LINKS ({len(links)} most recent):")
            for i, link in enumerate(links, 1):
                is_used = link['used_at'] is not None
                is_expired = link['expires_at'] < datetime.now(link['expires_at'].tzinfo) if link['expires_at'] else False
                
                if is_used:
                    status = "✅ USED"
                elif is_expired:
                    status = "❌ EXPIRED"
                else:
                    status = "⏳ ACTIVE"
                
                print(f"\n   Magic Link {i}:")
                print(f"   - Token: {link['token'][:20]}...")
                print(f"   - Status: {status}")
                print(f"   - Expires: {link['expires_at']}")
                print(f"   - Used at: {link['used_at'] if link['used_at'] else 'Not used'}")
                print(f"   - Created: {link['created_at']}")
        else:
            print("🔗 No magic links found for this user")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    email = "slathiap@gmail.com"
    asyncio.run(check_magic_links(email))