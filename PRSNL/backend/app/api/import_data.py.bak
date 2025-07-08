"""
Import API endpoints for PRSNL data
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
import csv
import io
# Security imports will be added when authentication is implemented
from app.db.database import get_db_connection
from app.core.capture_engine import CaptureEngine
from app.models.schemas import ItemCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/json")
async def import_json(
    file: UploadFile = File(...),
    merge_duplicates: bool = Form(False),
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
                        "SELECT id FROM items WHERE url = $1",
                        item_data['url']
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
                    # Create new item
                    await capture_engine.create_item(
                        url=item_create.url,
                        title=item_create.title,
                        type=item_create.type,
                        content=item_create.content,
                        summary=item_create.summary,
                        tags=item_create.tags,
                        metadata=item_data.get('metadata', {})
                    )
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
    conn=Depends(get_db_connection)
):
    """
    Import bookmarks from browser HTML export
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
        
        for bookmark in bookmarks:
            try:
                url = bookmark.get('href')
                title = bookmark.text.strip()
                
                if not url or url.startswith(('javascript:', 'place:')):
                    continue
                
                # Check for duplicates
                existing = await conn.fetchrow(
                    "SELECT id FROM items WHERE url = $1",
                    url
                )
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Get tags from folder structure if available
                tags = []
                parent = bookmark.parent
                while parent and parent.name != 'body':
                    if parent.name == 'dt' and parent.parent.name == 'dl':
                        # Look for folder name
                        prev_sibling = parent.find_previous_sibling('dt')
                        if prev_sibling and prev_sibling.h3:
                            tags.append(prev_sibling.h3.text.strip().lower())
                    parent = parent.parent
                
                # Create bookmark item
                if auto_fetch:
                    # Fetch full content
                    try:
                        await capture_engine.capture_url(url)
                        imported_count += 1
                    except Exception as fetch_error:
                        # Fall back to simple bookmark
                        await capture_engine.create_item(
                            url=url,
                            title=title,
                            type='bookmark',
                            content='',
                            tags=tags
                        )
                        imported_count += 1
                else:
                    # Just save as bookmark
                    await capture_engine.create_item(
                        url=url,
                        title=title,
                        type='bookmark',
                        content='',
                        tags=tags
                    )
                    imported_count += 1
                    
            except Exception as e:
                errors.append({
                    'bookmark': f"{title} ({url})",
                    'error': str(e)
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
                            await capture_engine.create_item(
                                url=None,
                                title=current_note['title'],
                                type='note',
                                content='\n'.join(current_note['content']),
                                tags=current_note['tags']
                            )
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
                    await capture_engine.create_item(
                        url=None,
                        title=current_note['title'],
                        type='note',
                        content='\n'.join(current_note['content']),
                        tags=current_note['tags']
                    )
                    imported_count += 1
                except Exception as e:
                    errors.append({
                        'note': current_note['title'],
                        'error': str(e)
                    })
        else:
            # Import as single note
            try:
                await capture_engine.create_item(
                    url=None,
                    title=file.filename or 'Imported Note',
                    type='note',
                    content=text_content,
                    tags=default_tags or ['imported', 'note']
                )
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