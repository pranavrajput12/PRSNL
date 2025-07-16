# PRSNL Authentication Implementation

## Overview

This document describes the JWT-based authentication system implemented for PRSNL to replace the temporary "temp-user-for-oauth" placeholder.

## Implementation Summary

### 1. Database Schema (✅ Completed)

Created comprehensive authentication tables in migration `017_add_user_authentication.sql`:
- `users` - Core user data with email, password hash, profile info
- `user_profiles` - Extended user information and preferences  
- `user_sessions` - JWT session management with refresh tokens
- `email_verifications` - Email verification tokens
- `password_resets` - Password reset tokens
- `oauth_connections` - OAuth provider connections (GitHub, Google, etc.)

A default admin user was created:
- Email: `admin@prsnl.local`
- Password: `admin123` (must be changed in production)

### 2. Dependencies (✅ Completed)

Added to `requirements.txt`:
```
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4  # Password hashing
email-validator==2.1.0  # Email validation
```

### 3. Authentication Models (✅ Completed)

Created Pydantic models in `app/models/auth.py`:
- Request models: `UserRegister`, `UserLogin`, `RefreshTokenRequest`, etc.
- Response models: `UserResponse`, `TokenResponse`, `UserProfileResponse`
- OAuth models: `OAuthProvider`, `OAuthCallback`, `OAuthConnection`
- Validation: Password complexity, email format, user types

### 4. JWT Service (✅ Completed)

Implemented `AuthService` in `app/services/auth_service.py`:
- Password hashing with bcrypt
- JWT token creation and validation
- User registration with email verification
- Login with password verification
- Token refresh mechanism
- Session management
- Password reset flow
- Email verification

Configuration:
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days
- Algorithm: HS256
- Secret key: From environment variable `SECRET_KEY`

### 5. API Endpoints (✅ Completed)

Created auth API in `app/api/auth.py`:

**Public endpoints:**
- `GET /api/auth/health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/request-password-reset` - Request reset
- `POST /api/auth/reset-password` - Reset password

**Protected endpoints:**
- `GET /api/auth/me` - Get current user
- `GET /api/auth/me/profile` - Get user profile
- `PUT /api/auth/me/profile` - Update profile
- `PUT /api/auth/me/preferences` - Update preferences
- `POST /api/auth/logout` - Logout
- `GET /api/auth/sessions` - List active sessions
- `DELETE /api/auth/sessions/{id}` - Revoke session
- `POST /api/auth/revoke-all-sessions` - Revoke all sessions

### 6. Core Auth Module (✅ Completed)

Updated `app/core/auth.py`:
- Replaced temp auth with JWT validation
- `get_current_user()` - Extract user from JWT
- `get_current_user_optional()` - Optional auth
- `get_current_user_ws()` - WebSocket auth
- `verify_token()` - Token validation
- Backward compatibility during migration

### 7. Middleware Update (✅ Completed)

Enhanced `app/middleware/auth.py`:
- JWT token validation middleware
- Public routes configuration
- Optional auth routes
- Token extraction from Authorization header
- User injection into request state
- Proper error responses

### 8. Code Migration (✅ Completed)

Replaced "temp-user-for-oauth" throughout:
- `app/services/github_service.py` - Now requires user ID in state
- `app/api/github.py` - All endpoints use authenticated user
- `app/api/codemirror.py` - Requires authentication
- Removed all hardcoded temp user references

### 9. Test Script (✅ Completed)

Created `test_auth_system.py` for end-to-end testing:
- Registration flow
- Login flow
- Protected endpoint access
- Token refresh
- Invalid token handling
- Logout flow
- Admin user test

## Migration Guide

### For Backend Developers

1. **Start the backend** with the new auth system:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

2. **Test the auth system**:
```bash
python3 test_auth_system.py
```

3. **Use authentication in new endpoints**:
```python
from app.core.auth import get_current_user, User

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"user_id": str(current_user.id)}
```

### For Frontend Developers

1. **Update API calls** to include JWT token:
```javascript
const response = await fetch('/api/protected', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
```

2. **Implement auth flow**:
```javascript
// Register
const register = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email, password, first_name, last_name
    })
});

// Login
const login = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
});

const { access_token, refresh_token, user } = await login.json();
```

3. **Handle token refresh**:
```javascript
const refresh = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
});
```

## Security Considerations

1. **Change admin password** immediately in production
2. **Set strong SECRET_KEY** in environment variables
3. **Use HTTPS** in production for all API calls
4. **Implement rate limiting** on auth endpoints
5. **Add email verification** before allowing full access
6. **Monitor failed login attempts**
7. **Implement 2FA** for enhanced security (future)

## Next Steps

1. **Frontend Integration**:
   - Create login/register pages
   - Implement token storage (localStorage/cookies)
   - Add auth state management
   - Update all API calls to include tokens

2. **Email Service**:
   - Implement email sending for verification
   - Password reset email templates
   - Welcome emails

3. **OAuth Providers**:
   - Complete GitHub OAuth integration
   - Add Google OAuth
   - Add other providers as needed

4. **Security Enhancements**:
   - Two-factor authentication
   - Account lockout after failed attempts
   - Session management UI
   - Security audit logging

## Testing

Run the test script to verify the auth system:
```bash
cd backend
python3 test_auth_system.py
```

This will test:
- Health check
- User registration
- Login
- Protected endpoints
- Token refresh
- Invalid tokens
- Logout
- Admin access

## Troubleshooting

### Common Issues

1. **500 errors on auth endpoints**
   - Check database connection
   - Verify migrations ran successfully
   - Check logs for detailed errors

2. **401 Unauthorized errors**
   - Verify token is included in Authorization header
   - Check token hasn't expired
   - Ensure user is verified if required

3. **Token validation failures**
   - Verify SECRET_KEY is set
   - Check token format (Bearer prefix)
   - Ensure same SECRET_KEY across instances

4. **Database errors**
   - Run migration: `psql -U pronav -p 5433 -d prsnl -f app/db/migrations/017_add_user_authentication.sql`
   - Check PostgreSQL is running on port 5433
   - Verify user tables exist

## Conclusion

The authentication system is now fully implemented and ready for integration. The temporary "temp-user-for-oauth" has been completely replaced with a proper JWT-based authentication system that provides secure user management, session handling, and token-based API access.