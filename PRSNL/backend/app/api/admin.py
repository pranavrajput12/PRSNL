from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.services.storage_manager import StorageManager
from app.core.exceptions import InternalServerError

router = APIRouter()

@router.get("/storage/metrics", response_model=Dict)
async def get_storage_metrics(storage_manager: StorageManager = Depends(StorageManager)):
    """Retrieve storage usage metrics."""
    try:
        metrics = await storage_manager.get_storage_metrics()
        return metrics
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve storage metrics: {e}")
