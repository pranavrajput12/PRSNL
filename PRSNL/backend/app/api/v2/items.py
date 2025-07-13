"""V2 Items API with standard responses and optional auth"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.errors import ErrorDetail, NotFoundError, ValidationError
from app.core.responses import (
    create_paginated_response,
    create_response,
    ResponseMessage,
)
from app.db.database import get_db_pool
from app.middleware.auth import optional_auth
from app.models.schemas import Item, ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/items")
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Optional[dict] = Depends(optional_auth)
):
    """List items with standard pagination"""
    try:
        offset = (page - 1) * per_page
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM items WHERE status = 'completed'")
            
            # Get items
            rows = await conn.fetch("""
                SELECT i.*, array_agg(t.name) as tags
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.status = 'completed'
                GROUP BY i.id
                ORDER BY i.created_at DESC
                LIMIT $1 OFFSET $2
            """, per_page, offset)
            
            items = []
            for row in rows:
                item_dict = dict(row)
                item_dict['tags'] = [tag for tag in (item_dict.get('tags') or []) if tag]
                # Handle JSONB metadata field
                if 'metadata' in item_dict and isinstance(item_dict['metadata'], str):
                    import json
                    try:
                        item_dict['metadata'] = json.loads(item_dict['metadata'])
                    except:
                        item_dict['metadata'] = {}
                items.append(Item(**item_dict))
        
        # Convert items to JSON-serializable format
        items_data = []
        for item in items:
            item_data = item.dict()
            # Convert UUID to string
            item_data['id'] = str(item_data['id'])
            items_data.append(item_data)
        
        return create_paginated_response(
            data=items_data,
            total=total,
            page=page,
            per_page=per_page,
            message="Items retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing items: {e}", exc_info=True)
        raise

@router.get("/items/{item_id}")
async def get_item(
    item_id: UUID,
    user: Optional[dict] = Depends(optional_auth)
):
    """Get a specific item with standard response"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT i.*, array_agg(t.name) as tags
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.id = $1
                GROUP BY i.id
            """, item_id)
            
            if not row:
                raise NotFoundError("Item", str(item_id))
            
            item_dict = dict(row)
            item_dict['tags'] = [tag for tag in (item_dict.get('tags') or []) if tag]
            # Handle JSONB metadata field
            if 'metadata' in item_dict and isinstance(item_dict['metadata'], str):
                import json
                try:
                    item_dict['metadata'] = json.loads(item_dict['metadata'])
                except:
                    item_dict['metadata'] = {}
            item = Item(**item_dict)
            
            # Update access count
            await conn.execute("""
                UPDATE items 
                SET access_count = access_count + 1,
                    accessed_at = NOW()
                WHERE id = $1
            """, item_id)
        
        # Convert to JSON-serializable format
        item_data = item.dict()
        item_data['id'] = str(item_data['id'])
        
        return create_response(
            data=item_data,
            message="Item retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        raise

@router.post("/items")
async def create_item(
    item_data: ItemCreate,
    user: Optional[dict] = Depends(optional_auth)
):
    """Create a new item with standard response"""
    try:
        # Validate required fields
        if not item_data.title:
            raise ValidationError(
                "Validation failed",
                [ErrorDetail("title", "Title is required")]
            )
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Create item
            item_id = await conn.fetchval("""
                INSERT INTO items (url, title, summary, status)
                VALUES ($1, $2, $3, 'completed')
                RETURNING id
            """, str(item_data.url) if item_data.url else None, 
                item_data.title, 
                item_data.summary)
            
            # Add tags
            if item_data.tags:
                for tag_name in item_data.tags:
                    # Get or create tag
                    tag_id = await conn.fetchval("""
                        INSERT INTO tags (name)
                        VALUES ($1)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """, tag_name.lower())
                    
                    # Link tag to item
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, item_id, tag_id)
        
        return create_response(
            data={"id": str(item_id)},
            message=ResponseMessage.CREATED,
            status_code=201
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise

@router.patch("/items/{item_id}")
async def update_item(
    item_id: UUID,
    item_update: ItemUpdate,
    user: Optional[dict] = Depends(optional_auth)
):
    """Update an item with standard response"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if item exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                item_id
            )
            
            if not exists:
                raise NotFoundError("Item", str(item_id))
            
            # Update fields
            update_fields = []
            values = []
            param_count = 1
            
            if item_update.title is not None:
                update_fields.append(f"title = ${param_count}")
                values.append(item_update.title)
                param_count += 1
            
            if item_update.summary is not None:
                update_fields.append(f"summary = ${param_count}")
                values.append(item_update.summary)
                param_count += 1
            
            if update_fields:
                values.append(item_id)
                query = f"""
                    UPDATE items 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = ${param_count}
                """
                await conn.execute(query, *values)
            
            # Update tags if provided
            if item_update.tags is not None:
                # Remove existing tags
                await conn.execute(
                    "DELETE FROM item_tags WHERE item_id = $1",
                    item_id
                )
                
                # Add new tags
                for tag_name in item_update.tags:
                    tag_id = await conn.fetchval("""
                        INSERT INTO tags (name)
                        VALUES ($1)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """, tag_name.lower())
                    
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id)
                        VALUES ($1, $2)
                    """, item_id, tag_id)
        
        return create_response(
            data={"id": str(item_id)},
            message=ResponseMessage.UPDATED
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        raise

@router.delete("/items/{item_id}")
async def delete_item(
    item_id: UUID,
    user: Optional[dict] = Depends(optional_auth)
):
    """Delete an item with standard response"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if item exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                item_id
            )
            
            if not exists:
                raise NotFoundError("Item", str(item_id))
            
            # Delete item (cascades to item_tags)
            await conn.execute("DELETE FROM items WHERE id = $1", item_id)
        
        return create_response(
            data={"id": str(item_id)},
            message=ResponseMessage.DELETED
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise