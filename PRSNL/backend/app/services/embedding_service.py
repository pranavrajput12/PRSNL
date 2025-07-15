import asyncio
import logging
from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.services.http_client_factory import http_client_factory, ClientType

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.enabled = bool(settings.AZURE_OPENAI_API_KEY)
        self.http_client_factory = http_client_factory
        
        if not self.enabled:
            logger.warning("Azure OpenAI API key not configured. Embedding generation disabled.")
            
        self.cache = {}  # Simple in-memory cache

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using available AI provider"""
        if not text:
            return None
            
        if not self.enabled:
            return None

        # Check cache first
        if text in self.cache:
            return self.cache[text]

        # Use Azure OpenAI
        try:
            embedding = await self._azure_embedding(text)
            if embedding:
                self.cache[text] = embedding
                return embedding
        except Exception as e:
            logger.error(f"Azure OpenAI embedding failed: {str(e)}")

        # Placeholder for Sentence Transformers or other local models
        # if settings.USE_SENTENCE_TRANSFORMERS:
        #     try:
        #         embedding = await self._sentence_transformer_embedding(text)
        #         if embedding:
        #             self.cache[text] = embedding
        #             return embedding
        #     except Exception as e:
        #         logger.warning(f"Sentence Transformer embedding failed: {str(e)}")

        logger.error(f"Failed to generate embedding for text: {text[:50]}...")
        return None

    async def batch_generate(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently"""
        if not texts:
            return []
            
        if not self.enabled:
            return [None] * len(texts)

        # Try Azure OpenAI batch processing first
        if self.enabled:
            try:
                embeddings = await self._azure_batch_embedding(texts)
                if embeddings and len(embeddings) == len(texts):
                    # Cache results from batch operation
                    for i, text in enumerate(texts):
                        self.cache[text] = embeddings[i]
                    return embeddings
            except Exception as e:
                logger.warning(f"Azure OpenAI batch embedding failed, falling back to individual: {str(e)}")

        # Fallback to individual generation for each text (concurrently)
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)


    async def _azure_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Azure OpenAI for a single text"""
        async with self.http_client_factory.client_session(ClientType.AZURE_OPENAI) as client:
            response = await client.post(
                f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings?api-version={settings.AZURE_OPENAI_API_VERSION}",
                json={
                    "input": text
                }
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    async def _azure_batch_embedding(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings using Azure OpenAI for a list of texts"""
        if not texts:
            return []
        async with self.http_client_factory.client_session(ClientType.AZURE_OPENAI) as client:
            response = await client.post(
                f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings?api-version={settings.AZURE_OPENAI_API_VERSION}",
                json={
                    "input": texts
                }
            )
            response.raise_for_status()
            # The API returns embeddings in the same order as the input texts
            return [item["embedding"] for item in response.json()["data"]]

    # async def _sentence_transformer_embedding(self, text: str) -> Optional[List[float]]:
    #     """Generate embedding using a local Sentence Transformer model"""
    #     # This would require a separate process or a way to load the model
    #     # For now, it's a placeholder.
    #     # Example:
    #     # from sentence_transformers import SentenceTransformer
    #     # model = SentenceTransformer('all-MiniLM-L6-v2')
    #     # return model.encode(text).tolist()
    #     raise NotImplementedError("Sentence Transformer integration not yet implemented.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # HTTP client cleanup is handled by the factory
        pass

# Create singleton instance
embedding_service = EmbeddingService()