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

async def apply_migrations():
    """Apply database migrations"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Read and execute migration files
        # In a real scenario, you'd want a more robust migration system
        # that tracks applied migrations. For this task, we'll just
        # execute the new migration file.
        migration_file_path = "/Users/pronav/Personal Knowledge Base/PRSNL/backend/app/db/migrations/003_add_embedding_to_items.sql"
        with open(migration_file_path, "r") as f:
            migration_sql = f.read()
        await conn.execute(migration_sql)
        print(f"Applied migration: {migration_file_path}")

        migration_file_path = "/Users/pronav/Personal Knowledge Base/PRSNL/backend/app/db/migrations/004_add_transcription_to_items.sql"
        with open(migration_file_path, "r") as f:
            migration_sql = f.read()
        await conn.execute(migration_sql)
        print(f"Applied migration: {migration_file_path}")

async def update_item_embedding(item_id: str, embedding: List[float]):
    """Update the embedding for a specific item"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE items SET embedding = $1 WHERE id = $2",
            embedding,
            item_id
        )