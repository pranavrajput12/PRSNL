#!/usr/bin/env python3
"""
Debug the refresh token 500 error
"""

import asyncio
import asyncpg
from app.config import settings
from app.services.auth_service import AuthService
from datetime import datetime
import pytz

async def debug_refresh():
    """Debug refresh token issues"""
    
    user_email = "slathiap@gmail.com"
    user_id = "5706f717-fe9f-4b15-aa50-a0bdd2032369"
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    print("Checking user sessions...")
    print("=" * 80)
    
    # Get the most recent non-revoked session
    sessions = await db.fetch("""
        SELECT 
            id,
            refresh_token,
            expires_at,
            refresh_expires_at,
            revoked_at,
            created_at,
            CASE 
                WHEN revoked_at IS NOT NULL THEN 'REVOKED'
                WHEN refresh_expires_at < NOW() THEN 'EXPIRED'
                ELSE 'ACTIVE'
            END as status
        FROM user_sessions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 5
    """, user_id)
    
    for i, session in enumerate(sessions):
        print(f"\nSession {i+1}:")
        print(f"  ID: {session['id']}")
        print(f"  Created: {session['created_at']}")
        print(f"  Status: {session['status']}")
        print(f"  Refresh Token: {session['refresh_token'][:30]}...")
        
        if session['status'] == 'ACTIVE':
            # Try to decode the token
            try:
                payload = AuthService.decode_token(session['refresh_token'])
                print(f"  Token Payload: {payload}")
                
                # Check if it's a refresh token
                if payload and payload.get('type') == 'refresh':
                    print(f"  ✅ Valid refresh token for user: {payload.get('sub')}")
                else:
                    print(f"  ❌ Not a refresh token, type: {payload.get('type') if payload else 'None'}")
                    
            except Exception as e:
                print(f"  ❌ Failed to decode token: {e}")
    
    # Check if there are ANY active sessions
    active_count = await db.fetchval("""
        SELECT COUNT(*) 
        FROM user_sessions
        WHERE user_id = $1
        AND revoked_at IS NULL
        AND refresh_expires_at > NOW()
    """, user_id)
    
    print(f"\n\nTotal active sessions: {active_count}")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(debug_refresh())