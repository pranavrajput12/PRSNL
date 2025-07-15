"""
Neo4j Graph Service - True graph relationship storage and analysis
Replaces JSONB metadata approach with proper graph database
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from pydantic import BaseModel, Field

from app.config import settings
from app.services.http_client_factory import http_client_factory, ClientType

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of relationships between content items"""
    PREREQUISITE = "PREREQUISITE"    # A requires B to understand
    RELATED = "RELATED"              # A and B are topically related
    REFERENCES = "REFERENCES"        # A mentions or cites B
    DEPENDS_ON = "DEPENDS_ON"        # A builds upon B
    SIMILAR_TO = "SIMILAR_TO"        # A is similar to B
    PART_OF = "PART_OF"              # A is part of B
    CREATED_BY = "CREATED_BY"        # A was created by B
    TAGGED_WITH = "TAGGED_WITH"      # A has tag B


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    title: str
    content_type: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class GraphRelationship:
    """Represents a relationship between two nodes"""
    from_node: str
    to_node: str
    relationship_type: RelationshipType
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    created_at: datetime = None


class GraphQuery(BaseModel):
    """Query model for graph operations"""
    node_id: str
    relationship_types: List[RelationshipType] = Field(default_factory=list)
    max_depth: int = 2
    min_weight: float = 0.1
    include_metadata: bool = True


class CommunityDetectionResult(BaseModel):
    """Result from community detection algorithm"""
    community_id: str
    nodes: List[str]
    size: int
    density: float
    internal_edges: int
    external_edges: int
    topics: List[str] = Field(default_factory=list)


