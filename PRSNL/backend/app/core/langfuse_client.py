"""Langfuse client initialization and configuration"""
import logging
from typing import Optional

from langfuse import Langfuse

from app.config import settings

logger = logging.getLogger(__name__)


class LangfuseClient:
    """Singleton Langfuse client for the application"""
    
    _instance: Optional[Langfuse] = None
    _initialized: bool = False
    
    @classmethod
    def get_client(cls) -> Optional[Langfuse]:
        """Get or create the Langfuse client instance"""
        if not settings.LANGFUSE_ENABLED:
            return None
            
        if cls._instance is None and not cls._initialized:
            try:
                # Only initialize if we have valid keys
                if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
                    cls._instance = Langfuse(
                        public_key=settings.LANGFUSE_PUBLIC_KEY,
                        secret_key=settings.LANGFUSE_SECRET_KEY,
                        host=settings.LANGFUSE_HOST
                    )
                    cls._initialized = True
                    logger.info("✅ Langfuse client initialized successfully")
                else:
                    logger.warning("⚠️ Langfuse keys not configured - running without observability")
                    cls._initialized = True
            except Exception as e:
                logger.error(f"❌ Failed to initialize Langfuse client: {e}")
                cls._initialized = True
                
        return cls._instance
    
    @classmethod
    def flush(cls):
        """Flush any pending Langfuse events"""
        if cls._instance:
            try:
                cls._instance.flush()
            except Exception as e:
                logger.error(f"Error flushing Langfuse: {e}")
    
    @classmethod
    def shutdown(cls):
        """Shutdown the Langfuse client gracefully"""
        if cls._instance:
            try:
                cls._instance.flush()
                cls._instance.shutdown()
                logger.info("Langfuse client shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down Langfuse: {e}")
            finally:
                cls._instance = None
                cls._initialized = False


# Initialize on import for decorator usage
langfuse_client = LangfuseClient.get_client()

# Export for use in other modules
__all__ = ["langfuse_client", "LangfuseClient"]