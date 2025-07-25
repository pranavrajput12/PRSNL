"""
Import API endpoints for PRSNL data
"""
import asyncio
import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, HttpUrl

from app.core.capture_engine import CaptureEngine
from app.agents.content.bookmark_categorization_agent import BookmarkCategorizationAgent

# Authentication
from app.core.auth import get_current_user, User
from app.db.database import get_db_connection
from app.models.schemas import ItemCreate
from app.services.embedding_manager import embedding_manager
from app.utils.fingerprint import calculate_content_fingerprint

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["import"])


class BulkURLRequest(BaseModel):
    urls: List[HttpUrl]
    auto_fetch: bool = False
    tags: Optional[List[str]] = []


@router.get("/")
async def get_import_options():
    """
    Get available import options and endpoints
    """
    return {
        "status": "available",
        "description": "PRSNL Data Import Service",
        "endpoints": {
            "/json": {
                "method": "POST",
                "description": "Import items from PRSNL JSON export",
                "content_type": "multipart/form-data",
                "parameters": {
                    "file": "JSON file to import",
                    "merge_duplicates": "Whether to merge duplicate items (default: false)"
                }
            },
            "/bookmarks": {
                "method": "POST", 
                "description": "Import bookmarks from browser HTML export",
                "content_type": "multipart/form-data",
                "parameters": {
                    "file": "HTML bookmark file",
                    "auto_fetch": "Whether to fetch content (default: true)",
                    "batch_size": "Processing batch size (default: 10)"
                }
            },
            "/notes": {
                "method": "POST",
                "description": "Import notes from text files",
                "content_type": "multipart/form-data", 
                "parameters": {
                    "file": "Text/Markdown file",
                    "format": "File format: markdown or text (default: markdown)",
                    "default_tags": "Tags to apply to all notes"
                }
            },
            "/urls/bulk": {
                "method": "POST",
                "description": "Import multiple URLs in bulk",
                "content_type": "application/json",
                "parameters": {
                    "urls": "List of URLs to import",
                    "auto_fetch": "Whether to fetch content (default: false)",
                    "tags": "Tags to apply to all URLs"
                }
            }
        }
    }

