#!/usr/bin/env python3
"""Check user status in PRSNL database"""
import asyncio
import os
import sys
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_user_status(email: str):
    """Check if user exists and their verification status"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5433/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Connecting to database...")
    print(f"Checking for user with email: {email}")
    print("-" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Query user information
        user_query = """
        SELECT 
            id,
            email,
            is_active,
            is_verified,
            created_at,
            updated_at
        FROM users 
        WHERE email = $1
        """
        
        user = await conn.fetchrow(user_query, email)
        
        if user:
            print("✅ USER FOUND!")
            print(f"   ID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Active: {'Yes' if user['is_active'] else 'No'}")
            print(f"   Verified: {'✅ YES' if user['is_verified'] else '❌ NO'}")
            print(f"   Created: {user['created_at']}")
            print(f"   Updated: {user['updated_at']}")
            print()
            
            # Check for email verifications
            token_query = """
            SELECT 
                id,
                token,
                expires_at,
                verified_at,
                created_at
            FROM email_verifications 
            WHERE user_id = $1
            ORDER BY created_at DESC
            """
            
            tokens = await conn.fetch(token_query, user['id'])
            
            if tokens:
                print(f"📧 EMAIL VERIFICATIONS ({len(tokens)} found):")
                for i, token in enumerate(tokens, 1):
                    is_verified = token['verified_at'] is not None
                    is_expired = token['expires_at'] < datetime.now(token['expires_at'].tzinfo) if token['expires_at'] else False
                    
                    if is_verified:
                        status = "✅ VERIFIED"
                    elif is_expired:
                        status = "❌ EXPIRED"
                    else:
                        status = "⏳ PENDING"
                    
                    print(f"\n   Verification {i}:")
                    print(f"   - Token: {token['token'][:20]}...")
                    print(f"   - Status: {status}")
                    print(f"   - Expires: {token['expires_at']}")
                    print(f"   - Verified at: {token['verified_at'] if token['verified_at'] else 'Not verified'}")
                    print(f"   - Created: {token['created_at']}")
            else:
                print("📧 No email verifications found for this user")
            
            # Check for active sessions
            session_query = """
            SELECT 
                id,
                refresh_token,
                expires_at,
                created_at
            FROM user_sessions 
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 5
            """
            
            sessions = await conn.fetch(session_query, user['id'])
            
            if sessions:
                print(f"\n🔐 USER SESSIONS ({len(sessions)} most recent):")
                for i, session in enumerate(sessions, 1):
                    is_expired = session['expires_at'] < datetime.now(session['expires_at'].tzinfo)
                    status = "❌ EXPIRED" if is_expired else "✅ ACTIVE"
                    print(f"\n   Session {i}:")
                    print(f"   - Status: {status}")
                    print(f"   - Token: {session['refresh_token'][:20]}...")
                    print(f"   - Expires: {session['expires_at']}")
                    print(f"   - Created: {session['created_at']}")
            else:
                print("\n🔐 No sessions found for this user")
                
        else:
            print(f"❌ USER NOT FOUND with email: {email}")
            
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    email = "slathiap@gmail.com"
    asyncio.run(check_user_status(email))