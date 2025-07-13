"""Database connection with safe pgvector handling"""
import logging
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_db_pool: Optional[asyncpg.Pool] = None


async def safe_register_vector(conn):
    """Safely register vector type if pgvector is available"""
    try:
        # Check if pgvector extension exists
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        
        if result:
            # Only import and register if extension exists
            from pgvector.asyncpg import register_vector
            await register_vector(conn)
            logger.info("pgvector registered successfully")
        else:
            logger.warning("pgvector extension not found in database - vector operations will be disabled")
    except Exception as e:
        logger.warning(f"Could not register pgvector: {e} - vector operations will be disabled")


async def create_db_pool():
    """Create database connection pool with safe pgvector handling"""
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=60,
        init=safe_register_vector  # Use safe registration
    )


async def close_db_pool():
    """Close database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    if not _db_pool:
        raise RuntimeError("Database pool not initialized")
    return _db_pool


async def get_db_connection() -> asyncpg.Connection:
    """Get a database connection from the pool"""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection