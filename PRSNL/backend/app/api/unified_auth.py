"""
Unified Authentication API endpoints for Keycloak + FusionAuth integration
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import httpx
import jwt
from datetime import datetime, timedelta
import secrets

from app.middleware.unified_auth import UnifiedAuthService
from app.core.config import settings
from app.services.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["unified-auth"])

# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    name: Optional[str] = None
    roles: list = []
    source: str
    isEmailVerified: bool = False

# Initialize unified auth service
unified_auth_service = UnifiedAuthService()

@router.post("/signup", response_model=TokenResponse)
async def signup_with_prsnl(request: SignupRequest):
    """
    Sign up a new user with PRSNL backend (will be synced to auth providers)
    """
    try:
        # Create user in PRSNL database
        async with get_db_connection() as conn:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", 
                request.email
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create new user
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, first_name, last_name, user_type, is_verified)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                request.email,
                # In production, hash the password properly
                f"hashed_{request.password}",  # Placeholder - implement proper hashing
                request.firstName,
                request.lastName,
                "individual",
                False
            )
            
            # Create auth tokens
            access_token = create_access_token({"sub": str(user_id), "email": request.email})
            refresh_token = create_refresh_token({"sub": str(user_id)})
            
            # Create user response
            user_data = {
                "id": str(user_id),
                "email": request.email,
                "firstName": request.firstName,
                "lastName": request.lastName,
                "name": f"{request.firstName} {request.lastName}".strip(),
                "roles": ["user"],
                "source": "prsnl",
                "isEmailVerified": False
            }
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_data
            )
            
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

@router.post("/login", response_model=TokenResponse)
async def login_with_prsnl(request: LoginRequest):
    """
    Login with PRSNL credentials
    """
    try:
        async with get_db_connection() as conn:
            # Find user by email
            user = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, password_hash, user_type, is_verified
                FROM users 
                WHERE email = $1
                """, 
                request.email
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # In production, verify password hash properly
            if user['password_hash'] != f"hashed_{request.password}":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Create auth tokens
            access_token = create_access_token({"sub": str(user['id']), "email": user['email']})
            refresh_token = create_refresh_token({"sub": str(user['id'])})
            
            # Create user response
            user_data = {
                "id": str(user['id']),
                "email": user['email'],
                "firstName": user['first_name'],
                "lastName": user['last_name'],
                "name": f"{user['first_name'] or ''} {user['last_name'] or ''}".strip(),
                "roles": ["user"],
                "source": "prsnl",
                "isEmailVerified": user['is_verified']
            }
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_data
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/verify")
async def verify_token(request: Request):
    """
    Verify authentication token and return user data
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Decode and verify token
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
                
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user data from database
        async with get_db_connection() as conn:
            user = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, user_type, is_verified
                FROM users 
                WHERE id = $1
                """, 
                user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return {
                "id": str(user['id']),
                "email": user['email'],
                "firstName": user['first_name'],
                "lastName": user['last_name'],
                "name": f"{user['first_name'] or ''} {user['last_name'] or ''}".strip(),
                "roles": ["user"],
                "source": "prsnl",
                "isEmailVerified": user['is_verified']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

@router.post("/logout")
async def logout(request: Request):
    """
    Logout (token blacklisting would go here in production)
    """
    # In production, you'd blacklist the token or invalidate it
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token
    """
    try:
        data = await request.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )
        
        # Verify refresh token
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user and create new tokens
        async with get_db_connection() as conn:
            user = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name
                FROM users 
                WHERE id = $1
                """, 
                user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Create new tokens
            access_token = create_access_token({"sub": str(user['id']), "email": user['email']})
            new_refresh_token = create_refresh_token({"sub": str(user['id'])})
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/fusionauth/callback")
async def fusionauth_callback(request: Request):
    """
    Handle FusionAuth OAuth callback
    """
    try:
        data = await request.json()
        code = data.get("code")
        redirect_uri = data.get("redirectUri")
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code required"
            )
        
        # Exchange code for token with FusionAuth
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{settings.FUSIONAUTH_URL}/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.FUSIONAUTH_CLIENT_ID,
                    "client_secret": settings.FUSIONAUTH_CLIENT_SECRET
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if not token_response.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            token_data = token_response.json()
            
            # Get user info from FusionAuth
            user_response = await client.get(
                f"{settings.FUSIONAUTH_URL}/oauth2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            
            if not user_response.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
            
            user_data = user_response.json()
            
            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "user": {
                    "id": user_data.get("sub"),
                    "email": user_data.get("email"),
                    "firstName": user_data.get("given_name"),
                    "lastName": user_data.get("family_name"),
                    "name": user_data.get("name"),
                    "roles": user_data.get("roles", []),
                    "source": "fusionauth",
                    "isEmailVerified": user_data.get("email_verified", False)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FusionAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FusionAuth callback failed"
        )

# Helper functions
def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)  # 15 minute expiry
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 day expiry
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")