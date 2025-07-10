"""
Knowledge Graph Service for PRSNL

This service builds and manages relationships between knowledge items:
- Automatic relationship detection
- Manual relationship creation
- Graph traversal and queries
- Related content discovery
- Knowledge path generation
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict, deque
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.db.models import Item
from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.llm_processor import LLMProcessor
from app.db.database import get_db

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_processor = LLMProcessor()
        
        # Relationship types
        self.RELATIONSHIP_TYPES = {
            "prerequisite": "Required before understanding this",
            "extends": "Builds upon this concept",
            "related": "Similar or connected topic",
            "contradicts": "Presents opposing view",
            "implements": "Practical application of concept",
            "references": "Cites or mentions this",
            "part_of": "Component of larger topic",
            "alternative": "Different approach to same problem"
        }
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two items
        
        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship
            confidence: Confidence score (0-1)
            metadata: Additional relationship metadata
            db: Database session
        
        Returns:
            Created relationship details
        """
        try:
            if relationship_type not in self.RELATIONSHIP_TYPES:
                raise ValueError(f"Invalid relationship type: {relationship_type}")
            
            # Check if both items exist
            source_result = await db.execute(
                select(Item).where(Item.id == source_id)
            )
            source_item = source_result.scalar_one_or_none()
            
            target_result = await db.execute(
                select(Item).where(Item.id == target_id)
            )
            target_item = target_result.scalar_one_or_none()
            
            if not source_item or not target_item:
                raise ValueError("Source or target item not found")
            
            # Create relationship in database
            # Using a JSON column to store relationships for now
            # In production, you'd want a separate relationship table
            relationships = source_item.metadata.get("relationships", []) if source_item.metadata else []
            
            # Check if relationship already exists
            existing = next(
                (r for r in relationships if r["target_id"] == target_id and r["type"] == relationship_type),
                None
            )
            
            if existing:
                # Update existing relationship
                existing["confidence"] = confidence
                existing["updated_at"] = datetime.utcnow().isoformat()
                if metadata:
                    existing["metadata"] = metadata
            else:
                # Create new relationship
                relationships.append({
                    "target_id": target_id,
                    "type": relationship_type,
                    "confidence": confidence,
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow().isoformat()
                })
            
            # Update source item metadata
            if not source_item.metadata:
                source_item.metadata = {}
            source_item.metadata["relationships"] = relationships
            
            await db.commit()
            
            return {
                "source_id": source_id,
                "target_id": target_id,
                "type": relationship_type,
                "confidence": confidence,
                "metadata": metadata,
                "source_title": source_item.title,
                "target_title": target_item.title
            }
            
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise
    
    async def discover_relationships(
        self,
        item_id: str,
        limit: int = 10,
        min_confidence: float = 0.7,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Discover potential relationships for an item using AI
        
        Args:
            item_id: Item ID to find relationships for
            limit: Maximum number of relationships to discover
            min_confidence: Minimum confidence threshold
            db: Database session
        
        Returns:
            List of discovered relationships
        """
        try:
            # Get the item
            result = await db.execute(
                select(Item).where(Item.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                raise ValueError(f"Item {item_id} not found")
            
            # Find similar items using embeddings
            similar_items = await self.embedding_service.find_similar(
                item_id=item_id,
                limit=limit * 2,  # Get more to filter
                db=db
            )
            
            if not similar_items:
                return []
            
            # Analyze relationships using AI
            relationships = []
            
            for similar in similar_items[:limit]:
                if similar["item_id"] == item_id:
                    continue
                
                # Get the similar item
                similar_result = await db.execute(
                    select(Item).where(Item.id == similar["item_id"])
                )
                similar_item = similar_result.scalar_one_or_none()
                
                if not similar_item:
                    continue
                
                # Use AI to determine relationship type
                prompt = f"""
                Analyze the relationship between these two items and determine the most appropriate relationship type.
                
                Item 1: {item.title}
                Summary: {item.summary or 'N/A'}
                Tags: {', '.join([t.name for t in item.tags]) if item.tags else 'N/A'}
                
                Item 2: {similar_item.title}
                Summary: {similar_item.summary or 'N/A'}
                Tags: {', '.join([t.name for t in similar_item.tags]) if similar_item.tags else 'N/A'}
                
                Relationship types:
                - prerequisite: Item 2 is required before understanding Item 1
                - extends: Item 1 builds upon Item 2
                - related: Similar or connected topics
                - contradicts: Opposing views or information
                - implements: Item 1 is a practical application of Item 2
                - references: Item 1 cites or mentions Item 2
                - part_of: Item 1 is a component of Item 2
                - alternative: Different approach to same problem
                
                Respond with JSON only:
                {{
                    "type": "relationship_type",
                    "confidence": 0.0-1.0,
                    "explanation": "brief explanation"
                }}
                """
                
                response = await self.llm_processor.process_with_llm(prompt, mode="extract")
                
                try:
                    result = json.loads(response)
                    
                    if result["confidence"] >= min_confidence:
                        relationships.append({
                            "source_id": item_id,
                            "target_id": similar["item_id"],
                            "type": result["type"],
                            "confidence": result["confidence"],
                            "similarity_score": similar["similarity"],
                            "explanation": result.get("explanation", ""),
                            "target_title": similar_item.title,
                            "target_summary": similar_item.summary
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response for relationship: {response}")
                    
                    # Fallback to similarity-based relationship
                    if similar["similarity"] >= 0.8:
                        relationships.append({
                            "source_id": item_id,
                            "target_id": similar["item_id"],
                            "type": "related",
                            "confidence": similar["similarity"],
                            "similarity_score": similar["similarity"],
                            "explanation": "High semantic similarity",
                            "target_title": similar_item.title,
                            "target_summary": similar_item.summary
                        })
            
            # Sort by confidence
            relationships.sort(key=lambda x: x["confidence"], reverse=True)
            
            return relationships[:limit]
            
        except Exception as e:
            logger.error(f"Error discovering relationships: {e}")
            raise
    
    async def get_knowledge_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
        db: AsyncSession = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Find learning paths between two items
        
        Args:
            start_id: Starting item ID
            end_id: Target item ID
            max_depth: Maximum path length
            db: Database session
        
        Returns:
            List of possible paths
        """
        try:
            # Use BFS to find paths
            queue = deque([(start_id, [start_id])])
            visited = set()
            paths = []
            
            while queue and len(paths) < 3:  # Find up to 3 paths
                current_id, path = queue.popleft()
                
                if len(path) > max_depth:
                    continue
                
                if current_id == end_id:
                    # Found a path
                    path_details = []
                    for i in range(len(path) - 1):
                        # Get relationship between consecutive items
                        source_result = await db.execute(
                            select(Item).where(Item.id == path[i])
                        )
                        source_item = source_result.scalar_one_or_none()
                        
                        target_result = await db.execute(
                            select(Item).where(Item.id == path[i + 1])
                        )
                        target_item = target_result.scalar_one_or_none()
                        
                        if source_item and target_item:
                            # Find relationship
                            relationships = source_item.metadata.get("relationships", []) if source_item.metadata else []
                            rel = next(
                                (r for r in relationships if r["target_id"] == path[i + 1]),
                                {"type": "related", "confidence": 0.5}
                            )
                            
                            path_details.append({
                                "source": {
                                    "id": source_item.id,
                                    "title": source_item.title
                                },
                                "target": {
                                    "id": target_item.id,
                                    "title": target_item.title
                                },
                                "relationship": rel["type"],
                                "confidence": rel.get("confidence", 0.5)
                            })
                    
                    paths.append(path_details)
                    continue
                
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # Get all relationships from current item
                result = await db.execute(
                    select(Item).where(Item.id == current_id)
                )
                item = result.scalar_one_or_none()
                
                if item and item.metadata:
                    relationships = item.metadata.get("relationships", [])
                    for rel in relationships:
                        if rel["target_id"] not in path:  # Avoid cycles
                            queue.append((rel["target_id"], path + [rel["target_id"]]))
            
            return paths
            
        except Exception as e:
            logger.error(f"Error finding knowledge path: {e}")
            raise
    
    async def get_item_graph(
        self,
        item_id: str,
        depth: int = 2,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Get the knowledge graph around an item
        
        Args:
            item_id: Center item ID
            depth: How many levels to expand
            db: Database session
        
        Returns:
            Graph structure with nodes and edges
        """
        try:
            nodes = {}
            edges = []
            visited = set()
            
            # BFS to build graph
            queue = deque([(item_id, 0)])
            
            while queue:
                current_id, current_depth = queue.popleft()
                
                if current_depth > depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # Get item details
                result = await db.execute(
                    select(Item).where(Item.id == current_id)
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    continue
                
                # Add node
                nodes[current_id] = {
                    "id": current_id,
                    "title": item.title,
                    "category": item.category,
                    "tags": [t.name for t in item.tags] if item.tags else [],
                    "depth": current_depth
                }
                
                # Get relationships
                if item.metadata:
                    relationships = item.metadata.get("relationships", [])
                    
                    for rel in relationships:
                        target_id = rel["target_id"]
                        
                        # Add edge
                        edges.append({
                            "source": current_id,
                            "target": target_id,
                            "type": rel["type"],
                            "confidence": rel.get("confidence", 1.0)
                        })
                        
                        # Add to queue if not at max depth
                        if current_depth < depth:
                            queue.append((target_id, current_depth + 1))
                
                # Also get reverse relationships (items pointing to this one)
                reverse_query = text("""
                    SELECT id, title, category, metadata
                    FROM items
                    WHERE metadata @> :relationship_json
                """)
                
                reverse_result = await db.execute(
                    reverse_query,
                    {"relationship_json": json.dumps({"relationships": [{"target_id": current_id}]})}
                )
                
                for row in reverse_result.all():
                    if row.id not in visited and current_depth < depth:
                        queue.append((row.id, current_depth + 1))
            
            return {
                "center_id": item_id,
                "nodes": list(nodes.values()),
                "edges": edges,
                "stats": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "max_depth_reached": max((n["depth"] for n in nodes.values()), default=0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error building item graph: {e}")
            raise
    
    async def suggest_learning_sequence(
        self,
        topic: str,
        skill_level: str = "beginner",
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest a learning sequence for a topic
        
        Args:
            topic: Topic to learn
            skill_level: Current skill level (beginner/intermediate/advanced)
            limit: Maximum items in sequence
            db: Database session
        
        Returns:
            Ordered list of items to study
        """
        try:
            # Search for items related to the topic
            search_query = text("""
                SELECT i.*, ts_rank(search_vector, plainto_tsquery(:topic)) as relevance
                FROM items i
                WHERE search_vector @@ plainto_tsquery(:topic)
                ORDER BY relevance DESC
                LIMIT :limit
            """)
            
            result = await db.execute(
                search_query,
                {"topic": topic, "limit": limit * 3}
            )
            
            items = result.fetchall()
            
            if not items:
                return []
            
            # Use AI to order items by difficulty and create sequence
            items_info = []
            for item in items:
                items_info.append({
                    "id": str(item.id),
                    "title": item.title,
                    "summary": item.summary or "",
                    "category": item.category or ""
                })
            
            prompt = f"""
            Create a learning sequence for someone who wants to learn about "{topic}" at {skill_level} level.
            
            Available items:
            {json.dumps(items_info, indent=2)}
            
            Order these items in a logical learning sequence, considering:
            1. Prerequisites should come before advanced topics
            2. Concepts before implementations
            3. Theory before practice
            4. Start with overview/introduction if available
            
            Return a JSON array of item IDs in the recommended order, with a brief explanation for each:
            [
                {{
                    "id": "item_id",
                    "order": 1,
                    "reason": "why this comes at this position"
                }}
            ]
            
            Include only the most relevant items (up to {limit}).
            """
            
            response = await self.llm_processor.process_with_llm(prompt, mode="extract")
            
            try:
                sequence = json.loads(response)
                
                # Enrich with full item details
                enriched_sequence = []
                for seq_item in sequence[:limit]:
                    item = next((i for i in items if str(i.id) == seq_item["id"]), None)
                    if item:
                        enriched_sequence.append({
                            "id": str(item.id),
                            "order": seq_item["order"],
                            "title": item.title,
                            "summary": item.summary,
                            "category": item.category,
                            "reason": seq_item["reason"],
                            "url": item.url
                        })
                
                return enriched_sequence
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response for learning sequence")
                # Fallback to relevance-based ordering
                return [
                    {
                        "id": str(item.id),
                        "order": idx + 1,
                        "title": item.title,
                        "summary": item.summary,
                        "category": item.category,
                        "reason": "Relevance-based ordering",
                        "url": item.url
                    }
                    for idx, item in enumerate(items[:limit])
                ]
                
        except Exception as e:
            logger.error(f"Error suggesting learning sequence: {e}")
            raise
    
    async def find_knowledge_gaps(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Find gaps in knowledge based on existing relationships
        
        Args:
            user_id: Filter by user
            category: Filter by category
            db: Database session
        
        Returns:
            List of suggested topics to explore
        """
        try:
            # Get items with many incoming but few outgoing relationships
            # These might be foundational topics the user hasn't explored
            
            query = select(Item)
            if user_id:
                query = query.where(Item.user_id == user_id)
            if category:
                query = query.where(Item.category == category)
            
            result = await db.execute(query)
            items = result.scalars().all()
            
            gaps = []
            
            for item in items:
                relationships = item.metadata.get("relationships", []) if item.metadata else []
                outgoing_count = len(relationships)
                
                # Count incoming relationships
                incoming_query = text("""
                    SELECT COUNT(*) as count
                    FROM items
                    WHERE metadata @> :relationship_json
                """)
                
                incoming_result = await db.execute(
                    incoming_query,
                    {"relationship_json": json.dumps({"relationships": [{"target_id": str(item.id)}]})}
                )
                incoming_count = incoming_result.scalar() or 0
                
                # Items with high incoming but low outgoing might indicate gaps
                if incoming_count > 2 and outgoing_count < 2:
                    gaps.append({
                        "id": str(item.id),
                        "title": item.title,
                        "category": item.category,
                        "incoming_relationships": incoming_count,
                        "outgoing_relationships": outgoing_count,
                        "gap_score": incoming_count / (outgoing_count + 1),
                        "suggestion": f"This appears to be a foundational topic. Consider exploring related concepts."
                    })
            
            # Sort by gap score
            gaps.sort(key=lambda x: x["gap_score"], reverse=True)
            
            return gaps[:10]
            
        except Exception as e:
            logger.error(f"Error finding knowledge gaps: {e}")
            raise