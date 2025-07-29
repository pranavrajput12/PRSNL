"""
Knowledge Graph API endpoints
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.database import get_db
from app.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])

# Additional response models for enhanced functionality
class GraphNode(BaseModel):
    id: str
    title: str
    type: str
    summary: Optional[str] = None
    tags: List[str] = []
    importance: float = 1.0
    metadata: dict = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    strength: float
    metadata: dict = {}

class VisualGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: dict = {}


# Request/Response Models
class CreateRelationshipRequest(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str = Field(
        ...,
        description="Type: prerequisite, extends, related, contradicts, implements, references, part_of, alternative"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Optional[dict] = None


class DiscoverRelationshipsRequest(BaseModel):
    item_id: str
    limit: int = Field(default=10, ge=1, le=50)
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class KnowledgePathRequest(BaseModel):
    start_id: str
    end_id: str
    max_depth: int = Field(default=5, ge=1, le=10)


class ItemGraphRequest(BaseModel):
    item_id: str
    depth: int = Field(default=2, ge=1, le=5)


class LearningSuggestionRequest(BaseModel):
    topic: str
    skill_level: str = Field(
        default="beginner",
        description="Skill level: beginner, intermediate, advanced"
    )
    limit: int = Field(default=10, ge=1, le=20)


class GraphResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None


# Initialize service
graph_service = KnowledgeGraphService()


@router.post("/relationships", response_model=GraphResponse)
async def create_relationship(
    request: CreateRelationshipRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a relationship between two knowledge items
    """
    try:
        result = await graph_service.create_relationship(
            source_id=request.source_id,
            target_id=request.target_id,
            relationship_type=request.relationship_type,
            confidence=request.confidence,
            metadata=request.metadata,
            db=db
        )
        
        return GraphResponse(
            success=True,
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(status_code=500, detail="Failed to create relationship")


@router.post("/discover", response_model=GraphResponse)
async def discover_relationships(
    request: DiscoverRelationshipsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Discover potential relationships for an item using AI
    """
    try:
        relationships = await graph_service.discover_relationships(
            item_id=request.item_id,
            limit=request.limit,
            min_confidence=request.min_confidence,
            db=db
        )
        
        return GraphResponse(
            success=True,
            data={"relationships": relationships}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error discovering relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to discover relationships")


@router.post("/path", response_model=GraphResponse)
async def find_knowledge_path(
    request: KnowledgePathRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Find learning paths between two knowledge items
    """
    try:
        paths = await graph_service.get_knowledge_path(
            start_id=request.start_id,
            end_id=request.end_id,
            max_depth=request.max_depth,
            db=db
        )
        
        return GraphResponse(
            success=True,
            data={
                "paths": paths,
                "path_count": len(paths)
            }
        )
    except Exception as e:
        logger.error(f"Error finding knowledge path: {e}")
        raise HTTPException(status_code=500, detail="Failed to find knowledge path")


@router.post("/graph", response_model=GraphResponse)
async def get_item_graph(
    request: ItemGraphRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the knowledge graph around a specific item
    """
    try:
        graph = await graph_service.get_item_graph(
            item_id=request.item_id,
            depth=request.depth,
            db=db
        )
        
        return GraphResponse(
            success=True,
            data=graph
        )
    except Exception as e:
        logger.error(f"Error getting item graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to get item graph")


@router.post("/learning-sequence", response_model=GraphResponse)
async def suggest_learning_sequence(
    request: LearningSuggestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a suggested learning sequence for a topic
    """
    try:
        if request.skill_level not in ["beginner", "intermediate", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid skill level. Use: beginner, intermediate, or advanced"
            )
        
        sequence = await graph_service.suggest_learning_sequence(
            topic=request.topic,
            skill_level=request.skill_level,
            limit=request.limit,
            db=db
        )
        
        return GraphResponse(
            success=True,
            data={
                "topic": request.topic,
                "skill_level": request.skill_level,
                "sequence": sequence
            }
        )
    except Exception as e:
        logger.error(f"Error suggesting learning sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest learning sequence")


@router.get("/gaps")
async def find_knowledge_gaps(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Find gaps in your knowledge graph
    """
    try:
        gaps = await graph_service.find_knowledge_gaps(
            user_id=current_user.id,
            category=category,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "gaps": gaps,
                "total": len(gaps)
            }
        }
    except Exception as e:
        logger.error(f"Error finding knowledge gaps: {e}")
        raise HTTPException(status_code=500, detail="Failed to find knowledge gaps")


@router.get("/relationships/{item_id}")
async def get_item_relationships(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all relationships for a specific item
    """
    try:
        from sqlalchemy import select

        from app.models.item import Item

        # Get the item
        result = await db.execute(
            select(Item).where(Item.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get outgoing relationships
        outgoing = item.metadata.get("relationships", []) if item.metadata else []
        
        # Get incoming relationships
        import json
        incoming_query = text("""
            SELECT id, title, category, metadata
            FROM items
            WHERE metadata @> :relationship_json
        """)
        
        incoming_result = await db.execute(
            incoming_query,
            {"relationship_json": json.dumps({"relationships": [{"target_id": item_id}]})}
        )
        
        incoming = []
        for row in incoming_result.all():
            relationships = row.metadata.get("relationships", []) if row.metadata else []
            for rel in relationships:
                if rel["target_id"] == item_id:
                    incoming.append({
                        "source_id": str(row.id),
                        "source_title": row.title,
                        "type": rel["type"],
                        "confidence": rel.get("confidence", 1.0),
                        "created_at": rel.get("created_at")
                    })
        
        return {
            "success": True,
            "data": {
                "item_id": item_id,
                "item_title": item.title,
                "outgoing_relationships": outgoing,
                "incoming_relationships": incoming,
                "total_relationships": len(outgoing) + len(incoming)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to get relationships")


@router.delete("/relationships")
async def delete_relationship(
    source_id: str = Query(..., description="Source item ID"),
    target_id: str = Query(..., description="Target item ID"),
    relationship_type: Optional[str] = Query(None, description="Specific relationship type to delete"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a relationship between two items
    """
    try:
        from sqlalchemy import select

        from app.models.item import Item

        # Get the source item
        result = await db.execute(
            select(Item).where(Item.id == source_id)
        )
        source_item = result.scalar_one_or_none()
        
        if not source_item:
            raise HTTPException(status_code=404, detail="Source item not found")
        
        # Get relationships
        relationships = source_item.metadata.get("relationships", []) if source_item.metadata else []
        
        # Filter out the relationship to delete
        if relationship_type:
            new_relationships = [
                r for r in relationships
                if not (r["target_id"] == target_id and r["type"] == relationship_type)
            ]
        else:
            new_relationships = [
                r for r in relationships
                if r["target_id"] != target_id
            ]
        
        if len(new_relationships) == len(relationships):
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        # Update metadata
        if not source_item.metadata:
            source_item.metadata = {}
        source_item.metadata["relationships"] = new_relationships
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Relationship deleted successfully",
            "deleted_count": len(relationships) - len(new_relationships)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting relationship: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete relationship")


# Import text from sqlalchemy
from sqlalchemy import text


# === NEW VISUAL GRAPH ENDPOINTS ===

@router.get("/visual/{item_id}", response_model=VisualGraphResponse)
async def get_visual_graph(
    item_id: str,
    depth: int = Query(2, ge=1, le=3, description="Graph depth"),
    limit: int = Query(50, ge=10, le=200, description="Max nodes"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get visual graph data centered on an item (for D3.js visualization).
    
    Returns nodes and edges formatted for frontend visualization.
    """
    try:
        graph_data = await graph_service.generate_item_graph(
            db=db,
            item_id=UUID(item_id),
            depth=depth,
            limit=limit
        )
        
        return VisualGraphResponse(**graph_data)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating visual graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate graph")


@router.get("/visual/full", response_model=VisualGraphResponse)
async def get_full_visual_graph(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(100, ge=10, le=500, description="Max nodes"),
    threshold: float = Query(0.7, ge=0.5, le=0.95, description="Similarity threshold"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the full knowledge graph with filters (for D3.js visualization).
    
    Returns complete graph data with automatic similarity-based edges.
    """
    try:
        graph_data = await graph_service.generate_full_graph(
            db=db,
            content_type=content_type,
            tag=tag,
            limit=limit,
            similarity_threshold=threshold
        )
        
        return VisualGraphResponse(**graph_data)
        
    except Exception as e:
        logger.error(f"Error generating full graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate graph")


@router.get("/path/{start_id}/{end_id}")
async def find_learning_path(
    start_id: str,
    end_id: str,
    max_steps: int = Query(10, ge=3, le=20, description="Max path length"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Find optimal learning path between two items.
    
    Uses A* search with semantic similarity as heuristic.
    """
    try:
        path_data = await graph_service.find_learning_path(
            db=db,
            start_id=UUID(start_id),
            end_id=UUID(end_id),
            max_steps=max_steps
        )
        
        if not path_data["path"]:
            raise HTTPException(
                status_code=404,
                detail="No learning path found between these items"
            )
        
        return path_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding learning path: {e}")
        raise HTTPException(status_code=500, detail="Failed to find path")


@router.get("/related/{item_id}")
async def get_semantically_related(
    item_id: str,
    limit: int = Query(10, ge=5, le=50, description="Number of items"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get semantically related items based on embeddings.
    
    Returns items with similarity scores.
    """
    try:
        related = await graph_service.find_related_items(
            db=db,
            item_id=UUID(item_id),
            limit=limit
        )
        
        return {
            "item_id": item_id,
            "related_items": related,
            "total": len(related)
        }
        
    except Exception as e:
        logger.error(f"Error finding related items: {e}")
        raise HTTPException(status_code=500, detail="Failed to find related items")


@router.post("/analyze/{item_id}")
async def analyze_connections(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Analyze item to discover and create automatic relationships.
    
    Finds highly similar items and creates relationships.
    """
    try:
        results = await graph_service.analyze_item_connections(
            db=db,
            item_id=UUID(item_id)
        )
        
        return {
            "success": True,
            "item_id": item_id,
            "relationships_created": results["count"],
            "relationships": results["relationships"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze connections")
