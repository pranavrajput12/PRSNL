# PRSNL Authentication System Documentation

## Overview
PRSNL uses a JWT-based authentication system with email verification and magic link support, built with FastAPI backend and SvelteKit frontend.

## Features
- ✅ JWT token-based authentication (access + refresh tokens)
- ✅ Email verification via Resend API
- ✅ Magic link authentication
- ✅ Password-based authentication with bcrypt
- ✅ Protected routes with auth guards
- ✅ Persistent auth state across page navigation
- ✅ User profile management
- ✅ Session management with PostgreSQL

## Backend Architecture

### Authentication Flow
1. **Registration**: User signs up → Password hashed → Account created → Verification email sent
2. **Login**: Email/password validated → JWT tokens generated → Session stored in database
3. **Token Refresh**: Refresh token validated → New access token issued
4. **Magic Link**: Email sent with token → Token validated → JWT tokens issued

### Key Components
- **Auth Service** (`/backend/app/services/auth_service.py`)
  - Handles user registration, login, token generation
  - Password hashing with bcrypt
  - JWT token creation and validation
  - Session management

- **Auth API** (`/backend/app/api/auth.py`)
  - REST endpoints for authentication
  - Token refresh endpoint
  - User profile endpoints

- **Auth Middleware** (`/backend/app/middleware/auth.py`)
  - JWT validation middleware
  - Protected route handling

### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    user_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Frontend Architecture

### Auth Store (`/frontend/src/lib/stores/auth.ts`)
- Centralized authentication state management
- Automatic token refresh
- LocalStorage persistence
- Auth actions: register, login, logout, magic link, email verification

### Protected Routes
- Auth guards check authentication before rendering
- Automatic redirect to login for unauthenticated users
- `(protected)` route group for authenticated pages

### Auth Pages
- `/auth/login` - Login with password or magic link
- `/auth/signup` - Multi-step registration flow
- `/auth/verify-email` - Email verification handler
- `/auth/magic-link` - Magic link verification handler

## Configuration

### Environment Variables
```bash
# Backend (.env)
RESEND_API_KEY=your_resend_api_key
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend
# Uses API_BASE_URL from window.location.origin
```

### Security Features
- Password requirements: 8+ chars, uppercase, lowercase, number
- JWT expiry handling
- Secure password hashing with bcrypt
- CORS configuration for frontend-backend communication

## Recent Fixes (2025-07-16)

### 1. Token Refresh 500 Errors
**Issue**: UUID conversion errors in refresh endpoint causing crashes during navigation
**Fix**: Added proper UUID handling in auth service methods:
- `refresh_access_token`: Safe UUID conversion from JWT claims
- `create_tokens`: Ensures proper string/UUID conversion
- `get_current_user`: Added error handling for invalid UUIDs

### 2. Session Validation Performance
**Issue**: Expensive database lookups on every authenticated request
**Fix**: Removed session validation from `get_current_user`, relying on JWT expiry for security

### 3. Authentication Persistence
**Issue**: Users getting logged out when navigating between pages
**Fix**: 
- Fixed token refresh mechanism
- Improved auth store token management
- Proper error handling in auth guard

### 4. Accessibility Improvements
- Fixed mobile backdrop keyboard accessibility
- Corrected self-closing HTML tags in components
- Added ARIA roles for interactive elements

## Usage Examples

### Register a New User
```javascript
import { authActions } from '$lib/stores/auth';

const success = await authActions.register({
  email: 'user@example.com',
  password: 'SecurePass123',
  first_name: 'John',
  last_name: 'Doe',
  user_type: 'individual'
});
```

### Login
```javascript
const success = await authActions.login({
  email: 'user@example.com',
  password: 'SecurePass123'
});
```

### Send Magic Link
```javascript
const success = await authActions.sendMagicLink('user@example.com');
```

### Check Authentication
```javascript
import { isAuthenticated, user } from '$lib/stores/auth';

// In Svelte component
$: if ($isAuthenticated) {
  console.log('User:', $user);
}
```

## Troubleshooting

### Common Issues
1. **"Token refresh failed"**: Clear localStorage and login again
2. **"Invalid refresh token"**: Token expired, user needs to login
3. **Email not received**: Check Resend API key configuration
4. **CORS errors**: Ensure backend is running on correct port (8000)

### Debug Commands
```bash
# Check sessions in database
psql -U pronav -p 5432 -d prsnl -c "SELECT * FROM user_sessions ORDER BY created_at DESC LIMIT 5;"

# Monitor auth logs
tail -f backend/backend.log | grep -E "(auth|token|session)"

# Clear all sessions for a user
psql -U pronav -p 5432 -d prsnl -c "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = 'user-uuid';"
```

## Future Enhancements
- [ ] OAuth integration (Google, GitHub)
- [ ] Two-factor authentication (2FA)
- [ ] Password reset flow
- [ ] Account lockout after failed attempts
- [ ] Session activity tracking
- [ ] Remember me functionality