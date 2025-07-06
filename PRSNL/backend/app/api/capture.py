"""Capture API endpoints"""
from fastapi import APIRouter, BackgroundTasks, Depends
from app.models.schemas import CaptureRequest, CaptureResponse
from app.core.capture_engine import CaptureEngine
from app.db.database import get_db_connection
import asyncpg
from uuid import uuid4


router = APIRouter(prefix="/capture", tags=["capture"])


@router.post("/", response_model=CaptureResponse)
async def capture_item(
    request: CaptureRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Quick capture endpoint - saves URL immediately and processes in background
    """
    # Generate item ID
    item_id = uuid4()
    
    # Quick save to database
    await conn.execute("""
        INSERT INTO items (id, url, title, status, created_at, updated_at)
        VALUES ($1, $2, $3, 'pending', NOW(), NOW())
    """, item_id, str(request.url), request.title or str(request.url))
    
    # Save tags if provided
    if request.tags:
        for tag in request.tags:
            # Insert tag if not exists
            await conn.execute("""
                INSERT INTO tags (name) VALUES ($1)
                ON CONFLICT (name) DO NOTHING
            """, tag)
            
            # Link tag to item
            await conn.execute("""
                INSERT INTO item_tags (item_id, tag_id)
                SELECT $1, id FROM tags WHERE name = $2
            """, item_id, tag)
    
    # Save highlight if provided
    if request.highlight:
        await conn.execute("""
            UPDATE items SET metadata = jsonb_set(
                COALESCE(metadata, '{}'), 
                '{highlight}', 
                to_jsonb($1::text)
            ) WHERE id = $2
        """, request.highlight, item_id)
    
    # Process in background
    capture_engine = CaptureEngine()
    background_tasks.add_task(
        capture_engine.process_item,
        item_id=item_id,
        url=str(request.url)
    )
    
    return CaptureResponse(
        id=item_id,
        status="queued",
        message="Capturing in background"
    )