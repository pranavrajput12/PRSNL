"""Database connection and pooling"""
import logging
from typing import AsyncGenerator, List, Optional

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

_db_pool: Optional[asyncpg.Pool] = None

# SQLAlchemy async engine and session
_engine = None
_async_session_maker = None


async def setup_connection(conn):
    """Setup individual connections to disable prepared statement caching"""
    # The correct way to disable prepared statements in asyncpg
    try:
        # Access the underlying connection and disable prepared statements
        if hasattr(conn, '_con'):
            conn._con._prepared_stmt_cache_size = 0
        logger.info("🔍 DISABLED prepared statement cache for connection")
    except Exception as e:
        logger.warning(f"Could not disable prepared statement cache: {e}")
        # Don't fail - just log the issue

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
    """Create database connection pool"""
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=60,
        server_settings={'jit': 'off'},  # Disable JIT for stability
        setup=setup_connection,  # Custom setup to disable prepared statements
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


# SQLAlchemy async session support
async def init_sqlalchemy():
    """Initialize SQLAlchemy async engine and session maker"""
    global _engine, _async_session_maker
    _engine = create_async_engine(
        settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        echo=False,
        pool_pre_ping=True
    )
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get SQLAlchemy async session"""
    global _async_session_maker
    if not _async_session_maker:
        await init_sqlalchemy()
    
    async with _async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

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

        # Migration 006: Add video fields
        migration_file_path = os.path.join(base_path, "migrations", "006_add_video_fields.sql")
        if os.path.exists(migration_file_path):
            # Check if type column already exists (key column from this migration)
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'items' AND column_name = 'type'
                )
            """)
            if not exists:
                with open(migration_file_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {migration_file_path}")
            else:
                print(f"Skipping migration {migration_file_path} - type column already exists")

        # Migration 009: Add content classification fields
        migration_file_path = os.path.join(base_path, "migrations", "009_add_content_classification.sql")
        if os.path.exists(migration_file_path):
            # Check if content_type column already exists (key column from this migration)
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'items' AND column_name = 'content_type'
                )
            """)
            if not exists:
                with open(migration_file_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {migration_file_path}")
            else:
                print(f"Skipping migration {migration_file_path} - content_type column already exists")

        # Migration 018: Add AI conversation tables
        migration_file_path = os.path.join(base_path, "migrations", "018_rename_ai_conversations_tables.sql")
        if os.path.exists(migration_file_path):
            # Check if ai_conversation_imports table already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'ai_conversation_imports'
                )
            """)
            if not exists:
                with open(migration_file_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {migration_file_path}")
            else:
                print(f"Skipping migration {migration_file_path} - ai_conversation_imports table already exists")

        # Development features migration
        dev_migration_path = os.path.join(os.path.dirname(base_path), "migrations", "001_add_development_features.sql")
        if os.path.exists(dev_migration_path):
            # Check if development_categories table already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'development_categories'
                )
            """)
            if not exists:
                with open(dev_migration_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {dev_migration_path}")
            else:
                print(f"Skipping migration {dev_migration_path} - development_categories table already exists")

        # Repository metadata migration
        repo_migration_path = os.path.join(base_path, "migrations", "016_add_repository_metadata.sql")
        if os.path.exists(repo_migration_path):
            # Check if repository_metadata column already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'items'
                    AND column_name = 'repository_metadata'
                )
            """)
            if not exists:
                with open(repo_migration_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {repo_migration_path}")
            else:
                print(f"Skipping migration {repo_migration_path} - repository_metadata column already exists")
        
        # GitHub tables migration
        github_migration_path = os.path.join(base_path, "migrations", "020_add_github_tables.sql")
        if os.path.exists(github_migration_path):
            # Check if github_accounts table already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'github_accounts'
                )
            """)
            if not exists:
                with open(github_migration_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {github_migration_path}")
            else:
                print(f"Skipping migration {github_migration_path} - github_accounts table already exists")
        
        # CodeMirror tables migration
        codemirror_migration_path = os.path.join(base_path, "migrations", "021_add_codemirror_tables_simple.sql")
        if os.path.exists(codemirror_migration_path):
            # Check if codemirror_analyses table already exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'codemirror_analyses'
                )
            """)
            if not exists:
                with open(codemirror_migration_path, "r") as f:
                    migration_sql = f.read()
                await conn.execute(migration_sql)
                print(f"Applied migration: {codemirror_migration_path}")
            else:
                print(f"Skipping migration {codemirror_migration_path} - codemirror_analyses table already exists")

async def update_item_embedding(item_id: str, embedding: List[float]):
    """Update the embedding for a specific item"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # When using pgvector with register_vector, pass the embedding directly as a list
        await conn.execute(
            "UPDATE items SET embedding = $2 WHERE id = $1",
            item_id,
            embedding  # Pass embedding directly as list
        )

async def find_similar_items_by_embedding(
    conn: asyncpg.Connection,
    embedding: List[float],
    limit: int = 10,
    exclude_id: Optional[str] = None
):
    """Find similar items based on a given embedding using a provided connection."""
    # When using pgvector with register_vector, pass the embedding directly as a list
    # The register_vector init function handles the conversion

    # Base query
    query = """
        SELECT id, title, url, summary, created_at, type,
               1 - (embedding <=> $1) as similarity
        FROM items
        WHERE embedding IS NOT NULL
    """
    params = [embedding]  # Pass embedding directly as list

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