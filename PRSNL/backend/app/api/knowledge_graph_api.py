"""
Knowledge Graph API

Phase 2: API endpoints for distributed knowledge graph operations
using Celery background processing.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.workers.knowledge_graph_tasks import (
    build_knowledge_graph_distributed,
    semantic_search_distributed_task,
    entity_linking_task
)
from app.db.database import get_db_connection
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


class KnowledgeGraphBuildRequest(BaseModel):
    entity_ids: List[str]
    graph_name: Optional[str] = None
    enhancement_options: Optional[Dict[str, Any]] = None


class SemanticSearchRequest(BaseModel):
    query: str
    content_types: Optional[List[str]] = ["text", "code", "conversation", "entity"]
    similarity_threshold: Optional[float] = 0.7
    limit: Optional[int] = 20
    ranking_criteria: Optional[List[str]] = ["relevance", "recency", "completeness"]


class EntityLinkingRequest(BaseModel):
    content_id: str
    linking_options: Optional[Dict[str, Any]] = None


@router.post("/build")
async def build_knowledge_graph(
    request: KnowledgeGraphBuildRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Build knowledge graph from entities using distributed processing.
    
    Creates a comprehensive knowledge graph by analyzing entities and their
    relationships in parallel using Celery workers.
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate entity IDs exist
        async with get_db_connection() as db:
            existing_entities = await db.fetch("""
                SELECT id FROM knowledge_entities 
                WHERE user_id = $1 AND id = ANY($2::uuid[])
            """, UUID(user_id), [UUID(eid) for eid in request.entity_ids])
            
            if len(existing_entities) != len(request.entity_ids):
                missing_ids = set(request.entity_ids) - {str(e["id"]) for e in existing_entities}
                raise HTTPException(
                    status_code=400,
                    detail=f"Entity IDs not found: {list(missing_ids)}"
                )
        
        # Start distributed knowledge graph construction
        options = {
            "graph_name": request.graph_name,
            "graph_enhancement": request.enhancement_options or {}
        }
        
        task_result = build_knowledge_graph_distributed.delay(
            entity_ids=request.entity_ids,
            user_id=user_id,
            options=options
        )
        
        return {
            "status": "initiated",
            "task_id": task_result.id,
            "entities_count": len(request.entity_ids),
            "message": "Knowledge graph construction started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge graph build failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform semantic search across knowledge graph using distributed processing.
    
    Uses AI-powered semantic search with pgvector similarity and intelligent ranking.
    """
    try:
        user_id = current_user["user_id"]
        
        search_options = {
            "content_types": request.content_types,
            "similarity_threshold": request.similarity_threshold,
            "limit": request.limit,
            "ranking_criteria": request.ranking_criteria,
            "per_type_limit": max(5, request.limit // len(request.content_types))
        }
        
        # Start distributed semantic search
        task_result = semantic_search_distributed_task.delay(
            query=request.query,
            user_id=user_id,
            search_options=search_options
        )
        
        return {
            "status": "initiated",
            "task_id": task_result.id,
            "query": request.query,
            "search_options": search_options,
            "message": "Semantic search started in background"
        }
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link-entities")
async def link_entities(
    request: EntityLinkingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Link entities within content to existing knowledge graph.
    
    Uses AI to identify and link entities mentioned in content to existing
    knowledge graph entities.
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate content exists
        async with get_db_connection() as db:
            content = await db.fetchrow("""
                SELECT id FROM embeddings 
                WHERE id = $1 AND user_id = $2
            """, UUID(request.content_id), UUID(user_id))
            
            if not content:
                raise HTTPException(
                    status_code=404,
                    detail=f"Content {request.content_id} not found"
                )
        
        # Start entity linking
        task_result = entity_linking_task.delay(
            content_id=request.content_id,
            user_id=user_id,
            linking_options=request.linking_options or {}
        )
        
        return {
            "status": "initiated",
            "task_id": task_result.id,
            "content_id": request.content_id,
            "message": "Entity linking started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity linking failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphs")
async def list_knowledge_graphs(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all knowledge graphs for the current user."""
    try:
        user_id = current_user["user_id"]
        
        async with get_db_connection() as db:
            graphs = await db.fetch("""
                SELECT 
                    id,
                    graph_name,
                    entities_count,
                    relationships_count,
                    created_at,
                    enhancement_metadata
                FROM knowledge_graphs 
                WHERE user_id = $1 
                ORDER BY created_at DESC
                LIMIT 50
            """, UUID(user_id))
            
            return {
                "graphs": [dict(graph) for graph in graphs],
                "total_count": len(graphs)
            }
            
    except Exception as e:
        logger.error(f"Failed to list knowledge graphs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphs/{graph_id}")
async def get_knowledge_graph(
    graph_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific knowledge graph."""
    try:
        user_id = current_user["user_id"]
        
        async with get_db_connection() as db:
            graph = await db.fetchrow("""
                SELECT * FROM knowledge_graphs 
                WHERE id = $1 AND user_id = $2
            """, UUID(graph_id), UUID(user_id))
            
            if not graph:
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge graph {graph_id} not found"
                )
            
            # Get relationships for this graph
            relationships = await db.fetch("""
                SELECT * FROM knowledge_relationships 
                WHERE graph_id = $1
                ORDER BY confidence_score DESC
                LIMIT 100
            """, UUID(graph_id))
            
            graph_data = dict(graph)
            graph_data["relationships"] = [dict(rel) for rel in relationships]
            
            return graph_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/graphs/{graph_id}")
async def delete_knowledge_graph(
    graph_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a knowledge graph and all its relationships."""
    try:
        user_id = current_user["user_id"]
        
        async with get_db_connection() as db:
            # Verify ownership
            graph = await db.fetchrow("""
                SELECT id FROM knowledge_graphs 
                WHERE id = $1 AND user_id = $2
            """, UUID(graph_id), UUID(user_id))
            
            if not graph:
                raise HTTPException(
                    status_code=404,
                    detail=f"Knowledge graph {graph_id} not found"
                )
            
            # Delete relationships first (foreign key constraint)
            deleted_relationships = await db.execute("""
                DELETE FROM knowledge_relationships 
                WHERE graph_id = $1
            """, UUID(graph_id))
            
            # Delete the graph
            await db.execute("""
                DELETE FROM knowledge_graphs 
                WHERE id = $1
            """, UUID(graph_id))
            
            return {
                "message": "Knowledge graph deleted successfully",
                "graph_id": graph_id,
                "relationships_deleted": deleted_relationships
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/connections")
async def get_entity_connections(
    entity_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    max_depth: int = 2
):
    """Get connections for a specific entity across all knowledge graphs."""
    try:
        user_id = current_user["user_id"]
        
        async with get_db_connection() as db:
            # Verify entity exists
            entity = await db.fetchrow("""
                SELECT id FROM knowledge_entities 
                WHERE id = $1 AND user_id = $2
            """, UUID(entity_id), UUID(user_id))
            
            if not entity:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity {entity_id} not found"
                )
            
            # Get direct connections
            connections = await db.fetch("""
                SELECT 
                    r.*,
                    kg.graph_name,
                    e1.name as source_name,
                    e2.name as target_name
                FROM knowledge_relationships r
                JOIN knowledge_graphs kg ON r.graph_id = kg.id
                LEFT JOIN knowledge_entities e1 ON r.source_entity = e1.id::text
                LEFT JOIN knowledge_entities e2 ON r.target_entity = e2.id::text
                WHERE kg.user_id = $1 
                AND (r.source_entity = $2 OR r.target_entity = $2)
                ORDER BY r.confidence_score DESC
                LIMIT 50
            """, UUID(user_id), entity_id)
            
            return {
                "entity_id": entity_id,
                "connections": [dict(conn) for conn in connections],
                "connection_count": len(connections)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity connections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status of a knowledge graph task."""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info if hasattr(result, 'info') else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))