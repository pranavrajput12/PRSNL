"""Items CRUD API endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import Item, ItemUpdate
from app.db.database import get_db_connection
import asyncpg
from uuid import UUID


router = APIRouter(prefix="/items", tags=["items"])


@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get a single item by ID
    """
    # Update access time and count
    await conn.execute("""
        UPDATE items 
        SET accessed_at = NOW(), access_count = access_count + 1
        WHERE id = $1
    """, item_id)
    
    # Fetch item with tags
    row = await conn.fetchrow("""
        SELECT 
            i.*,
            COALESCE(
                array_agg(t.name) FILTER (WHERE t.name IS NOT NULL), 
                '{}'::text[]
            ) as tags
        FROM items i
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.id = $1
        GROUP BY i.id
    """, item_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return Item(
        id=row['id'],
        url=row['url'],
        title=row['title'],
        summary=row['summary'],
        content=row['processed_content'],
        tags=row['tags'],
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        accessed_at=row['accessed_at'],
        access_count=row['access_count'],
        status=row['status']
    )


@router.patch("/{item_id}", response_model=Item)
async def update_item(
    item_id: UUID,
    item_update: ItemUpdate,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Update an item
    """
    # Build update query
    updates = []
    values = []
    param_count = 1
    
    if item_update.title is not None:
        updates.append(f"title = ${param_count}")
        values.append(item_update.title)
        param_count += 1
    
    if item_update.summary is not None:
        updates.append(f"summary = ${param_count}")
        values.append(item_update.summary)
        param_count += 1
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add updated_at
    updates.append("updated_at = NOW()")
    
    # Add item_id as last parameter
    values.append(item_id)
    
    # Execute update
    await conn.execute(f"""
        UPDATE items 
        SET {', '.join(updates)}
        WHERE id = ${param_count}
    """, *values)
    
    # Update tags if provided
    if item_update.tags is not None:
        # Remove existing tags
        await conn.execute("""
            DELETE FROM item_tags WHERE item_id = $1
        """, item_id)
        
        # Add new tags
        for tag in item_update.tags:
            await conn.execute("""
                INSERT INTO tags (name) VALUES ($1)
                ON CONFLICT (name) DO NOTHING
            """, tag)
            
            await conn.execute("""
                INSERT INTO item_tags (item_id, tag_id)
                SELECT $1, id FROM tags WHERE name = $2
            """, item_id, tag)
    
    # Return updated item
    return await get_item(item_id, conn)


@router.delete("/{item_id}")
async def delete_item(
    item_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Delete an item
    """
    result = await conn.execute("""
        DELETE FROM items WHERE id = $1
    """, item_id)
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}