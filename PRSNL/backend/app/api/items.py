from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.core.exceptions import ItemNotFound, InternalServerError
from app.db.database import get_db_pool

router = APIRouter()

class ItemDetail(BaseModel):
    id: str
    url: Optional[str] = None
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    item_type: str = "article"
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = []

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None

@router.get("/items/{item_id}")
async def get_item_detail(item_id: str):
    """Retrieve details of a specific item by ID."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get item with tags
            query = """
                SELECT 
                    i.id,
                    i.title,
                    i.url,
                    i.summary,
                    i.processed_content as content,
                    i.item_type,
                    i.created_at,
                    i.updated_at,
                    COALESCE(
                        ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL),
                        ARRAY[]::TEXT[]
                    ) as tags
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.id = $1 AND i.status = 'completed'
                GROUP BY i.id
            """
            
            row = await conn.fetchrow(query, UUID(item_id))
            
            if not row:
                raise ItemNotFound(item_id)
            
            return {
                "id": str(row["id"]),
                "title": row["title"],
                "url": row["url"],
                "content": row["content"],
                "summary": row["summary"],
                "item_type": row["item_type"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
                "tags": row["tags"]
            }
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve item {item_id}: {e}")

@router.patch("/items/{item_id}")
async def update_item(item_id: str, item_update: ItemUpdate):
    """Update an existing item."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Check if item exists
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                    UUID(item_id)
                )
                
                if not exists:
                    raise ItemNotFound(item_id)
                
                # Update item fields if provided
                update_fields = []
                params = [UUID(item_id)]
                param_count = 2
                
                if item_update.title is not None:
                    update_fields.append(f"title = ${param_count}")
                    params.append(item_update.title)
                    param_count += 1
                
                if item_update.summary is not None:
                    update_fields.append(f"summary = ${param_count}")
                    params.append(item_update.summary)
                    param_count += 1
                
                if update_fields:
                    update_fields.append("updated_at = NOW()")
                    update_query = f"""
                        UPDATE items 
                        SET {', '.join(update_fields)}
                        WHERE id = $1
                    """
                    await conn.execute(update_query, *params)
                
                # Handle tags update
                if item_update.tags is not None:
                    # Delete existing tags
                    await conn.execute(
                        "DELETE FROM item_tags WHERE item_id = $1",
                        UUID(item_id)
                    )
                    
                    # Insert new tags
                    for tag_name in item_update.tags:
                        # Get or create tag
                        tag_id = await conn.fetchval(
                            """
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                            """,
                            tag_name.lower()
                        )
                        
                        # Link tag to item
                        await conn.execute(
                            "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)",
                            UUID(item_id), tag_id
                        )
                
                return {"message": "Item updated successfully", "id": item_id}
                
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to update item {item_id}: {e}")

@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Check if item exists
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                    UUID(item_id)
                )
                
                if not exists:
                    raise ItemNotFound(item_id)
                
                # Delete item tags first (due to foreign key)
                await conn.execute(
                    "DELETE FROM item_tags WHERE item_id = $1",
                    UUID(item_id)
                )
                
                # Delete the item
                await conn.execute(
                    "DELETE FROM items WHERE id = $1",
                    UUID(item_id)
                )
                
                return {"message": "Item deleted successfully", "id": item_id}
                
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to delete item {item_id}: {e}")
