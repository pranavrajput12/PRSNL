#!/usr/bin/env python3
"""
FusionAuth Migration Script - Add your API key and run
"""

import asyncio
import asyncpg
import requests
import json
from datetime import datetime

# ⚠️ ADD YOUR API KEY HERE AFTER GENERATING IT IN FUSIONAUTH
FUSIONAUTH_API_KEY = "fs7t4gH-8k1cuE2uPEJq68uhGR3LFmZZ23Kwjd4Cz4PwejWIVvla3ZJC"  # <-- Replace this!

# Configuration
DATABASE_URL = "postgresql://pronav@localhost:5433/prsnl"
FUSIONAUTH_URL = "http://localhost:9011"
APPLICATION_ID = "4218d574-603a-48b4-b980-39a0b73e4cff"  # PRSNL app

def check_api_key():
    """Verify API key works"""
    if FUSIONAUTH_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Please add your FusionAuth API key to this script first!")
        print("\nTo generate an API key:")
        print("1. Login to http://localhost:9011")
        print("2. Go to Settings → API Keys")
        print("3. Click the green + button")
        print("4. Name it 'PRSNL Backend'")
        print("5. Select all permissions")
        print("6. Copy the key and paste it in this script")
        return False
    
    response = requests.get(
        f"{FUSIONAUTH_URL}/api/system-configuration",
        headers={"Authorization": FUSIONAUTH_API_KEY}
    )
    
    if response.status_code == 200:
        print("✅ API key is valid!")
        return True
    else:
        print(f"❌ API key is invalid. Status: {response.status_code}")
        return False

async def get_prsnl_users():
    """Get all users from PRSNL database"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        users = await conn.fetch("""
            SELECT 
                id as user_id,
                email,
                first_name,
                last_name,
                is_verified,
                created_at,
                user_type
            FROM users
            ORDER BY created_at
        """)
        return users
    finally:
        await conn.close()

def check_user_exists_in_fusionauth(email):
    """Check if user already exists in FusionAuth"""
    response = requests.get(
        f"{FUSIONAUTH_URL}/api/user?email={email}",
        headers={"Authorization": FUSIONAUTH_API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('user') is not None
    return False

def migrate_user(user):
    """Migrate a single user to FusionAuth"""
    email = user['email']
    
    # Check if already exists
    if check_user_exists_in_fusionauth(email):
        print(f"⏭️  {email} - Already exists in FusionAuth")
        return {'status': 'skipped', 'email': email}
    
    # Prepare user data
    user_data = {
        "user": {
            "email": email,
            "firstName": user['first_name'] or "",
            "lastName": user['last_name'] or "",
            "verified": user['is_verified'] or False,
            "data": {
                "migrated_from": "prsnl_database",
                "original_user_id": str(user['user_id']),
                "user_type": user['user_type'] or "individual",
                "migration_date": datetime.now().isoformat()
            }
        },
        "sendSetPasswordEmail": True,  # Send password reset email
        "skipVerification": True,  # Keep existing verification status
        "registration": {
            "applicationId": APPLICATION_ID,
            "roles": []
        }
    }
    
    # Assign roles based on email
    if email == "prsnlfyi@gmail.com":
        user_data["registration"]["roles"] = ["admin", "user"]
    else:
        user_data["registration"]["roles"] = ["user"]
    
    # Create user in FusionAuth
    response = requests.post(
        f"{FUSIONAUTH_URL}/api/user/registration",
        headers={
            "Authorization": FUSIONAUTH_API_KEY,
            "Content-Type": "application/json"
        },
        json=user_data
    )
    
    if response.status_code == 200:
        print(f"✅ {email} - Successfully migrated")
        return {'status': 'success', 'email': email}
    else:
        error_msg = response.json().get('fieldErrors', response.text)
        print(f"❌ {email} - Failed: {error_msg}")
        return {'status': 'failed', 'email': email, 'error': error_msg}

async def main():
    print("🚀 FusionAuth User Migration Script\n")
    
    # Check API key
    if not check_api_key():
        return
    
    print("\n📊 Fetching users from PRSNL database...")
    users = await get_prsnl_users()
    print(f"Found {len(users)} users to process\n")
    
    # Add admin user if not in database
    admin_exists = any(u['email'] == 'prsnlfyi@gmail.com' for u in users)
    if not admin_exists:
        print("📌 Adding prsnlfyi@gmail.com as admin (not in database)")
        admin_user = {
            'user_id': 'admin-manual',
            'email': 'prsnlfyi@gmail.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_verified': True,
            'created_at': datetime.now(),
            'user_type': 'admin'
        }
        users.append(admin_user)
    
    # Process each user
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    print("Starting migration...\n")
    for user in users:
        result = migrate_user(user)
        results[result['status']] += 1
    
    # Summary
    print(f"\n{'='*50}")
    print("📈 Migration Summary:")
    print(f"{'='*50}")
    print(f"Total processed: {len(users)}")
    print(f"✅ Successful: {results['success']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏭️  Skipped (already exists): {results['skipped']}")
    
    print("\n📧 Email Configuration:")
    if results['success'] > 0:
        print("⚠️  Users will receive password reset emails")
        print("   Configure SMTP in FusionAuth to enable email delivery")
        print("   Go to: Tenants → Default → Email")
    
    print("\n🎉 Migration complete!")
    print(f"   Visit http://localhost:9011/admin/user/ to manage users")

if __name__ == "__main__":
    # Check if API key is set
    if FUSIONAUTH_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  Please edit this script and add your FusionAuth API key first!")
        print("   Look for the FUSIONAUTH_API_KEY variable at the top of the file")
    else:
        asyncio.run(main())