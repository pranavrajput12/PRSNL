#!/usr/bin/env python3
"""
Check if user is now verified
"""

import asyncio
import asyncpg
from app.config import settings

async def check_status():
    """Check user verification status"""
    
    user_email = "slathiap@gmail.com"
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    user = await db.fetchrow("""
        SELECT id, email, is_verified, email_verified_at, 
               email_verification_token, email_verification_token_expires
        FROM users
        WHERE email = $1
    """, user_email)
    
    await db.close()
    
    print("User Verification Status")
    print("========================")
    print(f"Email: {user['email']}")
    print(f"Is Verified: {user['is_verified']} {'✅' if user['is_verified'] else '❌'}")
    print(f"Verified At: {user['email_verified_at'] or 'Never'}")
    print(f"Token: {user['email_verification_token'] or 'None (cleared)'}")
    print(f"Token Expires: {user['email_verification_token_expires'] or 'N/A'}")

if __name__ == "__main__":
    asyncio.run(check_status())