class Neo4jGraphService:
    """
    Neo4j-based graph service for relationship storage and analysis
    
    Features:
    - True graph relationship storage
    - Cypher query language support
    - Built-in graph algorithms (community detection, centrality, shortest paths)
    - Hybrid PostgreSQL + Neo4j architecture
    - Incremental sync from JSONB metadata
    """
    
    def __init__(self):
        self.driver = None
        self.neo4j_uri = f"bolt://localhost:{settings.NEO4J_BOLT_PORT or 7687}"
        self.neo4j_user = settings.NEO4J_USER or "neo4j"
        self.neo4j_password = settings.NEO4J_PASSWORD or "prsnl_graph_2024"
        self.connection_pool_size = 10
        self.max_connection_lifetime = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize Neo4j driver and create schema"""
        try:
            # Create async driver
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password),
                max_connection_pool_size=self.connection_pool_size,
                max_connection_lifetime=self.max_connection_lifetime
            )
            
            # Verify connectivity
            await self.driver.verify_connectivity()
            
            # Create initial schema
            await self._create_schema()
            
            logger.info("Neo4j Graph Service initialized successfully")
            
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            raise
    
    async def _create_schema(self):
        """Create indexes and constraints for optimal performance"""
        schema_queries = [
            # Node constraints and indexes
            "CREATE CONSTRAINT content_id IF NOT EXISTS FOR (n:Content) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (n:Tag) REQUIRE n.name IS UNIQUE",
            "CREATE INDEX content_type_idx IF NOT EXISTS FOR (n:Content) ON (n.content_type)",
            "CREATE INDEX content_title_idx IF NOT EXISTS FOR (n:Content) ON (n.title)",
            "CREATE INDEX content_created_idx IF NOT EXISTS FOR (n:Content) ON (n.created_at)",
            "CREATE INDEX tag_name_idx IF NOT EXISTS FOR (n:Tag) ON (n.name)",
            
            # Relationship indexes
            "CREATE INDEX rel_type_idx IF NOT EXISTS FOR ()-[r:PREREQUISITE]-() ON (r.weight)",
            "CREATE INDEX rel_weight_idx IF NOT EXISTS FOR ()-[r:RELATED]-() ON (r.weight)",
            "CREATE INDEX rel_confidence_idx IF NOT EXISTS FOR ()-[r:REFERENCES]-() ON (r.confidence)",
        ]
        
        async with self.driver.session() as session:
            for query in schema_queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Schema query failed (may already exist): {query} - {e}")
    
    async def create_node(self, node: GraphNode) -> bool:
        """Create or update a content node"""
        try:
            async with self.driver.session() as session:
                query = """
                MERGE (n:Content {id: $id})
                SET n.title = $title,
                    n.content_type = $content_type,
                    n.created_at = datetime($created_at),
                    n.updated_at = datetime($updated_at),
                    n.metadata = $metadata
                RETURN n
                """
                
                result = await session.run(
                    query,
                    id=node.id,
                    title=node.title,
                    content_type=node.content_type,
                    created_at=node.created_at.isoformat(),
                    updated_at=node.updated_at.isoformat(),
                    metadata=node.metadata or {}
                )
                
                # Create tag relationships
                if node.tags:
                    for tag in node.tags:
                        await self._create_tag_relationship(node.id, tag)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create node {node.id}: {e}")
            return False
    
    async def _create_tag_relationship(self, node_id: str, tag: str):
        """Create a tag relationship for a node"""
        async with self.driver.session() as session:
            query = """
            MERGE (t:Tag {name: $tag})
            WITH t
            MATCH (n:Content {id: $node_id})
            MERGE (n)-[:TAGGED_WITH]->(t)
            """
            
            await session.run(query, node_id=node_id, tag=tag)
    
    async def create_relationship(self, relationship: GraphRelationship) -> bool:
        """Create a relationship between two nodes"""
        try:
            async with self.driver.session() as session:
                query = f"""
                MATCH (from:Content {{id: $from_id}})
                MATCH (to:Content {{id: $to_id}})
                MERGE (from)-[r:{relationship.relationship_type.value}]->(to)
                SET r.weight = $weight,
                    r.confidence = $confidence,
                    r.metadata = $metadata,
                    r.created_at = datetime($created_at)
                RETURN r
                """
                
                await session.run(
                    query,
                    from_id=relationship.from_node,
                    to_id=relationship.to_node,
                    weight=relationship.weight,
                    confidence=relationship.confidence,
                    metadata=relationship.metadata or {},
                    created_at=(relationship.created_at or datetime.utcnow()).isoformat()
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create relationship {relationship.from_node} -> {relationship.to_node}: {e}")
            return False
    
    async def find_related_content(
        self,
        node_id: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 2,
        min_weight: float = 0.1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find content related to a given node using graph traversal
        
        Args:
            node_id: Starting node ID
            relationship_types: Types of relationships to follow
            max_depth: Maximum traversal depth
            min_weight: Minimum relationship weight
            limit: Maximum results to return
            
        Returns:
            List of related content with relationship paths
        """
        try:
            async with self.driver.session() as session:
                # Build relationship type filter
                if relationship_types:
                    rel_types = "|".join([rt.value for rt in relationship_types])
                    rel_filter = f":{rel_types}"
                else:
                    rel_filter = ""
                
                query = f"""
                MATCH path = (start:Content {{id: $node_id}})-[r{rel_filter}*1..{max_depth}]-(related:Content)
                WHERE ALL(rel in relationships(path) WHERE rel.weight >= $min_weight)
                WITH related, path, 
                     reduce(totalWeight = 0, rel in relationships(path) | totalWeight + rel.weight) as path_weight,
                     length(path) as path_length
                RETURN DISTINCT 
                    related.id as id,
                    related.title as title,
                    related.content_type as content_type,
                    related.created_at as created_at,
                    path_weight / path_length as relevance_score,
                    path_length as distance,
                    [rel in relationships(path) | type(rel)] as relationship_path
                ORDER BY relevance_score DESC, distance ASC
                LIMIT $limit
                """
                
                result = await session.run(
                    query,
                    node_id=node_id,
                    min_weight=min_weight,
                    limit=limit
                )
                
                related_content = []
                async for record in result:
                    related_content.append({
                        "id": record["id"],
                        "title": record["title"],
                        "content_type": record["content_type"],
                        "created_at": record["created_at"],
                        "relevance_score": record["relevance_score"],
                        "distance": record["distance"],
                        "relationship_path": record["relationship_path"]
                    })
                
                return related_content
                
        except Exception as e:
            logger.error(f"Failed to find related content for {node_id}: {e}")
            return []
    
    async def find_shortest_path(
        self,
        from_node: str,
        to_node: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 6
    ) -> Optional[Dict[str, Any]]:
        """
        Find the shortest path between two nodes
        
        Args:
            from_node: Source node ID
            to_node: Target node ID
            relationship_types: Types of relationships to follow
            max_depth: Maximum search depth
            
        Returns:
            Shortest path information or None if no path exists
        """
        try:
            async with self.driver.session() as session:
                # Build relationship type filter
                if relationship_types:
                    rel_types = "|".join([rt.value for rt in relationship_types])
                    rel_filter = f":{rel_types}"
                else:
                    rel_filter = ""
                
                query = f"""
                MATCH path = shortestPath((start:Content {{id: $from_id}})-[r{rel_filter}*1..{max_depth}]-(end:Content {{id: $to_id}}))
                WITH path, 
                     reduce(totalWeight = 0, rel in relationships(path) | totalWeight + rel.weight) as total_weight,
                     length(path) as path_length
                RETURN 
                    [node in nodes(path) | {{id: node.id, title: node.title, content_type: node.content_type}}] as nodes,
                    [rel in relationships(path) | {{type: type(rel), weight: rel.weight, confidence: rel.confidence}}] as relationships,
                    total_weight,
                    path_length
                ORDER BY total_weight DESC
                LIMIT 1
                """
                
                result = await session.run(
                    query,
                    from_id=from_node,
                    to_id=to_node
                )
                
                record = await result.single()
                if record:
                    return {
                        "nodes": record["nodes"],
                        "relationships": record["relationships"],
                        "total_weight": record["total_weight"],
                        "path_length": record["path_length"]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to find shortest path from {from_node} to {to_node}: {e}")
            return None
    
    async def detect_communities(
        self,
        algorithm: str = "louvain",
        min_community_size: int = 3,
        relationship_types: List[RelationshipType] = None
    ) -> List[CommunityDetectionResult]:
        """
        Detect communities in the knowledge graph
        
        Args:
            algorithm: Community detection algorithm ('louvain', 'label_propagation')
            min_community_size: Minimum size for a community
            relationship_types: Types of relationships to consider
            
        Returns:
            List of detected communities
        """
        try:
            async with self.driver.session() as session:
                # Build relationship type filter
                if relationship_types:
                    rel_types = "|".join([rt.value for rt in relationship_types])
                    rel_filter = f":{rel_types}"
                else:
                    rel_filter = ""
                
                # Create graph projection for GDS
                projection_query = f"""
                CALL gds.graph.project(
                    'knowledge-graph',
                    'Content',
                    {{
                        RELATIONSHIP: {{
                            type: '{rel_filter or "*"}',
                            properties: 'weight'
                        }}
                    }}
                )
                """
                
                try:
                    await session.run(projection_query)
                except Exception:
                    # Graph projection may already exist
                    pass
                
                # Run community detection
                if algorithm == "louvain":
                    community_query = """
                    CALL gds.louvain.stream('knowledge-graph')
                    YIELD nodeId, communityId
                    WITH gds.util.asNode(nodeId) AS node, communityId
                    RETURN communityId, 
                           collect(node.id) as node_ids,
                           collect(node.title) as node_titles,
                           count(*) as community_size
                    WHERE community_size >= $min_size
                    ORDER BY community_size DESC
                    """
                else:  # label_propagation
                    community_query = """
                    CALL gds.labelPropagation.stream('knowledge-graph')
                    YIELD nodeId, communityId
                    WITH gds.util.asNode(nodeId) AS node, communityId
                    RETURN communityId, 
                           collect(node.id) as node_ids,
                           collect(node.title) as node_titles,
                           count(*) as community_size
                    WHERE community_size >= $min_size
                    ORDER BY community_size DESC
                    """
                
                result = await session.run(community_query, min_size=min_community_size)
                
                communities = []
                async for record in result:
                    # Calculate community density
                    density = await self._calculate_community_density(
                        session, record["node_ids"]
                    )
                    
                    # Extract common topics from titles
                    topics = await self._extract_community_topics(
                        session, record["node_ids"]
                    )
                    
                    communities.append(CommunityDetectionResult(
                        community_id=str(record["communityId"]),
                        nodes=record["node_ids"],
                        size=record["community_size"],
                        density=density,
                        internal_edges=0,  # Will be calculated
                        external_edges=0,  # Will be calculated
                        topics=topics
                    ))
                
                # Clean up graph projection
                try:
                    await session.run("CALL gds.graph.drop('knowledge-graph')")
                except Exception:
                    pass
                
                return communities
                
        except Exception as e:
            logger.error(f"Failed to detect communities: {e}")
            return []
    
    async def _calculate_community_density(self, session, node_ids: List[str]) -> float:
        """Calculate the density of connections within a community"""
        try:
            query = """
            MATCH (n:Content)-[r]-(m:Content)
            WHERE n.id IN $node_ids AND m.id IN $node_ids
            RETURN count(r) as internal_edges, count(DISTINCT n) as node_count
            """
            
            result = await session.run(query, node_ids=node_ids)
            record = await result.single()
            
            if record and record["node_count"] > 1:
                internal_edges = record["internal_edges"]
                node_count = record["node_count"]
                max_edges = node_count * (node_count - 1)  # Directed graph
                return internal_edges / max_edges if max_edges > 0 else 0
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to calculate community density: {e}")
            return 0
    
    async def _extract_community_topics(self, session, node_ids: List[str]) -> List[str]:
        """Extract common topics/tags from a community"""
        try:
            query = """
            MATCH (n:Content)-[:TAGGED_WITH]->(t:Tag)
            WHERE n.id IN $node_ids
            RETURN t.name as topic, count(*) as frequency
            ORDER BY frequency DESC
            LIMIT 10
            """
            
            result = await session.run(query, node_ids=node_ids)
            topics = []
            async for record in result:
                topics.append(record["topic"])
            
            return topics
            
        except Exception as e:
            logger.error(f"Failed to extract community topics: {e}")
            return []
    
    async def calculate_centrality(
        self,
        algorithm: str = "pagerank",
        relationship_types: List[RelationshipType] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Calculate node centrality using various algorithms
        
        Args:
            algorithm: Centrality algorithm ('pagerank', 'betweenness', 'closeness')
            relationship_types: Types of relationships to consider
            limit: Maximum results to return
            
        Returns:
            List of nodes with centrality scores
        """
        try:
            async with self.driver.session() as session:
                # Build relationship type filter
                if relationship_types:
                    rel_types = "|".join([rt.value for rt in relationship_types])
                    rel_filter = f":{rel_types}"
                else:
                    rel_filter = ""
                
                # Create graph projection
                projection_query = f"""
                CALL gds.graph.project(
                    'centrality-graph',
                    'Content',
                    {{
                        RELATIONSHIP: {{
                            type: '{rel_filter or "*"}',
                            properties: 'weight'
                        }}
                    }}
                )
                """
                
                try:
                    await session.run(projection_query)
                except Exception:
                    pass
                
                # Run centrality algorithm
                if algorithm == "pagerank":
                    centrality_query = """
                    CALL gds.pageRank.stream('centrality-graph')
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN node.id as id, node.title as title, node.content_type as content_type, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """
                elif algorithm == "betweenness":
                    centrality_query = """
                    CALL gds.betweenness.stream('centrality-graph')
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN node.id as id, node.title as title, node.content_type as content_type, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """
                else:  # closeness
                    centrality_query = """
                    CALL gds.closeness.stream('centrality-graph')
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN node.id as id, node.title as title, node.content_type as content_type, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """
                
                result = await session.run(centrality_query, limit=limit)
                
                centrality_results = []
                async for record in result:
                    centrality_results.append({
                        "id": record["id"],
                        "title": record["title"],
                        "content_type": record["content_type"],
                        "centrality_score": record["score"],
                        "algorithm": algorithm
                    })
                
                # Clean up graph projection
                try:
                    await session.run("CALL gds.graph.drop('centrality-graph')")
                except Exception:
                    pass
                
                return centrality_results
                
        except Exception as e:
            logger.error(f"Failed to calculate centrality: {e}")
            return []
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        try:
            async with self.driver.session() as session:
                # Node statistics
                node_stats_query = """
                MATCH (n:Content)
                RETURN 
                    count(n) as total_nodes,
                    count(DISTINCT n.content_type) as content_types,
                    collect(DISTINCT n.content_type) as content_type_list
                """
                
                node_result = await session.run(node_stats_query)
                node_stats = await node_result.single()
                
                # Relationship statistics
                rel_stats_query = """
                MATCH ()-[r]->()
                RETURN 
                    count(r) as total_relationships,
                    count(DISTINCT type(r)) as relationship_types,
                    collect(DISTINCT type(r)) as relationship_type_list
                """
                
                rel_result = await session.run(rel_stats_query)
                rel_stats = await rel_result.single()
                
                # Tag statistics
                tag_stats_query = """
                MATCH (t:Tag)
                RETURN count(t) as total_tags
                """
                
                tag_result = await session.run(tag_stats_query)
                tag_stats = await tag_result.single()
                
                # Graph density
                density_query = """
                MATCH (n:Content)
                WITH count(n) as node_count
                MATCH ()-[r]->()
                WITH node_count, count(r) as edge_count
                RETURN 
                    node_count,
                    edge_count,
                    CASE 
                        WHEN node_count > 1 THEN toFloat(edge_count) / (node_count * (node_count - 1))
                        ELSE 0 
                    END as density
                """
                
                density_result = await session.run(density_query)
                density_stats = await density_result.single()
                
                return {
                    "nodes": {
                        "total": node_stats["total_nodes"],
                        "content_types": node_stats["content_types"],
                        "content_type_list": node_stats["content_type_list"]
                    },
                    "relationships": {
                        "total": rel_stats["total_relationships"],
                        "types": rel_stats["relationship_types"],
                        "type_list": rel_stats["relationship_type_list"]
                    },
                    "tags": {
                        "total": tag_stats["total_tags"]
                    },
                    "graph_metrics": {
                        "density": density_stats["density"],
                        "node_count": density_stats["node_count"],
                        "edge_count": density_stats["edge_count"]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j service health"""
        try:
            async with self.driver.session() as session:
                # Simple connectivity test
                result = await session.run("RETURN 1 as test")
                test_record = await result.single()
                
                if test_record["test"] == 1:
                    # Get basic stats
                    stats = await self.get_graph_statistics()
                    
                    return {
                        "status": "healthy",
                        "database": "neo4j",
                        "connectivity": True,
                        "node_count": stats.get("graph_metrics", {}).get("node_count", 0),
                        "edge_count": stats.get("graph_metrics", {}).get("edge_count", 0)
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "database": "neo4j",
                        "connectivity": False,
                        "error": "Test query failed"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "neo4j",
                "connectivity": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close the Neo4j driver"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j driver closed")


# Singleton instance
neo4j_graph_service = Neo4jGraphService()