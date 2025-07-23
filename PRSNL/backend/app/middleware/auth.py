"""
Authentication middleware for PRSNL API
Uses JWT tokens for authentication
"""
import logging
from typing import Optional, List

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Routes that are always public (no auth required)
PUBLIC_ROUTES = [
    "/",
    "/health",
    "/api/health",
    "/api/auth/health",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/verify-email",
    "/api/auth/request-password-reset",
    "/api/auth/reset-password",
    "/api/auth/magic-link",
    "/api/auth/magic-link/verify",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/media",  # Static files
    "/test",  # Test files
    "/api/capture/debug",  # Debug endpoint for testing
    "/api/github/auth/callback",  # OAuth callback
    "/metrics",  # Prometheus metrics
    "/api/voice/health",  # Voice health check
    "/api/voice/test",  # Voice test endpoint
    # WebSocket endpoints removed - they now require authentication
]

# Routes that optionally use auth (work with or without)
OPTIONAL_AUTH_ROUTES = [
    "/api/timeline",
    "/api/search",
    "/api/content-types",
    "/api/development",
    "/api/conversations",  # Neural Echo conversations
    "/api/conversation_groups",  # Conversation groups
    "/api/suggest-questions",  # Chat suggested questions
    "/api/videos",  # Video endpoints (temporary for dev)
    "/api/video-streaming",  # Video streaming endpoints (temporary for dev)
    "/api/items",  # Item endpoints (temporary for dev)
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware
    Validates JWT tokens and adds user to request state
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 🚫 DEVELOPMENT MODE: AUTHENTICATION COMPLETELY DISABLED
        path = request.url.path
        logger.debug(f"🚫 AUTH DISABLED: Allowing access to {path}")
        
        # Always proceed without any authentication checks
        return await call_next(request)


class APIKeyBearer(HTTPBearer):
    """
    FastAPI dependency for JWT authentication
    Can be used on individual endpoints for more granular control
    """
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # Get credentials from Authorization header
        credentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate JWT token
        token = credentials.credentials
        user = await AuthService.get_current_user(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user to request state
        request.state.user = user
        
        return credentials


# JWT auth dependency
require_jwt = APIKeyBearer()


async def optional_jwt(request: Request) -> Optional[dict]:
    """
    Optional JWT authentication - returns user info if authenticated, None otherwise
    This allows endpoints to work with or without authentication
    """
    try:
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = await AuthService.get_current_user(token)
            if user:
                return {
                    "authenticated": True,
                    "user": user,
                    "permissions": ["read", "write"]  # Can be extended with role-based permissions
                }
    except Exception as e:
        logger.debug(f"Optional auth check failed: {e}")
    
    return None


# Alias for backward compatibility
optional_auth = optional_jwt