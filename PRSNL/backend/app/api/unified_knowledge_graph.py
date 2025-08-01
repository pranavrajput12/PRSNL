"""
Unified Knowledge Graph API endpoints
Provides endpoints for accessing the unified entity and relationship system
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_optional
from app.db.database import get_db_pool
from app.services.entity_extraction_service import entity_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unified-knowledge-graph", tags=["unified-knowledge-graph"])


# Response Models for D3.js compatibility
class UnifiedGraphNode(BaseModel):
    id: str
    title: str
    type: str  # entity_type from unified_entities
    summary: Optional[str] = None
    content_type: Optional[str] = None
    confidence: float = 1.0
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = {}

class UnifiedGraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # relationship_type from unified_relationships
    strength: float = 1.0
    confidence: float = 1.0
    context: Optional[str] = None
    created_at: Optional[str] = None

class UnifiedGraphResponse(BaseModel):
    nodes: List[UnifiedGraphNode]
    edges: List[UnifiedGraphEdge]
    metadata: Dict[str, Any] = {}

class CreateRelationshipRequest(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence_score: float = 0.8
    strength: float = 1.0
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CreateRelationshipResponse(BaseModel):
    success: bool
    relationship_id: str
    message: str

class KnowledgePathRequest(BaseModel):
    start_entity_id: str
    end_entity_id: str
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum path depth")
    relationship_types: Optional[List[str]] = Field(default=None, description="Filter by relationship types")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")

class PathNode(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    confidence: float

class PathEdge(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float
    strength: float

class KnowledgePath(BaseModel):
    nodes: List[PathNode]
    edges: List[PathEdge]
    total_confidence: float
    path_length: int
    learning_difficulty: str  # 'easy', 'medium', 'hard'

class KnowledgePathResponse(BaseModel):
    paths: List[KnowledgePath]
    total_paths: int
    search_metadata: Dict[str, Any]

class RelationshipSuggestion(BaseModel):
    source_entity_id: str
    target_entity_id: str
    suggested_relationship: str
    confidence_score: float
    reasoning: str
    source_entity_name: str
    target_entity_name: str
    semantic_similarity: Optional[float] = None
    existing_connections: int = 0

class RelationshipSuggestionsRequest(BaseModel):
    entity_id: Optional[str] = Field(default=None, description="Get suggestions for specific entity")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum suggestions to return")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence threshold")
    relationship_types: Optional[List[str]] = Field(default=None, description="Filter by relationship types")
    exclude_existing: bool = Field(default=True, description="Exclude existing relationships")

class RelationshipSuggestionsResponse(BaseModel):
    suggestions: List[RelationshipSuggestion]
    total_suggestions: int
    analysis_metadata: Dict[str, Any]

class KnowledgeGap(BaseModel):
    gap_type: str  # 'missing_relationship', 'isolated_entity', 'weak_domain', 'conceptual_gap'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    affected_entities: List[str]
    suggested_actions: List[str]
    confidence_score: float
    domain: Optional[str] = None

class KnowledgeDomain(BaseModel):
    domain_name: str
    entity_count: int
    relationship_density: float
    completeness_score: float
    key_entities: List[str]
    missing_concepts: List[str]
    interconnectedness: float

class KnowledgeGapAnalysisRequest(BaseModel):
    analysis_depth: str = Field(default="standard", description="Analysis depth: 'quick', 'standard', 'comprehensive'")
    focus_domains: Optional[List[str]] = Field(default=None, description="Specific domains to analyze")
    min_severity: str = Field(default="medium", description="Minimum gap severity to include")
    include_suggestions: bool = Field(default=True, description="Include improvement suggestions")

class KnowledgeGapAnalysisResponse(BaseModel):
    gaps: List[KnowledgeGap]
    domains: List[KnowledgeDomain]
    overall_completeness: float
    analysis_summary: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]

class EntityCluster(BaseModel):
    cluster_id: str
    cluster_name: str
    entities: List[UnifiedGraphNode]
    central_entity: Optional[UnifiedGraphNode] = None
    cohesion_score: float
    cluster_type: str  # 'semantic', 'structural', 'temporal', 'mixed'
    description: str
    keywords: List[str] = []
    domain: Optional[str] = None

class SemanticClusteringRequest(BaseModel):
    min_cluster_size: int = Field(default=3, ge=2, le=20, description="Minimum entities per cluster")
    max_clusters: int = Field(default=10, ge=3, le=25, description="Maximum number of clusters")
    clustering_algorithm: str = Field(default="semantic", description="Algorithm: 'semantic', 'structural', 'hybrid'")
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum entity confidence")

class SemanticClusteringResponse(BaseModel):
    clusters: List[EntityCluster]
    total_entities_clustered: int
    clustering_metadata: Dict[str, Any]
    unclustered_entities: List[UnifiedGraphNode] = []


@router.get("/visual/full", response_model=UnifiedGraphResponse)
async def get_unified_visual_graph(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (text_entity, knowledge_concept)"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    limit: int = Query(100, ge=10, le=500, description="Max nodes"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user = Depends(get_current_user_optional)
):
    """
    Get the unified knowledge graph for D3.js visualization.
    
    Returns entities and relationships from the unified knowledge graph system.
    """
    try:
        logger.info(f"🧠 Fetching unified knowledge graph: entity_type={entity_type}, limit={limit}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Build entity query with filters
            entity_query = """
                SELECT 
                    ue.id,
                    ue.name as title,
                    ue.entity_type as type,
                    ue.description as summary,
                    ue.confidence_score as confidence,
                    ue.created_at,
                    ue.metadata,
                    i.content_type,
                    i.title as source_title,
                    i.url as source_url
                FROM unified_entities ue
                LEFT JOIN items i ON ue.source_content_id = i.id
                WHERE ue.confidence_score >= $1
            """
            
            params = [min_confidence]
            
            if entity_type:
                entity_query += " AND ue.entity_type = $" + str(len(params) + 1)
                params.append(entity_type)
            
            entity_query += " ORDER BY ue.confidence_score DESC, ue.created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            # Fetch entities
            entity_rows = await conn.fetch(entity_query, *params)
            
            # Build nodes
            nodes = []
            entity_ids = []
            
            for row in entity_rows:
                entity_ids.append(str(row['id']))
                
                # Parse metadata
                metadata = {}
                if row['metadata']:
                    try:
                        metadata = dict(row['metadata']) if isinstance(row['metadata'], dict) else {}
                    except:
                        metadata = {}
                
                # Add source information to metadata
                if row['source_title']:
                    metadata['source_title'] = row['source_title']
                if row['source_url']:
                    metadata['source_url'] = row['source_url']
                
                nodes.append(UnifiedGraphNode(
                    id=str(row['id']),
                    title=row['title'],
                    type=row['type'],  
                    summary=row['summary'],
                    content_type=row['content_type'],
                    confidence=float(row['confidence']),
                    created_at=row['created_at'].isoformat() if row['created_at'] else None,
                    metadata=metadata
                ))
            
            # Build relationship query
            if entity_ids:
                relationship_query = """
                    SELECT 
                        ur.id,
                        ur.source_entity_id,
                        ur.target_entity_id,
                        ur.relationship_type,
                        ur.confidence_score,
                        ur.strength,
                        ur.context,
                        ur.created_at,
                        ur.metadata
                    FROM unified_relationships ur
                    WHERE (ur.source_entity_id = ANY($1) OR ur.target_entity_id = ANY($1))
                    AND ur.confidence_score >= $2
                """
                
                rel_params = [entity_ids, min_confidence]
                
                if relationship_type:
                    relationship_query += " AND ur.relationship_type = $3"
                    rel_params.append(relationship_type)
                
                relationship_query += " ORDER BY ur.confidence_score DESC"
                
                # Fetch relationships
                relationship_rows = await conn.fetch(relationship_query, *rel_params)
                
                # Build edges (only include relationships between nodes we have)
                edges = []
                entity_id_set = set(entity_ids)
                
                for row in relationship_rows:
                    source_id = str(row['source_entity_id'])
                    target_id = str(row['target_entity_id'])
                    
                    # Only include relationships between entities we're showing
                    if source_id in entity_id_set and target_id in entity_id_set:
                        edges.append(UnifiedGraphEdge(
                            source=source_id,
                            target=target_id,
                            relationship=row['relationship_type'],
                            strength=float(row['strength']) if row['strength'] else 1.0,
                            confidence=float(row['confidence_score']),
                            context=row['context'],
                            created_at=row['created_at'].isoformat() if row['created_at'] else None
                        ))
            else:
                edges = []
            
            # Build metadata
            metadata = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filters": {
                    "entity_type": entity_type,
                    "relationship_type": relationship_type,
                    "min_confidence": min_confidence,
                    "limit": limit
                },
                "entity_types": {},
                "relationship_types": {}
            }
            
            # Count entity types
            for node in nodes:
                node_type = node.type
                metadata["entity_types"][node_type] = metadata["entity_types"].get(node_type, 0) + 1
            
            # Count relationship types
            for edge in edges:
                rel_type = edge.relationship
                metadata["relationship_types"][rel_type] = metadata["relationship_types"].get(rel_type, 0) + 1
            
            logger.info(f"✅ Generated unified knowledge graph: {len(nodes)} nodes, {len(edges)} edges")
            
            return UnifiedGraphResponse(
                nodes=nodes,
                edges=edges,
                metadata=metadata
            )
            
    except Exception as e:
        logger.error(f"❌ Error generating unified knowledge graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate unified knowledge graph: {str(e)}"
        )


@router.get("/visual/{item_id}", response_model=UnifiedGraphResponse)
async def get_unified_item_graph(
    item_id: UUID,
    depth: int = Query(2, ge=1, le=3, description="Relationship depth"),
    limit: int = Query(50, ge=10, le=200, description="Max nodes"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user = Depends(get_current_user_optional)
):
    """
    Get a knowledge graph centered around a specific content item.
    
    Returns entities and relationships connected to the specified item.
    """
    try:
        logger.info(f"🧠 Fetching item-centered knowledge graph for {item_id}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Get entities for the specific item
            center_entities = await conn.fetch("""
                SELECT 
                    ue.id,
                    ue.name as title,
                    ue.entity_type as type,
                    ue.description as summary,
                    ue.confidence_score as confidence,
                    ue.created_at,
                    ue.metadata,
                    i.content_type,
                    i.title as source_title,
                    i.url as source_url
                FROM unified_entities ue
                LEFT JOIN items i ON ue.source_content_id = i.id
                WHERE ue.source_content_id = $1
                AND ue.confidence_score >= $2
                ORDER BY ue.confidence_score DESC
            """, item_id, min_confidence)
            
            if not center_entities:
                return UnifiedGraphResponse(
                    nodes=[],
                    edges=[],
                    metadata={"message": f"No entities found for item {item_id}"}
                )
            
            # Collect all entity IDs to find related entities
            all_entity_ids = [str(row['id']) for row in center_entities]
            nodes = []
            
            # Add center entities to nodes
            for row in center_entities:
                metadata = {}
                if row['metadata']:
                    try:
                        metadata = dict(row['metadata']) if isinstance(row['metadata'], dict) else {}
                    except:
                        metadata = {}
                
                metadata['is_center'] = True
                if row['source_title']:
                    metadata['source_title'] = row['source_title']
                if row['source_url']:
                    metadata['source_url'] = row['source_url']
                
                nodes.append(UnifiedGraphNode(
                    id=str(row['id']),
                    title=row['title'],
                    type=row['type'],
                    summary=row['summary'],
                    content_type=row['content_type'],
                    confidence=float(row['confidence']),
                    created_at=row['created_at'].isoformat() if row['created_at'] else None,
                    metadata=metadata
                ))
            
            # Find related entities through relationships (up to specified depth)
            for current_depth in range(1, depth + 1):
                # Find entities connected to current entity set
                related_entities = await conn.fetch("""
                    SELECT DISTINCT
                        ue.id,
                        ue.name as title,
                        ue.entity_type as type,
                        ue.description as summary,
                        ue.confidence_score as confidence,
                        ue.created_at,
                        ue.metadata,
                        i.content_type,
                        i.title as source_title,
                        i.url as source_url
                    FROM unified_entities ue
                    LEFT JOIN items i ON ue.source_content_id = i.id
                    WHERE ue.id IN (
                        SELECT DISTINCT 
                            CASE 
                                WHEN ur.source_entity_id = ANY($1) THEN ur.target_entity_id
                                WHEN ur.target_entity_id = ANY($1) THEN ur.source_entity_id
                            END
                        FROM unified_relationships ur
                        WHERE (ur.source_entity_id = ANY($1) OR ur.target_entity_id = ANY($1))
                        AND ur.confidence_score >= $2
                    )
                    AND ue.id != ALL($1)
                    AND ue.confidence_score >= $2
                    ORDER BY ue.confidence_score DESC
                    LIMIT $3
                """, all_entity_ids, min_confidence, limit - len(nodes))
                
                # Add related entities to nodes
                for row in related_entities:
                    entity_id = str(row['id'])
                    if entity_id not in all_entity_ids:
                        all_entity_ids.append(entity_id)
                        
                        metadata = {}
                        if row['metadata']:
                            try:
                                metadata = dict(row['metadata']) if isinstance(row['metadata'], dict) else {}
                            except:
                                metadata = {}
                        
                        metadata['depth'] = current_depth
                        if row['source_title']:
                            metadata['source_title'] = row['source_title']
                        if row['source_url']:
                            metadata['source_url'] = row['source_url']
                        
                        nodes.append(UnifiedGraphNode(
                            id=entity_id,
                            title=row['title'],
                            type=row['type'],
                            summary=row['summary'],
                            content_type=row['content_type'],
                            confidence=float(row['confidence']),
                            created_at=row['created_at'].isoformat() if row['created_at'] else None,
                            metadata=metadata
                        ))
                
                # Stop if we've reached the limit
                if len(nodes) >= limit:
                    break
            
            # Get all relationships between the collected entities
            if all_entity_ids:
                relationship_rows = await conn.fetch("""
                    SELECT 
                        ur.id,
                        ur.source_entity_id,
                        ur.target_entity_id,
                        ur.relationship_type,
                        ur.confidence_score,
                        ur.strength,
                        ur.context,
                        ur.created_at
                    FROM unified_relationships ur
                    WHERE ur.source_entity_id = ANY($1) 
                    AND ur.target_entity_id = ANY($1)
                    AND ur.confidence_score >= $2
                    ORDER BY ur.confidence_score DESC
                """, all_entity_ids, min_confidence)
                
                edges = []
                for row in relationship_rows:
                    edges.append(UnifiedGraphEdge(
                        source=str(row['source_entity_id']),
                        target=str(row['target_entity_id']),
                        relationship=row['relationship_type'],
                        strength=float(row['strength']) if row['strength'] else 1.0,
                        confidence=float(row['confidence_score']),
                        context=row['context'],
                        created_at=row['created_at'].isoformat() if row['created_at'] else None
                    ))
            else:
                edges = []
            
            # Build metadata
            metadata = {
                "center_item_id": str(item_id),
                "depth": depth,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "entity_types": {},
                "relationship_types": {}
            }
            
            # Count types
            for node in nodes:
                node_type = node.type
                metadata["entity_types"][node_type] = metadata["entity_types"].get(node_type, 0) + 1
            
            for edge in edges:
                rel_type = edge.relationship
                metadata["relationship_types"][rel_type] = metadata["relationship_types"].get(rel_type, 0) + 1
            
            logger.info(f"✅ Generated item-centered knowledge graph: {len(nodes)} nodes, {len(edges)} edges")
            
            return UnifiedGraphResponse(
                nodes=nodes,
                edges=edges,
                metadata=metadata
            )
            
    except Exception as e:
        logger.error(f"❌ Error generating item-centered knowledge graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate item-centered knowledge graph: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_unified_graph_stats(
    current_user = Depends(get_current_user_optional)
):
    """
    Get statistics about the unified knowledge graph.
    """
    try:
        # Use the existing entity extraction service stats
        stats = await entity_extraction_service.get_entity_statistics()
        
        if 'error' in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {stats['error']}"
            )
        
        return {
            "unified_knowledge_graph": True,
            **stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting unified graph stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get graph statistics: {str(e)}"
        )


@router.post("/relationships", response_model=CreateRelationshipResponse)
async def create_unified_relationship(
    request: CreateRelationshipRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Create a new relationship between two entities in the unified knowledge graph.
    
    This endpoint allows manual creation of relationships between existing entities.
    """
    try:
        logger.info(f"🔗 Creating relationship: {request.source_entity_id} -> {request.target_entity_id} ({request.relationship_type})")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Verify both entities exist
            source_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM unified_entities WHERE id = $1)",
                request.source_entity_id
            )
            target_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM unified_entities WHERE id = $1)",
                request.target_entity_id
            )
            
            if not source_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source entity {request.source_entity_id} not found"
                )
            
            if not target_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target entity {request.target_entity_id} not found"
                )
            
            # Check if relationship already exists
            existing = await conn.fetchval("""
                SELECT id FROM unified_relationships 
                WHERE source_entity_id = $1 
                AND target_entity_id = $2 
                AND relationship_type = $3
            """, request.source_entity_id, request.target_entity_id, request.relationship_type)
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Relationship already exists between these entities"
                )
            
            # Create the relationship
            relationship_id = await conn.fetchval("""
                INSERT INTO unified_relationships (
                    source_entity_id, target_entity_id, relationship_type,
                    confidence_score, strength, context, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                RETURNING id
            """, 
                request.source_entity_id,
                request.target_entity_id, 
                request.relationship_type,
                request.confidence_score,
                request.strength,
                request.context,
                request.metadata
            )
            
            logger.info(f"✅ Created relationship {relationship_id}: {request.source_entity_id} -> {request.target_entity_id}")
            
            return CreateRelationshipResponse(
                success=True,
                relationship_id=str(relationship_id),
                message=f"Successfully created {request.relationship_type} relationship"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create relationship: {str(e)}"
        )


