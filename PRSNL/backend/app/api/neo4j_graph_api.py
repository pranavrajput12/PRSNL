"""
Neo4j Graph API endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.neo4j_graph_service import (
    neo4j_graph_service,
    GraphNode,
    GraphRelationship,
    GraphQuery,
    RelationshipType,
    CommunityDetectionResult
)

router = APIRouter()


class CreateNodeRequest(BaseModel):
    """Request model for creating a graph node"""
    id: str
    title: str
    content_type: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateRelationshipRequest(BaseModel):
    """Request model for creating a graph relationship"""
    from_node: str
    to_node: str
    relationship_type: RelationshipType
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelatedContentQuery(BaseModel):
    """Request model for finding related content"""
    node_id: str
    relationship_types: List[RelationshipType] = Field(default_factory=list)
    max_depth: int = 2
    min_weight: float = 0.1
    limit: int = 50


class ShortestPathQuery(BaseModel):
    """Request model for finding shortest path"""
    from_node: str
    to_node: str
    relationship_types: List[RelationshipType] = Field(default_factory=list)
    max_depth: int = 6


class CommunityDetectionQuery(BaseModel):
    """Request model for community detection"""
    algorithm: str = "louvain"
    min_community_size: int = 3
    relationship_types: List[RelationshipType] = Field(default_factory=list)


class CentralityQuery(BaseModel):
    """Request model for centrality calculation"""
    algorithm: str = "pagerank"
    relationship_types: List[RelationshipType] = Field(default_factory=list)
    limit: int = 20


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_graph_service(
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize the Neo4j graph service and create schema
    """
    try:
        await neo4j_graph_service.initialize()
        return {
            "status": "success",
            "message": "Neo4j graph service initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post("/nodes", response_model=Dict[str, Any])
async def create_node(
    request: CreateNodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new graph node
    
    Args:
        request: Node creation data
        
    Returns:
        Creation result
    """
    try:
        from datetime import datetime
        
        node = GraphNode(
            id=request.id,
            title=request.title,
            content_type=request.content_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tags=request.tags,
            metadata=request.metadata
        )
        
        success = await neo4j_graph_service.create_node(node)
        
        if success:
            return {
                "status": "success",
                "node_id": request.id,
                "message": "Node created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create node")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Node creation failed: {str(e)}")


@router.post("/relationships", response_model=Dict[str, Any])
async def create_relationship(
    request: CreateRelationshipRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a relationship between two nodes
    
    Args:
        request: Relationship creation data
        
    Returns:
        Creation result
    """
    try:
        from datetime import datetime
        
        relationship = GraphRelationship(
            from_node=request.from_node,
            to_node=request.to_node,
            relationship_type=request.relationship_type,
            weight=request.weight,
            confidence=request.confidence,
            metadata=request.metadata,
            created_at=datetime.utcnow()
        )
        
        success = await neo4j_graph_service.create_relationship(relationship)
        
        if success:
            return {
                "status": "success",
                "relationship": {
                    "from_node": request.from_node,
                    "to_node": request.to_node,
                    "type": request.relationship_type.value
                },
                "message": "Relationship created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create relationship")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relationship creation failed: {str(e)}")


@router.post("/query/related", response_model=Dict[str, Any])
async def find_related_content(
    query: RelatedContentQuery,
    current_user: dict = Depends(get_current_user)
):
    """
    Find content related to a given node using graph traversal
    
    Args:
        query: Related content search parameters
        
    Returns:
        List of related content with relationship paths
    """
    try:
        related_content = await neo4j_graph_service.find_related_content(
            node_id=query.node_id,
            relationship_types=query.relationship_types or None,
            max_depth=query.max_depth,
            min_weight=query.min_weight,
            limit=query.limit
        )
        
        return {
            "status": "success",
            "node_id": query.node_id,
            "related_content": related_content,
            "count": len(related_content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Related content query failed: {str(e)}")


@router.post("/query/shortest-path", response_model=Dict[str, Any])
async def find_shortest_path(
    query: ShortestPathQuery,
    current_user: dict = Depends(get_current_user)
):
    """
    Find the shortest path between two nodes
    
    Args:
        query: Shortest path search parameters
        
    Returns:
        Shortest path information or None if no path exists
    """
    try:
        path = await neo4j_graph_service.find_shortest_path(
            from_node=query.from_node,
            to_node=query.to_node,
            relationship_types=query.relationship_types or None,
            max_depth=query.max_depth
        )
        
        if path:
            return {
                "status": "success",
                "path": path,
                "path_exists": True
            }
        else:
            return {
                "status": "success",
                "path": None,
                "path_exists": False,
                "message": "No path found between nodes"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shortest path query failed: {str(e)}")


@router.post("/analysis/communities", response_model=Dict[str, Any])
async def detect_communities(
    query: CommunityDetectionQuery,
    current_user: dict = Depends(get_current_user)
):
    """
    Detect communities in the knowledge graph
    
    Args:
        query: Community detection parameters
        
    Returns:
        List of detected communities
    """
    try:
        communities = await neo4j_graph_service.detect_communities(
            algorithm=query.algorithm,
            min_community_size=query.min_community_size,
            relationship_types=query.relationship_types or None
        )
        
        return {
            "status": "success",
            "algorithm": query.algorithm,
            "communities": [community.dict() for community in communities],
            "community_count": len(communities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Community detection failed: {str(e)}")


@router.post("/analysis/centrality", response_model=Dict[str, Any])
async def calculate_centrality(
    query: CentralityQuery,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate node centrality using various algorithms
    
    Args:
        query: Centrality calculation parameters
        
    Returns:
        List of nodes with centrality scores
    """
    try:
        centrality_results = await neo4j_graph_service.calculate_centrality(
            algorithm=query.algorithm,
            relationship_types=query.relationship_types or None,
            limit=query.limit
        )
        
        return {
            "status": "success",
            "algorithm": query.algorithm,
            "centrality_results": centrality_results,
            "result_count": len(centrality_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centrality calculation failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_graph_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive graph statistics
    
    Returns:
        Graph statistics including nodes, relationships, and metrics
    """
    try:
        stats = await neo4j_graph_service.get_graph_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics query failed: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def neo4j_health_check():
    """
    Health check for Neo4j graph service
    
    Returns:
        Health status and basic connectivity information
    """
    try:
        health_status = await neo4j_graph_service.health_check()
        
        return {
            "status": "success",
            "health": health_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/relationship-types", response_model=Dict[str, Any])
async def get_relationship_types():
    """
    Get available relationship types
    
    Returns:
        List of available relationship types with descriptions
    """
    try:
        relationship_types = [
            {
                "type": rt.value,
                "description": {
                    RelationshipType.PREREQUISITE: "A requires B to understand",
                    RelationshipType.RELATED: "A and B are topically related",
                    RelationshipType.REFERENCES: "A mentions or cites B",
                    RelationshipType.DEPENDS_ON: "A builds upon B",
                    RelationshipType.SIMILAR_TO: "A is similar to B",
                    RelationshipType.PART_OF: "A is part of B",
                    RelationshipType.CREATED_BY: "A was created by B",
                    RelationshipType.TAGGED_WITH: "A has tag B"
                }.get(rt, "Relationship type")
            }
            for rt in RelationshipType
        ]
        
        return {
            "status": "success",
            "relationship_types": relationship_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationship types: {str(e)}")


@router.get("/algorithms", response_model=Dict[str, Any])
async def get_available_algorithms():
    """
    Get available graph algorithms
    
    Returns:
        List of available algorithms for community detection and centrality
    """
    try:
        algorithms = {
            "community_detection": [
                {
                    "name": "louvain",
                    "description": "Louvain algorithm for community detection",
                    "complexity": "O(m log n)",
                    "best_for": "Large graphs with clear community structure"
                },
                {
                    "name": "label_propagation",
                    "description": "Label propagation algorithm",
                    "complexity": "O(m + n)",
                    "best_for": "Fast community detection on large graphs"
                }
            ],
            "centrality": [
                {
                    "name": "pagerank",
                    "description": "PageRank centrality algorithm",
                    "complexity": "O(n + m)",
                    "best_for": "Identifying important nodes in directed graphs"
                },
                {
                    "name": "betweenness",
                    "description": "Betweenness centrality algorithm",
                    "complexity": "O(n³)",
                    "best_for": "Finding nodes that act as bridges"
                },
                {
                    "name": "closeness",
                    "description": "Closeness centrality algorithm",
                    "complexity": "O(n²)",
                    "best_for": "Identifying nodes with shortest paths to all others"
                }
            ]
        }
        
        return {
            "status": "success",
            "algorithms": algorithms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get algorithms: {str(e)}")


@router.delete("/nodes/{node_id}", response_model=Dict[str, Any])
async def delete_node(
    node_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a graph node and all its relationships
    
    Args:
        node_id: ID of the node to delete
        
    Returns:
        Deletion result
    """
    try:
        async with neo4j_graph_service.driver.session() as session:
            query = """
            MATCH (n:Content {id: $node_id})
            DETACH DELETE n
            RETURN count(n) as deleted_count
            """
            
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if record and record["deleted_count"] > 0:
                return {
                    "status": "success",
                    "node_id": node_id,
                    "message": "Node and all relationships deleted successfully"
                }
            else:
                return {
                    "status": "not_found",
                    "node_id": node_id,
                    "message": "Node not found"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Node deletion failed: {str(e)}")


@router.delete("/relationships", response_model=Dict[str, Any])
async def delete_relationship(
    from_node: str = Query(..., description="Source node ID"),
    to_node: str = Query(..., description="Target node ID"),
    relationship_type: RelationshipType = Query(..., description="Relationship type"),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific relationship between two nodes
    
    Args:
        from_node: Source node ID
        to_node: Target node ID
        relationship_type: Type of relationship to delete
        
    Returns:
        Deletion result
    """
    try:
        async with neo4j_graph_service.driver.session() as session:
            query = f"""
            MATCH (from:Content {{id: $from_id}})-[r:{relationship_type.value}]->(to:Content {{id: $to_id}})
            DELETE r
            RETURN count(r) as deleted_count
            """
            
            result = await session.run(query, from_id=from_node, to_id=to_node)
            record = await result.single()
            
            if record and record["deleted_count"] > 0:
                return {
                    "status": "success",
                    "relationship": {
                        "from_node": from_node,
                        "to_node": to_node,
                        "type": relationship_type.value
                    },
                    "message": "Relationship deleted successfully"
                }
            else:
                return {
                    "status": "not_found",
                    "relationship": {
                        "from_node": from_node,
                        "to_node": to_node,
                        "type": relationship_type.value
                    },
                    "message": "Relationship not found"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relationship deletion failed: {str(e)}")


# Add to main router
def include_neo4j_graph_routes(main_router):
    """Include Neo4j graph routes in main router"""
    main_router.include_router(
        router,
        prefix="/api/graph",
        tags=["neo4j_graph"]
    )