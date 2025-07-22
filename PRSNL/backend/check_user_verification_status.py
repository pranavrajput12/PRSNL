#!/usr/bin/env python3
"""
Check user verification token status for slathiap@gmail.com
"""
import asyncio
import asyncpg
from datetime import datetime
import pytz

# Database connection string (adjust credentials as needed)
DATABASE_URL = "postgresql://pronav@localhost:5432/prsnl"

async def check_verification_status():
    """Check the verification token status for the user"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("=== Checking Verification Status for slathiap@gmail.com ===\n")
        
        # 1. Check user details and verification token status
        user_query = """
            SELECT 
                id,
                email,
                is_verified,
                email_verified_at,
                email_verification_token,
                email_verification_token_expires,
                created_at,
                CASE 
                    WHEN email_verification_token_expires IS NULL THEN 'No token'
                    WHEN email_verification_token_expires < NOW() THEN 'Expired'
                    ELSE 'Valid'
                END as token_status,
                CASE 
                    WHEN email_verification_token_expires IS NOT NULL THEN
                        email_verification_token_expires - NOW()
                    ELSE NULL
                END as time_remaining
            FROM users 
            WHERE email = $1
        """
        
        user = await conn.fetchrow(user_query, 'slathiap@gmail.com')
        
        if not user:
            print("User not found!")
            return
            
        print("User Details:")
        print(f"  ID: {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Is Verified: {user['is_verified']}")
        print(f"  Email Verified At: {user['email_verified_at']}")
        print(f"  Created At: {user['created_at']}")
        print()
        
        print("Verification Token Status:")
        print(f"  Token: {user['email_verification_token'][:20] + '...' if user['email_verification_token'] else 'None'}")
        print(f"  Token Expires: {user['email_verification_token_expires']}")
        print(f"  Token Status: {user['token_status']}")
        if user['time_remaining']:
            print(f"  Time Remaining: {user['time_remaining']}")
        print()
        
        # 2. Check email_verifications table (if it exists)
        try:
            email_verifications_query = """
                SELECT 
                    id,
                    token,
                    expires_at,
                    verified_at,
                    created_at,
                    CASE 
                        WHEN expires_at < NOW() THEN 'Expired'
                        WHEN verified_at IS NOT NULL THEN 'Used'
                        ELSE 'Valid'
                    END as status
                FROM email_verifications 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            """
            
            verifications = await conn.fetch(email_verifications_query, user['id'])
            
            if verifications:
                print("Email Verifications Table Records:")
                for i, v in enumerate(verifications):
                    print(f"  Record {i+1}:")
                    print(f"    Token: {v['token'][:20] + '...'}")
                    print(f"    Created: {v['created_at']}")
                    print(f"    Expires: {v['expires_at']}")
                    print(f"    Verified: {v['verified_at']}")
                    print(f"    Status: {v['status']}")
                print()
        except asyncpg.UndefinedTableError:
            print("email_verifications table does not exist\n")
        
        # 3. Check email logs
        email_logs_query = """
            SELECT 
                id,
                email_type,
                template_name,
                status,
                provider_message_id,
                error_message,
                sent_at,
                created_at,
                metadata
            FROM email_logs 
            WHERE email_to = $1 AND email_type IN ('verification', 'welcome')
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        logs = await conn.fetch(email_logs_query, 'slathiap@gmail.com')
        
        if logs:
            print("Recent Email Logs:")
            for log in logs:
                print(f"  {log['created_at']} - {log['email_type']} - {log['status']}")
                if log['error_message']:
                    print(f"    Error: {log['error_message']}")
                if log['metadata']:
                    import json
                    try:
                        metadata = json.loads(log['metadata']) if isinstance(log['metadata'], str) else log['metadata']
                        if 'token' in metadata:
                            print(f"    Token: {metadata['token']}")
                    except:
                        pass
            print()
        
        # 4. Check for any recent verification attempts in the auth endpoint logs
        print("=== Analysis ===")
        print("\nPossible reasons for 'Invalid or expired verification token':")
        
        if user['is_verified']:
            print("1. ✓ User is already verified - token may have been cleared after successful verification")
        
        if user['token_status'] == 'Expired':
            print("2. ✗ Token has expired (default expiry is 24 hours)")
            print(f"   Token expired at: {user['email_verification_token_expires']}")
        
        if not user['email_verification_token']:
            print("3. ✗ No verification token exists in the database")
            print("   - Token may have been cleared after use")
            print("   - Token may not have been generated properly")
        
        if user['email_verification_token'] and user['token_status'] == 'Valid':
            print("4. ✗ Token exists and is valid - issue might be:")
            print("   - Token mismatch (provided token doesn't match stored token)")
            print("   - URL encoding issues")
            print("   - Case sensitivity issues")
        
        # 5. Suggest resolution
        print("\n=== Suggested Resolution ===")
        if not user['is_verified']:
            print("1. Generate a new verification token by calling the resend verification endpoint")
            print("2. Or manually verify the user:")
            print(f"   UPDATE users SET is_verified = true, email_verified_at = NOW() WHERE id = '{user['id']}';")
        else:
            print("User is already verified. No action needed.")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_verification_status())