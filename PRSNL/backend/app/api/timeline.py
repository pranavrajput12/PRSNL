from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.exceptions import InternalServerError

router = APIRouter()

class TimelineItem(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    created_at: datetime

@router.get("/timeline", response_model=List[TimelineItem])
async def get_timeline(limit: int = 20, offset: int = 0):
    """Retrieve a chronological list of captured items."""
    try:
        # Simulate timeline retrieval logic
        items = [
            {"id": "a", "title": "Timeline Item A", "url": "http://example.com/a", "created_at": datetime.now()},
            {"id": "b", "title": "Timeline Item B", "url": "http://example.com/b", "created_at": datetime.now()},
        ]
        return items
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve timeline: {e}")
