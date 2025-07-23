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
from app.services.auth_service import auth_service, AuthService
from app.services.email_service import EmailService
from app.models.auth import (
    UserRegister, UserLogin, UserResponse, 
    RefreshTokenRequest, PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest
)
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
    # Authenticate user
    user_data = await auth_service.authenticate_user(UserLogin(
        email=request.email,
        password=request.password
    ))
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token, refresh_token = await auth_service.create_tokens(str(user_data["id"]))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user_data["id"]),
            "email": user_data["email"],
            "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data["email"],
            "is_verified": user_data["is_verified"]
        }
    }


@router.post("/register", response_model=UserResponse)
async def register(request: PRSNLRegisterRequest):
    """Register a new user with PRSNL"""
    try:
        # Parse name into first and last
        name_parts = (request.name or "").split(" ", 1) if request.name else ["", ""]
        first_name = name_parts[0] or ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Register user
        user = await auth_service.register_user(UserRegister(
            email=request.email,
            password=request.password,
            first_name=first_name,
            last_name=last_name,
            user_type="standard"
        ))
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login/prsnl")
async def login_prsnl(request: PRSNLLoginRequest):
    """Login with PRSNL credentials"""
    # Use the same logic as the main login endpoint
    return await login(request)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """Logout the current user"""
    # In a real implementation, you might want to:
    # 1. Invalidate the refresh token in the database
    # 2. Add the access token to a blacklist
    # For now, we just return success
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    # Get full user data from database
    pool = await get_db_pool()
    async with pool.acquire() as db:
        user_data = await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user.id if isinstance(user.id, UUID) else UUID(user.id)
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=str(user_data["id"]),
            email=user_data["email"],
            name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data["email"],
            created_at=user_data["created_at"],
            is_verified=user_data["is_verified"]
        )


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        # Use the auth service to refresh token
        token_response = await auth_service.refresh_access_token(request)
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest):
    """Verify user's email address"""
    try:
        await auth_service.verify_email(request)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/resend-verification")
async def resend_verification(user: User = Depends(get_current_user)):
    """Resend email verification link"""
    await EmailService.send_verification_email(
        user_id=UUID(user.id),
        email=user.email,
        name=user.name
    )
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Request password reset email"""
    # Always return success to prevent email enumeration
    pool = await get_db_pool()
    async with pool.acquire() as db:
        user = await db.fetchrow(
            "SELECT id, first_name, last_name FROM users WHERE email = $1",
            email
        )
        
        if user:
            # Create password reset token
            token = await auth_service.create_password_reset_token(email)
            
            if token:
                # Send password reset email
                await EmailService.send_password_reset_email(
                    user_id=user["id"],
                    email=email,
                    name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or email
                )
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Reset password using token"""
    try:
        await auth_service.reset_password(request.token, request.new_password)
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )