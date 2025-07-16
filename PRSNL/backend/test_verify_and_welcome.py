#!/usr/bin/env python3
"""Test email verification and welcome email"""

import asyncio
from app.db.database import get_db_pool
from app.services.email_service import EmailService

async def test_verify_and_welcome():
    pool = await get_db_pool()
    
    async with pool.acquire() as db:
        # Get user details
        user = await db.fetchrow("""
            SELECT id, email, first_name, last_name, email_verification_token
            FROM users 
            WHERE email = 'delivered+test2@resend.dev'
        """)
        
        if not user:
            print("User not found")
            return
            
        print(f"User: {user['email']}")
        print(f"Token: {user['email_verification_token']}")
        
        # Verify the email using the service
        user_id = await EmailService.verify_email_token(user['email_verification_token'])
        
        if user_id:
            print(f"✅ Email verified for user {user_id}")
        else:
            print("❌ Email verification failed")

if __name__ == "__main__":
    asyncio.run(test_verify_and_welcome())