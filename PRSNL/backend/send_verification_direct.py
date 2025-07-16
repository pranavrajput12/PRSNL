#!/usr/bin/env python3
"""
Direct script to send verification email to slathiap@gmail.com
This runs within the backend context to have database access
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uuid import UUID
from app.services.email_service import EmailService
from app.db.database import create_db_pool, close_db_pool
from app.config import settings
import asyncpg

async def main():
    """Send verification email directly"""
    
    # User details for slathiap@gmail.com
    user_id = UUID("5706f717-fe9f-4b15-aa50-a0bdd2032369")
    email = "slathiap@gmail.com"
    name = "Prateek Lathia"
    
    print("PRSNL Direct Verification Email Sender")
    print("=====================================")
    print(f"Target: {email}")
    print(f"User ID: {user_id}")
    print(f"Name: {name}")
    
    # Check Resend API key
    if not settings.RESEND_API_KEY:
        print("\n❌ ERROR: RESEND_API_KEY is not configured!")
        print("Please set RESEND_API_KEY in your .env file")
        return 1
    
    print(f"\n✅ Resend API Key is configured")
    print(f"From: noreply@fyi.prsnl.fyi")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    
    # Initialize database pool
    print("\n🔌 Initializing database connection...")
    try:
        await create_db_pool()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1
    
    try:
        # Send verification email
        print("\n📧 Sending verification email...")
        success = await EmailService.send_verification_email(
            user_id=user_id,
            email=email,
            name=name
        )
        
        if success:
            print("✅ Verification email sent successfully!")
            
            # Get the verification link from database
            db = await asyncpg.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                database=settings.DATABASE_NAME
            )
            
            token_info = await db.fetchrow("""
                SELECT email_verification_token, email_verification_token_expires
                FROM users
                WHERE id = $1
            """, user_id)
            
            await db.close()
            
            if token_info and token_info['email_verification_token']:
                print(f"\n🔗 Verification link:")
                print(f"{settings.FRONTEND_URL}/auth/verify-email?token={token_info['email_verification_token']}")
                print(f"\n⏰ Token expires at: {token_info['email_verification_token_expires']}")
                print(f"\n📨 Email Details:")
                print(f"   To: {email}")
                print(f"   Subject: Verify your email for PRSNL")
                print(f"   From: PRSNL Security <noreply@fyi.prsnl.fyi>")
                print(f"\n✨ SUCCESS! Please check the inbox at {email}")
            else:
                print("\n⚠️  Warning: Token was not found in database")
                
            return 0
        else:
            print("❌ Failed to send verification email")
            print("Check the logs for more details")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Close database pool
        await close_db_pool()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)