# FusionAuth Admin Guide for PRSNL

## 🎯 Quick Access
- **FusionAuth Admin Panel**: http://localhost:9011
- **Admin Email**: prsnlfyi@gmail.com (to be updated)
- **Admin Password**: prsnl_admin_2024!

## 📊 Key Admin Features to Explore

### 1. **Dashboard** (Home Page)
- **Daily Active Users**: Track user engagement
- **Login Statistics**: Monitor authentication patterns
- **Registration Trends**: See user growth over time
- **System Health**: Monitor performance metrics

### 2. **Users Management** (`/admin/user/`)
**Essential Features:**
- **Search Users**: By email, username, or ID
- **User Details**: View complete user profiles
- **Edit Users**: Update email, roles, metadata
- **Login History**: Track user authentication events
- **Two-Factor Auth**: Enable/disable 2FA per user
- **Password Management**: Reset passwords, set temporary passwords
- **Account Actions**: Lock/unlock accounts, verify emails

**Power Features:**
- **Bulk Actions**: Select multiple users for batch operations
- **Export Users**: Download user data as CSV/JSON
- **Custom Data**: Add application-specific metadata
- **Registration Management**: View/edit app registrations

### 3. **Applications** (`/admin/application/`)
**Your PRSNL App Configuration:**
- **OAuth Settings**: Configure redirect URIs, grant types
- **JWT Configuration**: Customize token claims
- **Registration Settings**: Define required fields
- **Roles Management**: Create custom roles (admin, user, premium)
- **Email Templates**: Customize verification emails
- **Webhooks**: Set up event notifications

### 4. **Tenants** (`/admin/tenant/`)
**Multi-tenancy Features:**
- **Tenant Isolation**: Separate user bases
- **Custom Domains**: Brand per tenant
- **Theme Customization**: Different UI per tenant
- **JWT Signing Keys**: Tenant-specific security
- **Password Policies**: Custom rules per tenant

### 5. **Groups** (`/admin/group/`)
**User Organization:**
- Create groups like "Premium Users", "Beta Testers"
- Assign roles to entire groups
- Bulk permission management
- Group-based access control

### 6. **API Keys** (`/admin/api-key/`)
**Integration Security:**
- Generate API keys for backend integration
- Set key permissions (read/write)
- IP restrictions for keys
- Key rotation schedule

### 7. **Reports** (`/admin/report/`)
**Analytics & Insights:**
- **Daily Active Users Report**
- **Login Report**: Success/failure rates
- **Registration Report**: New user trends
- **Totals Report**: System-wide statistics

### 8. **System** (`/admin/system/`)
**Configuration & Maintenance:**
- **Email Configuration**: SMTP settings
- **Event Log**: Audit trail of all actions
- **Webhooks**: System-wide event handlers
- **Login Records**: Detailed authentication logs
- **Reindex**: Search engine maintenance

## 🚀 Immediate Actions for PRSNL

### 1. **Update Admin Email**
```bash
# Run the migration script
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL
python3 scripts/migrate_users_to_fusionauth.py
```

### 2. **Configure Email Service**
Navigate to **System → Email** and configure:
- SMTP Host: (your SMTP server)
- Port: 587 (TLS) or 465 (SSL)
- Username/Password: Your SMTP credentials
- From Email: noreply@prsnl.fyi

### 3. **Set Up Password Policy**
Go to **Tenants → Default → Password** and configure:
- Minimum length: 8 characters
- Require uppercase: Yes
- Require lowercase: Yes
- Require numbers: Yes
- Password history: Prevent last 5 passwords

### 4. **Create User Roles**
In **Applications → PRSNL → Roles**, create:
- `user` - Basic access
- `premium` - Premium features
- `admin` - Administrative access
- `moderator` - Content moderation

### 5. **Configure OAuth for Frontend**
In **Applications → PRSNL → OAuth**:
- Authorized redirect URLs: `http://localhost:3004/auth/callback`
- Logout URL: `http://localhost:3004/auth/logout`
- Enable refresh tokens
- Access token duration: 3600 seconds
- Refresh token duration: 43200 seconds

## 📈 User Migration Timeline

### Phase 1: Initial Setup (Now)
- ✅ Install FusionAuth
- ✅ Create admin user
- 🔄 Update admin email to prsnlfyi@gmail.com
- 🔄 Run user migration script

### Phase 2: Integration (Next)
- Configure unified auth to use FusionAuth
- Update frontend login/signup flows
- Implement SSO with FusionAuth
- Test authentication flows

### Phase 3: Advanced Features
- Enable social logins (Google, GitHub)
- Implement passwordless (magic links)
- Set up MFA/2FA
- Configure advanced webhooks

## 🔍 Exploring FusionAuth UI

### Navigation Tips
1. **Quick Search** (top right): Find users instantly
2. **Breadcrumbs**: Easy navigation between sections
3. **Help Icon**: Context-sensitive documentation
4. **Theme Toggle**: Dark/light mode

### User Search Queries
- `email:*@gmail.com` - Find all Gmail users
- `verified:false` - Find unverified users
- `registrations.roles:admin` - Find all admins
- `lastLogin:[2024-01-01 TO 2024-12-31]` - Login date range

### Useful Keyboard Shortcuts
- `Ctrl/Cmd + K`: Quick search
- `Ctrl/Cmd + /`: Show shortcuts
- `Escape`: Close modals

## 🛡️ Security Best Practices

1. **Regular API Key Rotation**: Rotate keys monthly
2. **Audit Logs**: Review weekly in System → Event Log
3. **Failed Login Monitoring**: Set up alerts for suspicious activity
4. **IP Restrictions**: Limit admin access to known IPs
5. **Webhook Security**: Use webhook signatures

## 📚 Learning Resources

### In-App Features to Explore
1. **User Details Page**: Click any user to see all available data
2. **Application Configuration**: Explore all OAuth settings
3. **Theme Editor**: Customize login pages
4. **Email Templates**: Preview and test emails

### Advanced Features
1. **Connectors**: LDAP/SAML integration
2. **Identity Providers**: Social login setup
3. **Lambda Functions**: Custom authentication logic
4. **Advanced Registration**: Multi-step forms

### Monitoring & Alerts
1. Set up login anomaly detection
2. Configure failed login thresholds
3. Create user registration notifications
4. Monitor API usage patterns

## 🔧 Troubleshooting Common Issues

### User Can't Login
1. Check user is verified
2. Verify application registration
3. Check account isn't locked
4. Review login records

### Email Not Sending
1. Verify SMTP configuration
2. Check email templates
3. Review email status in user details
4. Check spam folders

### API Authentication Failing
1. Verify API key permissions
2. Check tenant configuration
3. Validate JWT settings
4. Review CORS settings

## 📞 Next Steps

1. **Run the migration script** to sync your 15 existing users
2. **Update admin email** to prsnlfyi@gmail.com
3. **Configure email service** for user notifications
4. **Set up webhook** to sync user changes back to PRSNL DB
5. **Test user login** with migrated accounts

Visit http://localhost:9011 and start exploring these features. The UI is intuitive and well-documented. Click the help icons for context-sensitive guidance!