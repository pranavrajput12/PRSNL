#!/usr/bin/env python3
"""
Get the actual verification token for the user
"""
import asyncio
import asyncpg

# Database connection string
DATABASE_URL = "postgresql://pronav@localhost:5432/prsnl"

async def get_actual_token():
    """Get the actual token from the database"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        query = """
            SELECT 
                email_verification_token,
                email_verification_token_expires
            FROM users 
            WHERE email = 'slathiap@gmail.com'
        """
        
        result = await conn.fetchrow(query)
        
        if result and result['email_verification_token']:
            print("Actual verification token from database:")
            print(result['email_verification_token'])
            print(f"\nExpires at: {result['email_verification_token_expires']}")
            print(f"\nVerification URL should be:")
            print(f"http://localhost:3003/auth/verify-email?token={result['email_verification_token']}")
        else:
            print("No token found")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(get_actual_token())