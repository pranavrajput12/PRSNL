import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.database import get_db_pool
from app.middleware.rate_limit import mass_processing_limiter
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/embeddings/generate", status_code=status.HTTP_200_OK, dependencies=[Depends(mass_processing_limiter)])
async def generate_embeddings_for_existing_items(db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """Generates embeddings for existing items that do not have them."""
    try:
        await embedding_service.generate_embeddings_for_all_items()
        return {"message": "Embedding generation initiated for existing items."}
    except Exception as e:
        logger.error(f"Error generating embeddings for existing items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate embeddings: {e}")
