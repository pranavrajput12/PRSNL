#!/usr/bin/env python3
"""
Reset password for slathiap@gmail.com for testing
"""

import asyncio
import asyncpg
from app.config import settings
from app.services.auth_service import AuthService

async def reset_password():
    """Reset user password"""
    
    email = "slathiap@gmail.com"
    new_password = "Test123!"
    
    print(f"Resetting password for {email}")
    
    db = await asyncpg.connect(settings.DATABASE_URL)
    
    # Hash the new password
    password_hash = AuthService.hash_password(new_password)
    
    # Update user password
    result = await db.execute("""
        UPDATE users 
        SET password_hash = $1
        WHERE email = $2
    """, password_hash, email)
    
    await db.close()
    
    print(f"✅ Password updated successfully")
    print(f"   Email: {email}")
    print(f"   New Password: {new_password}")

if __name__ == "__main__":
    asyncio.run(reset_password())