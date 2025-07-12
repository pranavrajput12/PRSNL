#!/usr/bin/env python3
"""Script to create test permalinks for existing items."""

import os
import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/prsnl'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.slug_generator import SmartSlugGenerator
from app.db.models import Item

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)


async def create_permalinks():
    session = Session()
    
    try:
        # Check current state
        print('=== CURRENT STATE ===')
        item_count = session.execute(text('SELECT COUNT(*) FROM items')).scalar()
        print(f'Total items: {item_count}')
        
        url_count = session.execute(text('SELECT COUNT(*) FROM content_urls')).scalar()
        print(f'Total content URLs: {url_count}')
        
        # Get items without URLs
        sample_items = session.execute(text('''
            SELECT id, title, type, url, platform, summary, raw_content
            FROM items i
            WHERE NOT EXISTS (
                SELECT 1 FROM content_urls c 
                WHERE c.content_id = i.id
            )
            ORDER BY created_at DESC
            LIMIT 20
        ''')).fetchall()
        
        print(f'\nItems without URLs: {len(sample_items)}')
        
        if sample_items:
            print('\n=== CREATING PERMALINKS ===')
            
            for item in sample_items:
                # Create mock Item object for the classifier
                mock_item = type('MockItem', (), {
                    'id': item.id,
                    'title': item.title,
                    'type': item.type,
                    'url': item.url,
                    'platform': item.platform,
                    'summary': item.summary,
                    'raw_content': item.raw_content
                })()
                
                # Classify and generate slug
                category = SmartSlugGenerator._classify_content_category(mock_item)
                base_slug = SmartSlugGenerator._generate_base_slug(item.title or 'untitled')
                
                # Check if slug exists
                existing = session.execute(text('''
                    SELECT COUNT(*) FROM content_urls 
                    WHERE category = :category AND slug = :slug
                '''), {'category': category, 'slug': base_slug}).scalar()
                
                if existing > 0:
                    # Add number suffix
                    counter = 1
                    while True:
                        new_slug = f"{base_slug}-{counter}"
                        exists = session.execute(text('''
                            SELECT COUNT(*) FROM content_urls 
                            WHERE category = :category AND slug = :slug
                        '''), {'category': category, 'slug': new_slug}).scalar()
                        
                        if exists == 0:
                            base_slug = new_slug
                            break
                        counter += 1
                        if counter > 10:
                            base_slug = f"{base_slug}-{item.id[:8]}"
                            break
                
                # Insert content URL
                try:
                    session.execute(text('''
                        INSERT INTO content_urls (content_id, slug, category, meta_title, meta_description)
                        VALUES (:content_id, :slug, :category, :meta_title, :meta_description)
                    '''), {
                        'content_id': item.id,
                        'slug': base_slug,
                        'category': category,
                        'meta_title': (item.title or 'Untitled')[:160],
                        'meta_description': f'{category.title()} content: {(item.title or "Untitled")[:250]}...'
                    })
                    session.commit()
                    print(f'✅ Created: /c/{category}/{base_slug} for "{(item.title or "Untitled")[:50]}..."')
                except Exception as e:
                    session.rollback()
                    print(f'❌ Failed to create URL for item {item.id}: {str(e)}')
        
        # Final count
        final_url_count = session.execute(text('SELECT COUNT(*) FROM content_urls')).scalar()
        print(f'\n=== FINAL STATE ===')
        print(f'Total content URLs: {final_url_count}')
        
        # Show some examples
        if final_url_count > 0:
            print('\n=== EXAMPLE PERMALINKS ===')
            examples = session.execute(text('''
                SELECT c.category, c.slug, i.title, c.views
                FROM content_urls c
                JOIN items i ON c.content_id = i.id
                ORDER BY c.created_at DESC
                LIMIT 10
            ''')).fetchall()
            
            for ex in examples:
                print(f'/c/{ex.category}/{ex.slug} - "{ex.title[:50]}..." (views: {ex.views})')
    
    finally:
        session.close()


if __name__ == '__main__':
    asyncio.run(create_permalinks())