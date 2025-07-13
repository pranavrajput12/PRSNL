from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.exceptions import InternalServerError
from app.services.metrics_service import metrics_service

router = APIRouter()

@router.get("/metrics")
async def get_all_metrics() -> Dict[str, Any]:
    """
    Retrieves all collected performance metrics.
    """
    try:
        return metrics_service.get_metrics_summary()
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve metrics: {e}")
