#!/usr/bin/env python3
"""
Migrate existing PRSNL users to FusionAuth
Run from backend directory: python migrate_to_fusionauth.py
"""

import asyncio
import requests
import json
from datetime import datetime
from app.db.database import get_db_connection

# Configuration
FUSIONAUTH_URL = "http://localhost:9011"
FUSIONAUTH_API_KEY = "bf69486b-4733-4470-a592-f1bfce7af580"
FUSIONAUTH_TENANT_ID = "d7d09513-a3f5-401c-9685-34ab6c552453"
FUSIONAUTH_APPLICATION_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"

async def get_users_from_db():
    """Fetch all users from PRSNL database"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT 
                user_id,
                email,
                created_at,
                username,
                first_name,
                last_name,
                email_verified,
                profile_data
            FROM users
            ORDER BY created_at
        """)
        
        users = []
        for row in rows:
            user = {
                'user_id': row['user_id'],
                'email': row['email'],
                'created_at': row['created_at'],
                'username': row['username'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'email_verified': row['email_verified'] if row['email_verified'] is not None else False,
                'profile_data': row['profile_data'] if row['profile_data'] else {}
            }
            users.append(user)
        
        return users
    finally:
        await conn.close()

def check_user_exists(email):
    """Check if user already exists in FusionAuth"""
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user?email={email}",
            headers={"Authorization": FUSIONAUTH_API_KEY}
        )
        return response.status_code == 200 and response.json().get('user') is not None
    except:
        return False

def migrate_user_to_fusionauth(user):
    """Migrate a single user to FusionAuth"""
    try:
        if check_user_exists(user['email']):
            print(f"User {user['email']} already exists in FusionAuth, skipping...")
            return False
        
        fusionauth_user = {
            "user": {
                "email": user['email'],
                "username": user['username'] or user['email'].split('@')[0],
                "firstName": user['first_name'] or "",
                "lastName": user['last_name'] or "",
                "verified": user['email_verified'],
                "tenantId": FUSIONAUTH_TENANT_ID,
                "data": {
                    "migrated_from": "prsnl_db",
                    "original_user_id": user['user_id'],
                    "migration_date": datetime.now().isoformat(),
                    "profile_data": user['profile_data']
                }
            },
            "registration": {
                "applicationId": FUSIONAUTH_APPLICATION_ID,
                "roles": ["user"]
            },
            "sendSetPasswordEmail": True,  # Send password reset email
            "skipVerification": True
        }
        
        if user['email'] in ['admin@prsnl.local', 'prsnlfyi@gmail.com']:
            fusionauth_user['registration']['roles'] = ["admin", "user"]
        
        response = requests.post(
            f"{FUSIONAUTH_URL}/api/user/registration",
            headers={
                "Authorization": FUSIONAUTH_API_KEY,
                "Content-Type": "application/json"
            },
            json=fusionauth_user
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully migrated user: {user['email']}")
            return True
        else:
            print(f"❌ Failed to migrate user {user['email']}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error migrating user {user['email']}: {e}")
        return False

def update_admin_email(old_email, new_email):
    """Update the admin user's email address"""
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user?email={old_email}",
            headers={"Authorization": FUSIONAUTH_API_KEY}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            if user_data.get('user'):
                user_id = user_data['user']['id']
                
                update_response = requests.patch(
                    f"{FUSIONAUTH_URL}/api/user/{user_id}",
                    headers={
                        "Authorization": FUSIONAUTH_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "user": {
                            "email": new_email,
                            "verified": True
                        }
                    }
                )
                
                if update_response.status_code == 200:
                    print(f"✅ Successfully updated admin email from {old_email} to {new_email}")
                    return True
                else:
                    print(f"❌ Failed to update admin email: {update_response.text}")
        else:
            print(f"❌ Admin user with email {old_email} not found")
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating admin email: {e}")
        return False

async def main():
    print("🚀 Starting PRSNL to FusionAuth user migration...\n")
    
    # Update admin email
    print("📧 Attempting to update admin email...")
    # Try to find the admin with wrong email first
    wrong_emails = ["admin@prsnl.local", "admin@example.com", "test@test.com"]
    for email in wrong_emails:
        if update_admin_email(email, "prsnlfyi@gmail.com"):
            break
    print()
    
    # Get users from database
    print("📊 Fetching users from PRSNL database...")
    users = await get_users_from_db()
    print(f"Found {len(users)} users to migrate\n")
    
    # Migrate each user
    successful = 0
    failed = 0
    skipped = 0
    
    for user in users:
        result = migrate_user_to_fusionauth(user)
        if result:
            successful += 1
        elif check_user_exists(user['email']):
            skipped += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n📈 Migration Summary:")
    print(f"   Total users: {len(users)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏭️  Skipped (already exists): {skipped}")
    
    print("\n✨ Migration complete!")
    print(f"\n🔐 Next steps:")
    print(f"1. Visit http://localhost:9011")
    print(f"2. Login with: prsnlfyi@gmail.com / prsnl_admin_2024!")
    print(f"3. Users will receive password reset emails")
    print(f"4. Configure SMTP in System → Email for email delivery")

if __name__ == "__main__":
    asyncio.run(main())