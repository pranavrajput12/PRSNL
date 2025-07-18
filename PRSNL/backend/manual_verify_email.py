#!/usr/bin/env python3
"""
Manually verify an email address in PRSNL
"""
import asyncio
import asyncpg
from app.config import settings

async def verify_email(email: str):
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Update user verification status
        result = await conn.execute("""
            UPDATE users 
            SET is_verified = TRUE, 
                is_email_verified = TRUE,
                updated_at = NOW()
            WHERE email = $1
            RETURNING id, email, is_verified
        """, email)
        
        if result:
            print(f"✅ Successfully verified email: {email}")
            
            # Get user details
            user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            if user:
                print(f"   User ID: {user['id']}")
                print(f"   Name: {user['first_name']} {user['last_name']}")
                print(f"   Verified: {user['is_verified']}")
                print(f"   Email Verified: {user['is_email_verified']}")
        else:
            print(f"❌ User not found: {email}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 manual_verify_email.py <email>")
        print("Example: python3 manual_verify_email.py slathiap@gmail.com")
    else:
        email = sys.argv[1]
        print(f"🔍 Verifying email: {email}")
        asyncio.run(verify_email(email))