#!/usr/bin/env python3
"""
Admin Permalink Migration Script

This script provides administrative functions for managing the permalink system:
- Re-migrate items that failed initial migration
- Bulk update slugs and categories
- Fix duplicate slugs
- Generate redirects for legacy URLs
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.services.slug_generator import SmartSlugGenerator
from app.services.url_service import URLService


class PermalinkMigrationAdmin:
    """Administrative tools for permalink system migration."""
    
    def __init__(self):
        self.conn = None
        self.stats = {
            'items_processed': 0,
            'items_migrated': 0,
            'items_updated': 0,
            'duplicates_fixed': 0,
            'redirects_created': 0,
            'errors': 0
        }
    
    async def connect(self):
        """Establish database connection."""
        self.conn = await asyncpg.connect(settings.DATABASE_URL)
    
    async def disconnect(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
    
    async def migrate_unmigrated_items(self, limit: int = None) -> Dict[str, Any]:
        """
        Migrate items that don't have content URLs yet.
        
        Args:
            limit: Maximum number of items to migrate (None for all)
            
        Returns:
            Migration results
        """
        print("🔄 Starting migration of unmigrated items...")
        
        # Find items without content URLs
        query = """
            SELECT i.id, i.title, i.url, i.platform, i.type, i.summary, i.raw_content
            FROM items i
            LEFT JOIN content_urls cu ON i.id = cu.content_id
            WHERE cu.id IS NULL
            AND i.title IS NOT NULL
            AND i.title != ''
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        unmigrated_items = await self.conn.fetch(query)
        
        print(f"📊 Found {len(unmigrated_items)} items to migrate")
        
        for item in unmigrated_items:
            try:
                self.stats['items_processed'] += 1
                
                # Create Item-like object for URLService
                item_obj = type('Item', (), {
                    'id': item['id'],
                    'title': item['title'],
                    'url': item['url'],
                    'platform': item['platform'],
                    'type': item['type'],
                    'summary': item['summary'],
                    'raw_content': item['raw_content']
                })()
                
                # Generate URL data
                url_data = await SmartSlugGenerator.generate_slug_for_item(item_obj)
                
                # Create SEO metadata
                seo_data = URLService._generate_seo_metadata(
                    item_obj, 
                    url_data['category'], 
                    url_data['slug']
                )
                
                # Insert content URL
                await self.conn.execute("""
                    INSERT INTO content_urls (
                        content_id, slug, category, meta_title, 
                        meta_description, canonical_url
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    item['id'], 
                    url_data['slug'], 
                    url_data['category'],
                    seo_data['title'],
                    seo_data['description'],
                    seo_data['canonical_url']
                )
                
                # Create legacy redirects
                await self._create_legacy_redirects(
                    item['id'], 
                    url_data['category'], 
                    url_data['slug'],
                    item.get('platform')
                )
                
                self.stats['items_migrated'] += 1
                
                if self.stats['items_processed'] % 10 == 0:
                    print(f"   Processed {self.stats['items_processed']} items...")
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   ❌ Error migrating item {item['id']}: {e}")
        
        print(f"✅ Migration complete. Migrated {self.stats['items_migrated']} items")
        return self.stats
    
    async def fix_duplicate_slugs(self) -> Dict[str, Any]:
        """
        Fix duplicate slugs by making them unique.
        
        Returns:
            Fix results
        """
        print("🔧 Fixing duplicate slugs...")
        
        # Find duplicate slugs
        duplicates = await self.conn.fetch("""
            SELECT category, slug, array_agg(id ORDER BY created_at) as ids
            FROM content_urls
            GROUP BY category, slug
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        
        print(f"📊 Found {len(duplicates)} duplicate slug groups")
        
        for dup in duplicates:
            try:
                category = dup['category']
                slug = dup['slug']
                ids = dup['ids']
                
                print(f"   Fixing duplicate: {category}/{slug} ({len(ids)} instances)")
                
                # Keep the first one as-is, rename the others
                for i, content_url_id in enumerate(ids[1:], start=2):
                    new_slug = f"{slug}-{i}"
                    
                    # Ensure the new slug is unique
                    counter = 2
                    while await self._slug_exists(category, new_slug):
                        counter += 1
                        new_slug = f"{slug}-{counter}"
                    
                    # Update the slug
                    await self.conn.execute("""
                        UPDATE content_urls 
                        SET slug = $1, canonical_url = $2, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $3
                    """, new_slug, f"/c/{category}/{new_slug}", content_url_id)
                    
                    self.stats['duplicates_fixed'] += 1
                    print(f"     Updated {content_url_id} to use slug: {new_slug}")
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   ❌ Error fixing duplicate {dup['category']}/{dup['slug']}: {e}")
        
        print(f"✅ Fixed {self.stats['duplicates_fixed']} duplicate slugs")
        return self.stats
    
    async def regenerate_slugs_for_category(self, category: str, force: bool = False) -> Dict[str, Any]:
        """
        Regenerate slugs for all items in a category.
        
        Args:
            category: Category to regenerate slugs for
            force: Whether to regenerate even if slug already exists
            
        Returns:
            Regeneration results
        """
        print(f"🔄 Regenerating slugs for category: {category}")
        
        if category not in SmartSlugGenerator.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        
        # Get all content URLs for this category
        content_urls = await self.conn.fetch("""
            SELECT cu.id, cu.content_id, cu.slug, cu.category, i.title, i.url, 
                   i.platform, i.type, i.summary, i.raw_content
            FROM content_urls cu
            JOIN items i ON cu.content_id = i.id
            WHERE cu.category = $1
            ORDER BY cu.created_at
        """, category)
        
        print(f"📊 Found {len(content_urls)} items in {category} category")
        
        for cu in content_urls:
            try:
                self.stats['items_processed'] += 1
                
                # Create Item-like object
                item_obj = type('Item', (), {
                    'id': cu['content_id'],
                    'title': cu['title'],
                    'url': cu['url'],
                    'platform': cu['platform'],
                    'type': cu['type'],
                    'summary': cu['summary'],
                    'raw_content': cu['raw_content']
                })()
                
                # Generate new slug
                new_slug = await SmartSlugGenerator.generate_unique_slug(
                    cu['title'], 
                    category, 
                    str(cu['content_id'])
                )
                
                # Only update if slug changed or force is True
                if cu['slug'] != new_slug or force:
                    old_slug = cu['slug']
                    
                    # Update content URL
                    seo_data = URLService._generate_seo_metadata(
                        item_obj, category, new_slug
                    )
                    
                    await self.conn.execute("""
                        UPDATE content_urls 
                        SET slug = $1, canonical_url = $2, meta_title = $3, 
                            meta_description = $4, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $5
                    """, 
                        new_slug, 
                        seo_data['canonical_url'],
                        seo_data['title'],
                        seo_data['description'],
                        cu['id']
                    )
                    
                    # Create redirect from old slug if it changed
                    if old_slug != new_slug:
                        await self._create_redirect(
                            f"/c/{category}/{old_slug}",
                            f"/c/{category}/{new_slug}"
                        )
                    
                    self.stats['items_updated'] += 1
                    print(f"   Updated: {old_slug} → {new_slug}")
                
                if self.stats['items_processed'] % 10 == 0:
                    print(f"   Processed {self.stats['items_processed']} items...")
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   ❌ Error updating item {cu['content_id']}: {e}")
        
        print(f"✅ Updated {self.stats['items_updated']} slugs in {category}")
        return self.stats
    
    async def bulk_create_redirects(self) -> Dict[str, Any]:
        """
        Create redirects for all existing content URLs.
        
        Returns:
            Redirect creation results
        """
        print("🔄 Creating bulk redirects...")
        
        # Get all content URLs
        content_urls = await self.conn.fetch("""
            SELECT cu.content_id, cu.category, cu.slug, i.platform
            FROM content_urls cu
            JOIN items i ON cu.content_id = i.id
        """)
        
        print(f"📊 Creating redirects for {len(content_urls)} items")
        
        for cu in content_urls:
            try:
                await self._create_legacy_redirects(
                    cu['content_id'],
                    cu['category'],
                    cu['slug'],
                    cu['platform']
                )
                
                self.stats['items_processed'] += 1
                
                if self.stats['items_processed'] % 100 == 0:
                    print(f"   Processed {self.stats['items_processed']} items...")
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"   ❌ Error creating redirects for {cu['content_id']}: {e}")
        
        print(f"✅ Created redirects for {self.stats['redirects_created']} items")
        return self.stats
    
    async def validate_all_slugs(self) -> Dict[str, Any]:
        """
        Validate all slugs in the database and report issues.
        
        Returns:
            Validation results
        """
        print("🔍 Validating all slugs...")
        
        issues = []
        
        # Check for invalid slug formats
        invalid_slugs = await self.conn.fetch("""
            SELECT id, slug, category
            FROM content_urls
            WHERE NOT (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$' AND length(slug) <= 60)
        """)
        
        for slug_info in invalid_slugs:
            issues.append({
                'type': 'invalid_format',
                'id': slug_info['id'],
                'slug': slug_info['slug'],
                'category': slug_info['category']
            })
        
        # Check for empty or null slugs
        empty_slugs = await self.conn.fetch("""
            SELECT id, slug, category
            FROM content_urls
            WHERE slug IS NULL OR slug = ''
        """)
        
        for slug_info in empty_slugs:
            issues.append({
                'type': 'empty_slug',
                'id': slug_info['id'],
                'slug': slug_info['slug'],
                'category': slug_info['category']
            })
        
        # Check for duplicates
        duplicates = await self.conn.fetch("""
            SELECT category, slug, COUNT(*) as count
            FROM content_urls
            GROUP BY category, slug
            HAVING COUNT(*) > 1
        """)
        
        for dup in duplicates:
            issues.append({
                'type': 'duplicate',
                'category': dup['category'],
                'slug': dup['slug'],
                'count': dup['count']
            })
        
        print(f"📊 Validation complete. Found {len(issues)} issues:")
        
        issue_types = {}
        for issue in issues:
            issue_type = issue['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        for issue_type, count in issue_types.items():
            print(f"   {issue_type}: {count}")
        
        return {
            'total_issues': len(issues),
            'issues_by_type': issue_types,
            'issues': issues
        }
    
    async def get_migration_stats(self) -> Dict[str, Any]:
        """Get current migration statistics."""
        stats = {}
        
        # Total items
        stats['total_items'] = await self.conn.fetchval("SELECT COUNT(*) FROM items")
        
        # Migrated items
        stats['migrated_items'] = await self.conn.fetchval("""
            SELECT COUNT(*) FROM content_urls cu
            INNER JOIN items i ON cu.content_id = i.id
        """)
        
        # Items by category
        category_stats = await self.conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM content_urls
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['category_distribution'] = {row['category']: row['count'] for row in category_stats}
        
        # Total redirects
        stats['total_redirects'] = await self.conn.fetchval("""
            SELECT COUNT(*) FROM url_redirects WHERE active = true
        """)
        
        # Migration percentage
        stats['migration_percentage'] = (
            stats['migrated_items'] / stats['total_items'] * 100
        ) if stats['total_items'] > 0 else 0
        
        return stats
    
    # Helper methods
    async def _slug_exists(self, category: str, slug: str) -> bool:
        """Check if a slug exists in the given category."""
        result = await self.conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM content_urls 
                WHERE category = $1 AND slug = $2
            )
        """, category, slug)
        return result
    
    async def _create_legacy_redirects(self, content_id: str, category: str, slug: str, platform: str = None):
        """Create legacy redirects for an item."""
        new_path = f"/c/{category}/{slug}"
        
        # Always create /items/{id} redirect
        await self._create_redirect(f"/items/{content_id}", new_path)
        
        # Create /videos/{id} redirect for video content
        if platform in ['youtube', 'vimeo'] or 'video' in str(platform).lower():
            await self._create_redirect(f"/videos/{content_id}", new_path)
    
    async def _create_redirect(self, old_path: str, new_path: str):
        """Create a URL redirect if it doesn't exist."""
        try:
            await self.conn.execute("""
                INSERT INTO url_redirects (old_path, new_path, redirect_type)
                VALUES ($1, $2, 301)
                ON CONFLICT (old_path) DO NOTHING
            """, old_path, new_path)
            self.stats['redirects_created'] += 1
        except Exception:
            # Redirect might already exist
            pass


