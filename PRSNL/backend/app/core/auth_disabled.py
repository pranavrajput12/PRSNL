"""
TEMPORARY: Authentication disabled for development
This file disables all authentication for development purposes
RE-ENABLE BEFORE PRODUCTION DEPLOYMENT!
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User

# Development user - same as frontend expects
DEV_USER = User(
    id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
    email="test@example.com",
    name="Test User"
)

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Always returns the development user - NO AUTHENTICATION"""
    return DEV_USER

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Always returns the development user - NO AUTHENTICATION"""
    return DEV_USER

# Export the same function names as the original auth module
__all__ = ['get_current_user', 'get_optional_user', 'security']