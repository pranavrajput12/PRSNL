"""Configuration settings for PRSNL"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - Railway provides DATABASE_URL automatically
    _database_url = os.getenv("DATABASE_URL", "postgresql://pronav@localhost:5432/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    DATABASE_URL: str = _database_url.replace("postgres://", "postgresql://", 1) if _database_url.startswith("postgres://") else _database_url
    
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PRSNL"
    
    # 🔍 DEBUG LOGGING - DEVELOPMENT MODE
    LOG_LEVEL: str = "DEBUG"
    ENABLE_QUERY_LOGGING: bool = True
    ENABLE_VERBOSE_LOGGING: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000", 
        "http://localhost:3002", 
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:5173",
        "https://prsnl.fyi",
        "https://www.prsnl.fyi",
        "https://api.prsnl.fyi"
    ]
    
    # Authentication Services Configuration
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "prsnl")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "prsnl-frontend")
    
    FUSIONAUTH_URL: str = os.getenv("FUSIONAUTH_URL", "http://localhost:9011")
    FUSIONAUTH_API_KEY: str = os.getenv("FUSIONAUTH_API_KEY", "")
    FUSIONAUTH_APPLICATION_ID: str = os.getenv("FUSIONAUTH_APPLICATION_ID", "")
    FUSIONAUTH_CLIENT_ID: str = os.getenv("FUSIONAUTH_CLIENT_ID", "prsnl-frontend")
    FUSIONAUTH_CLIENT_SECRET: str = os.getenv("FUSIONAUTH_CLIENT_SECRET", "")
    
    # Auth Integration Settings
    AUTH_COOKIE_DOMAIN: str = os.getenv("AUTH_COOKIE_DOMAIN", "localhost")
    AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
    AUTH_SESSION_TIMEOUT: int = int(os.getenv("AUTH_SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # LLM
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4.1"  # Main GPT deployment with vision capability
    AZURE_OPENAI_LIBRECHAT_DEPLOYMENT: str = "gpt-4.1"  # Fast model for LibreChat
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"  # Model version 2
    AZURE_OPENAI_WHISPER_DEPLOYMENT: str = "whisper"  # Model version 001
    AZURE_OPENAI_API_VERSION: str = "2025-01-01-preview"

    
    # Storage
    MEDIA_DIR: str = "./media"  # Media directory path
    
    # Processing
    MAX_CONTENT_LENGTH: int = 50000  # Max chars to process
    PROCESSING_TIMEOUT: int = 30  # seconds
    MAX_VIDEO_SIZE_MB: int = 500 # Max video size for processing
    
    # Search
    SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_MIN_SCORE: float = 0.1
    
    # Cache (Redis optional)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    CACHE_ENABLED: bool = bool(os.getenv("REDIS_URL", False))
    
    # Celery configuration for distributed task processing
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    CACHE_TTL_SEARCH: int = 300  # 5 minutes for search results
    CACHE_TTL_ITEM: int = 1800  # 30 minutes for items
    
    # Additional settings from .env
    ENVIRONMENT: str = "development"
    PRSNL_API_KEY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    
    # Security
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "default-encryption-key-change-in-production")
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID", None)
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET", None)
    GITHUB_OAUTH_REDIRECT_URI: Optional[str] = os.getenv("GITHUB_OAUTH_REDIRECT_URI", None)
    
    # Firecrawl Web Scraping
    FIRECRAWL_API_KEY: Optional[str] = None
    FIRECRAWL_BASE_URL: str = "https://api.firecrawl.dev"
    
    # OpenCLIP Vision
    OPENCLIP_MODEL: str = "ViT-B-32"
    OPENCLIP_PRETRAINED: str = "openai"
    
    # Voice Settings
    VOICE_TTS_ENGINE: str = os.getenv("VOICE_TTS_ENGINE", "chatterbox")  # chatterbox, edge-tts
    VOICE_STT_MODEL: str = os.getenv("VOICE_STT_MODEL", "small")  # tiny, base, small, medium, large
    VOICE_USE_CREWAI: bool = os.getenv("VOICE_USE_CREWAI", "true").lower() == "true"
    VOICE_ENABLE_STREAMING: bool = os.getenv("VOICE_ENABLE_STREAMING", "false").lower() == "true"
    VOICE_DEFAULT_GENDER: str = os.getenv("VOICE_DEFAULT_GENDER", "female")  # male, female
    VOICE_EMOTION_STRENGTH: float = float(os.getenv("VOICE_EMOTION_STRENGTH", "1.0"))
    RATE_LIMITING_ENABLED: bool = True
    
    # Service Port Configuration (Exclusive Port Ownership)
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3003"))
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Frontend URL for OAuth callbacks
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3003")
    
    # Sentry Error Tracking & Performance Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))  # 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))  # 10% of transactions
    SENTRY_ENABLE_IN_DEV: bool = os.getenv("SENTRY_ENABLE_IN_DEV", "false").lower() == "true"
    
    # Version tracking
    VERSION: str = os.getenv("VERSION", "2.3.0")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-to-a-secure-random-value")
    
    # Email Configuration (Resend)
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM_ADDRESS: str = os.getenv("EMAIL_FROM_ADDRESS", "noreply@prsnl.ai")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "PRSNL")
    
    # Voice Chat Configuration
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "small")  # tiny, base, small, medium, large
    VOICE_DEFAULT_GENDER: str = os.getenv("VOICE_DEFAULT_GENDER", "female")
    VOICE_MAX_RECORDING_DURATION: int = int(os.getenv("VOICE_MAX_RECORDING_DURATION", "60"))  # seconds
    VOICE_ENABLE_ANALYTICS: bool = os.getenv("VOICE_ENABLE_ANALYTICS", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()