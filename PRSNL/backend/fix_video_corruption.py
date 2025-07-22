#!/usr/bin/env python3
"""
Fix Video Data Corruption

This script fixes the identified video corruption issues,
particularly the Rick Astley video title corruption.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to import app modules
sys.path.append(str(Path(__file__).parent))

import asyncpg
from app.config import settings


class VideoCorruptionFixer:
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        
    async def connect(self):
        """Connect to the database"""
        self.conn = await asyncpg.connect(self.db_url)
        
    async def disconnect(self):
        """Disconnect from the database"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            
    async def identify_rick_astley_corruption(self):
        """Identify the Rick Astley corruption specifically"""
        print("🔍 Identifying Rick Astley Video Corruption...")
        
        query = """
        SELECT 
            id,
            title,
            url,
            thumbnail_url,
            platform,
            status,
            created_at,
            updated_at
        FROM items 
        WHERE (url LIKE '%dQw4w9WgXcQ%')  -- Rick Astley Never Gonna Give You Up YouTube ID
          AND title NOT LIKE '%rick%'
          AND title NOT LIKE '%astley%' 
          AND title NOT LIKE '%never%gonna%'
          AND title NOT LIKE '%give you up%'
        ORDER BY created_at DESC;
        """
        
        rows = await self.conn.fetch(query)
        
        print(f"📋 Found {len(rows)} corrupted Rick Astley entries:")
        for row in rows:
            print(f"  • ID: {row['id']}")
            print(f"    Title: {row['title']}")
            print(f"    URL: {row['url']}")
            print(f"    Status: {row['status']}")
            print()
            
        return rows
        
    async def backup_corrupted_entries(self, entries):
        """Create backup of corrupted entries before fixing"""
        if not entries:
            print("✅ No entries to backup")
            return
            
        print("💾 Creating backup of corrupted entries...")
        
        # Create backup table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS corrupted_video_backup (
                id UUID,
                title TEXT,
                url TEXT,
                thumbnail_url TEXT,
                platform VARCHAR(50),
                status VARCHAR(20),
                metadata JSONB,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ,
                corruption_type TEXT,
                backup_created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Insert corrupted entries
        for entry in entries:
            await self.conn.execute("""
                INSERT INTO corrupted_video_backup 
                (id, title, url, thumbnail_url, platform, status, created_at, updated_at, corruption_type)
                SELECT id, title, url, thumbnail_url, platform, status, created_at, updated_at, 
                       'rick_astley_title_corruption'
                FROM items 
                WHERE id = $1;
            """, entry['id'])
            
        print(f"✅ Backed up {len(entries)} corrupted entries to corrupted_video_backup table")
        
    async def fix_rick_astley_titles(self, entries):
        """Fix the Rick Astley video titles"""
        if not entries:
            print("✅ No Rick Astley entries to fix")
            return
            
        print("🔧 Fixing Rick Astley video titles...")
        
        fixed_count = 0
        
        for entry in entries:
            # Update with correct Rick Astley title and metadata
            result = await self.conn.execute("""
                UPDATE items 
                SET 
                    title = 'Rick Astley - Never Gonna Give You Up (Official Video)',
                    summary = 'The official video for "Never Gonna Give You Up" by Rick Astley',
                    platform = 'youtube',
                    status = 'pending',
                    updated_at = NOW()
                WHERE id = $1;
            """, entry['id'])
            
            if result == 'UPDATE 1':
                fixed_count += 1
                print(f"  ✅ Fixed entry {entry['id']}")
            else:
                print(f"  ❌ Failed to fix entry {entry['id']}")
                
        print(f"🎯 Fixed {fixed_count} Rick Astley video entries")
        
    async def remove_duplicates(self):
        """Remove duplicate video entries with same URL and title"""
        print("🔧 Removing duplicate video entries...")
        
        # First, identify duplicates
        duplicates = await self.conn.fetch("""
            SELECT url, title, COUNT(*) as count, 
                   STRING_AGG(id::text, ', ') as ids
            FROM items 
            WHERE url IS NOT NULL 
              AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                   OR url LIKE '%youtube%' 
                   OR url LIKE '%youtu.be%'
                   OR url LIKE '%instagram%'
                   OR url LIKE '%tiktok%'
                   OR platform IS NOT NULL)
            GROUP BY url, title
            HAVING COUNT(*) > 1
            ORDER BY count DESC;
        """)
        
        print(f"📋 Found {len(duplicates)} sets of duplicate entries:")
        for dup in duplicates:
            print(f"  • {dup['count']} duplicates of: {dup['title'][:50]}...")
            
        if duplicates:
            # Remove duplicates, keeping the oldest one
            result = await self.conn.execute("""
                DELETE FROM items a USING items b 
                WHERE a.id > b.id 
                  AND a.url = b.url 
                  AND a.title = b.title 
                  AND a.url IS NOT NULL;
            """)
            
            deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
            print(f"🗑️  Removed {deleted_count} duplicate entries")
        else:
            print("✅ No duplicates found to remove")
            
    async def fix_platform_fields(self):
        """Fix platform field based on URL"""
        print("🔧 Fixing platform fields based on URLs...")
        
        result = await self.conn.execute("""
            UPDATE items SET platform = CASE
                WHEN url LIKE '%youtube%' OR url LIKE '%youtu.be%' THEN 'youtube'
                WHEN url LIKE '%instagram%' THEN 'instagram'  
                WHEN url LIKE '%tiktok%' THEN 'tiktok'
                WHEN url LIKE '%twitter%' OR url LIKE '%x.com%' THEN 'twitter'
                ELSE platform
            END
            WHERE platform IS NULL AND url IS NOT NULL
              AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                   OR url LIKE '%youtube%' 
                   OR url LIKE '%youtu.be%'
                   OR url LIKE '%instagram%'
                   OR url LIKE '%tiktok%');
        """)
        
        updated_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
        print(f"🎯 Updated platform field for {updated_count} entries")
        
    async def verify_fixes(self):
        """Verify that the fixes have been applied correctly"""
        print("✅ Verifying fixes...")
        
        # Check Rick Astley videos
        rick_check = await self.conn.fetch("""
            SELECT id, title, url, platform, status
            FROM items 
            WHERE url LIKE '%dQw4w9WgXcQ%'
            ORDER BY updated_at DESC;
        """)
        
        print(f"🎵 Rick Astley video status ({len(rick_check)} entries):")
        for entry in rick_check:
            print(f"  • Title: {entry['title']}")
            print(f"    Platform: {entry['platform']}")
            print(f"    Status: {entry['status']}")
            print()
            
        # Check for remaining duplicates
        remaining_dups = await self.conn.fetch("""
            SELECT url, COUNT(*) as count
            FROM items 
            WHERE url IS NOT NULL 
              AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                   OR url LIKE '%youtube%' 
                   OR url LIKE '%youtu.be%'
                   OR url LIKE '%instagram%'
                   OR url LIKE '%tiktok%'
                   OR platform IS NOT NULL)
            GROUP BY url
            HAVING COUNT(*) > 1;
        """)
        
        if remaining_dups:
            print(f"⚠️  {len(remaining_dups)} URLs still have duplicates")
        else:
            print("✅ No duplicate URLs remaining")
            
        # Overall video status
        status_summary = await self.conn.fetch("""
            SELECT status, COUNT(*) as count
            FROM items 
            WHERE type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
               OR url LIKE '%youtube%' 
               OR url LIKE '%youtu.be%'
               OR url LIKE '%instagram%'
               OR url LIKE '%tiktok%'
               OR platform IS NOT NULL
            GROUP BY status
            ORDER BY count DESC;
        """)
        
        print("📊 Video status summary:")
        for status in status_summary:
            print(f"  • {status['status']}: {status['count']} videos")
            
    async def run_full_fix(self):
        """Run the complete corruption fix process"""
        print("🔧 Starting Video Data Corruption Fix")
        print("=" * 50)
        
        try:
            await self.connect()
            
            # Step 1: Identify Rick Astley corruption
            corrupted_entries = await self.identify_rick_astley_corruption()
            
            if corrupted_entries:
                # Step 2: Backup corrupted entries
                await self.backup_corrupted_entries(corrupted_entries)
                
                # Step 3: Fix Rick Astley titles
                await self.fix_rick_astley_titles(corrupted_entries)
            
            # Step 4: Remove duplicates
            await self.remove_duplicates()
            
            # Step 5: Fix platform fields
            await self.fix_platform_fields()
            
            # Step 6: Verify fixes
            await self.verify_fixes()
            
            print("\n🎉 Video corruption fix completed successfully!")
            print("\n📋 Next Steps:")
            print("  1. Run video reprocessing for entries with status='pending'")
            print("  2. Verify thumbnails are regenerated correctly")
            print("  3. Monitor for any new corruption issues")
            
        except Exception as e:
            print(f"❌ Fix process failed: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.disconnect()


async def main():
    fixer = VideoCorruptionFixer()
    
    try:
        await fixer.run_full_fix()
        
    except KeyboardInterrupt:
        print("\n⏹️  Fix process interrupted by user")
    except Exception as e:
        print(f"\n❌ Fix process failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())