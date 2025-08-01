#!/usr/bin/env python3
"""
Apply the materialized views unique indexes migration
"""
import asyncio
import logging
import os
from pathlib import Path

import asyncpg
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_migration():
    """Apply the materialized view unique indexes migration"""
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Read migration file
        migration_path = Path(__file__).parent / "migrations" / "009_add_materialized_view_unique_indexes.sql"
        
        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False
            
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        logger.info(f"Applying migration: {migration_path}")
        
        # Execute migration
        await conn.execute(migration_sql)
        
        logger.info("Migration applied successfully!")
        
        # Test that unique indexes were created
        logger.info("Verifying unique indexes were created...")
        
        # Check entity_statistics unique index
        entity_index_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'entity_statistics_entity_type_unique_idx'
            )
        """)
        
        # Check relationship_statistics unique index
        relationship_index_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'relationship_statistics_relationship_type_unique_idx'
            )
        """)
        
        if entity_index_exists and relationship_index_exists:
            logger.info("✅ Both unique indexes created successfully!")
        else:
            logger.error(f"❌ Index creation failed. Entity index: {entity_index_exists}, Relationship index: {relationship_index_exists}")
            return False
            
        # Test the refresh function
        logger.info("Testing materialized view refresh...")
        try:
            await conn.execute("SELECT refresh_knowledge_graph_stats()")
            logger.info("✅ Materialized view refresh test passed!")
        except Exception as e:
            logger.error(f"❌ Materialized view refresh failed: {e}")
            return False
            
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


async def main():
    """Main function"""
    success = await apply_migration()
    if success:
        logger.info("🎉 Migration completed successfully!")
        exit(0)
    else:
        logger.error("💥 Migration failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())