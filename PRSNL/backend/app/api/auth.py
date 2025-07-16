"""
Authentication API endpoints for PRSNL
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    RefreshTokenRequest, PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest, AuthError, UserProfileResponse,
    UserProfileUpdate, UserPreferencesUpdate, HealthCheck,
    MagicLinkRequest, MagicLinkVerifyRequest
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.db.database import get_db_pool

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current authenticated user"""
    token = credentials.credentials
    user = await AuthService.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.get("/health", response_model=HealthCheck)
async def auth_health_check():
    """Check authentication service health"""
    return HealthCheck(
        status="healthy",
        auth_enabled=True,
        oauth_providers=["github", "google"],
        features={
            "registration": True,
            "email_verification": True,
            "password_reset": True,
            "oauth": True,
            "two_factor": False
        }
    )


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        user = await AuthService.register_user(user_data)
        access_token, refresh_token = await AuthService.create_tokens(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login with email and password"""
    try:
        user_dict = await AuthService.authenticate_user(login_data)
        
        if not user_dict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = UserResponse(**user_dict)
        access_token, refresh_token = await AuthService.create_tokens(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Refresh token request received: {refresh_data.refresh_token[:20]}...")
        
        token_response = await AuthService.refresh_access_token(refresh_data)
        return token_response
    except ValueError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Refresh token ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Refresh token Exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout current user"""
    try:
        token = credentials.credentials
        success = await AuthService.logout(token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's profile"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        query = """
            SELECT * FROM user_profiles WHERE user_id = $1
        """
        profile = await db.fetchrow(query, str(current_user.id))
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Convert JSON fields to lists
        profile_dict = dict(profile)
        profile_dict["skills"] = profile_dict.get("skills", [])
        profile_dict["interests"] = profile_dict.get("interests", [])
        
        return UserProfileResponse(**profile_dict)


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update current user's profile"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        # Build update query dynamically
        update_fields = []
        values = {"user_id": str(current_user.id)}
        
        for field, value in profile_update.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                values[field] = value
        
        if update_fields:
            update_query = f"""
                UPDATE user_profiles 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE user_id = :user_id
                RETURNING *
            """
            
            profile = await db.fetch_one(update_query, values=values)
            
            if not profile:
                # Create profile if it doesn't exist
                insert_query = """
                    INSERT INTO user_profiles (user_id, segment)
                    VALUES (:user_id, 'developer')
                    RETURNING *
                """
                profile = await db.fetch_one(insert_query, values={"user_id": str(current_user.id)})
            
            # Convert JSON fields to lists
            profile_dict = dict(profile)
            profile_dict["skills"] = profile_dict.get("skills", [])
            profile_dict["interests"] = profile_dict.get("interests", [])
            
            return UserProfileResponse(**profile_dict)
        
        return await get_my_profile(current_user)


@router.put("/me/preferences")
async def update_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user preferences"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        update_query = """
            UPDATE users 
            SET preferences = $1, updated_at = NOW()
            WHERE id = $2
        """
        
        await db.execute(
            update_query,
            preferences_update.preferences,
            str(current_user.id)
        )
        
        return {"message": "Preferences updated successfully"}


@router.post("/verify-email")
async def verify_email(verification_data: EmailVerificationRequest):
    """Verify email address"""
    try:
        success = await AuthService.verify_email(verification_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed"
            )
        
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/request-password-reset")
async def request_password_reset(reset_data: PasswordResetRequest):
    """Request a password reset"""
    try:
        token = await AuthService.create_password_reset_token(reset_data)
        
        # In production, send email with reset link
        # For now, return token (remove in production)
        return {
            "message": "Password reset email sent if account exists",
            "token": token  # REMOVE IN PRODUCTION
        }
    except Exception as e:
        # Don't reveal if user exists
        return {"message": "Password reset email sent if account exists"}


@router.post("/reset-password")
async def reset_password(reset_confirm: PasswordResetConfirm):
    """Reset password with token"""
    try:
        success = await AuthService.reset_password(
            reset_confirm.token,
            reset_confirm.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
        
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/sessions")
async def get_my_sessions(current_user: UserResponse = Depends(get_current_user)):
    """Get all active sessions for current user"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        query = """
            SELECT id, ip_address, user_agent, device_info, created_at, 
                   last_activity, expires_at
            FROM user_sessions 
            WHERE user_id = :user_id 
            AND revoked_at IS NULL
            AND expires_at > NOW()
            ORDER BY last_activity DESC
        """
        
        sessions = await db.fetch(query, str(current_user.id))
        
        return [dict(session) for session in sessions]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Revoke a specific session"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        update_query = """
            UPDATE user_sessions 
            SET revoked_at = NOW()
            WHERE id = $1 
            AND user_id = $2
        """
        
        result = await db.execute(
            update_query,
            values={
                "session_id": session_id,
                "user_id": str(current_user.id)
            }
        )
        
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}


@router.post("/revoke-all-sessions")
async def revoke_all_sessions(
    current_user: UserResponse = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Revoke all sessions except current"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        current_token = credentials.credentials
        
        update_query = """
            UPDATE user_sessions 
            SET revoked_at = NOW()
            WHERE user_id = $1 
            AND session_token != $2
        """
        
        result = await db.execute(
            update_query,
            values={
                "user_id": str(current_user.id),
                "current_token": current_token
            }
        )
        
        return {"message": f"Revoked {result} sessions"}


@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest):
    """Verify email address with token"""
    try:
        user_id = await EmailService.verify_email_token(request.token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        return {"message": "Email verified successfully", "user_id": str(user_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: UserResponse = Depends(get_current_user)
):
    """Resend email verification for current user"""
    try:
        if current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email
        success = await EmailService.send_verification_email(
            user_id=current_user.id,
            email=current_user.email,
            name=name
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        return {"message": "Verification email sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@router.post("/magic-link")
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link for passwordless login"""
    try:
        result = await EmailService.send_magic_link(request.email)
        return result
    except Exception as e:
        return {"success": True, "message": "If an account exists, a magic link has been sent"}


@router.post("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(request: MagicLinkVerifyRequest, req: Request):
    """Verify magic link and login user"""
    try:
        # Get client info
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        user_data = await AuthService.authenticate_magic_link(
            request.token, 
            ip_address, 
            user_agent
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired magic link"
            )
        
        user = UserResponse(**user_data)
        access_token, refresh_token = await AuthService.create_tokens(str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Magic link verification failed"
        )