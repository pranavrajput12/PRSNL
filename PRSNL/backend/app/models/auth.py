"""
Authentication Pydantic models for PRSNL
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Request Models
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    user_type: str = Field(default="individual", pattern="^(individual|team|enterprise)$")
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets security requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Ensure password meets security requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str


class MagicLinkRequest(BaseModel):
    """Magic link request"""
    email: EmailStr


class MagicLinkVerifyRequest(BaseModel):
    """Magic link verification request"""
    token: str


# Response Models
class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_verified: bool
    user_type: str
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: UUID
    user_id: UUID
    segment: Optional[str]
    skills: List[str] = []
    interests: List[str] = []
    github_username: Optional[str]
    linkedin_url: Optional[str]
    twitter_handle: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    timezone: str = "UTC"
    language: str = "en"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds
    user: UserResponse


class SessionInfo(BaseModel):
    """Session information"""
    id: UUID
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Dict[str, Any] = {}
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


# OAuth Models
class OAuthProvider(BaseModel):
    """OAuth provider information"""
    name: str  # github, google, etc.
    client_id: str
    authorization_url: str
    token_url: str
    user_info_url: str


class OAuthCallback(BaseModel):
    """OAuth callback data"""
    code: str
    state: str
    provider: str


class OAuthConnection(BaseModel):
    """OAuth connection information"""
    id: UUID
    user_id: UUID
    provider: str
    provider_user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Profile Update Models
class UserProfileUpdate(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    segment: Optional[str] = Field(None, pattern="^(developer|researcher|creator|knowledge_worker)$")
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    github_username: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    twitter_handle: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)


class UserPreferencesUpdate(BaseModel):
    """User preferences update"""
    preferences: Dict[str, Any] = {}


# Onboarding Models
class OnboardingStep(BaseModel):
    """Onboarding step completion"""
    step: str
    completed: bool
    data: Optional[Dict[str, Any]] = None


class OnboardingProgress(BaseModel):
    """Onboarding progress tracking"""
    user_id: UUID
    steps_completed: List[str]
    current_step: str
    total_steps: int
    completion_percentage: float
    data: Dict[str, Any] = {}


# Error Models
class AuthError(BaseModel):
    """Authentication error response"""
    error: str
    error_description: str
    status_code: int = 401


class ValidationError(BaseModel):
    """Validation error response"""
    field: str
    message: str
    
    
# Utility Models
class HealthCheck(BaseModel):
    """Auth service health check"""
    status: str = "healthy"
    auth_enabled: bool
    oauth_providers: List[str] = []
    features: Dict[str, bool] = {
        "registration": True,
        "email_verification": True,
        "password_reset": True,
        "oauth": True,
        "two_factor": False  # Future feature
    }