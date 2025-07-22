"""
Enhanced Embedding Manager Service - Multimodal Support
Handles creation, storage, and retrieval of embeddings for multiple modalities:
- Text embeddings (OpenAI)
- Image embeddings (CLIP)
- Multimodal embeddings (unified space)
- Cross-modal similarity search
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np

from app.db.database import get_db_pool
from app.services.unified_ai_service import unified_ai_service
from app.services.multimodal_embedding_service import multimodal_embedding_service
from app.utils.fingerprint import calculate_content_fingerprint

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Enhanced multimodal embedding manager with cross-modal capabilities"""
    
    def __init__(self):
        self.default_text_model = "text-embedding-ada-002"
        self.default_image_model = "clip-vit-base-patch32"
        self.default_multimodal_model = "clip-vit-base-patch32"
        self.default_version = "v1"
    
    async def create_embedding(
        self, 
        item_id: str,
        content: str,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        update_item: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Create and store embedding for an item.
        
        Args:
            item_id: UUID of the item
            content: Text content to embed
            model_name: Embedding model name (defaults to text-embedding-ada-002)
            model_version: Model version (defaults to v1)
            update_item: Whether to update item.embed_vector_id
            
        Returns:
            Dict with embedding details or None if failed
        """
        if not content:
            logger.warning(f"No content provided for item {item_id}")
            return None
        
        model_name = model_name or self.default_text_model
        model_version = model_version or self.default_version
        
        try:
            # Generate embedding using unified AI service
            embeddings = await unified_ai_service.generate_embeddings([content])
            if not embeddings:
                logger.error(f"Failed to generate embedding for item {item_id}")
                return None
            
            embedding_vector = embeddings[0]
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Check if embedding already exists for this item/model/type
                    existing = await conn.fetchrow("""
                        SELECT id FROM embeddings
                        WHERE item_id = $1 AND model_name = $2 AND model_version = $3 AND embedding_type = 'text'
                    """, UUID(item_id), model_name, model_version)
                    
                    if existing:
                        # Update existing embedding
                        embedding_id = existing['id']
                        await conn.execute("""
                            UPDATE embeddings
                            SET vector = $1, updated_at = NOW()
                            WHERE id = $2
                        """, embedding_vector, embedding_id)
                        logger.info(f"Updated embedding {embedding_id} for item {item_id}")
                    else:
                        # Insert new embedding
                        result = await conn.fetchrow("""
                            INSERT INTO embeddings (item_id, model_name, model_version, vector, embedding_type, content_source)
                            VALUES ($1, $2, $3, $4, 'text', 'direct_text')
                            RETURNING id, vector_norm
                        """, UUID(item_id), model_name, model_version, embedding_vector)
                        embedding_id = result['id']
                        logger.info(f"Created embedding {embedding_id} for item {item_id}")
                    
                    # Update item's embed_vector_id if requested
                    if update_item:
                        await conn.execute("""
                            UPDATE items
                            SET embed_vector_id = $1, updated_at = NOW()
                            WHERE id = $2
                        """, embedding_id, UUID(item_id))
                        
                        # Also update the legacy embedding column for backward compatibility
                        await conn.execute("""
                            UPDATE items
                            SET embedding = $1
                            WHERE id = $2
                        """, embedding_vector, UUID(item_id))
                    
                    return {
                        "embedding_id": str(embedding_id),
                        "item_id": item_id,
                        "model_name": model_name,
                        "model_version": model_version,
                        "vector_length": len(embedding_vector)
                    }
                    
        except Exception as e:
            logger.error(f"Error creating embedding for item {item_id}: {e}")
            return None
    
    async def create_image_embedding(
        self,
        item_id: str,
        image_path: Optional[str] = None,
        image_data: Optional[bytes] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create and store image embedding for an item.
        
        Args:
            item_id: UUID of the item
            image_path: Path to image file
            image_data: Raw image bytes
            model_name: CLIP model name
            model_version: Model version
            
        Returns:
            Dict with embedding details or None if failed
        """
        model_name = model_name or self.default_image_model
        model_version = model_version or self.default_version
        
        try:
            # Create image embedding using multimodal service
            embedding_data = await multimodal_embedding_service.create_image_embedding(
                image_path=image_path,
                image_data=image_data,
                model_name=model_name
            )
            
            # Store in database
            embedding_id = await multimodal_embedding_service.store_embedding(
                item_id, embedding_data, model_version
            )
            
            return {
                "embedding_id": embedding_id,
                "item_id": item_id,
                "model_name": model_name,
                "model_version": model_version,
                "embedding_type": "image",
                "vector_length": len(embedding_data['vector'])
            }
            
        except Exception as e:
            logger.error(f"Error creating image embedding for item {item_id}: {e}")
            return None
    
    async def create_multimodal_embedding(
        self,
        item_id: str,
        text: str,
        image_path: Optional[str] = None,
        image_data: Optional[bytes] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create and store multimodal embedding for an item.
        
        Args:
            item_id: UUID of the item
            text: Text content
            image_path: Optional image path
            image_data: Optional image bytes
            model_name: Multimodal model name
            model_version: Model version
            
        Returns:
            Dict with embedding details or None if failed
        """
        model_name = model_name or self.default_multimodal_model
        model_version = model_version or self.default_version
        
        try:
            # Create multimodal embedding
            embedding_data = await multimodal_embedding_service.create_multimodal_embedding(
                text=text,
                image_path=image_path,
                image_data=image_data,
                model_name=model_name
            )
            
            # Store in database
            embedding_id = await multimodal_embedding_service.store_embedding(
                item_id, embedding_data, model_version
            )
            
            return {
                "embedding_id": embedding_id,
                "item_id": item_id,
                "model_name": model_name,
                "model_version": model_version,
                "embedding_type": "multimodal",
                "vector_length": len(embedding_data['vector'])
            }
            
        except Exception as e:
            logger.error(f"Error creating multimodal embedding for item {item_id}: {e}")
            return None
    
    async def get_embedding(
        self, 
        item_id: str,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Get embedding vector for an item.
        
        Args:
            item_id: UUID of the item
            model_name: Specific model name (defaults to any)
            model_version: Specific model version (defaults to any)
            
        Returns:
            Numpy array of embedding vector or None
        """
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if model_name and model_version:
                # Get specific model embedding
                result = await conn.fetchrow("""
                    SELECT vector FROM embeddings
                    WHERE item_id = $1 AND model_name = $2 AND model_version = $3
                """, UUID(item_id), model_name, model_version)
            else:
                # Get item's current embedding via embed_vector_id
                result = await conn.fetchrow("""
                    SELECT e.vector 
                    FROM items i
                    JOIN embeddings e ON i.embed_vector_id = e.id
                    WHERE i.id = $1
                """, UUID(item_id))
            
            if result and result['vector']:
                return np.array(result['vector'])
            return None
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.5,
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar items using embedding similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            model_name: Filter by specific model
            
        Returns:
            List of similar items with similarity scores
        """
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if model_name:
                # Search within specific model embeddings
                results = await conn.fetch("""
                    SELECT 
                        i.id,
                        i.title,
                        i.url,
                        i.summary,
                        i.created_at,
                        1 - (e.vector <=> $1::vector) as similarity
                    FROM embeddings e
                    JOIN items i ON e.item_id = i.id
                    WHERE e.model_name = $2
                    AND 1 - (e.vector <=> $1::vector) > $3
                    ORDER BY similarity DESC
                    LIMIT $4
                """, query_embedding, model_name, threshold, limit)
            else:
                # Search using items' current embeddings
                results = await conn.fetch("""
                    SELECT 
                        i.id,
                        i.title,
                        i.url,
                        i.summary,
                        i.created_at,
                        1 - (e.vector <=> $1::vector) as similarity
                    FROM items i
                    JOIN embeddings e ON i.embed_vector_id = e.id
                    WHERE 1 - (e.vector <=> $1::vector) > $2
                    ORDER BY similarity DESC
                    LIMIT $3
                """, query_embedding, threshold, limit)
            
            return [
                {
                    "id": str(row['id']),
                    "title": row['title'],
                    "url": row['url'],
                    "summary": row['summary'],
                    "created_at": row['created_at'].isoformat(),
                    "similarity": float(row['similarity'])
                }
                for row in results
            ]
    
    async def cross_modal_search(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None,
        query_image_data: Optional[bytes] = None,
        search_types: List[str] = ['text', 'image', 'multimodal'],
        limit: int = 20,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Perform cross-modal search across all embedding types.
        
        Args:
            query_text: Text query
            query_image_path: Image file path for query
            query_image_data: Image bytes for query
            search_types: Types of embeddings to search
            limit: Maximum results
            threshold: Similarity threshold
            
        Returns:
            Cross-modal search results
        """
        try:
            results = await multimodal_embedding_service.unified_search(
                query_text=query_text,
                query_image_path=query_image_path,
                query_image_data=query_image_data,
                search_types=search_types,
                limit=limit,
                threshold=threshold
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in cross-modal search: {e}")
            return []
    
    async def get_multimodal_stats(self) -> Dict[str, Any]:
        """Get statistics about multimodal embeddings."""
        try:
            return await multimodal_embedding_service.get_embeddings_stats()
        except Exception as e:
            logger.error(f"Error getting multimodal stats: {e}")
            return {}
    
    async def migrate_legacy_embeddings(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Migrate embeddings from items.embedding to embeddings table.
        
        Args:
            batch_size: Number of items to process at once
            
        Returns:
            Dict with migration statistics
        """
        pool = await get_db_pool()
        migrated = 0
        skipped = 0
        failed = 0
        
        async with pool.acquire() as conn:
            # Get items with embeddings but no embed_vector_id
            while True:
                items = await conn.fetch("""
                    SELECT id, embedding
                    FROM items
                    WHERE embedding IS NOT NULL 
                    AND embed_vector_id IS NULL
                    LIMIT $1
                """, batch_size)
                
                if not items:
                    break
                
                for item in items:
                    try:
                        # Insert into embeddings table
                        result = await conn.fetchrow("""
                            INSERT INTO embeddings (item_id, model_name, model_version, vector)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (item_id, model_name, model_version) 
                            DO UPDATE SET vector = EXCLUDED.vector, updated_at = NOW()
                            RETURNING id
                        """, item['id'], self.default_model, self.default_version, item['embedding'])
                        
                        # Update item with embed_vector_id
                        await conn.execute("""
                            UPDATE items
                            SET embed_vector_id = $1
                            WHERE id = $2
                        """, result['id'], item['id'])
                        
                        migrated += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate embedding for item {item['id']}: {e}")
                        failed += 1
                
                logger.info(f"Migrated batch: {migrated} successful, {failed} failed")
        
        return {
            "migrated": migrated,
            "skipped": skipped,
            "failed": failed
        }
    
    async def update_all_embeddings(self, model_name: Optional[str] = None) -> Dict[str, int]:
        """
        Update embeddings for all items, using content fingerprint to detect changes.
        
        Args:
            model_name: Model to use for embedding generation
            
        Returns:
            Dict with update statistics
        """
        pool = await get_db_pool()
        updated = 0
        unchanged = 0
        failed = 0
        
        model_name = model_name or self.default_text_model
        
        async with pool.acquire() as conn:
            # Get all items
            items = await conn.fetch("""
                SELECT id, title, raw_content, processed_content, content_fingerprint
                FROM items
                WHERE (raw_content IS NOT NULL OR processed_content IS NOT NULL)
                ORDER BY created_at DESC
            """)
            
            for item in items:
                try:
                    # Use processed content if available, otherwise raw content
                    content = item['processed_content'] or item['raw_content']
                    if not content:
                        continue
                    
                    # Calculate current fingerprint
                    current_fingerprint = calculate_content_fingerprint(content)
                    
                    # Check if content has changed
                    if item['content_fingerprint'] == current_fingerprint:
                        unchanged += 1
                        continue
                    
                    # Update fingerprint
                    await conn.execute("""
                        UPDATE items
                        SET content_fingerprint = $1
                        WHERE id = $2
                    """, current_fingerprint, item['id'])
                    
                    # Create new embedding
                    result = await self.create_embedding(
                        str(item['id']),
                        f"{item['title']} {content[:1000]}",
                        model_name=model_name
                    )
                    
                    if result:
                        updated += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to update embedding for item {item['id']}: {e}")
                    failed += 1
        
        return {
            "updated": updated,
            "unchanged": unchanged,
            "failed": failed
        }


# Create singleton instance
embedding_manager = EmbeddingManager()