"""Configuration settings for PRSNL"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/prsnl"
    
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PRSNL"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3002", "http://localhost:5173"]
    
    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"
    AZURE_OPENAI_API_VERSION: str = "2025-01-01-preview"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    
    # Processing
    MAX_CONTENT_LENGTH: int = 50000  # Max chars to process
    PROCESSING_TIMEOUT: int = 30  # seconds
    MAX_VIDEO_SIZE_MB: int = 500 # Max video size for processing
    
    # Search
    SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_MIN_SCORE: float = 0.1
    
    # Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    CACHE_TTL_SEARCH: int = 300  # 5 minutes for search results
    CACHE_TTL_ITEM: int = 1800  # 30 minutes for items
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()