import os
import asyncio
from openai import AzureOpenAI, OpenAI
from typing import List, Optional
import logging
from app.db.database import get_db_pool
from app.config import settings
from app.services.ai_router import AIRouter, AITask, TaskType, AIProvider

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.ai_router = AIRouter()
        # Configure Azure OpenAI client
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            self.azure_client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.azure_deployment = "text-embedding-ada-002"  # Update with your deployment name
        else:
            self.azure_client = None
            
        # Fallback to standard OpenAI if available
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "text-embedding-ada-002"
        else:
            self.openai_client = None

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text, with fallback support"""
        text = text.replace("\n", " ")
        
        try:
            # Try Azure OpenAI first
            if self.azure_client:
                try:
                    response = await asyncio.to_thread(
                        self.azure_client.embeddings.create,
                        input=[text],
                        model=self.azure_deployment
                    )
                    return response.data[0].embedding
                except Exception as e:
                    logger.warning(f"Azure OpenAI embedding failed: {e}")
            
            # Fallback to standard OpenAI
            if self.openai_client:
                response = await asyncio.to_thread(
                    self.openai_client.embeddings.create,
                    input=[text],
                    model=self.model
                )
                return response.data[0].embedding
            
            logger.error("No embedding provider available")
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def get_embedding_sync(self, text: str) -> Optional[List[float]]:
        """Synchronous version for backward compatibility"""
        return asyncio.run(self.get_embedding(text))

    async def generate_embeddings_for_all_items(self):
        """Generate embeddings for all items that don't have them"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Fetch items that do not have embeddings
            items = await conn.fetch(
                "SELECT id, summary, content FROM items WHERE embedding IS NULL AND status = 'completed'"
            )
            
            generated = 0
            failed = 0
            
            for item in items:
                # Use summary if available, otherwise use content
                text = item['summary'] or item['content']
                if text:
                    embedding = await self.get_embedding(text)
                    if embedding:
                        await conn.execute(
                            "UPDATE items SET embedding = $1 WHERE id = $2",
                            embedding,
                            item['id']
                        )
                        generated += 1
                        logger.info(f"Generated embedding for item {item['id']}")
                    else:
                        failed += 1
                        logger.error(f"Failed to generate embedding for item {item['id']}")
            
            logger.info(f"Embedding generation complete: {generated} generated, {failed} failed")
            return {"generated": generated, "failed": failed}


# Create singleton instance
embedding_service = EmbeddingService()


