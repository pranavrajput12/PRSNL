#!/usr/bin/env python3
"""
Migrate existing PRSNL users to FusionAuth
This script syncs users from the PRSNL PostgreSQL database to FusionAuth
"""

import psycopg2
import requests
import json
from datetime import datetime
import sys

# Configuration
FUSIONAUTH_URL = "http://localhost:9011"
FUSIONAUTH_API_KEY = "bf69486b-4733-4470-a592-f1bfce7af580"  # From kickstart.json
FUSIONAUTH_TENANT_ID = "d7d09513-a3f5-401c-9685-34ab6c552453"  # Default tenant
FUSIONAUTH_APPLICATION_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"  # PRSNL app

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'prsnl',
    'user': 'pronav'
}

def get_users_from_db():
    """Fetch all users from PRSNL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get all users with their data
        cur.execute("""
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
        for row in cur.fetchall():
            user = {
                'user_id': row[0],
                'email': row[1],
                'created_at': row[2],
                'username': row[3],
                'first_name': row[4],
                'last_name': row[5],
                'email_verified': row[6] if row[6] is not None else False,
                'profile_data': row[7] if row[7] else {}
            }
            users.append(user)
        
        cur.close()
        conn.close()
        
        return users
    except Exception as e:
        print(f"Error fetching users from database: {e}")
        return []

def check_user_exists(email):
    """Check if user already exists in FusionAuth"""
    try:
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user?email={email}",
            headers={
                "Authorization": FUSIONAUTH_API_KEY
            }
        )
        return response.status_code == 200 and response.json().get('user') is not None
    except:
        return False

def migrate_user_to_fusionauth(user):
    """Migrate a single user to FusionAuth"""
    try:
        # Check if user already exists
        if check_user_exists(user['email']):
            print(f"User {user['email']} already exists in FusionAuth, skipping...")
            return False
        
        # Prepare user data for FusionAuth
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
                "roles": ["user"]  # Default role
            },
            "sendSetPasswordEmail": False,  # Don't send emails during migration
            "skipVerification": True  # Keep existing verification status
        }
        
        # If user is admin@prsnl.local, give admin role
        if user['email'] == 'admin@prsnl.local':
            fusionauth_user['registration']['roles'] = ["admin", "user"]
        
        # Create user in FusionAuth
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
        # First, find the user by old email
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user?email={old_email}",
            headers={
                "Authorization": FUSIONAUTH_API_KEY
            }
        )
        
        if response.status_code == 200:
            user_data = response.json()
            if user_data.get('user'):
                user_id = user_data['user']['id']
                
                # Update the email
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

def main():
    print("🚀 Starting PRSNL to FusionAuth user migration...\n")
    
    # First, update admin email if needed
    print("📧 Updating admin email address...")
    update_admin_email("admin@prsnl.local", "prsnlfyi@gmail.com")
    print()
    
    # Get users from database
    print("📊 Fetching users from PRSNL database...")
    users = get_users_from_db()
    print(f"Found {len(users)} users to migrate\n")
    
    # Migrate each user
    successful = 0
    failed = 0
    
    for user in users:
        if migrate_user_to_fusionauth(user):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n📈 Migration Summary:")
    print(f"   Total users: {len(users)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏭️  Skipped (already exists): {len(users) - successful - failed}")
    
    print("\n✨ Migration complete!")
    print(f"Visit http://localhost:9011 to manage users in FusionAuth")

if __name__ == "__main__":
    main()