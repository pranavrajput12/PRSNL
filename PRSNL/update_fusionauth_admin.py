#!/usr/bin/env python3
"""
Update FusionAuth admin email address

This script demonstrates how to update the admin email in FusionAuth using their API.
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FusionAuth configuration from environment
FUSIONAUTH_URL = os.getenv("FUSIONAUTH_URL", "http://localhost:9011")
FUSIONAUTH_API_KEY = os.getenv("FUSIONAUTH_API_KEY", "bf69486b-4733-4470-a592-f1bfce7af580")

def search_user_by_email(email):
    """Search for a user by email address"""
    headers = {
        "Authorization": FUSIONAUTH_API_KEY,
        "Content-Type": "application/json"
    }
    
    search_request = {
        "search": {
            "queryString": f"email:{email}",
            "numberOfResults": 1,
            "startRow": 0
        }
    }
    
    response = requests.post(
        f"{FUSIONAUTH_URL}/api/user/search",
        headers=headers,
        json=search_request
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("total", 0) > 0:
            return data["users"][0]
    return None

def update_user_email(user_id, new_email):
    """Update a user's email address"""
    headers = {
        "Authorization": FUSIONAUTH_API_KEY,
        "Content-Type": "application/json"
    }
    
    update_request = {
        "user": {
            "email": new_email,
            "verified": True  # Keep admin verified
        }
    }
    
    response = requests.patch(
        f"{FUSIONAUTH_URL}/api/user/{user_id}",
        headers=headers,
        json=update_request
    )
    
    return response

def main():
    print("FusionAuth Admin Email Update Tool")
    print("=" * 50)
    print(f"FusionAuth URL: {FUSIONAUTH_URL}")
    print(f"API Key: {FUSIONAUTH_API_KEY[:10]}...")
    print()
    
    # Current admin email from kickstart.json
    current_admin_email = "admin@prsnl.local"
    
    print(f"Searching for admin user with email: {current_admin_email}")
    
    # Search for the admin user
    admin_user = search_user_by_email(current_admin_email)
    
    if not admin_user:
        print(f"❌ Admin user with email '{current_admin_email}' not found!")
        print("\nTrying to list all users to find admin...")
        
        # List all users
        headers = {
            "Authorization": FUSIONAUTH_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{FUSIONAUTH_URL}/api/user",
            headers=headers
        )
        
        if response.status_code == 200:
            users = response.json().get("users", [])
            print(f"\nFound {len(users)} users:")
            for user in users[:5]:  # Show first 5 users
                print(f"  - {user['email']} (ID: {user['id']})")
                if user.get('registrations'):
                    for reg in user['registrations']:
                        print(f"    Roles: {reg.get('roles', [])}")
        return
    
    print(f"✅ Found admin user:")
    print(f"   ID: {admin_user['id']}")
    print(f"   Email: {admin_user['email']}")
    print(f"   Verified: {admin_user.get('verified', False)}")
    
    # Example: Update admin email
    new_admin_email = "admin@prsnl.fyi"  # Change this to your desired email
    
    print(f"\n📝 Example: To update admin email to '{new_admin_email}', you would:")
    print(f"   1. Call PATCH /api/user/{admin_user['id']}")
    print(f"   2. With body: ")
    print(json.dumps({
        "user": {
            "email": new_admin_email,
            "verified": True
        }
    }, indent=4))
    
    print("\n⚠️  Note: This is a dry run. To actually update, uncomment the code below:")
    print("=" * 50)
    print("""
    # Uncomment to actually update:
    # response = update_user_email(admin_user['id'], new_admin_email)
    # if response.status_code == 200:
    #     print(f"✅ Successfully updated admin email to {new_admin_email}")
    # else:
    #     print(f"❌ Failed to update: {response.status_code}")
    #     print(response.text)
    """)
    
    # Also show how to update the kickstart.json file
    print("\n📄 Don't forget to update the kickstart.json file:")
    print(f"   Change line 4: \"adminEmail\": \"{current_admin_email}\"")
    print(f"   To: \"adminEmail\": \"{new_admin_email}\"")

if __name__ == "__main__":
    main()