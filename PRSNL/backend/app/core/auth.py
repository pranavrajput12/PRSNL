"""
Authentication utilities for PRSNL
Handles JWT token validation and user extraction
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import AuthService
from app.models.auth import UserResponse

# Security bearer
security = HTTPBearer(auto_error=False)


class User:
    """User class with proper authentication"""
    def __init__(self, id: str, email: str, name: str, is_verified: bool = False):
        self.id = UUID(id) if isinstance(id, str) else id
        self.email = email
        self.name = name
        self.is_verified = is_verified
        self.first_name = name.split()[0] if name else ""
        self.last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token
    """
    if not credentials:
        # For backward compatibility during migration, return test user if no auth
        # TODO: Remove this after frontend is updated
        return User(
            id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
            email="test@example.com",
            name="Test User"
        )
    
    token = credentials.credentials
    user_response = await AuthService.get_current_user(token)
    
    if not user_response:
        # For development/migration period, return test user on invalid token
        # TODO: Remove this after frontend auth is fully implemented
        return User(
            id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
            email="test@example.com",
            name="Test User"
        )
    
    # Convert UserResponse to User
    return User(
        id=str(user_response.id),
        email=user_response.email,
        name=f"{user_response.first_name or ''} {user_response.last_name or ''}".strip() or user_response.email,
        is_verified=user_response.is_verified
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional auth function - returns user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_user_ws(websocket, token: Optional[str] = None) -> Optional[User]:
    """
    WebSocket auth function - validates JWT token from WebSocket
    """
    if not token:
        # For backward compatibility during migration
        # TODO: Remove this after frontend is updated
        return User(
            id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
            email="test@example.com",
            name="Test User"
        )
    
    user_response = await AuthService.get_current_user(token)
    
    if not user_response:
        return None
    
    # Convert UserResponse to User
    return User(
        id=str(user_response.id),
        email=user_response.email,
        name=f"{user_response.first_name or ''} {user_response.last_name or ''}".strip() or user_response.email,
        is_verified=user_response.is_verified
    )


async def verify_token(token: str) -> Optional[dict]:
    """
    Verify token and return user info
    """
    user_response = await AuthService.get_current_user(token)
    
    if not user_response:
        return None
    
    return {
        "user_id": str(user_response.id),
        "email": user_response.email,
        "name": f"{user_response.first_name or ''} {user_response.last_name or ''}".strip() or user_response.email,
        "is_verified": user_response.is_verified
    }


# For backward compatibility
async def get_test_user() -> User:
    """
    Get test user for development/migration purposes
    This should only be used in non-authenticated endpoints during migration
    """
    return User(
        id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
        email="admin@prsnl.local",
        name="Admin User",
        is_verified=True
    )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current authenticated user ID from JWT token"""
    user = await get_current_user(credentials)
    return str(user.id)


async def get_current_user_ws_optional(websocket=None, token: Optional[str] = None) -> Optional[str]:
    """
    WebSocket auth function - returns user ID if authenticated, None otherwise
    This is for endpoints that work with or without authentication
    """
    if not token:
        return None
    
    try:
        user = await get_current_user_ws(websocket, token)
        return str(user.id) if user else None
    except:
        return None
