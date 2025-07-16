#!/usr/bin/env python3
"""
Get the current verification link for slathiap@gmail.com
"""

import asyncio
import asyncpg
from app.config import settings
from datetime import datetime
import pytz

async def get_verification_link():
    """Get the current verification token and link"""
    
    user_email = "slathiap@gmail.com"
    user_id = "5706f717-fe9f-4b15-aa50-a0bdd2032369"
    
    print("PRSNL Verification Link Checker")
    print("===============================")
    print(f"User: {user_email}")
    print(f"User ID: {user_id}")
    
    # Connect to database
    try:
        db = await asyncpg.connect(settings.DATABASE_URL)
        
        # Get current token info
        token_info = await db.fetchrow("""
            SELECT 
                email_verification_token,
                email_verification_token_expires,
                is_verified,
                email_verified_at
            FROM users
            WHERE id = $1
        """, user_id)
        
        await db.close()
        
        if not token_info:
            print("\n❌ User not found!")
            return
            
        print(f"\n📊 Current Status:")
        print(f"   Is Verified: {token_info['is_verified']}")
        print(f"   Verified At: {token_info['email_verified_at'] or 'Never'}")
        
        if token_info['is_verified']:
            print("\n✅ User is already verified!")
            return
            
        if not token_info['email_verification_token']:
            print("\n❌ No verification token found!")
            print("   You need to send a new verification email.")
            return
            
        # Check if token is expired
        expires_at = token_info['email_verification_token_expires']
        now = datetime.now(pytz.UTC)
        
        if expires_at < now:
            print(f"\n❌ Token has expired!")
            print(f"   Expired at: {expires_at}")
            print(f"   Current time: {now}")
            print(f"   You need to send a new verification email.")
            return
            
        # Token is valid
        time_remaining = expires_at - now
        hours_remaining = time_remaining.total_seconds() / 3600
        
        print(f"\n✅ Token is valid!")
        print(f"   Expires at: {expires_at}")
        print(f"   Time remaining: {hours_remaining:.1f} hours")
        
        print(f"\n🔗 Current verification link:")
        print(f"\n{settings.FRONTEND_URL}/auth/verify-email?token={token_info['email_verification_token']}")
        
        print(f"\n📝 Token value (for debugging):")
        print(f"{token_info['email_verification_token']}")
        
        print(f"\n💡 Instructions:")
        print(f"1. Copy the entire link above")
        print(f"2. Paste it into your browser")
        print(f"3. Make sure you're using port 3004 for local development")
        print(f"4. If you get an error, make sure the frontend is running")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_verification_link())