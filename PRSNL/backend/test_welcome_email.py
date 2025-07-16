#!/usr/bin/env python3
"""Test welcome email sending"""

import asyncio
from uuid import UUID
from app.services.email_service import EmailService

async def test_welcome_email():
    user_id = UUID("b84541b6-6672-4061-9c40-eaaf4d3dfffa")
    email = "delivered@resend.dev"
    name = "Test User"
    
    print(f"Sending welcome email to {email}...")
    result = await EmailService.send_welcome_email(user_id, email, name)
    
    if result:
        print("✅ Welcome email sent successfully!")
    else:
        print("❌ Failed to send welcome email")

if __name__ == "__main__":
    asyncio.run(test_welcome_email())