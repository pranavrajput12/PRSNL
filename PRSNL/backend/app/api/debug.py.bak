"""
Debug endpoints for troubleshooting
"""
from fastapi import APIRouter, Depends
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db.database import get_db_connection

router = APIRouter()


@router.get("/debug/recent-items")
async def get_recent_items(
    hours: int = 1,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Get recently created items for debugging"""
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = """
        SELECT 
            id,
            title,
            url,
            status,
            item_type,
            created_at,
            updated_at,
            metadata
        FROM items
        WHERE created_at > $1
        ORDER BY created_at DESC
        LIMIT 20
    """
    
    rows = await db_connection.fetch(query, since)
    
    items = []
    for row in rows:
        items.append({
            "id": str(row["id"]),
            "title": row["title"],
            "url": row["url"],
            "status": row["status"],
            "item_type": row["item_type"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "metadata": row["metadata"]
        })
    
    # Also get status counts
    status_counts = await db_connection.fetch("""
        SELECT status, COUNT(*) as count
        FROM items
        WHERE created_at > $1
        GROUP BY status
    """, since)
    
    return {
        "recent_items": items,
        "total_count": len(items),
        "status_breakdown": {row["status"]: row["count"] for row in status_counts},
        "query_time": datetime.utcnow().isoformat(),
        "since": since.isoformat()
    }


@router.get("/debug/item-processing/{item_id}")
async def get_item_processing_status(
    item_id: str,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Get detailed processing status for a specific item"""
    
    query = """
        SELECT 
            id,
            title,
            url,
            status,
            item_type,
            created_at,
            updated_at,
            metadata,
            raw_content IS NOT NULL as has_raw_content,
            processed_content IS NOT NULL as has_processed_content,
            summary IS NOT NULL as has_summary,
            transcription IS NOT NULL as has_transcription,
            embedding IS NOT NULL as has_embedding,
            search_vector IS NOT NULL as has_search_vector
        FROM items
        WHERE id = $1::uuid
    """
    
    row = await db_connection.fetchrow(query, item_id)
    
    if not row:
        return {"error": "Item not found"}
    
    # Get associated tags
    tags = await db_connection.fetch("""
        SELECT t.name
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = $1::uuid
    """, item_id)
    
    return {
        "item": {
            "id": str(row["id"]),
            "title": row["title"],
            "url": row["url"],
            "status": row["status"],
            "item_type": row["item_type"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "metadata": row["metadata"],
            "processing_status": {
                "has_raw_content": row["has_raw_content"],
                "has_processed_content": row["has_processed_content"],
                "has_summary": row["has_summary"],
                "has_transcription": row["has_transcription"],
                "has_embedding": row["has_embedding"],
                "has_search_vector": row["has_search_vector"]
            },
            "tags": [tag["name"] for tag in tags]
        }
    }