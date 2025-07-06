from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.services.storage_manager import StorageManager
from app.core.exceptions import InternalServerError
from app.monitoring.metrics import STORAGE_USAGE_BYTES

router = APIRouter()

@router.get("/storage/metrics", response_model=Dict)
async def get_storage_metrics(storage_manager: StorageManager = Depends(StorageManager)):
    """Retrieve storage usage metrics."""
    try:
        metrics = await storage_manager.get_storage_metrics()
        
        # Update Prometheus metrics
        STORAGE_USAGE_BYTES.labels(type='total_disk_space').set(metrics['total_disk_space'])
        STORAGE_USAGE_BYTES.labels(type='used_disk_space').set(metrics['used_disk_space'])
        STORAGE_USAGE_BYTES.labels(type='free_disk_space').set(metrics['free_disk_space'])
        STORAGE_USAGE_BYTES.labels(type='managed_videos_size').set(metrics['managed_videos_size'])
        STORAGE_USAGE_BYTES.labels(type='managed_thumbnails_size').set(metrics['managed_thumbnails_size'])
        STORAGE_USAGE_BYTES.labels(type='managed_temp_size').set(metrics['managed_temp_size'])

        return metrics
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve storage metrics: {e}")
