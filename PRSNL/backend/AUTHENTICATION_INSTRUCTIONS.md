# PRSNL Development Authentication Instructions

## Quick Fix for Authentication Issues

The authentication system is now working! Follow these steps to login and access all pages:

### Step 1: Open the Development Login Page

Open this file in your browser:
```
file:///Users/pronav/Personal Knowledge Base/PRSNL/backend/dev_login.html
```

### Step 2: Login

1. The form is pre-filled with test credentials (any email/password will work)
2. Click "Login to PRSNL"
3. You should see "Login successful! Redirecting to chat..."

### Step 3: Verify Authentication

After login, you should be redirected to the chat page. If not, manually navigate to:
- http://localhost:3004/chat
- http://localhost:3004/code-cortex/codemirror

### What This Does

The development login page:
1. Calls `/api/auth/login/prsnl` with your credentials
2. Receives JWT tokens (access and refresh tokens)
3. Stores them in localStorage with the correct keys:
   - `prsnl_auth_token` - Access token
   - `prsnl_refresh_token` - Refresh token
   - `prsnl_auth_source` - Set to "prsnl"
   - `prsnl_token` - Legacy compatibility

### Troubleshooting

If you still see authentication errors:

1. **Check tokens in browser console:**
   ```javascript
   localStorage.getItem('prsnl_auth_token')
   ```
   Should return a JWT token starting with "eyJ..."

2. **Manually set tokens (if needed):**
   First get fresh tokens:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login/prsnl \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test"}'
   ```
   
   Then in browser console:
   ```javascript
   // Replace with tokens from curl response
   localStorage.setItem('prsnl_auth_token', 'YOUR_ACCESS_TOKEN');
   localStorage.setItem('prsnl_refresh_token', 'YOUR_REFRESH_TOKEN');
   localStorage.setItem('prsnl_auth_source', 'prsnl');
   localStorage.setItem('prsnl_token', 'YOUR_ACCESS_TOKEN');
   location.reload();
   ```

3. **Clear old tokens:**
   ```javascript
   localStorage.clear();
   location.reload();
   ```

### Security Note

⚠️ **DEVELOPMENT ONLY** - This authentication system accepts any credentials and is for development purposes only. See `/SECURITY_BYPASSES.md` for details on security bypasses that must be fixed before production.

### API Endpoints

The following authentication endpoints are available:
- `POST /api/auth/login/prsnl` - Login with email/password
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (clears tokens)