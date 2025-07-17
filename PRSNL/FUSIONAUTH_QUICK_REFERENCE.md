# 🚀 FusionAuth Quick Reference Card

## 🔐 Access Information
- **URL**: http://localhost:9011
- **Admin Email**: [Update to prsnlfyi@gmail.com]
- **Password**: prsnl_admin_2024!

## 📍 Essential URLs (Bookmark These!)
- **Dashboard**: http://localhost:9011/admin/
- **Users**: http://localhost:9011/admin/user/
- **API Keys**: http://localhost:9011/admin/api-key/
- **Applications**: http://localhost:9011/admin/application/
- **Email Config**: http://localhost:9011/admin/tenant/

## 🎯 Immediate Tasks

### 1. Generate API Key (5 minutes)
1. Go to: http://localhost:9011/admin/api-key/
2. Click green **+** button
3. Fill in:
   - **Name**: PRSNL Backend Integration
   - **Permissions**: Check "Super User" (grants all permissions)
4. Click **Save**
5. **COPY THE KEY IMMEDIATELY** (shown only once!)
6. Paste it in `backend/migrate_with_api_key.py`

### 2. Update Admin Email (2 minutes)
1. Go to: http://localhost:9011/admin/user/
2. Find your admin user
3. Click **Manage** → **Edit**
4. Change email to: `prsnlfyi@gmail.com`
5. Click **Save**

### 3. Run Migration (5 minutes)
```bash
cd backend
# Edit migrate_with_api_key.py and add your API key
nano migrate_with_api_key.py  # or use any editor
# Run migration
python3 migrate_with_api_key.py
```

### 4. Configure Email (10 minutes) - Optional but Recommended
1. Go to: http://localhost:9011/admin/tenant/
2. Click **Default** tenant
3. Go to **Email** tab
4. Configure SMTP:
   - **Host**: smtp.gmail.com
   - **Port**: 587
   - **Username**: your-email@gmail.com
   - **Password**: [App password, not regular password]
   - **Security**: STARTTLS

## 🔍 Key Features to Explore

### User Management Page
- **Search**: Type email or name to find users instantly
- **Bulk Actions**: Select multiple users → Actions menu
- **User Details**: Click any user to see:
  - Login history
  - Registered applications
  - Group memberships
  - Two-factor status
  - Custom data

### Quick Actions on Users
- 🔒 **Lock/Unlock**: Temporarily disable access
- 📧 **Resend Verification**: Send new verification email
- 🔑 **Reset Password**: Force password reset
- 📝 **Edit**: Update any user field
- 🗑️ **Delete**: Permanently remove (with confirmation)

### Power User Tips
- **Search Syntax**:
  - `verified:true` - Find all verified users
  - `registrations.roles:admin` - Find all admins
  - `email:*@gmail.com` - Find Gmail users
  - `loginCount:[10 TO *]` - Users with 10+ logins

- **Keyboard Shortcuts**:
  - `Cmd/Ctrl + K` - Quick search
  - `?` - Show all shortcuts
  - `Escape` - Close modals

## 📊 What You'll See After Migration

### Dashboard Metrics
- Total Users: 15+ (your existing users)
- Daily Active Users: Track engagement
- New Registrations: See growth
- Failed Logins: Security monitoring

### User List Features
- ✅ Green checkmark = Verified email
- 🔒 Lock icon = Account locked
- 📱 Phone icon = 2FA enabled
- 🎯 Target icon = Active session

## 🛠️ Advanced Features

### 1. **Roles** (Applications → PRSNL → Roles)
Create custom roles:
- `user` - Basic access
- `premium` - Premium features
- `admin` - Full access
- `moderator` - Content management

### 2. **Groups** (Left sidebar → Groups)
Organize users:
- "Beta Testers"
- "Premium Members"
- "Support Staff"

### 3. **Webhooks** (System → Webhooks)
Get notified on:
- User registration
- Login success/failure
- Password changes
- Profile updates

### 4. **Themes** (Customization → Themes)
Brand your login pages:
- Custom CSS
- Logo upload
- Color schemes

## 🚨 Common Issues & Solutions

### Can't Find Admin User?
```sql
# Check FusionAuth database
/opt/homebrew/opt/postgresql@16/bin/psql -U pronav -p 5433 -d fusionauth -c "SELECT email FROM users;"
```

### API Key Not Working?
- Ensure "Super User" permission is checked
- No spaces before/after the key
- Key is only shown once when created

### Users Not Receiving Emails?
- Configure SMTP first
- Check spam folders
- Verify "From" email is authorized

## 📞 Support Resources

### In-App Help
- Click **?** icons for context help
- Blue info boxes explain features
- Hover over fields for descriptions

### Documentation
- `/docs/FUSIONAUTH_ADMIN_GUIDE.md` - Complete guide
- `/docs/FUSIONAUTH_QUICK_ACTIONS.md` - Step-by-step
- FusionAuth Docs: https://fusionauth.io/docs/

## 🎉 You're Ready!
1. Generate API key ✓
2. Update admin email ✓
3. Run migration ✓
4. Start exploring! ✓

Remember: You're the sole admin with full control over user management, security policies, and system configuration.