"""Database connection and pooling"""
import asyncpg
from typing import Optional, List
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
        import os
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        migration_file_path = os.path.join(base_path, "migrations", "003_add_embedding_to_items.sql")
        if os.path.exists(migration_file_path):
            # Check if embedding column already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'items' AND column_name = 'embedding'
                )
            """)
            if not exists:
                with open(migration_file_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {migration_file_path}")
            else:
                print(f"Skipping migration {migration_file_path} - embedding column already exists")

        migration_file_path = os.path.join(base_path, "migrations", "004_add_transcription_to_items.sql")
        if os.path.exists(migration_file_path):
            # Check if transcription column already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'items' AND column_name = 'transcription'
                )
            """)
            if not exists:
                with open(migration_file_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {migration_file_path}")
            else:
                print(f"Skipping migration {migration_file_path} - transcription column already exists")

async def update_item_embedding(item_id: str, embedding: List[float]):
    """Update the embedding for a specific item"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Convert list to vector string format for pgvector
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        await conn.execute(
            "UPDATE items SET embedding = $2::vector WHERE id = $1",
            item_id,
            embedding_str
        )

async def find_similar_items_by_embedding(
    conn: asyncpg.Connection,
    embedding: List[float],
    limit: int = 10,
    exclude_id: Optional[str] = None
):
    """Find similar items based on a given embedding using a provided connection."""
    # Convert list to vector string format for pgvector
    embedding_str = f"[{','.join(map(str, embedding))}]"

    # Base query
    query = """
        SELECT id, title, url, summary, created_at, 1 - (embedding <=> $1) as similarity
        FROM items
        WHERE embedding IS NOT NULL
    """
    params = [embedding_str]

    # Exclude a specific item if requested
    if exclude_id:
        query += " AND id != $2"
        params.append(exclude_id)

    # Add ordering and limit
    query += f" ORDER BY embedding <=> $1 LIMIT ${len(params) + 1}"
    params.append(limit)

    try:
        return await conn.fetch(query, *params)
    except Exception as e:
        # Log the error for debugging
        print(f"Database error in find_similar_items_by_embedding: {e}")
        raise