@router.post("/json")
async def import_json(
    file: UploadFile = File(...),
    merge_duplicates: bool = Form(False),
    current_user: User = Depends(get_current_user),
    conn=Depends(get_db_connection)
):
    """
    Import items from PRSNL JSON export
    """
    try:
        # Read and parse JSON
        content = await file.read()
        data = json.loads(content)
        
        # Validate format
        if 'items' not in data:
            raise HTTPException(status_code=400, detail="Invalid JSON format: missing 'items' field")
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        capture_engine = CaptureEngine()
        
        for item_data in data['items']:
            try:
                # Check for duplicates
                existing = None
                if item_data.get('url'):
                    existing = await conn.fetchrow(
                        "SELECT id FROM items WHERE url = $1 AND user_id = $2",
                        item_data['url'],
                        str(current_user.id)
                    )
                
                if existing and not merge_duplicates:
                    skipped_count += 1
                    continue
                
                # Prepare item for import
                item_create = ItemCreate(
                    url=item_data.get('url'),
                    title=item_data.get('title', 'Imported Item'),
                    type=item_data.get('type', 'bookmark'),
                    content=item_data.get('content', ''),
                    summary=item_data.get('summary'),
                    tags=item_data.get('tags', [])
                )
                
                if existing and merge_duplicates:
                    # Update existing item
                    await _update_existing_item(conn, existing['id'], item_data)
                    imported_count += 1
                else:
                    # Create new item - insert directly then process
                    item_id = uuid4()
                    content_fingerprint = calculate_content_fingerprint(item_create.content or '')
                    
                    await conn.execute("""
                        INSERT INTO items (id, url, title, type, raw_content, summary, status, metadata, content_fingerprint, user_id)
                        VALUES ($1, $2, $3, $4, $5, $6, 'pending', $7::jsonb, $8, $9)
                    """, 
                        item_id,
                        str(item_create.url) if item_create.url else None,
                        item_create.title,
                        item_create.type,
                        item_create.content,
                        item_create.summary,
                        json.dumps(item_data.get('metadata', {})),
                        content_fingerprint,
                        str(current_user.id)
                    )
                    
                    # Create embedding if content exists
                    if item_create.content:
                        await embedding_manager.create_embedding(
                            str(item_id),
                            f"{item_create.title} {item_create.content}"[:2000],
                            update_item=True
                        )
                    
                    # Process tags
                    for tag_name in item_create.tags:
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                        """, tag_name.lower())
                        
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                    
                    # Process the item in background
                    asyncio.create_task(capture_engine.process_item(
                        item_id, 
                        str(item_create.url) if item_create.url else None, 
                        item_create.content
                    ))
                    imported_count += 1
                    
            except Exception as e:
                errors.append({
                    'item': item_data.get('title', 'Unknown'),
                    'error': str(e)
                })
        
        return {
            "status": "success",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors,
            "total": len(data['items'])
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Import JSON failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bookmarks")
async def import_bookmarks(
    file: UploadFile = File(...),
    auto_fetch: bool = Form(True),
    batch_size: int = Form(10),
    use_ai_categorization: bool = Form(True),
    current_user: User = Depends(get_current_user),
    conn=Depends(get_db_connection)
):
    """
    Import bookmarks from browser HTML export with AI-powered categorization
    """
    try:
        # Read HTML content
        content = await file.read()
        html_content = content.decode('utf-8')
        
        # Parse bookmarks using BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all bookmark links
        bookmarks = soup.find_all('a')
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        capture_engine = CaptureEngine()
        categorization_agent = BookmarkCategorizationAgent()
        
        # Use authenticated user ID
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        user_id = str(current_user.id)
        
        # Collect bookmark data for batch processing
        bookmark_data = []
        
        for bookmark in bookmarks:
            try:
                url = bookmark.get('href')
                title = bookmark.text.strip()
                
                if not url or url.startswith(('javascript:', 'place:')):
                    continue
                
                # Check for duplicates
                existing = await conn.fetchrow(
                    "SELECT id FROM items WHERE url = $1 AND user_id = $2",
                    url, user_id
                )
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Extract folder path from bookmark structure
                folder_path = ""
                folder_parts = []
                parent = bookmark.parent
                while parent and parent.name != 'body':
                    if parent.name == 'dt' and parent.parent.name == 'dl':
                        # Look for folder name
                        prev_sibling = parent.find_previous_sibling('dt')
                        if prev_sibling and prev_sibling.h3:
                            folder_parts.append(prev_sibling.h3.text.strip())
                    parent = parent.parent
                
                folder_path = " > ".join(reversed(folder_parts)) if folder_parts else ""
                
                # Collect bookmark for processing
                bookmark_data.append({
                    'url': url,
                    'title': title,
                    'folder_path': folder_path
                })
                
            except Exception as e:
                errors.append({
                    'bookmark': f"{title} ({url})",
                    'error': str(e)
                })
        
        logger.info(f"Collected {len(bookmark_data)} bookmarks for processing")
        
        # Process bookmarks in batches with AI categorization
        for i in range(0, len(bookmark_data), batch_size):
            batch = bookmark_data[i:i + batch_size]
            
            try:
                # Use AI categorization if enabled
                if use_ai_categorization:
                    logger.info(f"Processing batch {i//batch_size + 1} with AI categorization")
                    categorization_results = await categorization_agent.categorize_bulk_bookmarks(
                        batch, use_ai=True, batch_size=len(batch)
                    )
                else:
                    # Use rule-based categorization only
                    categorization_results = []
                    for bookmark_item in batch:
                        result = await categorization_agent.categorize_bookmark(
                            url=bookmark_item['url'],
                            title=bookmark_item['title'],
                            folder_path=bookmark_item['folder_path'],
                            use_ai=False
                        )
                        categorization_results.append(result)
                
                # Create items with categorization
                for bookmark_item, categorization in zip(batch, categorization_results):
                    try:
                        item_id = uuid4()
                        url = bookmark_item['url']
                        title = bookmark_item['title']
                        category = categorization.get('category', 'uncategorized')
                        ai_tags = categorization.get('tags', [])
                        
                        # Insert item with category
                        await conn.execute("""
                            INSERT INTO items (id, url, title, type, status, metadata, user_id)
                            VALUES ($1, $2, $3, 'bookmark', $4, $5, $6)
                        """, 
                        item_id, 
                        url, 
                        title, 
                        'pending' if auto_fetch else 'completed',
                        json.dumps({
                            'category': category,
                            'categorization_confidence': categorization.get('confidence', 0.0),
                            'categorization_method': categorization.get('method', 'unknown'),
                            'folder_path': bookmark_item['folder_path']
                        }),
                        user_id
                        )
                        
                        # Create and link tags
                        all_tags = set(ai_tags)
                        
                        # Add category as a tag if it's not already included
                        if category != 'uncategorized' and category not in all_tags:
                            all_tags.add(category)
                        
                        # Add folder-based tags
                        if bookmark_item['folder_path']:
                            folder_tags = [tag.strip().lower() for tag in bookmark_item['folder_path'].split('>')]
                            all_tags.update(folder_tags)
                        
                        # Insert tags and link to item
                        for tag_name in all_tags:
                            if tag_name and len(tag_name.strip()) > 0:
                                tag_id = await conn.fetchval("""
                                    INSERT INTO tags (name) VALUES ($1)
                                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                                    RETURNING id
                                """, tag_name.lower().strip())
                                
                                await conn.execute("""
                                    INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                                    ON CONFLICT DO NOTHING
                                """, item_id, tag_id)
                        
                        # Start background content fetching if enabled
                        if auto_fetch:
                            asyncio.create_task(capture_engine.process_item(item_id, url))
                        
                        imported_count += 1
                        
                    except Exception as item_error:
                        errors.append({
                            'bookmark': f"{title} ({url})",
                            'error': f"Failed to create item: {str(item_error)}"
                        })
                        
            except Exception as batch_error:
                logger.error(f"Batch processing failed: {batch_error}")
                for bookmark_item in batch:
                    errors.append({
                        'bookmark': f"{bookmark_item['title']} ({bookmark_item['url']})",
                        'error': f"Batch processing failed: {str(batch_error)}"
                    })
        
        return {
            "status": "success",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors,
            "total": len(bookmarks)
        }
        
    except Exception as e:
        logger.error(f"Import bookmarks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes")
async def import_notes(
    file: UploadFile = File(...),
    format: str = Form("markdown"),
    default_tags: Optional[List[str]] = Form(None),
    conn=Depends(get_db_connection)
):
    """
    Import notes from text files (Markdown, Plain text, etc.)
    """
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        imported_count = 0
        errors = []
        
        capture_engine = CaptureEngine()
        
        if format == "markdown":
            # Parse markdown and split by headers
            lines = text_content.split('\n')
            current_note = {
                'title': 'Imported Note',
                'content': [],
                'tags': default_tags or ['imported', 'note']
            }
            
            for line in lines:
                if line.startswith('# '):
                    # Save previous note if exists
                    if current_note['content']:
                        try:
                            item_id = uuid4()
                            await conn.execute("""
                                INSERT INTO items (id, title, type, raw_content, status)
                                VALUES ($1, $2, 'note', $3, 'completed')
                            """, item_id, current_note['title'], '\n'.join(current_note['content']))
                            
                            # Process tags
                            for tag_name in current_note['tags']:
                                tag_id = await conn.fetchval("""
                                    INSERT INTO tags (name) VALUES ($1)
                                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                                    RETURNING id
                                """, tag_name.lower())
                                
                                await conn.execute("""
                                    INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                                    ON CONFLICT DO NOTHING
                                """, item_id, tag_id)
                            imported_count += 1
                        except Exception as e:
                            errors.append({
                                'note': current_note['title'],
                                'error': str(e)
                            })
                    
                    # Start new note
                    current_note = {
                        'title': line[2:].strip(),
                        'content': [],
                        'tags': default_tags or ['imported', 'note']
                    }
                else:
                    current_note['content'].append(line)
            
            # Save last note
            if current_note['content']:
                try:
                    item_id = uuid4()
                    await conn.execute("""
                        INSERT INTO items (id, title, type, raw_content, status)
                        VALUES ($1, $2, 'note', $3, 'completed')
                    """, item_id, current_note['title'], '\n'.join(current_note['content']))
                    
                    # Process tags
                    for tag_name in current_note['tags']:
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                        """, tag_name.lower())
                        
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                    imported_count += 1
                except Exception as e:
                    errors.append({
                        'note': current_note['title'],
                        'error': str(e)
                    })
        else:
            # Import as single note
            try:
                item_id = uuid4()
                await conn.execute("""
                    INSERT INTO items (id, title, type, raw_content, status)
                    VALUES ($1, $2, 'note', $3, 'completed')
                """, item_id, file.filename or 'Imported Note', text_content)
                
                # Process tags
                for tag_name in (default_tags or ['imported', 'note']):
                    tag_id = await conn.fetchval("""
                        INSERT INTO tags (name) VALUES ($1)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """, tag_name.lower())
                    
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, item_id, tag_id)
                imported_count = 1
            except Exception as e:
                errors.append({
                    'note': file.filename,
                    'error': str(e)
                })
        
        return {
            "status": "success",
            "imported": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Import notes failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _update_existing_item(conn, item_id: UUID, new_data: Dict[str, Any]):
    """Update an existing item with new data"""
    # Update basic fields
    await conn.execute("""
        UPDATE items 
        SET title = COALESCE($2, title),
            summary = COALESCE($3, summary),
            content = COALESCE($4, content),
            metadata = COALESCE($5, metadata),
            updated_at = NOW()
        WHERE id = $1
    """, item_id, 
        new_data.get('title'),
        new_data.get('summary'),
        new_data.get('content'),
        json.dumps(new_data.get('metadata', {}))
    )
    
    # Update tags if provided
    if 'tags' in new_data and new_data['tags']:
        # Get or create tags
        for tag_name in new_data['tags']:
            tag = await conn.fetchrow(
                "INSERT INTO tags (name) VALUES ($1) ON CONFLICT (name) DO UPDATE SET name = $1 RETURNING id",
                tag_name.lower()
            )
            
            # Link tag to item
            await conn.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                item_id, tag['id']
            )


