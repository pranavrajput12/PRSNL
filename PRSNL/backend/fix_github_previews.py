#!/usr/bin/env python3
"""
Fix GitHub items by regenerating rich previews
"""
import asyncio
import asyncpg
import json
import sys

# Add the backend app to the path
sys.path.append('/Users/pronav/Personal Knowledge Base/PRSNL/backend')

from app.services.preview_service import preview_service

async def fix_github_previews():
    """Update existing GitHub items with rich previews"""
    
    # Connect to database
    conn = await asyncpg.connect("postgresql://pronav@localhost:5433/prsnl")
    
    try:
        # Get all GitHub items without rich previews
        github_items = await conn.fetch("""
            SELECT id, title, url, metadata
            FROM items 
            WHERE url ILIKE '%github.com%' 
            AND type = 'development'
            AND (metadata->'rich_preview' IS NULL OR metadata->'rich_preview'->>'type' = 'error')
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        print(f"Found {len(github_items)} GitHub items to update")
        
        for item in github_items:
            print(f"\n🔄 Updating: {item['title'][:60]}...")
            print(f"   URL: {item['url']}")
            
            try:
                # Generate rich preview
                preview_data = await preview_service.generate_preview(item['url'], 'development')
                
                if preview_data and preview_data.get('type') != 'error':
                    # Update metadata with rich preview
                    if isinstance(item['metadata'], str):
                        try:
                            current_metadata = json.loads(item['metadata'])
                        except:
                            current_metadata = {}
                    else:
                        current_metadata = item['metadata'] or {}
                    
                    current_metadata['rich_preview'] = preview_data
                    
                    # Update the item
                    await conn.execute("""
                        UPDATE items 
                        SET metadata = $1 
                        WHERE id = $2
                    """, json.dumps(current_metadata), item['id'])
                    
                    print(f"   ✅ Updated with {preview_data.get('type')} preview")
                    if preview_data.get('repo'):
                        print(f"   📊 {preview_data['stats'].get('stars', 0)} stars, {preview_data['stats'].get('forks', 0)} forks")
                else:
                    print(f"   ❌ Preview generation failed: {preview_data.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error updating item: {e}")
        
        print(f"\n✅ Finished updating GitHub previews")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_github_previews())