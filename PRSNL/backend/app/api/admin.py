from fastapi import APIRouter, Depends, HTTPException, status
from app.services.storage_manager import StorageManager
from app.db.database import get_db_connection
import asyncpg
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/admin/storage/stats", summary="Get Storage Statistics", response_model=dict)
async def get_storage_stats():
    """Retrieves current storage usage statistics for media files."""
    try:
        storage_manager = StorageManager()
        stats = await storage_manager.get_storage_metrics()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve storage statistics: {e}")

@router.post("/admin/cleanup/orphaned", summary="Run Orphaned File Cleanup", response_model=dict)
async def run_orphaned_cleanup():
    """Triggers a cleanup process for orphaned media files (not referenced in DB)."""
    try:
        storage_manager = StorageManager()
        await storage_manager.cleanup_orphaned_files()
        return {"message": "Orphaned file cleanup initiated. Check logs for details.", "status": "success"}
    except Exception as e:
        logger.error(f"Error initiating orphaned file cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate orphaned file cleanup: {e}")

@router.post("/admin/cleanup/temp", summary="Run Temporary File Cleanup", response_model=dict)
async def run_temp_cleanup(older_than_hours: int = 24):
    """Triggers a cleanup process for temporary files older than specified hours."""
    try:
        storage_manager = StorageManager()
        await storage_manager.cleanup_temp_files(older_than_hours=older_than_hours)
        return {"message": f"Temporary file cleanup initiated for files older than {older_than_hours} hours. Check logs for details.", "status": "success"}
    except Exception as e:
        logger.error(f"Error initiating temporary file cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate temporary file cleanup: {e}")

@router.get("/admin/debug/items", summary="Debug Items", response_model=dict)
async def debug_items(db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Debug endpoint to check items and their statuses."""
    try:
        # Get count of items by status
        status_counts = await db_connection.fetch("""
            SELECT status, COUNT(*) as count
            FROM items
            GROUP BY status
            ORDER BY status
        """)
        
        # Get the last 10 items with their details
        recent_items = await db_connection.fetch("""
            SELECT id, title, url, status, item_type, created_at, updated_at
            FROM items
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        # Get total count
        total_count = await db_connection.fetchval("SELECT COUNT(*) FROM items")
        
        return {
            "total_items": total_count,
            "status_counts": [dict(row) for row in status_counts],
            "recent_items": [dict(row) for row in recent_items]
        }
    except Exception as e:
        logger.error(f"Error in debug items: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to debug items: {e}")

@router.post("/admin/test/create-item", summary="Create Test Item", response_model=dict)
async def create_test_item(db_connection: asyncpg.Connection = Depends(get_db_connection)):
    """Create a test item with completed status for debugging."""
    try:
        from uuid import uuid4
        from datetime import datetime
        
        item_id = uuid4()
        
        # Create a test item
        await db_connection.execute("""
            INSERT INTO items (
                id, title, url, summary, status, item_type, 
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8
            )
        """, 
            item_id,
            f"Test Item {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "https://example.com/test",
            "This is a test item created for debugging the timeline display.",
            "completed",
            "article",
            datetime.now(),
            datetime.now()
        )
        
        # Add some test tags
        tag_names = ["test", "debug", "sample"]
        for tag_name in tag_names:
            tag_id = await db_connection.fetchval("""
                INSERT INTO tags (name) VALUES ($1)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, tag_name)
            
            await db_connection.execute("""
                INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, item_id, tag_id)
        
        return {
            "message": "Test item created successfully",
            "item_id": str(item_id)
        }
    except Exception as e:
        logger.error(f"Error creating test item: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create test item: {e}")