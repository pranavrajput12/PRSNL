#!/usr/bin/env python3
"""
Apply database index optimizations for PRSNL
"""
import asyncio
import asyncpg
import os
from pathlib import Path

async def apply_indexes():
    """Apply performance indexes to the database"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prsnl")
    
    # Read the migration file
    migration_file = Path(__file__).parent.parent / "app" / "db" / "migrations" / "002_add_performance_indexes.sql"
    
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        print("Applying performance indexes...")
        
        # First, ensure required extensions are enabled
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # Split the migration into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                print(f"Executing statement {i}/{len(statements)}...")
                await conn.execute(statement)
            except Exception as e:
                print(f"Warning: Statement {i} failed: {e}")
                # Continue with other statements
        
        print("✅ Performance indexes applied successfully!")
        
        # Get index statistics
        index_stats = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        print("\nCurrent indexes:")
        for row in index_stats:
            print(f"  - {row['tablename']}.{row['indexname']} ({row['size']})")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_indexes())