"""Configuration settings for PRSNL"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database - Railway provides DATABASE_URL automatically
    _database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prsnl")
    # Fix Railway's postgres:// to postgresql:// for asyncpg
    DATABASE_URL: str = _database_url.replace("postgres://", "postgresql://", 1) if _database_url.startswith("postgres://") else _database_url
    
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PRSNL"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"]
    
    # LLM
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4.1"  # Main GPT deployment with vision capability
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
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    CACHE_TTL_SEARCH: int = 300  # 5 minutes for search results
    CACHE_TTL_ITEM: int = 1800  # 30 minutes for items
    
    # Additional settings from .env
    ENVIRONMENT: str = "development"
    PRSNL_API_KEY: Optional[str] = None
    
    # Firecrawl Web Scraping
    FIRECRAWL_API_KEY: Optional[str] = None
    FIRECRAWL_BASE_URL: str = "https://api.firecrawl.dev"
    
    # OpenCLIP Vision
    OPENCLIP_MODEL: str = "ViT-B-32"
    OPENCLIP_PRETRAINED: str = "openai"
    RATE_LIMITING_ENABLED: bool = True
    
    # Service Port Configuration (Exclusive Port Ownership)
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3003"))
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()