#!/usr/bin/env python3
"""
Check user sessions for slathiap@gmail.com
"""

import asyncio
import asyncpg
from app.config import settings
from datetime import datetime
import pytz

async def check_sessions():
    """Check all sessions for the user"""
    
    user_email = "slathiap@gmail.com"
    user_id = "5706f717-fe9f-4b15-aa50-a0bdd2032369"
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    # Get all sessions for this user
    sessions = await db.fetch("""
        SELECT 
            id,
            refresh_token,
            expires_at,
            refresh_expires_at,
            revoked_at,
            created_at,
            LENGTH(refresh_token) as token_length
        FROM user_sessions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 10
    """, user_id)
    
    await db.close()
    
    print(f"User Sessions for {user_email}")
    print("=" * 80)
    print(f"Total sessions found: {len(sessions)}")
    
    now = datetime.now(pytz.UTC)
    
    for i, session in enumerate(sessions):
        print(f"\nSession {i+1}:")
        print(f"  ID: {session['id']}")
        print(f"  Created: {session['created_at']}")
        print(f"  Refresh Token Length: {session['token_length']} chars")
        print(f"  Refresh Token (first 20): {session['refresh_token'][:20] if session['refresh_token'] else 'None'}...")
        
        # Check expiration status
        if session['revoked_at']:
            print(f"  Status: ❌ REVOKED at {session['revoked_at']}")
        elif session['refresh_expires_at'] and session['refresh_expires_at'] < now:
            print(f"  Status: ❌ EXPIRED (refresh expired at {session['refresh_expires_at']})")
        elif session['expires_at'] and session['expires_at'] < now:
            print(f"  Status: ⚠️  ACCESS TOKEN EXPIRED (at {session['expires_at']})")
            print(f"  Refresh Token Valid Until: {session['refresh_expires_at']}")
        else:
            print(f"  Status: ✅ ACTIVE")
            print(f"  Access Token Expires: {session['expires_at']}")
            print(f"  Refresh Token Expires: {session['refresh_expires_at']}")
    
    # Check for any non-revoked, non-expired sessions
    active_sessions = await db.fetch("""
        SELECT COUNT(*) as count
        FROM user_sessions
        WHERE user_id = $1
        AND refresh_expires_at > NOW()
        AND revoked_at IS NULL
    """, user_id)
    
    print(f"\n✅ Active Sessions (valid for refresh): {active_sessions[0]['count']}")

if __name__ == "__main__":
    asyncio.run(check_sessions())