"""
Duplicate Detection API endpoints
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.services.duplicate_detection import duplicate_detection

router = APIRouter()


class DuplicateCheckRequest(BaseModel):
    url: Optional[str] = None
    title: str
    content: Optional[str] = None


class DuplicateItem(BaseModel):
    id: str
    title: str
    url: Optional[str]
    type: str  # exact_url, exact_content, semantic
    confidence: float
    created_at: str
    similarity: Optional[float] = None


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    duplicates: List[DuplicateItem]
    recommendation: str  # skip_duplicate, review_duplicate, possible_duplicate, no_duplicate


class DuplicateGroup(BaseModel):
    group_id: str
    items: List[Dict]
    count: int


class MergeDuplicatesRequest(BaseModel):
    keep_id: str
    duplicate_ids: List[str]


class MergeDuplicatesResponse(BaseModel):
    success: bool
    message: str
    merged_tags: Optional[List[str]] = None
    deleted_ids: Optional[List[str]] = None


@router.post("/duplicates/check", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest):
    """
    Check if content is a duplicate before saving
    """
    try:
        result = await duplicate_detection.check_duplicate(
            request.url,
            request.title,
            request.content
        )
        return DuplicateCheckResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for duplicates: {str(e)}"
        )


@router.get("/duplicates/find-all", response_model=List[DuplicateGroup])
async def find_all_duplicates(min_similarity: float = 0.85):
    """
    Find all duplicate groups in the database
    """
    try:
        groups = await duplicate_detection.find_all_duplicates(min_similarity)
        return [DuplicateGroup(**group) for group in groups]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find duplicates: {str(e)}"
        )


@router.post("/duplicates/merge", response_model=MergeDuplicatesResponse)
async def merge_duplicates(request: MergeDuplicatesRequest):
    """
    Merge duplicate items into one
    """
    try:
        result = await duplicate_detection.merge_duplicates(
            request.keep_id,
            request.duplicate_ids
        )
        return MergeDuplicatesResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge duplicates: {str(e)}"
        )