@router.post("/urls/bulk")
async def import_bulk_urls(
    request: BulkURLRequest,
    conn=Depends(get_db_connection)
):
    """
    Import multiple URLs in bulk - optimized for speed
    """
    try:
        imported_count = 0
        skipped_count = 0
        errors = []
        
        capture_engine = CaptureEngine()
        
        # Process URLs concurrently in batches
        batch_size = 20  # Process 20 URLs at a time
        
        async def process_url(url: str, tags: List[str]):
            try:
                # Check for duplicates
                existing = await conn.fetchrow(
                    "SELECT id FROM items WHERE url = $1",
                    str(url)
                )
                
                if existing:
                    return 'skipped', None
                
                # Quick import without fetching content
                if not request.auto_fetch:
                    item_id = uuid4()
                    await conn.execute("""
                        INSERT INTO items (id, url, title, type, status)
                        VALUES ($1, $2, $3, 'bookmark', 'completed')
                    """, item_id, str(url), str(url).split('/')[-1] or 'Bookmarked URL')
                    
                    # Process tags
                    for tag_name in tags:
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                        """, tag_name.lower())
                        
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                    return 'imported', None
                else:
                    # Fetch content
                    item_id = uuid4()
                    await conn.execute("""
                        INSERT INTO items (id, url, title, type, status)
                        VALUES ($1, $2, $3, 'bookmark', 'pending')
                    """, item_id, str(url), str(url).split('/')[-1] or 'Bookmarked URL')
                    
                    # Process tags
                    for tag_name in tags:
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                        """, tag_name.lower())
                        
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                    
                    # Process the URL content in background
                    asyncio.create_task(capture_engine.process_item(item_id, str(url)))
                    return 'imported', None
                    
            except Exception as e:
                return 'error', str(e)
        
        # Process in batches
        for i in range(0, len(request.urls), batch_size):
            batch = request.urls[i:i + batch_size]
            
            # Process batch concurrently
            results = await asyncio.gather(
                *[process_url(url, request.tags) for url in batch],
                return_exceptions=True
            )
            
            for j, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append({
                        'url': str(batch[j]),
                        'error': str(result)
                    })
                else:
                    status, error = result
                    if status == 'imported':
                        imported_count += 1
                    elif status == 'skipped':
                        skipped_count += 1
                    elif status == 'error':
                        errors.append({
                            'url': str(batch[j]),
                            'error': error
                        })
        
        return {
            "status": "success",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors,
            "total": len(request.urls)
        }
        
    except Exception as e:
        logger.error(f"Bulk URL import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))