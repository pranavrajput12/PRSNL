#!/usr/bin/env python3
"""
Optimized startup script for PRSNL backend with uvloop performance optimization.

This script ensures uvloop is properly configured for maximum async performance.
Expected improvements:
- 2-4x faster database operations with asyncpg
- 30-60% improved API throughput
- Better concurrent request handling
- Faster Azure OpenAI API calls
"""

import sys
import os
import logging

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def main():
    """Start the FastAPI application with uvloop optimization."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check platform compatibility
    if sys.platform == 'win32':
        logger.warning("⚠️ uvloop is not supported on Windows - using default asyncio")
        loop_type = "auto"
    else:
        logger.info("🚀 Using uvloop for optimized async performance")
        loop_type = "uvloop"
    
    try:
        import uvicorn
        from app.config import settings
        
        # Start with uvloop configuration
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=settings.BACKEND_PORT,
            loop=loop_type,
            workers=1,  # Single worker for development
            reload=False,  # Disable reload for production performance
            access_log=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Install with: pip install uvloop uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()