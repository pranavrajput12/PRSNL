"""
Authentication middleware for PRSNL API
"""
import logging
import os
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Simple API key authentication for now
# In production, this should be replaced with proper JWT/OAuth
API_KEY = os.getenv("PRSNL_API_KEY", None)
PROTECTED_ROUTES = [
    "/api/admin",
    "/api/capture",
    "/api/items",
    "/api/tags"
]

# Routes that are always public
PUBLIC_ROUTES = [
    "/health",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/media",  # Static files
    "/api/capture/debug"  # Debug endpoint for testing
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Simple authentication middleware using API keys.
    This is a temporary solution and should be replaced with proper auth.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for public routes
        path = request.url.path
        
        # Check if route is public
        for public_route in PUBLIC_ROUTES:
            if path.startswith(public_route):
                return await call_next(request)
        
        # Check if route needs protection
        needs_auth = False
        for protected_route in PROTECTED_ROUTES:
            if path.startswith(protected_route):
                needs_auth = True
                break
        
        if needs_auth and API_KEY:
            # Check for API key in header
            api_key = request.headers.get("X-API-Key")
            
            if not api_key:
                # Check Authorization header as fallback
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    api_key = auth_header.split(" ")[1]
            
            if api_key != API_KEY:
                logger.warning(f"Unauthorized access attempt to {path}")
                return Response(
                    content='{"detail": "Invalid or missing API key"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"WWW-Authenticate": "Bearer"},
                    media_type="application/json"
                )
        
        return await call_next(request)


class APIKeyBearer(HTTPBearer):
    """
    FastAPI dependency for API key authentication
    Can be used on individual endpoints for more granular control
    """
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # First try X-API-Key header
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            if API_KEY and api_key == API_KEY:
                return HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_key)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Fall back to Authorization Bearer token
        credentials = await super().__call__(request)
        
        if credentials:
            if API_KEY and credentials.credentials == API_KEY:
                return credentials
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Optional: Decorator for protecting individual endpoints
def require_api_key(api_key_bearer: APIKeyBearer = APIKeyBearer()):
    """
    Dependency to require API key for specific endpoints
    Usage: 
    @router.get("/protected")
    async def protected_endpoint(auth: HTTPAuthorizationCredentials = Depends(require_api_key)):
        return {"message": "This is protected"}
    """
    return api_key_bearer

async def optional_auth(request: Request) -> Optional[dict]:
    """
    Optional authentication - returns user info if authenticated, None otherwise
    This allows endpoints to work with or without authentication
    """
    try:
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            # Check Authorization header as fallback
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header.split(" ")[1]
        
        if api_key and API_KEY and api_key == API_KEY:
            # Return basic user info (in real app, this would come from JWT or database)
            return {
                "authenticated": True,
                "api_key": api_key[:8] + "...",  # Partial key for logging
                "permissions": ["read", "write"]
            }
    except Exception as e:
        logger.debug(f"Optional auth check failed: {e}")
    
    return None