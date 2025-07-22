# Security Bypasses for Development

**CRITICAL: These bypasses MUST be removed before any production deployment\!**

## Added on 2025-07-19

### 1. Backend Authentication Bypass
**File**: `backend/app/core/auth.py`
- **Lines**: 38-42, 50-54, 131
- **Issue**: Returns hardcoded test user when no authentication provided
- **Fix**: Remove the bypass and implement proper authentication

### 2. WebSocket Authentication Bypass  
**File**: `backend/app/api/ws.py`
- **Lines**: 78-82
- **Issue**: Hardcoded user_id for WebSocket connections
- **Fix**: Implement proper WebSocket authentication

### 3. Frontend Auth Guard Bypass
**File**: `frontend/src/lib/auth/auth-guard.ts`
- **Lines**: 91-101
- **Issue**: Allows access without authentication and sets dummy token
- **Fix**: Remove bypass and require proper authentication

### 4. Voice WebSocket Endpoint Bypass
**File**: `backend/app/middleware/auth.py`
- **Lines**: 41 (PUBLIC_ROUTES)
- **Issue**: Added `/api/voice/ws` to public routes to bypass auth for voice chat
- **Fix**: Implement proper WebSocket authentication for voice endpoint

### 5. Chat WebSocket Endpoints Bypass (Added 2025-07-22)
**File**: `backend/app/middleware/auth.py`
- **Lines**: 42-43 (PUBLIC_ROUTES)
- **Issue**: Added `/ws/chat` and `/ws/floating-chat` to public routes to bypass auth for chat WebSocket connections
- **Fix**: Implement proper WebSocket authentication for chat endpoints

## Summary
These bypasses were added to allow development to continue while the authentication system is being implemented. They create serious security vulnerabilities and must be removed before any public deployment.

## To Remove Bypasses:
1. Implement proper authentication system (Keycloak/FusionAuth)
2. Remove all code blocks marked with "SECURITY BYPASS" or "TEMPORARY DEVELOPMENT BYPASS"
3. Test all functionality with proper authentication
4. Run security audit before deployment
EOF < /dev/null