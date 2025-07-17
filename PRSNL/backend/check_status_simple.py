#!/usr/bin/env python3
"""
Simple status check for FusionAuth and PRSNL users
"""

import asyncio
import asyncpg
import requests
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://pronav@localhost:5433/prsnl"

async def check_users():
    """Check PRSNL database users"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Count users
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        print(f"\n📊 PRSNL Database Status:")
        print(f"Total users: {count}")
        
        # Get recent users
        users = await conn.fetch("""
            SELECT email, created_at, is_verified, first_name, last_name 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        print("\nRecent users:")
        for user in users:
            verified = "✅" if user['is_verified'] else "❌"
            created = user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'Unknown'
            print(f"  {verified} {user['email']} (created: {created})")
        
        # Get admin user
        admin = await conn.fetchrow("SELECT * FROM users WHERE email = 'prsnlfyi@gmail.com'")
        if admin:
            print(f"\n✅ Admin user found: prsnlfyi@gmail.com")
        else:
            print(f"\n⚠️  Admin user prsnlfyi@gmail.com not found in database")
            
    finally:
        await conn.close()

def check_fusionauth():
    """Check FusionAuth status"""
    print("\n🔐 FusionAuth Status:")
    
    try:
        response = requests.get("http://localhost:9011", timeout=5)
        if response.status_code == 200:
            print("✅ FusionAuth is running at http://localhost:9011")
        else:
            print(f"⚠️  FusionAuth returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ FusionAuth is not accessible: {e}")
        return
    
    # Try the kickstart API key
    api_key = "bf69486b-4733-4470-a592-f1bfce7af580"
    try:
        api_response = requests.get(
            "http://localhost:9011/api/system-configuration",
            headers={"Authorization": api_key},
            timeout=5
        )
        if api_response.status_code == 200:
            print(f"✅ Kickstart API key is valid")
            return api_key
        else:
            print(f"❌ Kickstart API key returned: {api_response.status_code}")
            print("\n📌 You need to generate a new API key:")
            print("1. Login to http://localhost:9011")
            print("2. Go to Settings → API Keys")
            print("3. Create a new key with full permissions")
    except Exception as e:
        print(f"❌ API check failed: {e}")
    
    return None

def show_next_steps(has_api_key):
    """Show what to do next"""
    print("\n📋 Next Steps:")
    
    if not has_api_key:
        print("\n1️⃣  Generate API Key in FusionAuth:")
        print("   - Login to http://localhost:9011")
        print("   - Navigate to Settings → API Keys")
        print("   - Click the green + button")
        print("   - Name: 'PRSNL Backend Integration'")
        print("   - Permissions: Select all")
        print("   - Copy the generated key")
    
    print("\n2️⃣  Update Admin Email (if needed):")
    print("   - Go to Users section")
    print("   - Find your admin user")
    print("   - Click Edit")
    print("   - Change email to: prsnlfyi@gmail.com")
    
    print("\n3️⃣  Configure Email (for password resets):")
    print("   - Go to Tenants → Default → Email")
    print("   - Configure SMTP settings")
    print("   - Test with your email")
    
    if has_api_key:
        print("\n4️⃣  Run User Migration:")
        print("   Once you have the API key, create a file 'api_key.txt' with the key")
        print("   Then run: python migrate_with_key.py")
    
    print("\n📚 Documentation:")
    print("   - Admin Guide: /docs/FUSIONAUTH_ADMIN_GUIDE.md")
    print("   - Quick Actions: /docs/FUSIONAUTH_QUICK_ACTIONS.md")

async def main():
    print("🔍 PRSNL + FusionAuth Integration Status\n")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check database
    await check_users()
    
    # Check FusionAuth
    api_key = check_fusionauth()
    
    # Show next steps
    show_next_steps(api_key is not None)
    
    print("\n✨ Status check complete!")

if __name__ == "__main__":
    asyncio.run(main())