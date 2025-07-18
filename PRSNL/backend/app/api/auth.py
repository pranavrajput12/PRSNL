"""
Authentication API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from app.core.auth import User, get_current_user, get_current_user_optional
from app.core.exceptions import AuthenticationError, InvalidInput
from app.db.database import get_db_pool
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    is_verified: bool = False


class PRSNLLoginRequest(BaseModel):
    email: EmailStr
    password: str


class PRSNLRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    invite_code: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(request: PRSNLLoginRequest):
    """Login endpoint for email/password authentication"""
    # DEVELOPMENT BYPASS: Accept any email/password for now
    # This matches the security bypass pattern documented in SECURITY_BYPASSES.md
    logger.warning("SECURITY BYPASS: Accepting any login credentials for development")
    
    # Generate development tokens using the existing auth service
    user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"  # Test user ID
    access_token = auth_service.create_access_token({"sub": user_id})
    refresh_token = auth_service.create_refresh_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": request.email,
            "name": "Test User",
            "is_verified": True
        }
    }


@router.post("/register", response_model=UserResponse)
async def register(request: PRSNLRegisterRequest):
    """Register a new user with PRSNL - DEVELOPMENT BYPASS"""
    # For development, just return a test user
    logger.warning("SECURITY BYPASS: Registration always succeeds with test user")
    return UserResponse(
        id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
        email=request.email,
        name=request.name or "Test User",
        created_at=datetime.utcnow(),
        is_verified=True
    )


@router.post("/login/prsnl")
async def login_prsnl(request: PRSNLLoginRequest):
    """Login with PRSNL credentials"""
    # DEVELOPMENT BYPASS: Accept any email/password for now
    # This matches the security bypass pattern documented in SECURITY_BYPASSES.md
    logger.warning("SECURITY BYPASS: Accepting any login credentials for development")
    
    # Generate development tokens using the existing auth service
    user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"  # Test user ID
    access_token = auth_service.create_access_token({"sub": user_id})
    refresh_token = auth_service.create_refresh_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": request.email,
            "name": "Test User",
            "is_verified": True
        }
    }


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """Logout the current user"""
    # In a real implementation, you might want to:
    # 1. Invalidate the refresh token in the database
    # 2. Add the access token to a blacklist
    # For now, we just return success
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request):
    """Get current authenticated user info"""
    # DEVELOPMENT BYPASS: Return test user for any request
    # This aligns with the security bypasses documented
    logger.warning("SECURITY BYPASS: Returning test user for /api/auth/me")
    
    # Check if there's a token in the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Token is present, return test user
        return UserResponse(
            id="e03c9686-09b0-4a06-b236-d0839ac7f5df",
            email="test@example.com",
            name="Test User",
            created_at=datetime.utcnow(),
            is_verified=True
        )
    else:
        # No token, return 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        # For development, always return new tokens
        user_id = "e03c9686-09b0-4a06-b236-d0839ac7f5df"
        access_token = auth_service.create_access_token({"sub": user_id})
        refresh_token = auth_service.create_refresh_token({"sub": user_id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(token: str, user: User = Depends(get_current_user)):
    """Verify user's email address - DEVELOPMENT BYPASS"""
    logger.warning("SECURITY BYPASS: Email verification always succeeds")
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(user: User = Depends(get_current_user)):
    """Resend email verification link - DEVELOPMENT BYPASS"""
    logger.warning("SECURITY BYPASS: Verification email not actually sent")
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Request password reset email - DEVELOPMENT BYPASS"""
    logger.warning("SECURITY BYPASS: Password reset email not actually sent")
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password using token - DEVELOPMENT BYPASS"""
    logger.warning("SECURITY BYPASS: Password reset always succeeds")
    return {"message": "Password reset successfully"}