@router.delete("/relationships/{relationship_id}")
async def delete_unified_relationship(
    relationship_id: str,
    current_user = Depends(get_current_user_optional)
):
    """
    Delete a relationship from the unified knowledge graph.
    """
    try:
        logger.info(f"🗑️ Deleting relationship: {relationship_id}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Check if relationship exists and delete it
            deleted_count = await conn.fetchval(
                "DELETE FROM unified_relationships WHERE id = $1 RETURNING 1",
                relationship_id
            )
            
            if not deleted_count:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship not found"
                )
            
            logger.info(f"✅ Deleted relationship: {relationship_id}")
            
            return {
                "success": True,
                "message": "Relationship deleted successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete relationship: {str(e)}"
        )


@router.post("/paths/discover", response_model=KnowledgePathResponse)
async def discover_knowledge_paths(
    request: KnowledgePathRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Discover learning paths between two entities using graph traversal algorithms.
    
    Uses breadth-first search with confidence weighting to find optimal paths.
    """
    try:
        logger.info(f"🔍 Discovering paths: {request.start_entity_id} → {request.end_entity_id}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Verify both entities exist
            start_entity = await conn.fetchrow(
                "SELECT id, name, entity_type, confidence_score FROM unified_entities WHERE id = $1",
                request.start_entity_id
            )
            end_entity = await conn.fetchrow(
                "SELECT id, name, entity_type, confidence_score FROM unified_entities WHERE id = $1",
                request.end_entity_id
            )
            
            if not start_entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Start entity {request.start_entity_id} not found"
                )
            
            if not end_entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"End entity {request.end_entity_id} not found"
                )
            
            # Build query with optional relationship type filtering
            relationship_filter = ""
            params = [request.min_confidence]
            
            if request.relationship_types:
                placeholders = ','.join(f'${i+2}' for i in range(len(request.relationship_types)))
                relationship_filter = f" AND ur.relationship_type = ANY(ARRAY[{placeholders}])"
                params.extend(request.relationship_types)
            
            # Get all relationships above confidence threshold
            relationships_query = f"""
                SELECT 
                    ur.source_entity_id,
                    ur.target_entity_id,
                    ur.relationship_type,
                    ur.confidence_score,
                    ur.strength,
                    se.name as source_name,
                    se.entity_type as source_type,
                    te.name as target_name,
                    te.entity_type as target_type
                FROM unified_relationships ur
                JOIN unified_entities se ON ur.source_entity_id = se.id
                JOIN unified_entities te ON ur.target_entity_id = te.id
                WHERE ur.confidence_score >= $1
                {relationship_filter}
                ORDER BY ur.confidence_score DESC
            """
            
            relationships = await conn.fetch(relationships_query, *params)
            
            # Build adjacency graph for pathfinding
            graph = {}
            entity_info = {}
            
            for rel in relationships:
                source_id = str(rel['source_entity_id'])
                target_id = str(rel['target_entity_id'])
                
                # Store entity info
                entity_info[source_id] = {
                    'name': rel['source_name'],
                    'type': rel['source_type']
                }
                entity_info[target_id] = {
                    'name': rel['target_name'],
                    'type': rel['target_type']
                }
                
                # Build adjacency list (bidirectional for pathfinding)
                if source_id not in graph:
                    graph[source_id] = []
                if target_id not in graph:
                    graph[target_id] = []
                
                graph[source_id].append({
                    'target': target_id,
                    'relationship': rel['relationship_type'],
                    'confidence': float(rel['confidence_score']),
                    'strength': float(rel['strength'])
                })
                
                # Add reverse direction for better pathfinding
                reverse_relationship = _get_reverse_relationship(rel['relationship_type'])
                graph[target_id].append({
                    'target': source_id,
                    'relationship': reverse_relationship,
                    'confidence': float(rel['confidence_score']),
                    'strength': float(rel['strength'])
                })
            
            # Find paths using BFS with confidence weighting
            paths = await _find_knowledge_paths(
                graph, entity_info, 
                request.start_entity_id, request.end_entity_id,
                request.max_depth, start_entity, end_entity
            )
            
            # Sort paths by total confidence (best paths first)
            paths.sort(key=lambda p: p.total_confidence, reverse=True)
            
            # Limit to top 5 paths to avoid overwhelming users
            top_paths = paths[:5]
            
            logger.info(f"✅ Found {len(top_paths)} knowledge paths")
            
            return KnowledgePathResponse(
                paths=top_paths,
                total_paths=len(paths),
                search_metadata={
                    "start_entity": start_entity['name'],
                    "end_entity": end_entity['name'],
                    "max_depth": request.max_depth,
                    "min_confidence": request.min_confidence,
                    "relationship_types": request.relationship_types,
                    "total_relationships_considered": len(relationships)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error discovering knowledge paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover knowledge paths: {str(e)}"
        )


async def _find_knowledge_paths(
    graph: Dict, entity_info: Dict, start_id: str, end_id: str, 
    max_depth: int, start_entity, end_entity
) -> List[KnowledgePath]:
    """
    Find paths between entities using BFS with confidence weighting.
    """
    from collections import deque
    
    if start_id not in graph or end_id not in graph:
        return []
    
    paths = []
    queue = deque([(start_id, [start_id], [], 1.0)])  # (current_node, path, edges, confidence)
    visited_paths = set()
    
    while queue:
        current_node, path, edges, path_confidence = queue.popleft()
        
        # Avoid revisiting the same path
        path_key = tuple(path)
        if path_key in visited_paths:
            continue
        visited_paths.add(path_key)
        
        # Check if we reached the destination
        if current_node == end_id and len(path) > 1:
            # Build path nodes
            path_nodes = []
            for i, entity_id in enumerate(path):
                if entity_id == start_id:
                    entity_data = start_entity
                elif entity_id == end_id:
                    entity_data = end_entity
                else:
                    entity_data = {
                        'name': entity_info.get(entity_id, {}).get('name', 'Unknown'),
                        'entity_type': entity_info.get(entity_id, {}).get('type', 'unknown'),
                        'confidence_score': 1.0
                    }
                
                path_nodes.append(PathNode(
                    entity_id=entity_id,
                    entity_name=entity_data['name'],
                    entity_type=entity_data['entity_type'],
                    confidence=float(entity_data.get('confidence_score', 1.0))
                ))
            
            # Calculate learning difficulty based on path characteristics
            difficulty = _calculate_learning_difficulty(path_confidence, len(path), edges)
            
            paths.append(KnowledgePath(
                nodes=path_nodes,
                edges=edges,
                total_confidence=round(path_confidence, 3),
                path_length=len(path) - 1,
                learning_difficulty=difficulty
            ))
            continue
        
        # Explore neighbors if we haven't exceeded max depth
        if len(path) < max_depth + 1:
            neighbors = graph.get(current_node, [])
            for neighbor in neighbors:
                target_id = neighbor['target']
                
                # Avoid cycles
                if target_id not in path:
                    new_path = path + [target_id]
                    new_edges = edges + [PathEdge(
                        source_id=current_node,
                        target_id=target_id,
                        relationship_type=neighbor['relationship'],
                        confidence=neighbor['confidence'],
                        strength=neighbor['strength']
                    )]
                    
                    # Update path confidence (geometric mean for conservative estimation)
                    new_confidence = (path_confidence * neighbor['confidence']) ** 0.5
                    
                    queue.append((target_id, new_path, new_edges, new_confidence))
    
    return paths


def _get_reverse_relationship(relationship_type: str) -> str:
    """
    Get the reverse relationship type for bidirectional pathfinding.
    """
    reverse_map = {
        'precedes': 'follows',
        'follows': 'precedes',
        'contains': 'part_of',
        'part_of': 'contains',
        'explains': 'explained_by',
        'teaches': 'learned_from',
        'prerequisite': 'enables',
        'enables': 'prerequisite',
        'depends_on': 'enables',
        # Symmetric relationships
        'related_to': 'related_to',
        'similar_to': 'similar_to',
        'concurrent': 'concurrent',
        'opposite_of': 'opposite_of'
    }
    return reverse_map.get(relationship_type, 'related_to')


def _calculate_learning_difficulty(confidence: float, path_length: int, edges: List[PathEdge]) -> str:
    """
    Calculate learning difficulty based on path characteristics.
    """
    # Factor in path confidence, length, and relationship complexity
    base_score = confidence
    
    # Longer paths are generally harder
    length_penalty = max(0, (path_length - 2) * 0.1)
    
    # Complex relationships (like 'implements', 'extends') are harder than simple ones
    complex_relationships = {'implements', 'extends', 'applies', 'demonstrates'}
    complexity_bonus = sum(0.05 for edge in edges if edge.relationship_type in complex_relationships)
    
    difficulty_score = base_score - length_penalty + complexity_bonus
    
    if difficulty_score >= 0.8:
        return 'easy'
    elif difficulty_score >= 0.6:
        return 'medium'
    else:
        return 'hard'


@router.post("/relationships/suggest", response_model=RelationshipSuggestionsResponse)
async def suggest_relationships(
    request: RelationshipSuggestionsRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Get AI-powered relationship suggestions based on semantic similarity and existing patterns.
    
    Analyzes entity content, existing relationships, and semantic patterns to suggest
    potential new relationships that would enhance the knowledge graph.
    """
    try:
        logger.info(f"🧠 Generating relationship suggestions: entity_id={request.entity_id}, limit={request.limit}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Build entity query based on whether we're focusing on specific entity
            if request.entity_id:
                # Get suggestions for a specific entity
                target_entity = await conn.fetchrow(
                    "SELECT id, name, entity_type, description, confidence_score FROM unified_entities WHERE id = $1",
                    request.entity_id
                )
                
                if not target_entity:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Entity {request.entity_id} not found"
                    )
                
                # Get other entities that don't have relationships with target entity
                entities_query = """
                    SELECT ue.id, ue.name, ue.entity_type, ue.description, ue.confidence_score,
                           ue.metadata, ue.created_at
                    FROM unified_entities ue
                    WHERE ue.id != $1
                    AND ue.confidence_score >= $2
                    AND NOT EXISTS (
                        SELECT 1 FROM unified_relationships ur 
                        WHERE (ur.source_entity_id = $1 AND ur.target_entity_id = ue.id)
                           OR (ur.target_entity_id = $1 AND ur.source_entity_id = ue.id)
                    )
                    ORDER BY ue.confidence_score DESC, ue.created_at DESC
                    LIMIT 100
                """
                
                candidate_entities = await conn.fetch(entities_query, request.entity_id, request.min_confidence)
                focus_entities = [target_entity]
                
            else:
                # Get general suggestions across all entities
                entities_query = """
                    SELECT ue.id, ue.name, ue.entity_type, ue.description, ue.confidence_score,
                           ue.metadata, ue.created_at
                    FROM unified_entities ue
                    WHERE ue.confidence_score >= $1
                    ORDER BY ue.confidence_score DESC, ue.created_at DESC
                    LIMIT 50
                """
                
                all_entities = await conn.fetch(entities_query, request.min_confidence)
                focus_entities = list(all_entities[:10])  # Focus on top 10 entities
                candidate_entities = list(all_entities[10:])  # Consider remaining as candidates
            
            # Get existing relationships to understand patterns
            existing_relationships = await conn.fetch("""
                SELECT relationship_type, COUNT(*) as frequency,
                       AVG(confidence_score) as avg_confidence
                FROM unified_relationships
                WHERE confidence_score >= $1
                GROUP BY relationship_type
                ORDER BY frequency DESC
            """, request.min_confidence)
            
            # Build relationship frequency map
            relationship_patterns = {
                row['relationship_type']: {
                    'frequency': row['frequency'],
                    'avg_confidence': float(row['avg_confidence'])
                }
                for row in existing_relationships
            }
            
            # Debug logging
            logger.info(f"📊 Analysis setup: {len(focus_entities)} focus entities, {len(candidate_entities)} candidates")
            logger.info(f"🔍 Relationship patterns: {list(relationship_patterns.keys())}")
            
            # Generate AI-powered suggestions
            suggestions = await _generate_relationship_suggestions(
                focus_entities, candidate_entities, relationship_patterns,
                request.limit, request.min_confidence, request.relationship_types
            )
            
            # Debug logging
            logger.info(f"💡 Generated {len(suggestions)} suggestions before filtering")
            
            # Sort by confidence score
            suggestions.sort(key=lambda s: s.confidence_score, reverse=True)
            
            logger.info(f"✅ Generated {len(suggestions)} relationship suggestions")
            
            return RelationshipSuggestionsResponse(
                suggestions=suggestions[:request.limit],
                total_suggestions=len(suggestions),
                analysis_metadata={
                    "focus_entity_id": request.entity_id,
                    "entities_analyzed": len(focus_entities) + len(candidate_entities),
                    "existing_relationship_patterns": len(relationship_patterns),
                    "min_confidence": request.min_confidence,
                    "relationship_types_filter": request.relationship_types,
                    "most_common_relationships": list(relationship_patterns.keys())[:5]
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating relationship suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate relationship suggestions: {str(e)}"
        )


async def _generate_relationship_suggestions(
    focus_entities: List, candidate_entities: List, relationship_patterns: Dict,
    limit: int, min_confidence: float, relationship_types_filter: Optional[List[str]]
) -> List[RelationshipSuggestion]:
    """
    Generate AI-powered relationship suggestions using semantic analysis and pattern matching.
    """
    suggestions = []
    
    # Define relationship suggestion rules based on entity types and content
    relationship_rules = {
        # Content-based relationships
        ('text_entity', 'knowledge_concept'): [
            ('explains', 0.75, "Text entity provides explanation of concept"),
            ('references', 0.65, "Text entity mentions or references concept"),
            ('demonstrates', 0.7, "Text entity shows practical application"),
            ('contains', 0.8, "Text entity contains knowledge concept")
        ],
        ('knowledge_concept', 'text_entity'): [
            ('explained_by', 0.75, "Concept is explained by text entity"),
            ('described_in', 0.7, "Concept is described in text"),
            ('applied_in', 0.65, "Concept is applied in text")
        ],
        ('knowledge_concept', 'knowledge_concept'): [
            ('related_to', 0.65, "Concepts share semantic similarity"),
            ('builds_on', 0.75, "One concept builds upon another"),
            ('similar_to', 0.7, "Concepts have overlapping characteristics"),
            ('enables', 0.7, "One concept enables understanding of another"),
            ('prerequisite', 0.8, "One concept is prerequisite for another")
        ],
        # Cross-modal relationships
        ('video_segment', 'text_entity'): [
            ('transcribes', 0.9, "Video segment content matches text"),
            ('visualizes', 0.8, "Video demonstrates textual concept"),
            ('supplements', 0.7, "Video provides additional context")
        ],
        ('text_entity', 'video_segment'): [
            ('transcribed_from', 0.9, "Text transcribed from video"),
            ('describes', 0.8, "Text describes video content")
        ],
        ('code_function', 'knowledge_concept'): [
            ('implements', 0.85, "Code function implements conceptual algorithm"),
            ('demonstrates', 0.8, "Code shows practical application of concept"),
            ('applies', 0.75, "Code applies theoretical principle")
        ],
        ('knowledge_concept', 'code_function'): [
            ('implemented_by', 0.85, "Concept is implemented by code"),
            ('demonstrated_by', 0.8, "Concept is demonstrated by code")
        ]
    }
    
    # Generate suggestions for each focus entity
    logger.info(f"🎯 Starting suggestion generation for {len(focus_entities)} focus entities")
    
    for focus_entity in focus_entities:
        focus_type = focus_entity['entity_type']
        focus_name = focus_entity['name'].lower()
        focus_description = (focus_entity['description'] or '').lower()
        
        logger.info(f"🔍 Processing focus entity: {focus_entity['name']} ({focus_type})")
        
        candidates_processed = 0
        for candidate in candidate_entities:
            candidate_type = candidate['entity_type']
            candidate_name = candidate['name'].lower()
            candidate_description = (candidate['description'] or '').lower()
            
            # Skip if same entity
            if focus_entity['id'] == candidate['id']:
                continue
            
            candidates_processed += 1
            
            # Check for applicable relationship rules
            rules = relationship_rules.get((focus_type, candidate_type), [])
            if not rules:
                # Try reverse direction
                rules = relationship_rules.get((candidate_type, focus_type), [])  
                if rules:
                    # Reverse the relationship direction
                    rules = [(rule[0], rule[1], rule[2]) for rule in rules]
            
            if not rules:
                continue  # No applicable rules found
            
            logger.info(f"  🔗 Found {len(rules)} applicable rules for {candidate['name']} ({candidate_type})")
            
            # Generate suggestions based on rules
            for relationship_type, base_confidence, reasoning in rules:
                
                # Skip if relationship type filter is specified and doesn't match
                if relationship_types_filter and relationship_type not in relationship_types_filter:
                    continue
                
                # Calculate semantic similarity based on name and description overlap
                semantic_score = _calculate_semantic_similarity(
                    focus_name, focus_description, candidate_name, candidate_description
                )
                
                # Adjust confidence based on semantic similarity and existing patterns
                pattern_boost = 0
                if relationship_type in relationship_patterns:
                    # Boost confidence for commonly used relationship types
                    pattern_frequency = relationship_patterns[relationship_type]['frequency']
                    pattern_boost = min(0.1, pattern_frequency / 100.0)  # Max 0.1 boost
                
                final_confidence = min(1.0, base_confidence * semantic_score + pattern_boost)
                
                # Only suggest if meets minimum confidence
                if final_confidence >= min_confidence:
                    suggestions.append(RelationshipSuggestion(
                        source_entity_id=str(focus_entity['id']),
                        target_entity_id=str(candidate['id']),
                        suggested_relationship=relationship_type,
                        confidence_score=round(final_confidence, 3),
                        reasoning=f"{reasoning} (semantic similarity: {semantic_score:.2f})",
                        source_entity_name=focus_entity['name'],
                        target_entity_name=candidate['name'],
                        semantic_similarity=round(semantic_score, 3),
                        existing_connections=0  # Could be enhanced to count indirect connections
                    ))
        
        logger.info(f"  📊 Processed {candidates_processed} candidates for {focus_entity['name']}")
    
    logger.info(f"🎉 Total suggestions generated: {len(suggestions)}")
    return suggestions


def _calculate_semantic_similarity(name1: str, desc1: str, name2: str, desc2: str) -> float:
    """
    Calculate semantic similarity between two entities based on name and description overlap.
    
    Enhanced version with domain-specific similarity detection.
    """
    # Normalize inputs
    text1 = (name1 + ' ' + desc1).lower().strip()
    text2 = (name2 + ' ' + desc2).lower().strip()
    
    # Extract meaningful words
    import re
    words1 = set(re.findall(r'\b[a-z]{3,}\b', text1))  # Words 3+ chars
    words2 = set(re.findall(r'\b[a-z]{3,}\b', text2))
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'but', 'for', 'with', 'from', 'this', 'that', 'they', 'them',
        'have', 'has', 'had', 'will', 'would', 'could', 'should', 'can', 'may',
        'also', 'very', 'much', 'more', 'most', 'some', 'any', 'all', 'each',
        'your', 'you', 'its', 'their', 'our', 'his', 'her'
    }
    words1 = words1 - stop_words
    words2 = words2 - stop_words
    
    if not words1 or not words2:
        return 0.4  # Neutral baseline
    
    # Calculate different similarity metrics
    
    # 1. Jaccard similarity (word intersection)
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    jaccard_sim = intersection / union if union > 0 else 0
    
    # 2. Name similarity boosters
    name_boost = 0
    if name1 in name2 or name2 in name1:
        name_boost = 0.4
    elif any(word in name2 for word in name1.split() if len(word) > 2):
        name_boost = 0.2
    elif any(word in name1 for word in name2.split() if len(word) > 2):
        name_boost = 0.2
    
    # 3. Domain-specific keyword boosters
    tech_keywords = {
        'javascript', 'python', 'react', 'node', 'api', 'web', 'development', 
        'framework', 'library', 'code', 'programming', 'software', 'application',
        'database', 'server', 'client', 'frontend', 'backend', 'fullstack'
    }
    
    ai_keywords = {
        'artificial', 'intelligence', 'machine', 'learning', 'neural', 'network',
        'algorithm', 'model', 'training', 'data', 'analysis', 'chatbot', 'prompt'
    }
    
    seo_keywords = {
        'search', 'engine', 'optimization', 'ranking', 'keyword', 'content',
        'traffic', 'organic', 'visibility', 'google', 'indexing'
    }
    
    domain_boost = 0
    if words1.intersection(tech_keywords) and words2.intersection(tech_keywords):
        domain_boost = 0.15
    elif words1.intersection(ai_keywords) and words2.intersection(ai_keywords):
        domain_boost = 0.15  
    elif words1.intersection(seo_keywords) and words2.intersection(seo_keywords):
        domain_boost = 0.15
    
    # 4. Semantic relationship indicators
    semantic_boost = 0
    relation_words1 = words1.intersection({'tool', 'method', 'technique', 'process', 'system', 'approach'})
    relation_words2 = words2.intersection({'tool', 'method', 'technique', 'process', 'system', 'approach'})
    if relation_words1 and relation_words2:
        semantic_boost = 0.1
    
    # Combine all similarity signals
    final_similarity = jaccard_sim + name_boost + domain_boost + semantic_boost
    
    # Normalize to 0.4-1.0 range for better distribution
    final_similarity = max(0.4, min(1.0, final_similarity))
    
    return final_similarity


@router.post("/analysis/gaps", response_model=KnowledgeGapAnalysisResponse)
async def analyze_knowledge_gaps(
    request: KnowledgeGapAnalysisRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Analyze the knowledge graph to identify gaps, missing relationships, and areas for improvement.
    
    Performs comprehensive analysis including:
    - Missing relationship detection
    - Isolated entity identification  
    - Domain completeness assessment
    - Conceptual gap analysis
    """
    try:
        logger.info(f"🔍 Starting knowledge gap analysis: depth={request.analysis_depth}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Get comprehensive graph data
            entities = await conn.fetch("""
                SELECT ue.id, ue.name, ue.entity_type, ue.description, 
                       ue.confidence_score, ue.metadata, ue.created_at
                FROM unified_entities ue
                WHERE ue.confidence_score >= 0.3
                ORDER BY ue.confidence_score DESC
            """)
            
            relationships = await conn.fetch("""
                SELECT ur.id, ur.source_entity_id, ur.target_entity_id, 
                       ur.relationship_type, ur.confidence_score, ur.strength,
                       se.name as source_name, se.entity_type as source_type,
                       te.name as target_name, te.entity_type as target_type
                FROM unified_relationships ur
                JOIN unified_entities se ON ur.source_entity_id = se.id
                JOIN unified_entities te ON ur.target_entity_id = te.id
                WHERE ur.confidence_score >= 0.3
            """)
            
            # Perform gap analysis
            gaps, domains, overall_completeness = await _analyze_knowledge_gaps(
                entities, relationships, request
            )
            
            # Generate recommendations
            recommendations = _generate_gap_recommendations(gaps, domains, overall_completeness)
            
            # Filter gaps by severity
            severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            min_severity_level = severity_order.get(request.min_severity, 2)
            filtered_gaps = [
                gap for gap in gaps 
                if severity_order.get(gap.severity, 1) >= min_severity_level
            ]
            
            logger.info(f"✅ Gap analysis complete: {len(filtered_gaps)} gaps, {len(domains)} domains")
            
            return KnowledgeGapAnalysisResponse(
                gaps=filtered_gaps,
                domains=domains,
                overall_completeness=overall_completeness,
                analysis_summary={
                    "total_entities": len(entities),
                    "total_relationships": len(relationships),
                    "gaps_identified": len(filtered_gaps),
                    "domains_analyzed": len(domains),
                    "analysis_depth": request.analysis_depth,
                    "avg_domain_completeness": sum(d.completeness_score for d in domains) / len(domains) if domains else 0,
                    "relationship_density": len(relationships) / len(entities) if entities else 0
                },
                recommendations=recommendations,
                metadata={
                    "analysis_timestamp": "now",
                    "focus_domains": request.focus_domains,
                    "min_severity": request.min_severity,
                    "analysis_depth": request.analysis_depth
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Error analyzing knowledge gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze knowledge gaps: {str(e)}"
        )


async def _analyze_knowledge_gaps(entities, relationships, request) -> tuple[List[KnowledgeGap], List[KnowledgeDomain], float]:
    """
    Core knowledge gap analysis algorithm.
    """
    gaps = []
    domains = {}
    
    # Build entity lookup and relationship graph
    entity_map = {str(e['id']): e for e in entities}
    entity_relationships = {}
    
    for rel in relationships:
        source_id = str(rel['source_entity_id'])
        target_id = str(rel['target_entity_id'])
        
        if source_id not in entity_relationships:
            entity_relationships[source_id] = []
        if target_id not in entity_relationships:
            entity_relationships[target_id] = []
            
        entity_relationships[source_id].append(rel)
        entity_relationships[target_id].append(rel)
    
    # 1. Identify isolated entities (entities with few or no relationships)
    for entity in entities:
        entity_id = str(entity['id'])
        connection_count = len(entity_relationships.get(entity_id, []))
        
        if connection_count == 0:
            gaps.append(KnowledgeGap(
                gap_type="isolated_entity",
                severity="high",
                title=f"Isolated Entity: {entity['name']}",
                description=f"Entity '{entity['name']}' has no relationships with other entities",
                affected_entities=[entity['name']],
                suggested_actions=[
                    "Review entity content for potential relationships",
                    "Consider connecting to related concepts",
                    "Verify entity is correctly categorized"
                ],
                confidence_score=0.9,
                domain=_classify_entity_domain(entity)
            ))
        elif connection_count == 1:
            gaps.append(KnowledgeGap(
                gap_type="weakly_connected",
                severity="medium",
                title=f"Weakly Connected: {entity['name']}",
                description=f"Entity '{entity['name']}' has only one relationship",
                affected_entities=[entity['name']],
                suggested_actions=[
                    "Explore additional relationships for this entity",
                    "Consider prerequisite or dependent concepts"
                ],
                confidence_score=0.7,
                domain=_classify_entity_domain(entity)
            ))
    
    # 2. Analyze knowledge domains
    domain_entities = {}
    for entity in entities:
        domain = _classify_entity_domain(entity)
        if domain not in domain_entities:
            domain_entities[domain] = []
        domain_entities[domain].append(entity)
    
    for domain_name, domain_entity_list in domain_entities.items():
        # Calculate domain metrics
        domain_relationships = []
        for entity in domain_entity_list:
            entity_id = str(entity['id'])
            domain_relationships.extend(entity_relationships.get(entity_id, []))
        
        # Remove duplicates
        domain_relationships = list({rel['id']: rel for rel in domain_relationships}.values())
        
        entity_count = len(domain_entity_list)
        relationship_count = len(domain_relationships)
        relationship_density = relationship_count / (entity_count * (entity_count - 1)) if entity_count > 1 else 0
        
        # Calculate completeness score
        expected_relationships = _calculate_expected_relationships(domain_name, entity_count)
        completeness_score = min(1.0, relationship_count / expected_relationships) if expected_relationships > 0 else 1.0
        
        # Calculate interconnectedness
        interconnected_entities = set()
        for rel in domain_relationships:
            interconnected_entities.add(str(rel['source_entity_id']))
            interconnected_entities.add(str(rel['target_entity_id']))
        interconnectedness = len(interconnected_entities) / entity_count if entity_count > 0 else 0
        
        # Identify key entities (highest confidence or most connected)
        key_entities = sorted(domain_entity_list, key=lambda e: e['confidence_score'], reverse=True)[:3]
        key_entity_names = [e['name'] for e in key_entities]
        
        # Identify missing concepts (basic domain analysis)
        missing_concepts = _identify_missing_concepts(domain_name, domain_entity_list)
        
        domains[domain_name] = KnowledgeDomain(
            domain_name=domain_name,
            entity_count=entity_count,
            relationship_density=relationship_density,
            completeness_score=completeness_score,
            key_entities=key_entity_names,
            missing_concepts=missing_concepts,
            interconnectedness=interconnectedness
        )
        
        # Create gaps for weak domains
        if completeness_score < 0.5 and entity_count > 2:
            gaps.append(KnowledgeGap(
                gap_type="weak_domain",
                severity="medium" if completeness_score > 0.2 else "high",
                title=f"Incomplete Domain: {domain_name}",
                description=f"Domain '{domain_name}' has low relationship density ({relationship_density:.2f}) and completeness ({completeness_score:.2f})",
                affected_entities=key_entity_names,
                suggested_actions=[
                    f"Add relationships between {domain_name} concepts",
                    "Consider missing foundational concepts",
                    "Review prerequisite relationships"
                ],
                confidence_score=0.8,
                domain=domain_name
            ))
    
    # 3. Identify conceptual gaps in learning paths
    if request.analysis_depth in ["standard", "comprehensive"]:
        conceptual_gaps = await _identify_conceptual_gaps(entities, relationships, entity_map)
        gaps.extend(conceptual_gaps)
    
    # Calculate overall completeness
    domain_scores = [d.completeness_score for d in domains.values()]
    overall_completeness = sum(domain_scores) / len(domain_scores) if domain_scores else 0.0
    
    return gaps, list(domains.values()), overall_completeness


def _classify_entity_domain(entity) -> str:
    """
    Classify entity into knowledge domain based on name and description.
    """
    name = entity['name'].lower()
    desc = (entity['description'] or '').lower()
    text = name + ' ' + desc
    
    # Domain classification rules
    if any(keyword in text for keyword in ['javascript', 'python', 'react', 'code', 'programming', 'api', 'framework']):
        return 'Technology'
    elif any(keyword in text for keyword in ['seo', 'marketing', 'content', 'traffic', 'optimization', 'keyword']):
        return 'Digital Marketing'
    elif any(keyword in text for keyword in ['ai', 'machine learning', 'artificial intelligence', 'neural', 'model', 'chatbot']):
        return 'Artificial Intelligence'
    elif any(keyword in text for keyword in ['design', 'ui', 'ux', 'user experience', 'interface', 'visual']):
        return 'Design'
    elif any(keyword in text for keyword in ['business', 'strategy', 'management', 'leadership', 'entrepreneurship']):
        return 'Business'
    elif any(keyword in text for keyword in ['data', 'analytics', 'analysis', 'statistics', 'metrics']):
        return 'Data Science'
    else:
        return 'General Knowledge'


def _calculate_expected_relationships(domain_name: str, entity_count: int) -> int:
    """
    Calculate expected number of relationships for a domain based on its characteristics.
    """
    domain_complexity = {
        'Technology': 2.5,  # High interconnection expected
        'Artificial Intelligence': 2.0,
        'Data Science': 2.0,
        'Digital Marketing': 1.5,
        'Design': 1.5,
        'Business': 1.8,
        'General Knowledge': 1.0
    }
    
    complexity_factor = domain_complexity.get(domain_name, 1.0)
    return int(entity_count * complexity_factor)


def _identify_missing_concepts(domain_name: str, entities: list) -> List[str]:
    """
    Identify potentially missing foundational concepts for a domain.
    """
    entity_names = {e['name'].lower() for e in entities}
    
    foundational_concepts = {
        'Technology': ['fundamentals', 'best practices', 'architecture', 'testing', 'deployment'],
        'Artificial Intelligence': ['algorithms', 'training', 'data preprocessing', 'evaluation', 'ethics'],
        'Digital Marketing': ['analytics', 'conversion', 'audience', 'strategy', 'metrics'],
        'Design': ['principles', 'accessibility', 'user research', 'prototyping', 'testing'],
        'Business': ['strategy', 'analysis', 'planning', 'execution', 'metrics'],
        'Data Science': ['statistics', 'visualization', 'modeling', 'validation', 'interpretation']
    }
    
    expected_concepts = foundational_concepts.get(domain_name, [])
    missing = []
    
    for concept in expected_concepts:
        # Check if any entity contains this concept
        if not any(concept in name for name in entity_names):
            missing.append(concept.title())
    
    return missing[:3]  # Return top 3 missing concepts


async def _identify_conceptual_gaps(entities, relationships, entity_map) -> List[KnowledgeGap]:
    """
    Identify conceptual gaps in learning paths and prerequisite chains.
    """
    gaps = []
    
    # Look for broken prerequisite chains
    prerequisite_rels = [r for r in relationships if r['relationship_type'] in ['prerequisite', 'builds_on', 'enables']]
    
    for rel in prerequisite_rels:
        source_entity = entity_map.get(str(rel['source_entity_id']))
        target_entity = entity_map.get(str(rel['target_entity_id']))
        
        if source_entity and target_entity:
            # Check if there are intermediate concepts that might be missing
            confidence_gap = source_entity['confidence_score'] - target_entity['confidence_score']
            
            if confidence_gap > 0.3:  # Significant confidence gap suggests missing intermediate concepts
                gaps.append(KnowledgeGap(
                    gap_type="conceptual_gap",
                    severity="medium",
                    title=f"Learning Gap: {source_entity['name']} → {target_entity['name']}",
                    description=f"Large confidence gap between prerequisite concepts suggests missing intermediate knowledge",
                    affected_entities=[source_entity['name'], target_entity['name']],
                    suggested_actions=[
                        "Identify intermediate concepts between these entities",
                        "Add bridging knowledge or examples",
                        "Consider breaking down complex concepts"
                    ],
                    confidence_score=0.6,
                    domain=_classify_entity_domain(source_entity)
                ))
    
    return gaps


def _generate_gap_recommendations(gaps: List[KnowledgeGap], domains: List[KnowledgeDomain], overall_completeness: float) -> List[str]:
    """
    Generate high-level recommendations based on gap analysis.
    """
    recommendations = []
    
    # Overall completeness recommendations
    if overall_completeness < 0.6:
        recommendations.append("Focus on building more relationships between existing entities to improve knowledge graph completeness")
    
    # Domain-specific recommendations
    weak_domains = [d for d in domains if d.completeness_score < 0.5]
    if weak_domains:
        domain_names = [d.domain_name for d in weak_domains[:2]]
        recommendations.append(f"Strengthen knowledge domains: {', '.join(domain_names)} by adding foundational concepts")
    
    # Gap-type specific recommendations
    gap_types = {}
    for gap in gaps:
        gap_types[gap.gap_type] = gap_types.get(gap.gap_type, 0) + 1
    
    if gap_types.get('isolated_entity', 0) > 5:
        recommendations.append("Review isolated entities and connect them to related concepts to improve knowledge integration")
    
    if gap_types.get('conceptual_gap', 0) > 3:
        recommendations.append("Add intermediate concepts to bridge learning gaps and create smoother knowledge paths")
    
    if not recommendations:
        recommendations.append("Knowledge graph shows good completeness - consider expanding into new domains or deepening existing knowledge areas")
    
    return recommendations[:4]  # Return top 4 recommendations


@router.post("/clustering/semantic", response_model=SemanticClusteringResponse)
async def perform_semantic_clustering(
    request: SemanticClusteringRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Perform semantic clustering of entities in the knowledge graph.
    
    Groups related entities into clusters based on semantic similarity, structural patterns,
    and relationship analysis. Useful for identifying knowledge themes and organizing content.
    """
    try:
        logger.info(f"🔬 Starting semantic clustering: algorithm={request.clustering_algorithm}, max_clusters={request.max_clusters}")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            
            # Build entity query with filters
            entity_query = """
                SELECT 
                    ue.id,
                    ue.name as title,
                    ue.entity_type as type,
                    ue.description as summary,
                    ue.confidence_score as confidence,
                    ue.created_at,
                    ue.metadata,
                    i.content_type,
                    i.title as source_title,
                    i.url as source_url
                FROM unified_entities ue
                LEFT JOIN items i ON ue.source_content_id = i.id
                WHERE ue.confidence_score >= $1
            """
            
            params = [request.min_confidence]
            
            if request.entity_types:
                placeholders = ','.join(f'${i+2}' for i in range(len(request.entity_types)))
                entity_query += f" AND ue.entity_type = ANY(ARRAY[{placeholders}])"
                params.extend(request.entity_types)
            
            entity_query += " ORDER BY ue.confidence_score DESC"
            
            # Fetch entities
            entity_rows = await conn.fetch(entity_query, *params)
            
            if len(entity_rows) < request.min_cluster_size:
                return SemanticClusteringResponse(
                    clusters=[],
                    total_entities_clustered=0,
                    clustering_metadata={"message": "Not enough entities to form clusters"},
                    unclustered_entities=[]
                )
            
            # Convert to node objects
            nodes = []
            entity_ids = []
            
            for row in entity_rows:
                entity_ids.append(str(row['id']))
                
                metadata = {}
                if row['metadata']:
                    try:
                        metadata = dict(row['metadata']) if isinstance(row['metadata'], dict) else {}
                    except:
                        metadata = {}
                
                if row['source_title']:
                    metadata['source_title'] = row['source_title']
                if row['source_url']:
                    metadata['source_url'] = row['source_url']
                
                nodes.append(UnifiedGraphNode(
                    id=str(row['id']),
                    title=row['title'],
                    type=row['type'],  
                    summary=row['summary'],
                    content_type=row['content_type'],
                    confidence=float(row['confidence']),
                    created_at=row['created_at'].isoformat() if row['created_at'] else None,
                    metadata=metadata
                ))
            
            # Get relationships between these entities
            relationships = []
            if entity_ids:
                relationship_rows = await conn.fetch("""
                    SELECT 
                        ur.source_entity_id,
                        ur.target_entity_id,
                        ur.relationship_type,
                        ur.confidence_score,
                        ur.strength
                    FROM unified_relationships ur
                    WHERE ur.source_entity_id = ANY($1) 
                    AND ur.target_entity_id = ANY($1)
                    AND ur.confidence_score >= $2
                """, entity_ids, request.min_confidence)
                
                relationships = [dict(row) for row in relationship_rows]
            
            # Perform clustering based on selected algorithm
            clusters = await _perform_entity_clustering(
                nodes, relationships, request
            )
            
            # Calculate total entities clustered
            total_clustered = sum(len(cluster.entities) for cluster in clusters)
            
            # Find unclustered entities
            clustered_entity_ids = set()
            for cluster in clusters:
                for entity in cluster.entities:
                    clustered_entity_ids.add(entity.id)
            
            unclustered_entities = [
                node for node in nodes
                if node.id not in clustered_entity_ids
            ]
            
            logger.info(f"✅ Semantic clustering complete: {len(clusters)} clusters, {total_clustered} entities clustered")
            
            return SemanticClusteringResponse(
                clusters=clusters,
                total_entities_clustered=total_clustered,
                clustering_metadata={
                    "algorithm": request.clustering_algorithm,
                    "total_entities_processed": len(nodes),
                    "clustering_parameters": {
                        "min_cluster_size": request.min_cluster_size,
                        "max_clusters": request.max_clusters,
                        "min_confidence": request.min_confidence
                    },
                    "entity_types_filter": request.entity_types,
                    "relationships_considered": len(relationships)
                },
                unclustered_entities=unclustered_entities[:10]  # Limit unclustered list
            )
            
    except Exception as e:
        logger.error(f"❌ Error performing semantic clustering: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic clustering: {str(e)}"
        )


async def _perform_entity_clustering(
    nodes: List[UnifiedGraphNode], 
    relationships: List[Dict], 
    request: SemanticClusteringRequest
) -> List[EntityCluster]:
    """
    Core clustering algorithm that groups entities based on semantic and structural similarity.
    """
    import uuid
    from collections import defaultdict
    
    if request.clustering_algorithm == "semantic":
        return await _semantic_clustering(nodes, relationships, request)
    elif request.clustering_algorithm == "structural":
        return await _structural_clustering(nodes, relationships, request)
    elif request.clustering_algorithm == "hybrid":
        return await _hybrid_clustering(nodes, relationships, request)
    else:
        # Default to semantic clustering
        return await _semantic_clustering(nodes, relationships, request)


async def _semantic_clustering(
    nodes: List[UnifiedGraphNode], 
    relationships: List[Dict], 
    request: SemanticClusteringRequest
) -> List[EntityCluster]:
    """
    Semantic clustering based on content similarity and shared concepts.
    """
    import uuid
    from collections import defaultdict
    
    clusters = []
    used_nodes = set()
    
    # Build similarity matrix
    similarity_matrix = {}
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i >= j:
                continue
            
            similarity = _calculate_content_similarity(node1, node2)
            if similarity >= 0.4:  # Only store significant similarities
                similarity_matrix[(node1.id, node2.id)] = similarity
    
    # Group nodes by domain/type for initial clustering
    domain_groups = defaultdict(list)
    for node in nodes:
        domain = _classify_node_domain(node)
        domain_groups[domain].append(node)
    
    # Create clusters within each domain
    for domain, domain_nodes in domain_groups.items():
        if len(domain_nodes) < request.min_cluster_size:
            continue
        
        # Find highly connected subgroups within the domain
        domain_clusters = _find_semantic_subgroups(
            domain_nodes, similarity_matrix, request.min_cluster_size
        )
        
        for i, cluster_nodes in enumerate(domain_clusters):
            if len(cluster_nodes) >= request.min_cluster_size:
                cluster_id = str(uuid.uuid4())
                
                # Find central entity (highest average similarity to others)
                central_entity = _find_cluster_center(cluster_nodes, similarity_matrix)
                
                # Calculate cohesion score
                cohesion_score = _calculate_cluster_cohesion(cluster_nodes, similarity_matrix)
                
                # Generate cluster name and description
                cluster_name, description, keywords = _generate_cluster_metadata(cluster_nodes, domain)
                
                clusters.append(EntityCluster(
                    cluster_id=cluster_id,
                    cluster_name=cluster_name,
                    entities=cluster_nodes,
                    central_entity=central_entity,
                    cohesion_score=cohesion_score,
                    cluster_type="semantic",
                    description=description,
                    keywords=keywords,
                    domain=domain
                ))
                
                # Mark nodes as used
                for node in cluster_nodes:
                    used_nodes.add(node.id)
                
                if len(clusters) >= request.max_clusters:
                    break
        
        if len(clusters) >= request.max_clusters:
            break
    
    # Sort clusters by cohesion score (best first)
    clusters.sort(key=lambda c: c.cohesion_score, reverse=True)
    
    return clusters[:request.max_clusters]


async def _structural_clustering(
    nodes: List[UnifiedGraphNode], 
    relationships: List[Dict], 
    request: SemanticClusteringRequest
) -> List[EntityCluster]:
    """
    Structural clustering based on relationship patterns and graph topology.
    """
    import uuid
    from collections import defaultdict, deque
    
    clusters = []
    
    # Build adjacency graph
    adjacency = defaultdict(list)
    node_map = {node.id: node for node in nodes}
    
    for rel in relationships:
        source_id = str(rel['source_entity_id'])
        target_id = str(rel['target_entity_id'])
        
        if source_id in node_map and target_id in node_map:
            adjacency[source_id].append({
                'target': target_id,
                'relationship': rel['relationship_type'],
                'strength': rel.get('strength', 1.0),
                'confidence': rel['confidence_score']
            })
            # Add reverse for undirected clustering
            adjacency[target_id].append({
                'target': source_id,
                'relationship': rel['relationship_type'],
                'strength': rel.get('strength', 1.0),
                'confidence': rel['confidence_score']
            })
    
    # Find connected components using BFS
    visited = set()
    components = []
    
    for node in nodes:
        if node.id not in visited:
            component = []
            queue = deque([node.id])
            visited.add(node.id)
            
            while queue:
                current_id = queue.popleft()
                component.append(node_map[current_id])
                
                for neighbor in adjacency.get(current_id, []):
                    neighbor_id = neighbor['target']
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)
            
            if len(component) >= request.min_cluster_size:
                components.append(component)
    
    # Convert components to clusters
    for i, component in enumerate(components[:request.max_clusters]):
        cluster_id = str(uuid.uuid4())
        
        # Find central entity (most connected)
        central_entity = max(component, key=lambda n: len(adjacency.get(n.id, [])))
        
        # Calculate structural cohesion
        total_edges = sum(len(adjacency.get(node.id, [])) for node in component)
        max_possible_edges = len(component) * (len(component) - 1)
        cohesion_score = (total_edges / max_possible_edges) if max_possible_edges > 0 else 0
        
        # Determine dominant domain
        domain_counts = defaultdict(int)
        for node in component:
            domain = _classify_node_domain(node)
            domain_counts[domain] += 1
        dominant_domain = max(domain_counts.items(), key=lambda x: x[1])[0]
        
        # Generate cluster metadata
        cluster_name, description, keywords = _generate_cluster_metadata(component, dominant_domain)
        
        clusters.append(EntityCluster(
            cluster_id=cluster_id,
            cluster_name=f"Connected Group: {cluster_name}",
            entities=component,
            central_entity=central_entity,
            cohesion_score=round(cohesion_score, 3),
            cluster_type="structural",
            description=f"Structurally connected entities: {description}",
            keywords=keywords,
            domain=dominant_domain
        ))
    
    return clusters


async def _hybrid_clustering(
    nodes: List[UnifiedGraphNode], 
    relationships: List[Dict], 
    request: SemanticClusteringRequest
) -> List[EntityCluster]:
    """
    Hybrid clustering combining semantic similarity and structural connections.
    """
    # Get both semantic and structural clusters
    semantic_clusters = await _semantic_clustering(nodes, relationships, request)
    structural_clusters = await _structural_clustering(nodes, relationships, request)
    
    # Merge and refine clusters
    all_clusters = semantic_clusters + structural_clusters
    
    # Remove duplicates and merge overlapping clusters
    final_clusters = []
    used_entities = set()
    
    for cluster in all_clusters:
        cluster_entity_ids = {e.id for e in cluster.entities}
        
        # Check for significant overlap with existing clusters
        overlap_found = False
        for existing_cluster in final_clusters:
            existing_entity_ids = {e.id for e in existing_cluster.entities}
            overlap = len(cluster_entity_ids.intersection(existing_entity_ids))
            overlap_ratio = overlap / min(len(cluster_entity_ids), len(existing_entity_ids))
            
            if overlap_ratio > 0.5:  # Significant overlap
                # Merge clusters by keeping the one with higher cohesion
                if cluster.cohesion_score > existing_cluster.cohesion_score:
                    final_clusters.remove(existing_cluster)
                    final_clusters.append(cluster)
                overlap_found = True
                break
        
        if not overlap_found:
            final_clusters.append(cluster)
        
        if len(final_clusters) >= request.max_clusters:
            break
    
    # Update cluster types to hybrid
    for cluster in final_clusters:
        cluster.cluster_type = "hybrid"
        cluster.cluster_name = f"Hybrid: {cluster.cluster_name}"
    
    return final_clusters[:request.max_clusters]


def _calculate_content_similarity(node1: UnifiedGraphNode, node2: UnifiedGraphNode) -> float:
    """
    Calculate content similarity between two nodes using enhanced semantic analysis.
    """
    # Use the enhanced similarity function from relationship suggestions
    return _calculate_semantic_similarity(
        node1.title.lower(),
        (node1.summary or '').lower(),
        node2.title.lower(), 
        (node2.summary or '').lower()
    )


def _classify_node_domain(node: UnifiedGraphNode) -> str:
    """
    Classify node into domain for clustering purposes.
    """
    # Create a simplified entity object for the existing classification function
    entity = {
        'name': node.title,
        'description': node.summary,
        'entity_type': node.type
    }
    return _classify_entity_domain(entity)


def _find_semantic_subgroups(
    nodes: List[UnifiedGraphNode], 
    similarity_matrix: Dict, 
    min_size: int
) -> List[List[UnifiedGraphNode]]:
    """
    Find subgroups of semantically similar nodes within a domain.
    """
    subgroups = []
    used_nodes = set()
    
    # Sort nodes by average similarity to others
    node_scores = {}
    for node in nodes:
        total_similarity = 0
        count = 0
        for other_node in nodes:
            if node.id != other_node.id:
                sim_key = (node.id, other_node.id) if node.id < other_node.id else (other_node.id, node.id)
                similarity = similarity_matrix.get(sim_key, 0)
                total_similarity += similarity
                count += 1
        node_scores[node.id] = total_similarity / count if count > 0 else 0
    
    sorted_nodes = sorted(nodes, key=lambda n: node_scores.get(n.id, 0), reverse=True)
    
    # Form subgroups using similarity threshold
    for seed_node in sorted_nodes:
        if seed_node.id in used_nodes:
            continue
        
        subgroup = [seed_node]
        used_nodes.add(seed_node.id)
        
        # Add similar nodes to the subgroup
        for candidate_node in sorted_nodes:
            if candidate_node.id in used_nodes:
                continue
            
            # Check similarity with all nodes in current subgroup
            avg_similarity = 0
            for existing_node in subgroup:
                sim_key = (candidate_node.id, existing_node.id) if candidate_node.id < existing_node.id else (existing_node.id, candidate_node.id)
                similarity = similarity_matrix.get(sim_key, 0)
                avg_similarity += similarity
            
            avg_similarity /= len(subgroup)
            
            if avg_similarity >= 0.5:  # Similarity threshold
                subgroup.append(candidate_node)
                used_nodes.add(candidate_node.id)
        
        if len(subgroup) >= min_size:
            subgroups.append(subgroup)
    
    return subgroups


def _find_cluster_center(nodes: List[UnifiedGraphNode], similarity_matrix: Dict) -> UnifiedGraphNode:
    """
    Find the most central entity in a cluster based on average similarity.
    """
    best_node = nodes[0]
    best_score = 0
    
    for node in nodes:
        total_similarity = 0
        count = 0
        
        for other_node in nodes:
            if node.id != other_node.id:
                sim_key = (node.id, other_node.id) if node.id < other_node.id else (other_node.id, node.id)
                similarity = similarity_matrix.get(sim_key, 0)
                total_similarity += similarity
                count += 1
        
        avg_similarity = total_similarity / count if count > 0 else 0
        
        if avg_similarity > best_score:
            best_score = avg_similarity
            best_node = node
    
    return best_node


def _calculate_cluster_cohesion(nodes: List[UnifiedGraphNode], similarity_matrix: Dict) -> float:
    """
    Calculate cohesion score for a cluster based on internal similarities.
    """
    if len(nodes) < 2:
        return 1.0
    
    total_similarity = 0
    pair_count = 0
    
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i >= j:
                continue
            
            sim_key = (node1.id, node2.id) if node1.id < node2.id else (node2.id, node1.id)
            similarity = similarity_matrix.get(sim_key, 0)
            total_similarity += similarity
            pair_count += 1
    
    return round(total_similarity / pair_count, 3) if pair_count > 0 else 0


def _generate_cluster_metadata(nodes: List[UnifiedGraphNode], domain: str) -> tuple[str, str, List[str]]:
    """
    Generate cluster name, description, and keywords based on cluster entities.
    """
    import re
    from collections import Counter
    
    # Extract common terms from entity names
    all_words = []
    entity_names = []
    
    for node in nodes:
        entity_names.append(node.title)
        # Extract meaningful words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', node.title.lower())
        all_words.extend(words)
        
        if node.summary:
            summary_words = re.findall(r'\b[a-zA-Z]{3,}\b', node.summary.lower())
            all_words.extend(summary_words)
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'but', 'for', 'with', 'from', 'this', 'that', 'they', 'them',
        'have', 'has', 'had', 'will', 'would', 'could', 'should', 'can', 'may',
        'also', 'very', 'much', 'more', 'most', 'some', 'any', 'all', 'each'
    }
    
    meaningful_words = [word for word in all_words if word not in stop_words and len(word) > 2]
    
    # Find most common terms
    word_counts = Counter(meaningful_words)
    common_words = [word for word, count in word_counts.most_common(5) if count >= 2]
    
    # Generate cluster name
    if common_words:
        cluster_name = f"{domain}: {' & '.join(common_words[:2]).title()}"
    else:
        cluster_name = f"{domain} Concepts"
    
    # Generate description
    if len(nodes) <= 3:
        entity_list = ', '.join(entity_names)
        description = f"Small cluster containing: {entity_list}"
    else:
        description = f"Cluster of {len(nodes)} related {domain.lower()} entities focusing on {', '.join(common_words[:3])}"
    
    # Extract keywords
    keywords = common_words[:5] + [domain.lower()]
    
    return cluster_name, description, keywords