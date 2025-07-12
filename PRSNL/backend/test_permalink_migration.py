#!/usr/bin/env python3
"""
Permalink System Migration Verification Script

This script verifies that the permalink system migration was successful
and identifies any issues that need to be fixed.
"""

import asyncio
import asyncpg
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.services.url_service import URLService
from app.services.slug_generator import SmartSlugGenerator


class PermalinkMigrationVerifier:
    """Verifies the permalink system migration and identifies issues."""
    
    def __init__(self):
        self.issues = []
        self.stats = {
            'total_items': 0,
            'migrated_items': 0,
            'items_without_urls': 0,
            'duplicate_slugs': 0,
            'invalid_categories': 0,
            'invalid_slugs': 0,
            'redirect_count': 0,
            'broken_redirects': 0
        }
    
    async def run_verification(self) -> Dict[str, Any]:
        """Run complete verification of the permalink system."""
        print("🔍 Starting permalink system verification...")
        
        conn = await asyncpg.connect(settings.DATABASE_URL)
        try:
            await self._verify_database_structure(conn)
            await self._verify_migration_results(conn)
            await self._verify_slug_uniqueness(conn)
            await self._verify_category_classification(conn)
            await self._verify_redirects(conn)
            await self._test_url_generation()
            
            return {
                'success': len(self.issues) == 0,
                'issues': self.issues,
                'stats': self.stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        finally:
            await conn.close()
    
    async def _verify_database_structure(self, conn: asyncpg.Connection):
        """Verify that required tables and indexes exist."""
        print("📋 Verifying database structure...")
        
        # Check if content_urls table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'content_urls'
            );
        """)
        
        if not result:
            self.issues.append({
                'type': 'critical',
                'category': 'database',
                'message': 'content_urls table does not exist'
            })
            return
        
        # Check if url_redirects table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'url_redirects'
            );
        """)
        
        if not result:
            self.issues.append({
                'type': 'critical',
                'category': 'database',
                'message': 'url_redirects table does not exist'
            })
        
        # Check for required indexes
        indexes_to_check = [
            'idx_content_urls_category_slug',
            'idx_content_urls_content_id',
            'idx_url_redirects_old_path'
        ]
        
        for index_name in indexes_to_check:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = $1
                );
            """, index_name)
            
            if not result:
                self.issues.append({
                    'type': 'warning',
                    'category': 'performance',
                    'message': f'Missing index: {index_name}'
                })
        
        print("✅ Database structure verification complete")
    
    async def _verify_migration_results(self, conn: asyncpg.Connection):
        """Verify that items were properly migrated to content URLs."""
        print("📊 Verifying migration results...")
        
        # Count total items
        self.stats['total_items'] = await conn.fetchval("SELECT COUNT(*) FROM items")
        
        # Count migrated items
        self.stats['migrated_items'] = await conn.fetchval("""
            SELECT COUNT(*) FROM content_urls cu
            INNER JOIN items i ON cu.content_id = i.id
        """)
        
        # Count items without content URLs
        self.stats['items_without_urls'] = await conn.fetchval("""
            SELECT COUNT(*) FROM items i
            LEFT JOIN content_urls cu ON i.id = cu.content_id
            WHERE cu.id IS NULL
        """)
        
        migration_percentage = (self.stats['migrated_items'] / self.stats['total_items'] * 100) if self.stats['total_items'] > 0 else 0
        
        print(f"📈 Migration stats:")
        print(f"   Total items: {self.stats['total_items']}")
        print(f"   Migrated items: {self.stats['migrated_items']}")
        print(f"   Items without URLs: {self.stats['items_without_urls']}")
        print(f"   Migration percentage: {migration_percentage:.1f}%")
        
        if migration_percentage < 95:
            self.issues.append({
                'type': 'warning',
                'category': 'migration',
                'message': f'Only {migration_percentage:.1f}% of items were migrated to new URL structure'
            })
        
        # Check for items with missing titles (would cause slug generation issues)
        items_without_titles = await conn.fetchval("""
            SELECT COUNT(*) FROM items 
            WHERE title IS NULL OR title = ''
        """)
        
        if items_without_titles > 0:
            self.issues.append({
                'type': 'error',
                'category': 'data_quality',
                'message': f'{items_without_titles} items have missing titles'
            })
    
    async def _verify_slug_uniqueness(self, conn: asyncpg.Connection):
        """Verify that slugs are unique within each category."""
        print("🔍 Verifying slug uniqueness...")
        
        # Find duplicate slugs within categories
        duplicates = await conn.fetch("""
            SELECT category, slug, COUNT(*) as count
            FROM content_urls
            GROUP BY category, slug
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        self.stats['duplicate_slugs'] = len(duplicates)
        
        if duplicates:
            for dup in duplicates:
                self.issues.append({
                    'type': 'error',
                    'category': 'data_integrity',
                    'message': f'Duplicate slug "{dup["slug"]}" in category "{dup["category"]}" ({dup["count"]} instances)'
                })
        
        print(f"   Found {len(duplicates)} duplicate slug combinations")
    
    async def _verify_category_classification(self, conn: asyncpg.Connection):
        """Verify that categories are valid and well-distributed."""
        print("📂 Verifying category classification...")
        
        # Check for invalid categories
        invalid_categories = await conn.fetch("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM content_urls
            WHERE category NOT IN ('dev', 'learn', 'media', 'ideas')
            GROUP BY category
        """)
        
        self.stats['invalid_categories'] = len(invalid_categories)
        
        if invalid_categories:
            for cat in invalid_categories:
                self.issues.append({
                    'type': 'error',
                    'category': 'data_integrity',
                    'message': f'Invalid category "{cat["category"]}" found ({cat["count"]} items)'
                })
        
        # Get category distribution
        distribution = await conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM content_urls
            GROUP BY category
            ORDER BY count DESC
        """)
        
        print("   Category distribution:")
        for cat in distribution:
            percentage = (cat['count'] / self.stats['migrated_items'] * 100) if self.stats['migrated_items'] > 0 else 0
            print(f"     {cat['category']}: {cat['count']} items ({percentage:.1f}%)")
        
        # Warn if any category is too dominant (>80%) or too sparse (<1%)
        for cat in distribution:
            percentage = (cat['count'] / self.stats['migrated_items'] * 100) if self.stats['migrated_items'] > 0 else 0
            if percentage > 80:
                self.issues.append({
                    'type': 'warning',
                    'category': 'classification',
                    'message': f'Category "{cat["category"]}" is over-represented ({percentage:.1f}%)'
                })
            elif percentage < 1 and cat['count'] > 0:
                self.issues.append({
                    'type': 'info',
                    'category': 'classification',
                    'message': f'Category "{cat["category"]}" has very few items ({percentage:.1f}%)'
                })
    
    async def _verify_slug_format(self, conn: asyncpg.Connection):
        """Verify that all slugs follow the correct format."""
        print("🔤 Verifying slug format...")
        
        # Check for invalid slug formats
        invalid_slugs = await conn.fetch("""
            SELECT slug, category, COUNT(*) as count
            FROM content_urls
            WHERE NOT (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$' AND length(slug) <= 60)
            GROUP BY slug, category
            ORDER BY count DESC
            LIMIT 10
        """)
        
        self.stats['invalid_slugs'] = len(invalid_slugs)
        
        if invalid_slugs:
            for slug_info in invalid_slugs:
                self.issues.append({
                    'type': 'error',
                    'category': 'format',
                    'message': f'Invalid slug format: "{slug_info["slug"]}" in category "{slug_info["category"]}"'
                })
        
        print(f"   Found {len(invalid_slugs)} invalid slug formats")
    
    async def _verify_redirects(self, conn: asyncpg.Connection):
        """Verify that redirects are properly configured."""
        print("🔄 Verifying URL redirects...")
        
        # Count total redirects
        self.stats['redirect_count'] = await conn.fetchval("SELECT COUNT(*) FROM url_redirects WHERE active = true")
        
        # Check for redirects pointing to non-existent content
        broken_redirects = await conn.fetch("""
            SELECT ur.old_path, ur.new_path
            FROM url_redirects ur
            WHERE ur.active = true
            AND ur.new_path LIKE '/c/%'
            AND NOT EXISTS (
                SELECT 1 FROM content_urls cu
                WHERE ur.new_path = '/c/' || cu.category || '/' || cu.slug
            )
            LIMIT 10
        """)
        
        self.stats['broken_redirects'] = len(broken_redirects)
        
        if broken_redirects:
            for redirect in broken_redirects:
                self.issues.append({
                    'type': 'error',
                    'category': 'redirects',
                    'message': f'Broken redirect: {redirect["old_path"]} → {redirect["new_path"]}'
                })
        
        print(f"   Total active redirects: {self.stats['redirect_count']}")
        print(f"   Broken redirects: {self.stats['broken_redirects']}")
    
    async def _test_url_generation(self):
        """Test URL generation for edge cases."""
        print("🧪 Testing URL generation...")
        
        test_cases = [
            "How to Build a React App",
            "Python Tutorial: Getting Started",
            "🚀 Advanced JavaScript Concepts",
            "API Design Best Practices & Tips",
            "Machine Learning with TensorFlow 2.0",
            "Very Long Title That Should Be Truncated Because It Exceeds The Maximum Length Limit",
            "Special@Characters#Test&More+Symbols%Here",
            "",  # Empty title
            "   ",  # Whitespace only
        ]
        
        for title in test_cases:
            try:
                slug = SmartSlugGenerator._generate_base_slug(title)
                if not SmartSlugGenerator.validate_slug(slug):
                    self.issues.append({
                        'type': 'error',
                        'category': 'slug_generation',
                        'message': f'Generated invalid slug "{slug}" from title "{title}"'
                    })
                    
            except Exception as e:
                self.issues.append({
                    'type': 'error',
                    'category': 'slug_generation',
                    'message': f'Error generating slug for "{title}": {str(e)}'
                })
        
        print("✅ URL generation tests complete")


async def main():
    """Run the permalink migration verification."""
    verifier = PermalinkMigrationVerifier()
    
    try:
        results = await verifier.run_verification()
        
        print("\n" + "="*60)
        print("📊 VERIFICATION RESULTS")
        print("="*60)
        
        if results['success']:
            print("✅ All checks passed! The permalink system is working correctly.")
        else:
            print(f"⚠️  Found {len(results['issues'])} issues that need attention.")
        
        print(f"\n📈 Statistics:")
        for key, value in results['stats'].items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        if results['issues']:
            print(f"\n🚨 Issues Found:")
            for issue in results['issues']:
                icon = {'critical': '🔴', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(issue['type'], '❓')
                print(f"   {icon} [{issue['type'].upper()}] {issue['category']}: {issue['message']}")
        
        print(f"\n🕒 Verification completed at: {results['timestamp']}")
        
        # Return appropriate exit code
        return 0 if results['success'] else 1
        
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)