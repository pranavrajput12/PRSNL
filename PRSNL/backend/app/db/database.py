"""Database connection and pooling"""
import asyncpg
from typing import Optional
from app.config import settings

_db_pool: Optional[asyncpg.Pool] = None


async def create_db_pool():
    """Create database connection pool"""
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=60
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