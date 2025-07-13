#!/usr/bin/env python3
"""
Migration script for PRSNL Simplified Permalink System

Migrates existing content to the new /c/category/slug URL structure.
Creates ContentUrl entries and redirects for all existing items.
"""

import asyncio
import logging
import sys
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import ContentUrl, Item, UrlRedirect
from app.services.slug_generator import SmartSlugGenerator
from app.services.url_service import URLService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class URLMigrator:
    """Handles migration of existing content to new URL structure."""
    
    def __init__(self):
        # Use asyncpg driver for async operations
        database_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
        self.engine = create_async_engine(database_url)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.stats = {
            'total_items': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0,
            'redirects_created': 0
        }
    
    async def run_migration(self, dry_run: bool = False, batch_size: int = 100):
        """Run the complete migration process."""
        logger.info("Starting PRSNL URL migration...")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"Batch size: {batch_size}")
        
        try:
            # Apply database migration first
            await self.apply_database_migration(dry_run)
            
            # Migrate content
            await self.migrate_content(dry_run, batch_size)
            
            # Create legacy redirects
            await self.create_legacy_redirects(dry_run)
            
            # Print final statistics
            self.print_stats()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.engine.dispose()
    
    async def apply_database_migration(self, dry_run: bool):
        """Apply the database schema migration."""
        logger.info("Applying database schema migration...")
        
        if dry_run:
            logger.info("DRY RUN: Would apply migration 012_add_simplified_permalinks.sql")
            return
        
        async with self.session_factory() as session:
            try:
                # Check if tables already exist
                from sqlalchemy import text
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'content_urls'
                    );
                """))
                tables_exist = result.scalar()
                
                if not tables_exist:
                    # Read and execute migration file
                    with open('app/db/migrations/012_add_simplified_permalinks.sql', 'r') as f:
                        migration_sql = f.read()
                    
                    # Execute migration
                    await session.execute(text(migration_sql))
                    await session.commit()
                    logger.info("Database migration applied successfully")
                else:
                    logger.info("Tables already exist, skipping migration")
                    
            except Exception as e:
                logger.error(f"Database migration failed: {e}")
                raise
    
    async def migrate_content(self, dry_run: bool, batch_size: int):
        """Migrate existing content to new URL structure."""
        logger.info("Starting content migration...")
        
        async with self.session_factory() as session:
            # Get total count
            count_result = await session.execute(select(func.count()).select_from(Item))
            self.stats['total_items'] = count_result.scalar()
            
            logger.info(f"Found {self.stats['total_items']} items to migrate")
            
            # Process in batches
            offset = 0
            while True:
                # Get batch of items
                query = select(Item).offset(offset).limit(batch_size)
                result = await session.execute(query)
                items = result.scalars().all()
                
                if not items:
                    break
                
                logger.info(f"Processing batch {offset//batch_size + 1}: {len(items)} items")
                
                for item in items:
                    await self.migrate_item(session, item, dry_run)
                
                if not dry_run:
                    await session.commit()
                
                offset += batch_size
    
    async def migrate_item(self, session, item: Item, dry_run: bool):
        """Migrate a single item to new URL structure."""
        try:
            # Check if already migrated
            existing_query = select(ContentUrl).where(ContentUrl.content_id == item.id)
            existing_result = await session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                self.stats['skipped'] += 1
                return
            
            # Generate category and slug
            url_data = await SmartSlugGenerator.generate_slug_for_item(item)
            category = url_data['category']
            slug = url_data['slug']
            
            if dry_run:
                logger.info(f"DRY RUN: Would create URL /c/{category}/{slug} for item {item.id} ({item.title})")
                self.stats['migrated'] += 1
                return
            
            # Create ContentUrl
            content_url = await URLService.create_content_url(item)
            
            logger.debug(f"Created URL /c/{content_url.category}/{content_url.slug} for item {item.id}")
            self.stats['migrated'] += 1
            
        except Exception as e:
            logger.error(f"Failed to migrate item {item.id}: {e}")
            self.stats['errors'] += 1
    
    async def create_legacy_redirects(self, dry_run: bool):
        """Create redirects for legacy URLs."""
        logger.info("Creating legacy redirects...")
        
        # Static redirects (already in migration SQL)
        static_redirects = [
            ('/timeline', '/p/timeline'),
            ('/insights', '/p/insights'),
            ('/chat', '/p/chat'),
            ('/videos', '/p/visual'),
            ('/code-cortex', '/p/code'),
            ('/import', '/s/import'),
            ('/import/v1', '/s/import?v=v1'),
            ('/import/v2', '/s/import?v=v2'),
            ('/settings', '/s/settings'),
            ('/docs', '/s/docs')
        ]
        
        async with self.session_factory() as session:
            # Create dynamic redirects for items
            query = select(ContentUrl, Item).join(Item, ContentUrl.content_id == Item.id)
            result = await session.execute(query)
            content_urls = result.all()
            
            for content_url, item in content_urls:
                # Create /items/{id} redirect
                old_path = f"/items/{item.id}"
                new_path = f"/c/{content_url.category}/{content_url.slug}"
                
                if dry_run:
                    logger.info(f"DRY RUN: Would create redirect {old_path} -> {new_path}")
                    self.stats['redirects_created'] += 1
                    continue
                
                try:
                    await URLService.create_redirect(old_path, new_path, 301)
                    
                    # Create /videos/{id} redirect if it's video content
                    if item.platform in ['youtube', 'vimeo'] or item.type == 'video':
                        video_path = f"/videos/{item.id}"
                        await URLService.create_redirect(video_path, new_path, 301)
                        self.stats['redirects_created'] += 1
                    
                    self.stats['redirects_created'] += 1
                    
                except Exception as e:
                    logger.debug(f"Redirect already exists or failed: {old_path} -> {new_path}: {e}")
            
            if not dry_run:
                await session.commit()
                logger.info(f"Created {self.stats['redirects_created']} redirects")
    
    def print_stats(self):
        """Print migration statistics."""
        logger.info("\n" + "="*50)
        logger.info("MIGRATION STATISTICS")
        logger.info("="*50)
        logger.info(f"Total items found:      {self.stats['total_items']:,}")
        logger.info(f"Successfully migrated:  {self.stats['migrated']:,}")
        logger.info(f"Skipped (existing):     {self.stats['skipped']:,}")
        logger.info(f"Errors:                 {self.stats['errors']:,}")
        logger.info(f"Redirects created:      {self.stats['redirects_created']:,}")
        logger.info("="*50)
        
        if self.stats['errors'] > 0:
            logger.warning(f"Migration completed with {self.stats['errors']} errors")
        else:
            logger.info("Migration completed successfully!")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate PRSNL to simplified permalink system')
    parser.add_argument('--dry-run', action='store_true', help='Preview migration without making changes')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of items to process per batch')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = URLMigrator()
    await migrator.run_migration(dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == '__main__':
    asyncio.run(main())