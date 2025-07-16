#!/usr/bin/env python3
"""
Trigger verification email for slathiap@gmail.com
"""

import asyncio
from uuid import UUID
from app.services.email_service import EmailService
from app.db.database import get_db_pool
from app.config import settings

async def send_verification_email_to_slathiap():
    """Send verification email to slathiap@gmail.com"""
    
    # User details found from database
    user_id = UUID("5706f717-fe9f-4b15-aa50-a0bdd2032369")
    email = "slathiap@gmail.com"
    name = "Prateek Lathia"  # Using the name from database
    
    print(f"Sending verification email to: {email}")
    print(f"User ID: {user_id}")
    print(f"Name: {name}")
    print(f"From: noreply@fyi.prsnl.fyi")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    
    # Check if Resend API key is configured
    if not settings.RESEND_API_KEY:
        print("\n❌ ERROR: RESEND_API_KEY is not configured!")
        print("Please set RESEND_API_KEY in your .env file")
        return False
    
    print("\n📧 Triggering verification email...")
    
    # Send the verification email
    success = await EmailService.send_verification_email(
        user_id=user_id,
        email=email,
        name=name
    )
    
    if success:
        print("✅ Verification email sent successfully!")
        
        # Get the verification token from DB to show the link
        pool = await get_db_pool()
        async with pool.acquire() as db:
            token_info = await db.fetchrow("""
                SELECT email_verification_token, email_verification_token_expires
                FROM users
                WHERE id = $1
            """, user_id)
            
            if token_info and token_info['email_verification_token']:
                print(f"\n🔗 Verification link that was sent in the email:")
                print(f"{settings.FRONTEND_URL}/auth/verify-email?token={token_info['email_verification_token']}")
                print(f"\n⏰ Token expires at: {token_info['email_verification_token_expires']}")
                print("\n📨 The user should check their inbox at slathiap@gmail.com")
                print("   Subject: 'Verify your email for PRSNL'")
                print("   From: 'PRSNL Security <noreply@fyi.prsnl.fyi>'")
            else:
                print("\n⚠️  Warning: Token was not saved to database properly")
    else:
        print("❌ Failed to send verification email")
        print("Check the backend logs for more details")
    
    return success

async def main():
    """Main function"""
    print("PRSNL Email Verification Script")
    print("==============================")
    print(f"Target: slathiap@gmail.com")
    print(f"Backend URL: http://localhost:{settings.BACKEND_PORT}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Resend API Key configured: {'Yes' if settings.RESEND_API_KEY else 'No'}")
    print("")
    
    # Send the email
    success = await send_verification_email_to_slathiap()
    
    if success:
        print("\n✨ SUCCESS! Verification email has been sent.")
        print("Next steps:")
        print("1. Check inbox at slathiap@gmail.com")
        print("2. Click the verification link in the email")
        print("3. Try logging in again after verification")
    else:
        print("\n❌ FAILED! Could not send verification email.")
        print("Please check:")
        print("1. RESEND_API_KEY is set in .env file")
        print("2. Backend server is running")
        print("3. Check backend logs for detailed error messages")

if __name__ == "__main__":
    asyncio.run(main())