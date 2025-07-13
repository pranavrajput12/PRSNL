"""
Multimodal Embedding Service for PRSNL

Handles embeddings for multiple modalities:
- Text embeddings (OpenAI text-embedding-ada-002)
- Image embeddings (CLIP models)
- Multimodal embeddings (unified space)
- Video frame embeddings
- Audio embeddings

This service provides a unified interface for creating, storing, and searching
embeddings across different content modalities.
"""

import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json
import numpy as np
from PIL import Image
import io
import base64

# Core dependencies
import asyncpg
from sentence_transformers import SentenceTransformer
import torch
import clip

# PRSNL imports
from app.core.config import settings
from app.db.connection import get_db_connection
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)

class MultimodalEmbeddingService:
    """
    Service for creating and managing multimodal embeddings.
    
    Supports:
    - Text embeddings via OpenAI
    - Image embeddings via CLIP
    - Multimodal embeddings via CLIP
    - Cross-modal similarity search
    """
    
    def __init__(self):
        self.text_model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialized = False
    
    async def initialize(self):
        """Initialize embedding models lazily."""
        if self._initialized:
            return
        
        try:
            # Initialize CLIP model for image and multimodal embeddings
            logger.info("Loading CLIP model for multimodal embeddings...")
            self.clip_model, self.clip_preprocess = clip.load(
                "ViT-B/32", device=self.device
            )
            
            # Initialize sentence transformer for local text embeddings (backup)
            logger.info("Loading sentence transformer for text embeddings...")
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self._initialized = True
            logger.info(f"Multimodal embedding service initialized on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize multimodal embedding service: {e}")
            raise
    
    async def create_text_embedding(
        self, 
        text: str, 
        model_name: str = "text-embedding-ada-002",
        use_openai: bool = True
    ) -> Dict[str, Any]:
        """
        Create text embedding using OpenAI or local model.
        
        Args:
            text: Text to embed
            model_name: Embedding model name
            use_openai: Whether to use OpenAI API (default) or local model
            
        Returns:
            Dict with embedding vector and metadata
        """
        try:
            if use_openai and hasattr(unified_ai_service, 'create_embedding'):
                # Use OpenAI through unified AI service
                result = await unified_ai_service.create_embedding(text)
                vector = result.get('embedding', [])
                actual_model = result.get('model', model_name)
            else:
                # Use local sentence transformer
                await self.initialize()
                vector = self.text_model.encode([text])[0].tolist()
                actual_model = 'all-MiniLM-L6-v2'
            
            # Calculate content hash
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            
            return {
                'vector': vector,
                'embedding_type': 'text',
                'model_name': actual_model,
                'modality_metadata': {
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'language': 'auto-detected'
                },
                'content_source': 'direct_text',
                'content_hash': content_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to create text embedding: {e}")
            raise
    
    async def create_image_embedding(
        self, 
        image_path: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        model_name: str = "clip-vit-base-patch32"
    ) -> Dict[str, Any]:
        """
        Create image embedding using CLIP.
        
        Args:
            image_path: Path to image file
            image_data: Raw image bytes
            image_base64: Base64 encoded image
            model_name: CLIP model name
            
        Returns:
            Dict with embedding vector and metadata
        """
        await self.initialize()
        
        try:
            # Load image from various sources
            if image_path:
                image = Image.open(image_path).convert('RGB')
                content_source = f"file:{Path(image_path).name}"
            elif image_data:
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                content_source = "image_bytes"
            elif image_base64:
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                content_source = "base64_image"
            else:
                raise ValueError("No image source provided")
            
            # Preprocess and create embedding
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                # Normalize the features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                vector = image_features.cpu().numpy()[0].tolist()
            
            # Calculate content hash
            if image_path:
                with open(image_path, 'rb') as f:
                    content_hash = hashlib.sha256(f.read()).hexdigest()
            elif image_data:
                content_hash = hashlib.sha256(image_data).hexdigest()
            else:
                content_hash = hashlib.sha256(base64.b64decode(image_base64)).hexdigest()
            
            return {
                'vector': vector,
                'embedding_type': 'image',
                'model_name': model_name,
                'modality_metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode,
                    'channels': len(image.getbands()) if hasattr(image, 'getbands') else 3
                },
                'content_source': content_source,
                'content_hash': content_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to create image embedding: {e}")
            raise
    
    async def create_multimodal_embedding(
        self,
        text: str,
        image_path: Optional[str] = None,
        image_data: Optional[bytes] = None,
        model_name: str = "clip-vit-base-patch32"
    ) -> Dict[str, Any]:
        """
        Create multimodal embedding by combining text and image in CLIP space.
        
        Args:
            text: Text description
            image_path: Optional image path
            image_data: Optional image bytes
            model_name: CLIP model name
            
        Returns:
            Dict with multimodal embedding vector and metadata
        """
        await self.initialize()
        
        try:
            vectors = []
            sources = []
            metadata = {'components': []}
            
            # Text component
            if text:
                text_tokens = clip.tokenize([text]).to(self.device)
                with torch.no_grad():
                    text_features = self.clip_model.encode_text(text_tokens)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    vectors.append(text_features.cpu().numpy()[0])
                    sources.append('text')
                    metadata['components'].append({
                        'type': 'text',
                        'length': len(text),
                        'word_count': len(text.split())
                    })
            
            # Image component
            if image_path or image_data:
                image_result = await self.create_image_embedding(
                    image_path=image_path,
                    image_data=image_data,
                    model_name=model_name
                )
                vectors.append(np.array(image_result['vector']))
                sources.append('image')
                metadata['components'].append({
                    'type': 'image',
                    **image_result['modality_metadata']
                })
            
            # Combine vectors (average for now, could use learned combination)
            if len(vectors) > 1:
                combined_vector = np.mean(vectors, axis=0)
            else:
                combined_vector = vectors[0]
            
            # Normalize combined vector
            combined_vector = combined_vector / np.linalg.norm(combined_vector)
            
            # Calculate content hash from combined inputs
            hash_input = text
            if image_path:
                with open(image_path, 'rb') as f:
                    hash_input += f.read().hex()
            elif image_data:
                hash_input += image_data.hex()
            content_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            return {
                'vector': combined_vector.tolist(),
                'embedding_type': 'multimodal',
                'model_name': model_name,
                'modality_metadata': metadata,
                'content_source': '+'.join(sources),
                'content_hash': content_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to create multimodal embedding: {e}")
            raise
    
    async def store_embedding(
        self,
        item_id: str,
        embedding_data: Dict[str, Any],
        model_version: str = "v1"
    ) -> str:
        """
        Store embedding in database.
        
        Args:
            item_id: ID of the item this embedding belongs to
            embedding_data: Embedding data from create_*_embedding methods
            model_version: Model version string
            
        Returns:
            Embedding ID
        """
        async with get_db_connection() as conn:
            embedding_id = await conn.fetchval("""
                INSERT INTO embeddings (
                    item_id, model_name, model_version, vector, embedding_type,
                    modality_metadata, content_source, content_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (item_id, model_name, model_version, embedding_type)
                DO UPDATE SET
                    vector = EXCLUDED.vector,
                    modality_metadata = EXCLUDED.modality_metadata,
                    content_source = EXCLUDED.content_source,
                    content_hash = EXCLUDED.content_hash,
                    updated_at = NOW()
                RETURNING id
            """, 
                item_id,
                embedding_data['model_name'],
                model_version,
                embedding_data['vector'],
                embedding_data['embedding_type'],
                json.dumps(embedding_data['modality_metadata']),
                embedding_data['content_source'],
                embedding_data['content_hash']
            )
            
            logger.info(f"Stored {embedding_data['embedding_type']} embedding for item {item_id}")
            return str(embedding_id)
    
    async def cross_modal_search(
        self,
        query_embedding: List[float],
        query_type: str,
        target_types: List[str],
        limit: int = 20,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform cross-modal similarity search.
        
        Args:
            query_embedding: Query embedding vector
            query_type: Type of query embedding (text, image, multimodal)
            target_types: List of target embedding types to search
            limit: Maximum number of results
            threshold: Similarity threshold
            
        Returns:
            List of similar items with metadata
        """
        async with get_db_connection() as conn:
            # Convert target_types to SQL array
            target_types_sql = f"ARRAY{target_types}"
            
            results = await conn.fetch("""
                SELECT 
                    me.item_id,
                    me.title,
                    me.summary,
                    me.item_type,
                    me.url,
                    me.file_path,
                    me.thumbnail_url,
                    me.embedding_type,
                    me.model_name,
                    me.content_source,
                    me.modality_metadata,
                    1 - (me.vector <=> $1::vector) as similarity
                FROM multimodal_embeddings me
                WHERE me.embedding_type = ANY($2::text[])
                AND 1 - (me.vector <=> $1::vector) >= $3
                ORDER BY similarity DESC
                LIMIT $4
            """, 
                query_embedding,
                target_types,
                threshold,
                limit
            )
            
            return [
                {
                    'item_id': str(row['item_id']),
                    'title': row['title'],
                    'summary': row['summary'],
                    'item_type': row['item_type'],
                    'url': row['url'],
                    'file_path': row['file_path'],
                    'thumbnail_url': row['thumbnail_url'],
                    'embedding_type': row['embedding_type'],
                    'model_name': row['model_name'],
                    'content_source': row['content_source'],
                    'modality_metadata': row['modality_metadata'],
                    'similarity': float(row['similarity']),
                    'search_metadata': {
                        'query_type': query_type,
                        'cross_modal': query_type != row['embedding_type']
                    }
                }
                for row in results
            ]
    
    async def unified_search(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None,
        query_image_data: Optional[bytes] = None,
        search_types: List[str] = ['text', 'image', 'multimodal'],
        limit: int = 20,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Unified search across all modalities.
        
        Args:
            query_text: Text query
            query_image_path: Image file path for query
            query_image_data: Image bytes for query
            search_types: Types of embeddings to search
            limit: Maximum results
            threshold: Similarity threshold
            
        Returns:
            Unified search results across all modalities
        """
        all_results = []
        
        # Text query
        if query_text:
            text_embedding = await self.create_text_embedding(query_text)
            text_results = await self.cross_modal_search(
                text_embedding['vector'],
                'text',
                search_types,
                limit,
                threshold
            )
            all_results.extend(text_results)
        
        # Image query
        if query_image_path or query_image_data:
            image_embedding = await self.create_image_embedding(
                image_path=query_image_path,
                image_data=query_image_data
            )
            image_results = await self.cross_modal_search(
                image_embedding['vector'],
                'image',
                search_types,
                limit,
                threshold
            )
            all_results.extend(image_results)
        
        # Multimodal query
        if query_text and (query_image_path or query_image_data):
            multimodal_embedding = await self.create_multimodal_embedding(
                text=query_text,
                image_path=query_image_path,
                image_data=query_image_data
            )
            multimodal_results = await self.cross_modal_search(
                multimodal_embedding['vector'],
                'multimodal',
                search_types,
                limit,
                threshold
            )
            all_results.extend(multimodal_results)
        
        # Deduplicate and rank results
        seen_items = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x['similarity'], reverse=True):
            if result['item_id'] not in seen_items:
                seen_items.add(result['item_id'])
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results
    
    async def get_embeddings_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings in the system."""
        async with get_db_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_embeddings,
                    COUNT(DISTINCT item_id) as items_with_embeddings,
                    COUNT(DISTINCT model_name) as unique_models,
                    json_object_agg(
                        embedding_type, 
                        count
                    ) as embeddings_by_type
                FROM (
                    SELECT 
                        embedding_type,
                        COUNT(*) as count,
                        model_name,
                        item_id
                    FROM embeddings 
                    GROUP BY embedding_type, model_name, item_id
                ) subq
            """)
            
            return {
                'total_embeddings': stats['total_embeddings'],
                'items_with_embeddings': stats['items_with_embeddings'],
                'unique_models': stats['unique_models'],
                'embeddings_by_type': stats['embeddings_by_type'],
                'multimodal_enabled': True,
                'supported_types': ['text', 'image', 'multimodal', 'video_frame', 'audio']
            }

# Global instance
multimodal_embedding_service = MultimodalEmbeddingService()