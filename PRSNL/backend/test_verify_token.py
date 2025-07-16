#!/usr/bin/env python3
"""
Test email verification token directly
"""

import asyncio
import httpx
from app.config import settings

async def test_verify_token():
    """Test the verification endpoint"""
    
    # The token from the database
    token = "pnVn87rkr-uFlemyLEmLoLxeFG8ajyo7q-Oa59bXkJg"
    
    print("Testing Email Verification")
    print("==========================")
    print(f"Token: {token}")
    print(f"Endpoint: POST /api/auth/verify-email")
    
    url = f"http://localhost:{settings.BACKEND_PORT}/api/auth/verify-email"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json={"token": token}
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("\n✅ Verification successful!")
            else:
                print("\n❌ Verification failed!")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_verify_token())