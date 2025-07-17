#!/usr/bin/env python3
"""
Check FusionAuth status and current users
"""

import asyncio
import requests
from app.db.database import get_db_connection

# Try to find the API key from various sources
def find_api_key():
    # Check if there's a new API key in environment or config
    possible_keys = [
        "bf69486b-4733-4470-a592-f1bfce7af580",  # Original kickstart key
        # Add new keys here after generating from FusionAuth UI
    ]
    
    for key in possible_keys:
        response = requests.get(
            "http://localhost:9011/api/system-configuration",
            headers={"Authorization": key}
        )
        if response.status_code == 200:
            return key
    return None

async def check_prsnl_users():
    """Check users in PRSNL database"""
    print("📊 Checking PRSNL Database Users...")
    async with get_db_connection() as conn:
        # Get user count
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        print(f"Total users in PRSNL: {count}")
        
        # Get recent users
        users = await conn.fetch("""
            SELECT email, username, created_at, email_verified 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        print("\nRecent users:")
        for user in users:
            verified = "✅" if user['email_verified'] else "❌"
            print(f"  {verified} {user['email']} (created: {user['created_at'].strftime('%Y-%m-%d')})")
        
        return await conn.fetch("SELECT * FROM users")

def check_fusionauth_status():
    """Check FusionAuth configuration"""
    print("\n🔐 Checking FusionAuth Status...")
    
    # Check if FusionAuth is accessible
    response = requests.get("http://localhost:9011")
    if response.status_code != 200:
        print("❌ FusionAuth is not accessible")
        return None
    
    print("✅ FusionAuth is running")
    
    # Try to find working API key
    api_key = find_api_key()
    if api_key:
        print(f"✅ Found working API key: {api_key[:8]}...")
        
        # Get system info
        sys_response = requests.get(
            "http://localhost:9011/api/system-configuration",
            headers={"Authorization": api_key}
        )
        if sys_response.status_code == 200:
            data = sys_response.json()
            print(f"✅ FusionAuth version: {data.get('systemConfiguration', {}).get('version', 'Unknown')}")
        
        return api_key
    else:
        print("❌ No working API key found")
        print("\n📌 To generate an API key:")
        print("1. Login to http://localhost:9011")
        print("2. Go to Settings → API Keys")
        print("3. Click the green + button")
        print("4. Name it 'PRSNL Backend'")
        print("5. Select all permissions")
        print("6. Copy the key and add it to this script")
        return None

def create_migration_script(api_key):
    """Create a ready-to-use migration script"""
    script_content = f'''#!/usr/bin/env python3
import requests
import asyncio
from app.db.database import get_db_connection

API_KEY = "{api_key}"
FUSIONAUTH_URL = "http://localhost:9011"
APPLICATION_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"

async def migrate_users():
    async with get_db_connection() as conn:
        users = await conn.fetch("SELECT * FROM users")
        
        for user in users:
            # Check if user exists
            check = requests.get(
                f"{{FUSIONAUTH_URL}}/api/user?email={{user['email']}}",
                headers={{"Authorization": API_KEY}}
            )
            
            if check.status_code == 200 and check.json().get('user'):
                print(f"⏭️  User {{user['email']}} already exists")
                continue
            
            # Create user
            user_data = {{
                "user": {{
                    "email": user['email'],
                    "username": user['username'] or user['email'].split('@')[0],
                    "verified": user['email_verified'] or False
                }},
                "sendSetPasswordEmail": True,
                "registration": {{
                    "applicationId": APPLICATION_ID,
                    "roles": ["admin"] if user['email'] == "prsnlfyi@gmail.com" else ["user"]
                }}
            }}
            
            response = requests.post(
                f"{{FUSIONAUTH_URL}}/api/user/registration",
                headers={{"Authorization": API_KEY, "Content-Type": "application/json"}},
                json=user_data
            )
            
            if response.status_code == 200:
                print(f"✅ Migrated: {{user['email']}}")
            else:
                print(f"❌ Failed: {{user['email']}} - {{response.text}}")

if __name__ == "__main__":
    print("Starting migration...")
    asyncio.run(migrate_users())
    print("\\n✅ Migration complete!")
'''
    
    with open("/Users/pronav/Personal Knowledge Base/PRSNL/backend/migrate_now.py", "w") as f:
        f.write(script_content)
    
    print("\n✅ Created migration script: backend/migrate_now.py")
    print("Run it with: cd backend && python migrate_now.py")

async def main():
    print("🔍 PRSNL FusionAuth Integration Status Check\n")
    
    # Check PRSNL users
    users = await check_prsnl_users()
    
    # Check FusionAuth
    api_key = check_fusionauth_status()
    
    if api_key:
        print("\n✅ Ready for migration!")
        create_migration_script(api_key)
    else:
        print("\n⚠️  Complete these steps first:")
        print("1. Login to FusionAuth at http://localhost:9011")
        print("2. Update your admin email to prsnlfyi@gmail.com")
        print("3. Generate an API key with full permissions")
        print("4. Add the API key to this script")
    
    print("\n📚 Documentation:")
    print("- Admin Guide: /docs/FUSIONAUTH_ADMIN_GUIDE.md")
    print("- Quick Actions: /docs/FUSIONAUTH_QUICK_ACTIONS.md")

if __name__ == "__main__":
    asyncio.run(main())