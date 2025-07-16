#!/usr/bin/env python3
"""
Test script to trigger a verification email for PRSNL

This script provides multiple methods to trigger a verification email:
1. Direct method call (requires user_id)
2. API endpoint call (requires authentication token)
3. Create a new test user and send verification
"""

import asyncio
import httpx
import json
from uuid import UUID
from datetime import datetime
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from app.models.auth import UserRegister
from app.db.database import get_db_pool
from app.config import settings

async def method1_direct_email_service(user_id: UUID, email: str, name: str):
    """Method 1: Direct call to EmailService.send_verification_email"""
    print("\n=== Method 1: Direct EmailService Call ===")
    print(f"Sending verification email to: {email}")
    print(f"User ID: {user_id}")
    print(f"Name: {name}")
    
    success = await EmailService.send_verification_email(
        user_id=user_id,
        email=email,
        name=name
    )
    
    if success:
        print("✅ Verification email sent successfully!")
        
        # Get the verification token from DB
        pool = await get_db_pool()
        async with pool.acquire() as db:
            token_info = await db.fetchrow("""
                SELECT email_verification_token, email_verification_token_expires
                FROM users
                WHERE id = $1
            """, user_id)
            
            if token_info:
                print(f"Verification link: {settings.FRONTEND_URL}/auth/verify-email?token={token_info['email_verification_token']}")
                print(f"Token expires at: {token_info['email_verification_token_expires']}")
    else:
        print("❌ Failed to send verification email")
    
    return success

async def method2_api_endpoint(auth_token: str):
    """Method 2: Call the resend-verification API endpoint"""
    print("\n=== Method 2: API Endpoint Call ===")
    print("Calling POST /api/auth/resend-verification")
    
    url = f"http://localhost:{settings.BACKEND_PORT}/api/auth/resend-verification"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200

async def method3_create_test_user():
    """Method 3: Create a new test user and send verification"""
    print("\n=== Method 3: Create New Test User ===")
    
    # Generate unique test email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"test_verification_{timestamp}@resend.dev"
    
    user_data = UserRegister(
        email=test_email,
        password="Test123!@#",
        first_name="Test",
        last_name="User"
    )
    
    print(f"Creating user: {test_email}")
    
    try:
        # Register user (this automatically sends verification email)
        user = await AuthService.register_user(user_data)
        print(f"✅ User created successfully!")
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Verification email has been sent automatically")
        
        # Get verification link
        pool = await get_db_pool()
        async with pool.acquire() as db:
            token_info = await db.fetchrow("""
                SELECT email_verification_token, email_verification_token_expires
                FROM users
                WHERE id = $1
            """, user.id)
            
            if token_info:
                print(f"\nVerification link: {settings.FRONTEND_URL}/auth/verify-email?token={token_info['email_verification_token']}")
                print(f"Token expires at: {token_info['email_verification_token_expires']}")
        
        return user
        
    except ValueError as e:
        print(f"❌ Failed to create user: {e}")
        return None

async def get_existing_unverified_user():
    """Get an existing unverified user from the database"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        user = await db.fetchrow("""
            SELECT id, email, first_name, last_name
            FROM users
            WHERE is_verified = false
            LIMIT 1
        """)
        return user

async def get_specific_user(email: str):
    """Get a specific user by email"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        user = await db.fetchrow("""
            SELECT id, email, first_name, last_name, is_verified
            FROM users
            WHERE email = $1
        """, email)
        return user

async def main():
    print("PRSNL Email Verification Test Script")
    print("====================================")
    print(f"Backend URL: http://localhost:{settings.BACKEND_PORT}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Resend API Key configured: {'Yes' if settings.RESEND_API_KEY else 'No'}")
    
    if not settings.RESEND_API_KEY:
        print("\n❌ ERROR: RESEND_API_KEY is not configured!")
        print("Please set RESEND_API_KEY in your .env file")
        return
    
    print("\nChoose a method to trigger verification email:")
    print("1. Direct EmailService call (requires existing unverified user)")
    print("2. API endpoint call (requires auth token)")
    print("3. Create new test user (automatic verification email)")
    print("4. Send to specific email: slathiap@gmail.com")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Method 1: Direct call
        user = await get_existing_unverified_user()
        if user:
            name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or user['email']
            await method1_direct_email_service(
                user_id=user['id'],
                email=user['email'],
                name=name
            )
        else:
            print("No unverified users found. Try method 3 to create a test user.")
    
    elif choice == "2":
        # Method 2: API call
        print("\nYou need an auth token from a logged-in user.")
        print("You can get this by:")
        print("1. Logging in via the frontend")
        print("2. Using the login API endpoint")
        print("3. Creating a test user (method 3) which returns tokens")
        
        token = input("\nEnter auth token (or press Enter to skip): ").strip()
        if token:
            await method2_api_endpoint(token)
        else:
            print("Skipping API method...")
    
    elif choice == "3":
        # Method 3: Create test user
        await method3_create_test_user()
    
    elif choice == "4":
        # Method 4: Send to slathiap@gmail.com
        print("\n=== Method 4: Send to slathiap@gmail.com ===")
        user = await get_specific_user("slathiap@gmail.com")
        if user:
            print(f"Found user: {user['email']}")
            print(f"User ID: {user['id']}")
            print(f"Verified: {user['is_verified']}")
            
            if user['is_verified']:
                print("⚠️  Warning: This user is already verified!")
                confirm = input("Send verification email anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Cancelled.")
                    return
            
            name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or user['email']
            await method1_direct_email_service(
                user_id=user['id'],
                email=user['email'],
                name=name
            )
        else:
            print("❌ User slathiap@gmail.com not found in database!")
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main())