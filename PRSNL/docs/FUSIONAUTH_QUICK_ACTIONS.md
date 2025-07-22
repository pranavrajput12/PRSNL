# FusionAuth Quick Actions Guide

## 🚨 Immediate Actions Required

### 1. Update Admin Email (Via UI)
Since you just set up FusionAuth, the easiest way to update your admin email is through the UI:

1. **Login to FusionAuth**: http://localhost:9011
   - Use the wrong email you entered by mistake
   - Password: prsnl_admin_2024!

2. **Navigate to your profile**:
   - Click on your username in the top right
   - Select "Account" or "Profile"

3. **Update email**:
   - Change email to: `prsnlfyi@gmail.com`
   - Save changes

4. **Alternatively, go to Users section**:
   - Navigate to Users → Search
   - Find your admin user
   - Click "Manage" → "Edit"
   - Update email to `prsnlfyi@gmail.com`
   - Save

### 2. Generate API Key for Integration
1. Go to **Settings → API Keys**
2. Click **Add** (Green + button)
3. Configure:
   - **Name**: PRSNL Backend Integration
   - **Permissions**: Select all (for admin access)
4. Copy the generated key
5. Update the migration script with the new key

### 3. Quick User Count Check

To see your current users in PRSNL database:

```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate
python3 -c "
import asyncio
from app.db.database import get_db_connection

async def count_users():
    async with get_db_connection() as conn:
        result = await conn.fetchval('SELECT COUNT(*) FROM users')
        users = await conn.fetch('SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 10')
        print(f'Total users: {result}')
        print('\nRecent users:')
        for user in users:
            print(f'  - {user[\"email\"]} (created: {user[\"created_at\"]})')

asyncio.run(count_users())
"
```

### 4. Configure Email (Essential for User Management)

1. **Navigate to**: Tenants → Default → Email
2. **Configure SMTP**:
   - **Host**: smtp.gmail.com (for Gmail)
   - **Port**: 587
   - **Username**: your-email@gmail.com
   - **Password**: App-specific password (not regular password)
   - **Security**: STARTTLS
   
3. **For Gmail Users**:
   - Enable 2FA on your Google account
   - Generate app password: https://myaccount.google.com/apppasswords
   - Use the app password in FusionAuth

4. **Test Configuration**:
   - Click "Send test email"
   - Enter your email
   - Verify receipt

### 5. Key Admin Panels to Explore Now

#### Users Section (Most Important)
- **URL**: http://localhost:9011/admin/user/
- **Features**:
  - Search users by email
  - View login history
  - Edit user details
  - Reset passwords
  - Manage roles

#### Dashboard
- **URL**: http://localhost:9011/admin/
- **Shows**:
  - Total users
  - Daily active users
  - Recent registrations
  - Login statistics

#### Applications
- **URL**: http://localhost:9011/admin/application/
- **Your app**: PRSNL (should be auto-created)
- **Configure**:
  - OAuth settings
  - Roles (user, admin, premium)
  - Registration settings

## 📊 User Migration (After Email Update)

Once you've updated your admin email and generated an API key:

```bash
# Simple migration command
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL
cat > quick_migrate.py << 'EOF'
import requests

# Update these after getting from FusionAuth
FUSIONAUTH_API_KEY = "YOUR_NEW_API_KEY_HERE"
ADMIN_EMAIL = "prsnlfyi@gmail.com"

# Test connection
response = requests.get(
    "http://localhost:9011/api/user?email=" + ADMIN_EMAIL,
    headers={"Authorization": FUSIONAUTH_API_KEY}
)

if response.status_code == 200:
    print("✅ API Key works! Found admin user")
    print("Ready for migration")
else:
    print("❌ Check your API key")
    print(f"Status: {response.status_code}")
EOF

python3 quick_migrate.py
```

## 🎯 Priority Order

1. **First**: Update admin email in UI
2. **Second**: Generate API key
3. **Third**: Configure email (for password resets)
4. **Fourth**: Run user migration
5. **Fifth**: Explore features

## 🔍 Finding Your Admin User

If you forgot which email you used:

1. Check browser autofill
2. Look at FusionAuth logs:
   ```bash
   docker logs prsnl-fusionauth | grep -i "user created"
   ```
3. Check PostgreSQL directly:
   ```bash
   /opt/homebrew/opt/postgresql@16/bin/psql -U pronav -p 5432 -d fusionauth -c "SELECT email FROM users;"
   ```

## 💡 Pro Tips

1. **Bookmark these URLs**:
   - Users: http://localhost:9011/admin/user/
   - Dashboard: http://localhost:9011/admin/
   - API Keys: http://localhost:9011/admin/api-key/

2. **Enable dark mode**: Click sun/moon icon in top right

3. **Quick search**: Press `Cmd+K` to search users instantly

4. **Keyboard shortcuts**: Press `?` to see all shortcuts

Need help? The UI has excellent inline documentation - look for the (?) icons!