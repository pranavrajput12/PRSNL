#!/usr/bin/env python3
"""Test Resend email integration"""

import asyncio
from app.services.email_service import EmailService
from app.config import settings

async def test_resend():
    print("Testing Resend email integration...")
    print(f"Resend API Key configured: {'Yes' if settings.RESEND_API_KEY else 'No'}")
    print(f"From Address: {settings.EMAIL_FROM_ADDRESS}")
    print(f"From Name: {settings.EMAIL_FROM_NAME}")
    
    # Test sending a simple email to Resend's test email
    test_email = "delivered@resend.dev"  # Resend's test email address
    
    print(f"\nSending test email to: {test_email}")
    
    result = await EmailService.send_email(
        to=test_email,
        subject="PRSNL Test Email",
        html="<h1>Test Email</h1><p>This is a test email from PRSNL to verify Resend integration.</p>",
        text="Test Email\n\nThis is a test email from PRSNL to verify Resend integration."
    )
    
    if result:
        print(f"✅ Email sent successfully! Message ID: {result}")
    else:
        print("❌ Failed to send email")

if __name__ == "__main__":
    asyncio.run(test_resend())