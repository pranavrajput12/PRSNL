#!/usr/bin/env python3
"""
PRSNL Database Integrity Checker

This script performs comprehensive data integrity checks on the PRSNL database,
identifying issues with URLs, content types, permalinks, and data consistency.

Usage:
    python3 scripts/check_data_integrity.py [--output report.json] [--quiet]

Arguments:
    --output, -o    Output file for detailed JSON report (default: integrity_report.json)
    --quiet, -q     Suppress console output (only saves report file)

Checks performed:
1. YouTube/Vimeo URLs tagged as non-video types (bookmark, article, etc.)
2. Video items without video_url field set
3. Content URLs pointing to wrong item types (e.g., media category with articles)
4. Duplicate URLs with different content types
5. Missing permalinks for items that should have them
6. Orphaned content_urls without corresponding items
7. Items with invalid platform values
8. Inconsistent video metadata between URL and platform fields

Exit codes:
    0 - No integrity issues found
    1 - Issues found (check report for details)

Examples:
    # Run basic check with console output
    python3 scripts/check_data_integrity.py

    # Run quietly and save to custom location
    python3 scripts/check_data_integrity.py --quiet --output /path/to/report.json

    # Use in CI/CD pipelines
    python3 scripts/check_data_integrity.py --quiet && echo "DB OK" || echo "DB Issues Found"

Author: Claude Code
Date: July 2025
"""

import asyncio
import asyncpg
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import argparse
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.db.database import create_db_pool, close_db_pool

