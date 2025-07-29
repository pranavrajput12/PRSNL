"""
Enhanced Knowledge Graph Service for PRSNL

This service extends the existing knowledge graph functionality with:
- Automatic relationship detection using embeddings
- Visual graph generation for D3.js
- Learning path calculation
- Semantic similarity analysis
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Item
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_graph import KnowledgeGraphService as BaseKnowledgeGraphService

logger = logging.getLogger(__name__)


class KnowledgeGraphService(BaseKnowledgeGraphService):
    """Enhanced Knowledge Graph Service with visualization support"""
    
    def __init__(self):
        super().__init__()
        self.embedding_service = EmbeddingService()
        
    async def generate_item_graph(
        self,
        db: AsyncSession,
        item_id: UUID,
        depth: int = 2,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Generate a graph centered on a specific item.
        
        Returns data formatted for D3.js visualization.
        """
        nodes = []
        edges = []
        visited = set()
        node_map = {}
        
        # Get the center item
        result = await db.execute(
            select(Item).where(Item.id == item_id)
        )
        center_item = result.scalar_one_or_none()
        
        if not center_item:
            raise ValueError(f"Item {item_id} not found")
        
        # Add center node
        center_node = self._create_graph_node(center_item, importance=2.0)
        nodes.append(center_node)
        node_map[str(center_item.id)] = center_node
        visited.add(str(center_item.id))
        
        # BFS to explore graph
        queue = deque([(str(center_item.id), 0)])
        
        while queue and len(nodes) < limit:
            current_id, current_depth = queue.popleft()
            
            if current_depth >= depth:
                continue
            
            # Find related items using embeddings
            related_items = await self._find_semantically_related(
                db, UUID(current_id), limit=10
            )
            
            for item, similarity in related_items:
                item_id_str = str(item.id)
                
                if item_id_str not in visited and len(nodes) < limit:
                    # Add node
                    node = self._create_graph_node(
                        item, 
                        importance=1.5 - (current_depth * 0.3)
                    )
                    nodes.append(node)
                    node_map[item_id_str] = node
                    visited.add(item_id_str)
                    
                    # Add edge
                    edge = {
                        "source": current_id,
                        "target": item_id_str,
                        "relationship": self._infer_relationship(similarity),
                        "strength": float(similarity),
                        "metadata": {
                            "similarity_score": float(similarity),
                            "depth": current_depth + 1
                        }
                    }
                    edges.append(edge)
                    
                    # Add to queue for next level
                    if current_depth + 1 < depth:
                        queue.append((item_id_str, current_depth + 1))
        
        # Add manual relationships if they exist
        manual_edges = await self._get_manual_relationships(db, visited)
        edges.extend(manual_edges)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "center_id": str(item_id),
                "depth": depth,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }
    
    async def generate_full_graph(
        self,
        db: AsyncSession,
        content_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate the complete knowledge graph with filters.
        """
        # Build query
        query = select(Item).where(Item.embed_vector_id.isnot(None))
        
        if content_type:
            query = query.where(Item.type == content_type)
        
        if tag:
            query = query.where(
                Item.metadata['tags'].astext.contains(tag)
            )
        
        query = query.limit(limit)
        
        # Get items
        result = await db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return {"nodes": [], "edges": [], "metadata": {}}
        
        # Create nodes
        nodes = []
        node_map = {}
        item_ids = []
        
        for item in items:
            node = self._create_graph_node(item)
            nodes.append(node)
            node_map[str(item.id)] = node
            item_ids.append(str(item.id))
        
        # Calculate similarities and create edges
        edges = []
        embeddings = await self._get_embeddings_batch(db, items)
        
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if embeddings[i] is not None and embeddings[j] is not None:
                    similarity = self._cosine_similarity(
                        embeddings[i], embeddings[j]
                    )
                    
                    if similarity >= similarity_threshold:
                        edge = {
                            "source": str(items[i].id),
                            "target": str(items[j].id),
                            "relationship": self._infer_relationship(similarity),
                            "strength": float(similarity),
                            "metadata": {
                                "similarity_score": float(similarity),
                                "auto_generated": True
                            }
                        }
                        edges.append(edge)
        
        # Add manual relationships
        manual_edges = await self._get_manual_relationships(db, set(item_ids))
        edges.extend(manual_edges)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filters": {
                    "content_type": content_type,
                    "tag": tag,
                    "similarity_threshold": similarity_threshold
                }
            }
        }
    
    async def find_learning_path(
        self,
        db: AsyncSession,
        start_id: UUID,
        end_id: UUID,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Find optimal learning path between two items using A* search.
        """
        # Get items and their embeddings
        start_item = await self._get_item_with_embedding(db, start_id)
        end_item = await self._get_item_with_embedding(db, end_id)
        
        if not start_item or not end_item:
            raise ValueError("Start or end item not found")
        
        if not start_item["embedding"] or not end_item["embedding"]:
            raise ValueError("Items must have embeddings for path finding")
        
        # A* search implementation
        path = await self._astar_search(
            db,
            start_item,
            end_item,
            max_steps
        )
        
        if not path:
            return {"path": [], "total_items": 0, "estimated_time": 0}
        
        # Create response
        path_nodes = []
        difficulty_progression = []
        estimated_time = 0
        
        for item in path:
            node = self._create_graph_node(item["item"])
            path_nodes.append(node)
            
            # Extract difficulty if available
            difficulty = item["item"].metadata.get("difficulty_level", 3)
            difficulty_progression.append(difficulty)
            
            # Estimate reading/learning time
            content_length = len(item["item"].content or "") + len(item["item"].summary or "")
            estimated_time += max(5, content_length // 200)  # ~200 wpm reading speed
        
        return {
            "path": path_nodes,
            "total_items": len(path),
            "estimated_time": estimated_time,
            "difficulty_progression": difficulty_progression
        }
    
    async def find_related_items(
        self,
        db: AsyncSession,
        item_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find items most related to the specified item.
        """
        related = await self._find_semantically_related(db, item_id, limit)
        
        results = []
        for item, similarity in related:
            results.append({
                "id": str(item.id),
                "title": item.title,
                "type": item.type,
                "summary": item.summary,
                "similarity_score": float(similarity),
                "relationship": self._infer_relationship(similarity)
            })
        
        return results
    
    async def analyze_item_connections(
        self,
        db: AsyncSession,
        item_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze an item to discover and create automatic relationships.
        """
        # Get the item
        result = await db.execute(
            select(Item).where(Item.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        # Find related items
        related = await self._find_semantically_related(db, item_id, limit=20)
        
        relationships = []
        for related_item, similarity in related:
            if similarity > 0.8:  # High similarity threshold for auto-creation
                rel_type = self._infer_relationship(similarity)
                
                # Create relationship in metadata
                await self.create_relationship(
                    source_id=str(item_id),
                    target_id=str(related_item.id),
                    relationship_type=rel_type,
                    confidence=float(similarity),
                    metadata={"auto_generated": True},
                    db=db
                )
                
                relationships.append({
                    "target_id": str(related_item.id),
                    "target_title": related_item.title,
                    "relationship": rel_type,
                    "confidence": float(similarity)
                })
        
        return {
            "count": len(relationships),
            "relationships": relationships
        }
    
    # Helper methods
    
    def _create_graph_node(self, item: Item, importance: float = 1.0) -> Dict[str, Any]:
        """Create a node object for graph visualization."""
        return {
            "id": str(item.id),
            "title": item.title,
            "type": item.type,
            "summary": item.summary,
            "tags": item.metadata.get("tags", []) if item.metadata else [],
            "importance": importance,
            "metadata": {
                "created_at": item.created_at.isoformat(),
                "difficulty_level": item.metadata.get("difficulty_level") if item.metadata else None,
                "programming_language": item.metadata.get("programming_language") if item.metadata else None
            }
        }
    
    def _infer_relationship(self, similarity: float) -> str:
        """Infer relationship type based on similarity score."""
        if similarity > 0.95:
            return "duplicate"
        elif similarity > 0.85:
            return "extends"
        elif similarity > 0.75:
            return "related"
        else:
            return "references"
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _find_semantically_related(
        self,
        db: AsyncSession,
        item_id: UUID,
        limit: int = 10
    ) -> List[Tuple[Item, float]]:
        """Find semantically related items using embeddings."""
        # Get the item and its embedding
        item_data = await self._get_item_with_embedding(db, item_id)
        
        if not item_data or not item_data["embedding"]:
            return []
        
        # Use pgvector for similarity search
        query = text("""
            SELECT i.*, e.embedding <=> :target_embedding AS distance
            FROM items i
            JOIN embeddings e ON i.embed_vector_id = e.id
            WHERE i.id != :item_id
                AND e.embedding IS NOT NULL
            ORDER BY distance
            LIMIT :limit
        """)
        
        result = await db.execute(
            query,
            {
                "target_embedding": item_data["embedding"].tolist(),
                "item_id": str(item_id),
                "limit": limit
            }
        )
        
        related = []
        for row in result:
            # Convert distance to similarity (1 - distance for normalized vectors)
            similarity = 1 - row.distance
            related.append((row, similarity))
        
        return related
    
    async def _get_item_with_embedding(
        self,
        db: AsyncSession,
        item_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get item with its embedding."""
        query = text("""
            SELECT i.*, e.embedding
            FROM items i
            LEFT JOIN embeddings e ON i.embed_vector_id = e.id
            WHERE i.id = :item_id
        """)
        
        result = await db.execute(query, {"item_id": str(item_id)})
        row = result.first()
        
        if not row:
            return None
        
        return {
            "item": row,
            "embedding": np.array(row.embedding) if row.embedding else None
        }
    
    async def _get_embeddings_batch(
        self,
        db: AsyncSession,
        items: List[Item]
    ) -> List[Optional[np.ndarray]]:
        """Get embeddings for multiple items."""
        embed_ids = [item.embed_vector_id for item in items if item.embed_vector_id]
        
        if not embed_ids:
            return [None] * len(items)
        
        query = text("""
            SELECT id, embedding
            FROM embeddings
            WHERE id = ANY(:ids)
        """)
        
        result = await db.execute(query, {"ids": embed_ids})
        
        # Create mapping
        embedding_map = {}
        for row in result:
            embedding_map[row.id] = np.array(row.embedding)
        
        # Return in order
        embeddings = []
        for item in items:
            if item.embed_vector_id and item.embed_vector_id in embedding_map:
                embeddings.append(embedding_map[item.embed_vector_id])
            else:
                embeddings.append(None)
        
        return embeddings
    
    async def _get_manual_relationships(
        self,
        db: AsyncSession,
        item_ids: Set[str]
    ) -> List[Dict[str, Any]]:
        """Get manually created relationships for a set of items."""
        if not item_ids:
            return []
        
        query = text("""
            SELECT id, metadata
            FROM items
            WHERE id = ANY(:ids)
                AND metadata ? 'relationships'
        """)
        
        result = await db.execute(query, {"ids": list(item_ids)})
        
        edges = []
        for row in result:
            relationships = row.metadata.get("relationships", [])
            for rel in relationships:
                if rel.get("target_id") in item_ids:
                    edges.append({
                        "source": str(row.id),
                        "target": rel["target_id"],
                        "relationship": rel["type"],
                        "strength": rel.get("confidence", 0.9),
                        "metadata": {
                            "manual": True,
                            "created_at": rel.get("created_at")
                        }
                    })
        
        return edges
    
    async def _astar_search(
        self,
        db: AsyncSession,
        start: Dict[str, Any],
        goal: Dict[str, Any],
        max_steps: int
    ) -> List[Dict[str, Any]]:
        """
        A* search implementation for finding learning paths.
        """
        import heapq
        
        # Heuristic: semantic similarity to goal
        def heuristic(item_embedding):
            return 1 - self._cosine_similarity(item_embedding, goal["embedding"])
        
        # Priority queue: (f_score, g_score, current_item, path)
        open_set = [(0, 0, start, [start])]
        visited = set()
        
        while open_set and len(visited) < max_steps * 10:  # Prevent infinite loops
            f_score, g_score, current, path = heapq.heappop(open_set)
            
            current_id = str(current["item"].id)
            
            if current_id == str(goal["item"].id):
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if len(path) >= max_steps:
                continue
            
            # Get neighbors
            neighbors = await self._find_semantically_related(
                db, UUID(current_id), limit=5
            )
            
            for neighbor_item, similarity in neighbors:
                neighbor_id = str(neighbor_item.id)
                
                if neighbor_id not in visited:
                    neighbor_data = await self._get_item_with_embedding(
                        db, neighbor_item.id
                    )
                    
                    if neighbor_data and neighbor_data["embedding"] is not None:
                        # Calculate new g_score (cost from start)
                        new_g_score = g_score + (1 - similarity)
                        
                        # Calculate h_score (heuristic to goal)
                        h_score = heuristic(neighbor_data["embedding"])
                        
                        # f_score = g_score + h_score
                        new_f_score = new_g_score + h_score
                        
                        new_path = path + [neighbor_data]
                        
                        heapq.heappush(
                            open_set,
                            (new_f_score, new_g_score, neighbor_data, new_path)
                        )
        
        return []  # No path found