async def main():
    """Main CLI interface for the admin script."""
    parser = argparse.ArgumentParser(description='Permalink Migration Admin Tool')
    parser.add_argument('command', choices=[
        'migrate-unmigrated',
        'fix-duplicates', 
        'regenerate-category',
        'create-redirects',
        'validate-slugs',
        'stats'
    ], help='Command to execute')
    
    parser.add_argument('--category', type=str, help='Category for category-specific operations')
    parser.add_argument('--limit', type=int, help='Limit for batch operations')
    parser.add_argument('--force', action='store_true', help='Force operation even if not needed')
    
    args = parser.parse_args()
    
    admin = PermalinkMigrationAdmin()
    
    try:
        await admin.connect()
        
        print(f"🚀 Running command: {args.command}")
        print("="*50)
        
        if args.command == 'migrate-unmigrated':
            results = await admin.migrate_unmigrated_items(args.limit)
            
        elif args.command == 'fix-duplicates':
            results = await admin.fix_duplicate_slugs()
            
        elif args.command == 'regenerate-category':
            if not args.category:
                print("❌ --category is required for regenerate-category command")
                return 1
            results = await admin.regenerate_slugs_for_category(args.category, args.force)
            
        elif args.command == 'create-redirects':
            results = await admin.bulk_create_redirects()
            
        elif args.command == 'validate-slugs':
            results = await admin.validate_all_slugs()
            
        elif args.command == 'stats':
            results = await admin.get_migration_stats()
            print("\n📊 Current Migration Statistics:")
            for key, value in results.items():
                if isinstance(value, dict):
                    print(f"\n{key.replace('_', ' ').title()}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
            return 0
        
        print("\n" + "="*50)
        print("📊 OPERATION RESULTS")
        print("="*50)
        
        if isinstance(results, dict) and 'total_issues' in results:
            # Validation results
            if results['total_issues'] == 0:
                print("✅ All slugs are valid!")
            else:
                print(f"⚠️ Found {results['total_issues']} validation issues")
                for issue_type, count in results['issues_by_type'].items():
                    print(f"   {issue_type}: {count}")
        else:
            # Migration/fix results
            print(f"📈 Statistics:")
            for key, value in results.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
            
            if results.get('errors', 0) == 0:
                print("\n✅ Operation completed successfully!")
            else:
                print(f"\n⚠️ Operation completed with {results['errors']} errors")
        
        return 0
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1
        
    finally:
        await admin.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)