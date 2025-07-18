#!/usr/bin/env python3
"""
Fix authentication issues by creating a fresh login token
"""
import asyncio
import asyncpg
from app.config import settings
from app.services.auth_service import AuthService
from app.db.database import create_db_pool, close_db_pool
from datetime import datetime, timezone

async def create_fresh_token():
    # Initialize database pool
    await create_db_pool()
    
    # Connect to database
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    # Find the user
    user = await conn.fetchrow("""
        SELECT * FROM users 
        WHERE email = 'prsnlfyi@gmail.com'
    """)
    
    if not user:
        print("User not found!")
        await conn.close()
        return
    
    print(f"Found user: {user['email']} (ID: {user['id']})")
    
    # Create fresh tokens
    access_token, refresh_token = await AuthService.create_tokens(str(user['id']))
    
    print("\n✅ Fresh tokens created successfully!")
    print(f"\nAccess Token:\n{access_token}")
    print(f"\nRefresh Token:\n{refresh_token}")
    
    # Get the session info
    session = await conn.fetchrow("""
        SELECT * FROM user_sessions 
        WHERE user_id = $1 
        AND revoked_at IS NULL 
        ORDER BY created_at DESC 
        LIMIT 1
    """, user['id'])
    
    if session:
        print(f"\nSession created at: {session['created_at']}")
        print(f"Session expires at: {session['expires_at']}")
    
    await conn.close()
    await close_db_pool()
    
    print("\n📝 To fix the authentication issue:")
    print("1. Open your browser's Developer Console (F12)")
    print("2. Go to the Application/Storage tab")
    print("3. Find localStorage for localhost:3004")
    print("4. Set these values:")
    print(f"   - prsnl_auth_token: {access_token}")
    print(f"   - prsnl_refresh_token: {refresh_token}")
    print("   - prsnl_auth_source: prsnl")
    print("5. Refresh the page")

if __name__ == "__main__":
    asyncio.run(create_fresh_token())