from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.exceptions import ItemNotFound, InternalServerError

router = APIRouter()

class ItemDetail(BaseModel):
    id: str
    url: Optional[str] = None
    title: str
    content: Optional[str] = None

@router.get("/items/{item_id}", response_model=ItemDetail)
async def get_item_detail(item_id: str):
    """Retrieve details of a specific item by ID."""
    try:
        # Simulate item retrieval logic
        if item_id == "non_existent_id":
            raise ItemNotFound(item_id)
        return {"id": item_id, "title": "Sample Item Detail", "url": "http://example.com/detail", "content": "Detailed content of the item."}
    except ItemNotFound:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve item {item_id}: {e}")
