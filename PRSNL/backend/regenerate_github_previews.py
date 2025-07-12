#!/usr/bin/env python3
"""
Regenerate GitHub Previews with README Content

This script updates all existing GitHub entries in the database to include
README content that was previously missing due to the placeholder token issue.
"""

import asyncio
import asyncpg
import json
import sys
import os
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.preview_service import preview_service

async def regenerate_github_previews():
    """Regenerate GitHub previews for all existing GitHub entries."""
    
    conn = await asyncpg.connect('postgresql://pronav@localhost:5433/prsnl')
    
    try:
        # Find all GitHub entries
        query = '''
        SELECT id, title, url, metadata->'rich_preview' as current_preview 
        FROM items 
        WHERE url LIKE '%github.com%' 
        AND metadata->'rich_preview' IS NOT NULL
        ORDER BY created_at DESC
        '''
        
        rows = await conn.fetch(query)
        total_entries = len(rows)
        
        print(f"Found {total_entries} GitHub entries to update")
        
        updated_count = 0
        failed_count = 0
        
        for i, row in enumerate(rows, 1):
            item_id = row['id']
            url = row['url']
            title = row['title']
            
            print(f"\n[{i}/{total_entries}] Processing: {title[:50]}...")
            print(f"URL: {url}")
            
            try:
                # Generate new preview with README content
                new_preview = await preview_service.generate_preview(url, 'development')
                
                if new_preview.get('type') == 'error':
                    print(f"  ❌ Error generating preview: {new_preview.get('error')}")
                    failed_count += 1
                    continue
                
                # Check if we got README content
                readme = new_preview.get('readme', {})
                readme_length = len(readme.get('full_content', '') or '')
                
                if readme_length > 0:
                    print(f"  ✅ Found README content ({readme_length} chars)")
                else:
                    print(f"  ⚠️  No README content found")
                
                # Update the database
                update_query = '''
                UPDATE items 
                SET metadata = jsonb_set(metadata, '{rich_preview}', $1::jsonb)
                WHERE id = $2
                '''
                
                await conn.execute(update_query, json.dumps(new_preview), item_id)
                updated_count += 1
                print(f"  💾 Updated database entry")
                
            except Exception as e:
                print(f"  ❌ Failed to process {url}: {e}")
                failed_count += 1
                continue
        
        print(f"\n🎉 Regeneration complete!")
        print(f"✅ Updated: {updated_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📊 Total: {total_entries}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🔄 Starting GitHub preview regeneration...")
    print("This will update all existing GitHub entries to include README content.")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(regenerate_github_previews())