#!/usr/bin/env python3
"""
Create PRSNL application in FusionAuth
"""

import requests
import json
import uuid

API_KEY = "fs7t4gH-8k1cuE2uPEJq68uhGR3LFmZZ23Kwjd4Cz4PwejWIVvla3ZJC"
FUSIONAUTH_URL = "http://localhost:9011"

# Application configuration
app_data = {
    "application": {
        "id": str(uuid.uuid4()),  # Generate new ID
        "name": "PRSNL",
        "active": True,
        "roles": [
            {
                "name": "user",
                "description": "Standard user access",
                "isDefault": True
            },
            {
                "name": "admin",
                "description": "Administrative access",
                "isDefault": False,
                "isSuperRole": True
            },
            {
                "name": "premium",
                "description": "Premium user features",
                "isDefault": False
            }
        ],
        "oauthConfiguration": {
            "authorizedRedirectURLs": [
                "http://localhost:3004/auth/callback",
                "http://localhost:3004/auth/fusionauth/callback",
                "https://prsnl.fyi/auth/callback"
            ],
            "clientId": str(uuid.uuid4()),
            "clientSecret": str(uuid.uuid4()),
            "enabledGrants": [
                "authorization_code",
                "refresh_token",
                "password"
            ],
            "logoutURL": "http://localhost:3004/auth/logout",
            "generateRefreshTokens": True,
            "requireClientAuthentication": True
        },
        "jwtConfiguration": {
            "enabled": True,
            "timeToLiveInSeconds": 3600,
            "refreshTokenTimeToLiveInMinutes": 10080,  # 7 days
            "refreshTokenExpirationPolicy": "SlidingWindow"
        },
        "registrationConfiguration": {
            "enabled": True,
            "confirmPassword": True,
            "loginIdType": "email",
            "firstName": {
                "enabled": True,
                "required": False
            },
            "lastName": {
                "enabled": True,
                "required": False
            }
        },
        "loginConfiguration": {
            "allowTokenRefresh": True,
            "generateRefreshTokens": True,
            "requireAuthentication": True
        },
        "passwordlessConfiguration": {
            "enabled": True
        },
        "verificationStrategy": "ClickableLink",
        "verifyRegistration": False,  # Will enable after email templates are configured
        "emailConfiguration": {
            "emailVerificationEmailTemplateId": None,
            "emailVerifiedEmailTemplateId": None,
            "forgotPasswordEmailTemplateId": None,
            "loginIdInUseOnCreateEmailTemplateId": None,
            "loginIdInUseOnUpdateEmailTemplateId": None,
            "loginNewDeviceEmailTemplateId": None,
            "loginSuspiciousEmailTemplateId": None,
            "passwordResetSuccessEmailTemplateId": None,
            "passwordUpdateEmailTemplateId": None,
            "passwordlessEmailTemplateId": None,
            "setPasswordEmailTemplateId": None,
            "twoFactorMethodAddEmailTemplateId": None,
            "twoFactorMethodRemoveEmailTemplateId": None
        }
    }
}

print("🚀 Creating PRSNL Application in FusionAuth\n")

# Create the application
response = requests.post(
    f"{FUSIONAUTH_URL}/api/application",
    headers={
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    },
    json=app_data
)

if response.status_code == 200:
    app = response.json()['application']
    print("✅ PRSNL Application created successfully!")
    print(f"\n📋 Application Details:")
    print(f"   ID: {app['id']}")
    print(f"   Client ID: {app['oauthConfiguration']['clientId']}")
    print(f"   Client Secret: {app['oauthConfiguration']['clientSecret']}")
    print(f"\n🎯 Roles created:")
    for role in app['roles']:
        print(f"   - {role['name']}: {role['description']}")
    
    # Save the application ID for migration
    print(f"\n💾 Saving application ID for migration...")
    with open("prsnl_app_id.txt", "w") as f:
        f.write(app['id'])
    
    print(f"\n✨ Application ready! You can now run the migration script.")
    print(f"   The migration script will be updated automatically with the new app ID.")
    
    # Update the migration script with the new app ID
    migration_file = "migrate_with_api_key.py"
    with open(migration_file, 'r') as f:
        content = f.read()
    
    # Replace the old app ID with the new one
    old_id = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"
    new_content = content.replace(old_id, app['id'])
    
    with open(migration_file, 'w') as f:
        f.write(new_content)
    
    print(f"\n✅ Migration script updated with new application ID")
    
else:
    print(f"❌ Failed to create application: {response.status_code}")
    print(f"   Error: {response.text}")
    error_data = response.json()
    if 'fieldErrors' in error_data:
        print("\nField errors:")
        for field, errors in error_data['fieldErrors'].items():
            for error in errors:
                print(f"   - {field}: {error['message']}")