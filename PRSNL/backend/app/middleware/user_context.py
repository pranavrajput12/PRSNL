"""
User context middleware for extracting user_id from JWT tokens
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional, Dict, Any
import jwt
from uuid import UUID

from app.config import settings
from app.db.database import get_db_pool


class UserContextMiddleware:
    """Extract user_id from JWT tokens and make it available to endpoints"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def get_current_user_id(self, request: Request) -> Optional[UUID]:
        """Extract user_id from JWT token in request headers"""
        
        # Get authorization header
        authorization = request.headers.get("authorization")
        if not authorization:
            return None
        
        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return None
        except ValueError:
            return None
        
        # Decode JWT token
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Validate user_id is a valid UUID
            return UUID(user_id)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            return None
        except ValueError:
            return None
    
    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get full user info from database using user_id"""
        
        user_id = await self.get_current_user_id(request)
        if not user_id:
            return None
        
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                user_row = await conn.fetchrow(
                    "SELECT id, email, name, is_active, is_verified FROM users WHERE id = $1",
                    user_id
                )
                
                if not user_row:
                    return None
                
                return {
                    "id": user_row["id"],
                    "email": user_row["email"],
                    "name": user_row["name"],
                    "is_active": user_row["is_active"],
                    "is_verified": user_row["is_verified"]
                }
        except Exception:
            return None


# Global instance
user_context = UserContextMiddleware()


async def get_current_user_id(request: Request) -> Optional[UUID]:
    """Dependency function to get current user_id"""
    return await user_context.get_current_user_id(request)


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency function to get current user"""
    return await user_context.get_current_user(request)


async def require_user_id(request: Request) -> UUID:
    """Dependency function that requires authentication"""
    user_id = await get_current_user_id(request)
    if not user_id:
        # DEV MODE: Return a default user ID for development
        import logging
        logging.warning("🚨 DEV MODE: Using default user ID for unauthenticated request")
        return UUID("00000000-0000-0000-0000-000000000001")
    return user_id


async def require_user(request: Request) -> Dict[str, Any]:
    """Dependency function that requires authentication and returns user info"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user