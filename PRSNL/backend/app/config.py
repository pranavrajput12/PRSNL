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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    
    # Processing
    MAX_CONTENT_LENGTH: int = 50000  # Max chars to process
    PROCESSING_TIMEOUT: int = 30  # seconds
    
    # Search
    SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_MIN_SCORE: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()