class DataIntegrityChecker:
    """Main class for performing database integrity checks"""
    
    def __init__(self, quiet=False):
        self.pool = None
        self.quiet = quiet
        self.issues = {
            'video_url_mismatches': [],
            'missing_video_urls': [],
            'content_url_mismatches': [],
            'duplicate_urls': [],
            'missing_permalinks': [],
            'orphaned_content_urls': [],
            'invalid_platforms': [],
            'inconsistent_metadata': [],
            'summary': {}
        }
        
        # Video URL patterns
        self.video_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'vimeo\.com/',
            r'twitch\.tv/',
            r'dailymotion\.com/',
            r'rumble\.com/',
            r'bitchute\.com/'
        ]
        
        # Expected video types
        self.video_types = ['video', 'youtube', 'vimeo', 'twitch']
        
        # Expected non-video types for URLs
        self.non_video_types = ['bookmark', 'article', 'blog', 'news', 'documentation', 'tool', 'github_repo']

    async def connect(self):
        """Initialize database connection"""
        if not self.quiet:
            print("🔌 Connecting to database...")
        
        # Create connection pool directly using asyncpg
        import asyncpg
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        if not self.quiet:
            print("✅ Database connection established")

    async def disconnect(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            if not self.quiet:
                print("🔌 Database connection closed")

    def is_video_url(self, url: str) -> bool:
        """Check if URL is a video platform URL"""
        if not url:
            return False
        
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in self.video_patterns)

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL for platform detection"""
        if not url:
            return None
            
        # YouTube patterns
        youtube_patterns = [
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtu\.be/([^?]+)',
            r'youtube\.com/embed/([^?]+)'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Vimeo pattern
        vimeo_match = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo_match:
            return vimeo_match.group(1)
        
        return None

    def detect_platform_from_url(self, url: str) -> Optional[str]:
        """Detect platform from URL"""
        if not url:
            return None
            
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'vimeo.com' in url_lower:
            return 'vimeo'
        elif 'twitch.tv' in url_lower:
            return 'twitch'
        elif 'dailymotion.com' in url_lower:
            return 'dailymotion'
        elif 'rumble.com' in url_lower:
            return 'rumble'
        elif 'bitchute.com' in url_lower:
            return 'bitchute'
        
        return None

    async def check_video_url_mismatches(self):
        """Check for YouTube/Vimeo URLs tagged as non-video types"""
        if not self.quiet:
            print("🔍 Checking for video URLs with non-video types...")
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, title, url, type, platform, video_url, created_at
                FROM items 
                WHERE url IS NOT NULL 
                AND url != ''
                ORDER BY created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                url = row['url']
                item_type = row['type']
                platform = row['platform']
                video_url = row['video_url']
                
                if self.is_video_url(url):
                    detected_platform = self.detect_platform_from_url(url)
                    
                    # Check if it's marked as non-video type
                    if item_type in self.non_video_types:
                        self.issues['video_url_mismatches'].append({
                            'id': str(row['id']),
                            'title': row['title'],
                            'url': url,
                            'current_type': item_type,
                            'detected_platform': detected_platform,
                            'suggested_type': 'video',
                            'issue': f"Video URL marked as '{item_type}' instead of video type",
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None
                        })
                    
                    # Check platform consistency
                    if platform and platform != detected_platform:
                        self.issues['inconsistent_metadata'].append({
                            'id': str(row['id']),
                            'title': row['title'],
                            'url': url,
                            'current_platform': platform,
                            'detected_platform': detected_platform,
                            'issue': f"Platform mismatch: stored as '{platform}', detected as '{detected_platform}'",
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None
                        })

        if not self.quiet:
            print(f"   Found {len(self.issues['video_url_mismatches'])} video URL type mismatches")
            print(f"   Found {len(self.issues['inconsistent_metadata'])} platform inconsistencies")

    async def check_missing_video_urls(self):
        """Check for video items that don't have video_url set"""
        if not self.quiet:
            print("🔍 Checking for video items without video_url...")
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, title, url, type, platform, video_url, created_at
                FROM items 
                WHERE type IN ('video', 'youtube', 'vimeo', 'twitch')
                AND (video_url IS NULL OR video_url = '')
                ORDER BY created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                # If the main URL is a video URL, it could be used as video_url
                suggested_video_url = row['url'] if self.is_video_url(row['url']) else None
                
                self.issues['missing_video_urls'].append({
                    'id': str(row['id']),
                    'title': row['title'],
                    'url': row['url'],
                    'type': row['type'],
                    'platform': row['platform'],
                    'suggested_video_url': suggested_video_url,
                    'issue': f"Video type item missing video_url",
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

        if not self.quiet:
            print(f"   Found {len(self.issues['missing_video_urls'])} video items without video_url")

    async def check_content_url_mismatches(self):
        """Check for content_urls pointing to wrong item types"""
        if not self.quiet:
            print("🔍 Checking content_urls for type mismatches...")
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT cu.id as content_url_id, cu.slug, cu.category, cu.views,
                       i.id as item_id, i.title, i.type, i.url, i.created_at
                FROM content_urls cu
                JOIN items i ON cu.content_id = i.id
                ORDER BY cu.created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                category = row['category']
                item_type = row['type']
                
                # Define expected mappings
                category_type_mappings = {
                    'videos': ['video', 'youtube', 'vimeo', 'twitch'],
                    'articles': ['article', 'blog', 'news'],
                    'tools': ['tool', 'software', 'app'],
                    'projects': ['github_repo', 'project'],
                    'docs': ['documentation', 'guide', 'manual']
                }
                
                # Check for mismatches
                mismatch_found = False
                expected_types = category_type_mappings.get(category, [])
                
                if expected_types and item_type not in expected_types:
                    mismatch_found = True
                
                # Special case: media category should only contain video types
                if category == 'media' and not self.is_video_url(row['url']):
                    mismatch_found = True
                
                if mismatch_found:
                    self.issues['content_url_mismatches'].append({
                        'content_url_id': str(row['content_url_id']),
                        'item_id': str(row['item_id']),
                        'slug': row['slug'],
                        'category': category,
                        'item_type': item_type,
                        'item_title': row['title'],
                        'item_url': row['url'],
                        'expected_types': expected_types,
                        'views': row['views'],
                        'issue': f"Category '{category}' contains item of type '{item_type}'",
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })

        if not self.quiet:
            print(f"   Found {len(self.issues['content_url_mismatches'])} content URL type mismatches")

    async def check_duplicate_urls(self):
        """Check for duplicate URLs with different types"""
        if not self.quiet:
            print("🔍 Checking for duplicate URLs with different types...")
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT url, array_agg(DISTINCT type) as types, 
                       array_agg(id::text) as item_ids,
                       array_agg(title) as titles,
                       count(*) as count
                FROM items 
                WHERE url IS NOT NULL 
                AND url != ''
                GROUP BY url 
                HAVING count(*) > 1
                ORDER BY count DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                types = row['types']
                
                # Only flag if there are actually different types
                if len(set(types)) > 1:
                    self.issues['duplicate_urls'].append({
                        'url': row['url'],
                        'types': types,
                        'item_ids': row['item_ids'],
                        'titles': row['titles'],
                        'count': row['count'],
                        'issue': f"URL appears {row['count']} times with different types: {', '.join(set(types))}",
                        'suggested_action': 'Review and merge or deduplicate items'
                    })

        if not self.quiet:
            print(f"   Found {len(self.issues['duplicate_urls'])} URLs with type conflicts")

    async def check_missing_permalinks(self):
        """Check for items that should have permalinks but don't"""
        if not self.quiet:
            print("🔍 Checking for missing permalinks...")
        
        async with self.pool.acquire() as conn:
            # Check items that should have content_urls but don't
            query = """
                SELECT i.id, i.title, i.type, i.url, i.created_at
                FROM items i
                LEFT JOIN content_urls cu ON i.id = cu.content_id
                WHERE cu.id IS NULL
                AND i.type IN ('video', 'article', 'blog', 'documentation', 'tool', 'github_repo')
                AND i.title IS NOT NULL
                AND i.title != ''
                ORDER BY i.created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                # Suggest category based on type
                type_to_category = {
                    'video': 'videos',
                    'youtube': 'videos', 
                    'vimeo': 'videos',
                    'article': 'articles',
                    'blog': 'articles',
                    'documentation': 'docs',
                    'tool': 'tools',
                    'github_repo': 'projects'
                }
                
                suggested_category = type_to_category.get(row['type'], 'articles')
                
                self.issues['missing_permalinks'].append({
                    'id': str(row['id']),
                    'title': row['title'],
                    'type': row['type'],
                    'url': row['url'],
                    'suggested_category': suggested_category,
                    'issue': f"Item of type '{row['type']}' missing permalink",
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

        if not self.quiet:
            print(f"   Found {len(self.issues['missing_permalinks'])} items missing permalinks")

    async def check_orphaned_content_urls(self):
        """Check for content_urls without corresponding items"""
        if not self.quiet:
            print("🔍 Checking for orphaned content URLs...")
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT cu.id, cu.slug, cu.category, cu.content_id, cu.created_at
                FROM content_urls cu
                LEFT JOIN items i ON cu.content_id = i.id
                WHERE i.id IS NULL
                ORDER BY cu.created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                self.issues['orphaned_content_urls'].append({
                    'content_url_id': str(row['id']),
                    'slug': row['slug'],
                    'category': row['category'],
                    'missing_item_id': str(row['content_id']),
                    'issue': "Content URL references non-existent item",
                    'suggested_action': 'Delete orphaned content URL',
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

        if not self.quiet:
            print(f"   Found {len(self.issues['orphaned_content_urls'])} orphaned content URLs")

    async def check_invalid_platforms(self):
        """Check for items with invalid platform values"""
        if not self.quiet:
            print("🔍 Checking for invalid platform values...")
        
        valid_platforms = ['youtube', 'vimeo', 'twitch', 'dailymotion', 'rumble', 'bitchute', 'tiktok']
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, title, url, type, platform, created_at
                FROM items 
                WHERE platform IS NOT NULL 
                AND platform != ''
                ORDER BY created_at DESC
            """
            
            rows = await conn.fetch(query)
            
            for row in rows:
                platform = row['platform']
                url = row['url']
                
                # Check if platform is valid
                if platform not in valid_platforms:
                    detected_platform = self.detect_platform_from_url(url)
                    
                    self.issues['invalid_platforms'].append({
                        'id': str(row['id']),
                        'title': row['title'],
                        'url': url,
                        'type': row['type'],
                        'invalid_platform': platform,
                        'detected_platform': detected_platform,
                        'valid_platforms': valid_platforms,
                        'issue': f"Invalid platform value: '{platform}'",
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })

        if not self.quiet:
            print(f"   Found {len(self.issues['invalid_platforms'])} items with invalid platforms")

    async def generate_summary(self):
        """Generate summary statistics"""
        if not self.quiet:
            print("📊 Generating summary statistics...")
        
        async with self.pool.acquire() as conn:
            # Get total counts
            total_items = await conn.fetchval("SELECT COUNT(*) FROM items")
            total_content_urls = await conn.fetchval("SELECT COUNT(*) FROM content_urls")
            
            # Get type distribution
            type_dist = await conn.fetch("""
                SELECT type, COUNT(*) as count 
                FROM items 
                GROUP BY type 
                ORDER BY count DESC
            """)
            
            # Get platform distribution
            platform_dist = await conn.fetch("""
                SELECT platform, COUNT(*) as count 
                FROM items 
                WHERE platform IS NOT NULL
                GROUP BY platform 
                ORDER BY count DESC
            """)
            
            # Get category distribution
            category_dist = await conn.fetch("""
                SELECT category, COUNT(*) as count 
                FROM content_urls 
                GROUP BY category 
                ORDER BY count DESC
            """)
            
            self.issues['summary'] = {
                'total_items': total_items,
                'total_content_urls': total_content_urls,
                'total_issues_found': sum(len(issues) for key, issues in self.issues.items() if key != 'summary'),
                'type_distribution': [{'type': row['type'], 'count': row['count']} for row in type_dist],
                'platform_distribution': [{'platform': row['platform'], 'count': row['count']} for row in platform_dist],
                'category_distribution': [{'category': row['category'], 'count': row['count']} for row in category_dist],
                'issue_breakdown': {
                    'video_url_mismatches': len(self.issues['video_url_mismatches']),
                    'missing_video_urls': len(self.issues['missing_video_urls']),
                    'content_url_mismatches': len(self.issues['content_url_mismatches']),
                    'duplicate_urls': len(self.issues['duplicate_urls']),
                    'missing_permalinks': len(self.issues['missing_permalinks']),
                    'orphaned_content_urls': len(self.issues['orphaned_content_urls']),
                    'invalid_platforms': len(self.issues['invalid_platforms']),
                    'inconsistent_metadata': len(self.issues['inconsistent_metadata'])
                }
            }

    async def run_all_checks(self):
        """Run all integrity checks"""
        if not self.quiet:
            print("🔍 Starting comprehensive data integrity checks...")
            print("=" * 60)
        
        await self.check_video_url_mismatches()
        await self.check_missing_video_urls()
        await self.check_content_url_mismatches()
        await self.check_duplicate_urls()
        await self.check_missing_permalinks()
        await self.check_orphaned_content_urls()
        await self.check_invalid_platforms()
        await self.generate_summary()
        
        if not self.quiet:
            print("=" * 60)
            print("✅ All integrity checks completed")

    def print_report(self):
        """Print a detailed console report"""
        print("\n" + "=" * 80)
        print("📋 DATA INTEGRITY REPORT")
        print("=" * 80)
        
        summary = self.issues['summary']
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Items: {summary['total_items']:,}")
        print(f"   Total Content URLs: {summary['total_content_urls']:,}")
        print(f"   Total Issues Found: {summary['total_issues_found']:,}")
        
        print(f"\n🔢 ISSUE BREAKDOWN:")
        for issue_type, count in summary['issue_breakdown'].items():
            if count > 0:
                issue_name = issue_type.replace('_', ' ').title()
                print(f"   {issue_name}: {count}")
        
        # Print detailed issues if any found
        if summary['total_issues_found'] > 0:
            print(f"\n🚨 DETAILED ISSUES:")
            
            if self.issues['video_url_mismatches']:
                print(f"\n   🎥 Video URL Type Mismatches ({len(self.issues['video_url_mismatches'])}):")
                for issue in self.issues['video_url_mismatches'][:5]:  # Show first 5
                    print(f"      • {issue['title'][:50]}... | Type: {issue['current_type']} → {issue['suggested_type']}")
                if len(self.issues['video_url_mismatches']) > 5:
                    print(f"      ... and {len(self.issues['video_url_mismatches']) - 5} more")
            
            if self.issues['missing_video_urls']:
                print(f"\n   🎬 Missing Video URLs ({len(self.issues['missing_video_urls'])}):")
                for issue in self.issues['missing_video_urls'][:5]:
                    print(f"      • {issue['title'][:50]}... | Type: {issue['type']}")
                if len(self.issues['missing_video_urls']) > 5:
                    print(f"      ... and {len(self.issues['missing_video_urls']) - 5} more")
            
            if self.issues['duplicate_urls']:
                print(f"\n   🔄 Duplicate URLs ({len(self.issues['duplicate_urls'])}):")
                for issue in self.issues['duplicate_urls'][:3]:
                    print(f"      • {issue['url'][:60]}... | Types: {', '.join(issue['types'])}")
                if len(self.issues['duplicate_urls']) > 3:
                    print(f"      ... and {len(self.issues['duplicate_urls']) - 3} more")
            
            if self.issues['missing_permalinks']:
                print(f"\n   🔗 Missing Permalinks ({len(self.issues['missing_permalinks'])}):")
                for issue in self.issues['missing_permalinks'][:5]:
                    print(f"      • {issue['title'][:50]}... | Type: {issue['type']}")
                if len(self.issues['missing_permalinks']) > 5:
                    print(f"      ... and {len(self.issues['missing_permalinks']) - 5} more")
        
        else:
            print(f"\n✅ No data integrity issues found!")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if self.issues['video_url_mismatches']:
            print(f"   • Update {len(self.issues['video_url_mismatches'])} items with video URLs to use video types")
        if self.issues['missing_video_urls']:
            print(f"   • Set video_url field for {len(self.issues['missing_video_urls'])} video items")
        if self.issues['duplicate_urls']:
            print(f"   • Review and deduplicate {len(self.issues['duplicate_urls'])} URL conflicts")
        if self.issues['missing_permalinks']:
            print(f"   • Generate permalinks for {len(self.issues['missing_permalinks'])} items")
        if self.issues['orphaned_content_urls']:
            print(f"   • Clean up {len(self.issues['orphaned_content_urls'])} orphaned content URLs")
        
        print("=" * 80)

    def save_report(self, output_file: str):
        """Save detailed report to JSON file"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'database_url': settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'localhost',
            'issues': self.issues
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        if not self.quiet:
            print(f"📄 Detailed report saved to: {output_file}")

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='PRSNL Database Integrity Checker')
    parser.add_argument('--output', '-o', default='integrity_report.json',
                      help='Output file for detailed JSON report')
    parser.add_argument('--quiet', '-q', action='store_true',
                      help='Suppress console output')
    
    args = parser.parse_args()
    
    checker = DataIntegrityChecker(quiet=args.quiet)
    
    try:
        await checker.connect()
        await checker.run_all_checks()
        
        if not args.quiet:
            checker.print_report()
        
        checker.save_report(args.output)
        
        # Exit with error code if issues found
        total_issues = checker.issues['summary']['total_issues_found']
        if total_issues > 0:
            if not args.quiet:
                print(f"\n⚠️  Found {total_issues} integrity issues. Review the report for details.")
            sys.exit(1)
        else:
            if not args.quiet:
                print(f"\n✅ Database integrity check passed!")
            sys.exit(0)
            
    except Exception as e:
        if not args.quiet:
            print(f"❌ Error during integrity check: {e}")
        sys.exit(1)
    finally:
        await checker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())