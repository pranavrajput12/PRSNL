from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.exceptions import InvalidInput, InternalServerError

router = APIRouter()

class CaptureRequest(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None

@router.post("/capture", status_code=status.HTTP_201_CREATED, response_model=dict)
async def capture_item(request: CaptureRequest):
    """Capture a new item (web page, note, etc.)."""
    if not request.url and not request.content:
        raise InvalidInput("Either URL or content must be provided.")
    try:
        # Simulate item capture logic
        item_id = "mock_item_id_123"
        return {"message": "Item captured successfully", "item_id": item_id}
    except Exception as e:
        raise InternalServerError(f"Failed to capture item: {e}")
