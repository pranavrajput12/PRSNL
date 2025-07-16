"""
Authentication service for PRSNL
Handles JWT tokens, user authentication, and session management
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db_pool
from app.services.email_service import EmailService
from app.models.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    RefreshTokenRequest, PasswordResetRequest, EmailVerificationRequest
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1


class AuthService:
    """Main authentication service"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @classmethod
    async def register_user(cls, user_data: UserRegister) -> UserResponse:
        """Register a new user"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check if user exists
            existing = await db.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user_data.email
            )
            
            if existing:
                raise ValueError("User with this email already exists")
            
            # Create user
            hashed_password = cls.get_password_hash(user_data.password)
            
            user_record = await db.fetchrow("""
                INSERT INTO users (email, password_hash, first_name, last_name, user_type)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, email, first_name, last_name, is_active, is_verified, 
                          user_type, onboarding_completed, created_at, updated_at, last_login_at
            """, user_data.email, hashed_password, user_data.first_name, 
                user_data.last_name, user_data.user_type)
            
            # Create user profile
            await db.execute("""
                INSERT INTO user_profiles (user_id, segment)
                VALUES ($1, $2)
            """, user_record["id"], "developer")
            
            # Send verification email
            name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or user_data.email
            await EmailService.send_verification_email(
                user_id=user_record["id"],
                email=user_data.email,
                name=name
            )
            
            return UserResponse(**dict(user_record))
    
    @classmethod
    async def authenticate_user(cls, login_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate a user with email and password"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            user = await db.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                login_data.email
            )
            
            if not user:
                return None
            
            if not cls.verify_password(login_data.password, user["password_hash"]):
                return None
            
            if not user["is_active"]:
                raise ValueError("User account is inactive")
            
            # Update last login
            await db.execute(
                "UPDATE users SET last_login_at = NOW() WHERE id = $1",
                user["id"]
            )
            
            # Return user data without password_hash
            user_dict = dict(user)
            user_dict.pop("password_hash", None)
            return user_dict
    
    @classmethod
    async def authenticate_magic_link(cls, token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate user with magic link token"""
        user_data = await EmailService.verify_magic_link(token, ip_address, user_agent)
        
        if not user_data:
            return None
            
        # Return user data without password_hash (similar to authenticate_user)
        return user_data
    
    @classmethod
    async def create_tokens(cls, user_id: str) -> Tuple[str, str]:
        """Create access and refresh tokens for a user"""
        # Ensure user_id is string for JWT
        user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
        
        access_token = cls.create_access_token(data={"sub": user_id_str})
        refresh_token = cls.create_refresh_token(data={"sub": user_id_str})
        
        # Store session
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Convert to UUID for database
            try:
                user_uuid = UUID(user_id_str)
            except ValueError:
                raise ValueError(f"Invalid user ID format: {user_id_str}")
                
            await db.execute("""
                INSERT INTO user_sessions 
                (user_id, session_token, refresh_token, expires_at, refresh_expires_at)
                VALUES ($1, $2, $3, $4, $5)
            """, user_uuid, access_token, refresh_token,
                datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        
        return access_token, refresh_token
    
    @classmethod
    async def refresh_access_token(cls, refresh_data: RefreshTokenRequest) -> TokenResponse:
        """Refresh an access token using a refresh token"""
        payload = cls.decode_token(refresh_data.refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        
        # Verify session
        pool = await get_db_pool()
        async with pool.acquire() as db:
            session = await db.fetchrow("""
                SELECT * FROM user_sessions 
                WHERE refresh_token = $1 
                AND refresh_expires_at > NOW()
                AND revoked_at IS NULL
            """, refresh_data.refresh_token)
            
            if not session:
                raise ValueError("Invalid or expired refresh token")
            
            # Get user
            try:
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid user ID format: {user_id}")
                
            user = await db.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_uuid
            )
            
            if not user:
                raise ValueError("User not found")
            
            # Create new tokens
            access_token, new_refresh_token = await cls.create_tokens(user_id)
            
            # Revoke old session
            await db.execute(
                "UPDATE user_sessions SET revoked_at = NOW() WHERE id = $1",
                session["id"]
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                user=UserResponse(**dict(user))
            )
    
    @classmethod
    async def get_current_user(cls, token: str) -> Optional[UserResponse]:
        """Get current user from JWT token"""
        payload = cls.decode_token(token)
        
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Get user directly from JWT claims - session validation is expensive
            # and causes issues during navigation. JWT expiry handles timeout.
            try:
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            except (ValueError, TypeError):
                return None
                
            user = await db.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_uuid
            )
            
            if not user:
                return None
            
            return UserResponse(**dict(user))
    
    @classmethod
    async def logout(cls, token: str) -> bool:
        """Logout a user by revoking their session"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            result = await db.execute(
                "UPDATE user_sessions SET revoked_at = NOW() WHERE session_token = $1 AND revoked_at IS NULL",
                token
            )
            return result != "UPDATE 0"
    
    @classmethod
    async def create_email_verification_token(cls, user_id: str) -> str:
        """Create an email verification token"""
        token = secrets.token_urlsafe(32)
        
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                INSERT INTO email_verifications (user_id, token, expires_at)
                VALUES ($1, $2, $3)
            """, UUID(user_id), token,
                datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS))
        
        return token
    
    @classmethod
    async def verify_email(cls, verification_data: EmailVerificationRequest) -> bool:
        """Verify a user's email address"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check token in users table (where it's actually stored)
            user = await db.fetchrow("""
                SELECT id, email_verification_token, email_verification_token_expires, is_verified
                FROM users 
                WHERE email_verification_token = $1 
                AND email_verification_token_expires > NOW()
                AND is_verified = FALSE
            """, verification_data.token)
            
            if not user:
                # Also check email_verifications table for backward compatibility
                verification = await db.fetchrow("""
                    SELECT * FROM email_verifications 
                    WHERE token = $1 
                    AND expires_at > NOW()
                    AND verified_at IS NULL
                """, verification_data.token)
                
                if not verification:
                    raise ValueError("Invalid or expired verification token")
                
                # Mark as verified in email_verifications
                await db.execute(
                    "UPDATE email_verifications SET verified_at = NOW() WHERE id = $1",
                    verification["id"]
                )
                
                # Update user
                await db.execute(
                    "UPDATE users SET is_verified = TRUE, email_verified_at = NOW() WHERE id = $1",
                    verification["user_id"]
                )
            else:
                # Update user - clear token and mark as verified
                await db.execute("""
                    UPDATE users 
                    SET is_verified = TRUE, 
                        email_verified_at = NOW(),
                        email_verification_token = NULL,
                        email_verification_token_expires = NULL
                    WHERE id = $1
                """, user["id"])
            
            return True
    
    @classmethod
    async def create_password_reset_token(cls, reset_data: PasswordResetRequest) -> str:
        """Create a password reset token"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check if user exists
            user = await db.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                reset_data.email
            )
            
            if not user:
                # Don't reveal if user exists
                return None
            
            token = secrets.token_urlsafe(32)
            
            await db.execute("""
                INSERT INTO password_resets (user_id, token, expires_at)
                VALUES ($1, $2, $3)
            """, user["id"], token,
                datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS))
            
            # TODO: Send reset email
            return token
    
    @classmethod
    async def reset_password(cls, token: str, new_password: str) -> bool:
        """Reset a user's password"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check token
            reset = await db.fetchrow("""
                SELECT * FROM password_resets 
                WHERE token = $1 
                AND expires_at > NOW()
                AND used_at IS NULL
            """, token)
            
            if not reset:
                raise ValueError("Invalid or expired reset token")
            
            # Update password
            hashed_password = cls.get_password_hash(new_password)
            
            await db.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                hashed_password, reset["user_id"]
            )
            
            # Mark token as used
            await db.execute(
                "UPDATE password_resets SET used_at = NOW() WHERE id = $1",
                reset["id"]
            )
            
            # Revoke all sessions
            await db.execute(
                "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = $1",
                reset["user_id"]
            )
            
            return True