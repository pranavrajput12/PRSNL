"""
Neo4j Cypher Query Service - Advanced graph query interface
Provides safe Cypher query execution with validation and templates
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.neo4j_graph_service import neo4j_graph_service, RelationshipType

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of Cypher queries"""
    READ = "read"
    WRITE = "write"
    ANALYSIS = "analysis"
    MAINTENANCE = "maintenance"


class SecurityLevel(str, Enum):
    """Security levels for query execution"""
    SAFE = "safe"          # Pre-defined templates only
    RESTRICTED = "restricted"  # Limited Cypher with validation
    ADVANCED = "advanced"      # Full Cypher with admin approval


@dataclass
class QueryTemplate:
    """Represents a predefined Cypher query template"""
    name: str
    description: str
    query: str
    parameters: List[str]
    query_type: QueryType
    security_level: SecurityLevel
    example_params: Dict[str, Any]
    expected_results: str


@dataclass
class QueryResult:
    """Represents the result of a Cypher query execution"""
    query: str
    parameters: Dict[str, Any]
    results: List[Dict[str, Any]]
    execution_time: float
    record_count: int
    query_type: QueryType
    timestamp: datetime
    warnings: List[str] = None


class Neo4jCypherService:
    """
    Advanced Cypher query service for complex graph operations
    
    Features:
    - Safe query execution with validation
    - Pre-defined query templates for common operations
    - Complex path-finding algorithms
    - Performance optimization and caching
    - Query security and access control
    """
    
    def __init__(self):
        self.query_templates = {}
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.max_results = 1000
        self.query_timeout = 30  # seconds
        self._setup_query_templates()
        
    def _setup_query_templates(self):
        """Initialize predefined query templates"""
        self.query_templates = {
            
            # Path Finding Templates
            "find_shortest_path": QueryTemplate(
                name="find_shortest_path",
                description="Find the shortest path between two nodes",
                query="""
                MATCH path = shortestPath((start:Content {id: $start_id})-[*1..{max_depth}]-(end:Content {id: $end_id}))
                RETURN 
                    [node in nodes(path) | {id: node.id, title: node.title, content_type: node.content_type}] as nodes,
                    [rel in relationships(path) | {type: type(rel), weight: rel.weight}] as relationships,
                    length(path) as path_length
                """,
                parameters=["start_id", "end_id", "max_depth"],
                query_type=QueryType.READ,
                security_level=SecurityLevel.SAFE,
                example_params={"start_id": "item1", "end_id": "item2", "max_depth": 6},
                expected_results="Path information with nodes and relationships"
            ),
            
            "find_all_paths": QueryTemplate(
                name="find_all_paths",
                description="Find all paths between two nodes up to a maximum depth",
                query="""
                MATCH path = (start:Content {id: $start_id})-[*1..{max_depth}]-(end:Content {id: $end_id})
                WITH path, 
                     reduce(totalWeight = 0, rel in relationships(path) | totalWeight + rel.weight) as total_weight,
                     length(path) as path_length
                RETURN 
                    [node in nodes(path) | {id: node.id, title: node.title}] as nodes,
                    [rel in relationships(path) | {type: type(rel), weight: rel.weight}] as relationships,
                    total_weight,
                    path_length
                ORDER BY total_weight DESC, path_length ASC
                LIMIT $limit
                """,
                parameters=["start_id", "end_id", "max_depth", "limit"],
                query_type=QueryType.READ,
                security_level=SecurityLevel.SAFE,
                example_params={"start_id": "item1", "end_id": "item2", "max_depth": 4, "limit": 10},
                expected_results="List of paths with weights and lengths"
            ),
            
            "find_knowledge_path": QueryTemplate(
                name="find_knowledge_path",
                description="Find learning path through prerequisite relationships",
                query="""
                MATCH path = (start:Content {id: $start_id})-[:PREREQUISITE*1..{max_depth}]->(end:Content {id: $end_id})
                WITH path, 
                     reduce(totalWeight = 0, rel in relationships(path) | totalWeight + rel.weight) as total_weight,
                     length(path) as path_length
                RETURN 
                    [node in nodes(path) | {id: node.id, title: node.title, content_type: node.content_type}] as learning_path,
                    total_weight as difficulty_score,
                    path_length as steps_required
                ORDER BY total_weight DESC, path_length ASC
                LIMIT $limit
                """,
                parameters=["start_id", "end_id", "max_depth", "limit"],
                query_type=QueryType.READ,
                security_level=SecurityLevel.SAFE,
                example_params={"start_id": "basic_concept", "end_id": "advanced_topic", "max_depth": 6, "limit": 5},
                expected_results="Ordered learning paths with difficulty scores"
            ),
            
            # Neighborhood Analysis Templates
            "expand_neighborhood": QueryTemplate(
                name="expand_neighborhood",
                description="Expand neighborhood around a node with configurable depth and filters",
                query="""
                MATCH (center:Content {id: $center_id})
                CALL {
                    WITH center
                    MATCH path = (center)-[r*1..{depth}]-(neighbor:Content)
                    WHERE ALL(rel in relationships(path) WHERE rel.weight >= $min_weight)
                    AND ($content_types IS NULL OR neighbor.content_type IN $content_types)
                    RETURN neighbor, path, 
                           reduce(totalWeight = 0, rel in relationships(path) | totalWeight + rel.weight) as path_weight,
                           length(path) as distance
                }
                RETURN DISTINCT
                    neighbor.id as id,
                    neighbor.title as title,
                    neighbor.content_type as content_type,
                    path_weight / distance as relevance_score,
                    distance,
                    [rel in relationships(path) | type(rel)] as relationship_path
                ORDER BY relevance_score DESC, distance ASC
                LIMIT $limit
                """,
                parameters=["center_id", "depth", "min_weight", "content_types", "limit"],
                query_type=QueryType.READ,
                security_level=SecurityLevel.SAFE,
                example_params={"center_id": "item1", "depth": 2, "min_weight": 0.1, "content_types": ["item", "document"], "limit": 50},
                expected_results="Neighborhood nodes with relevance scores"
            ),
            
            "find_influencers": QueryTemplate(
                name="find_influencers",
                description="Find nodes with high influence in the graph using degree centrality",
                query="""
                MATCH (n:Content)
                WITH n, 
                     size((n)-[]-()) as total_connections,
                     size((n)-[:REFERENCES]-()) as reference_count,
                     size((n)-[:PREREQUISITE]-()) as prerequisite_count
                WHERE total_connections >= $min_connections
                RETURN 
                    n.id as id,
                    n.title as title,
                    n.content_type as content_type,
                    total_connections,
                    reference_count,
                    prerequisite_count,
                    (total_connections + reference_count * 2 + prerequisite_count * 3) as influence_score
                ORDER BY influence_score DESC
                LIMIT $limit
                """,
                parameters=["min_connections", "limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"min_connections": 3, "limit": 20},
                expected_results="Nodes with high influence scores"
            ),
            
            # Pattern Discovery Templates
            "find_common_patterns": QueryTemplate(
                name="find_common_patterns",
                description="Find common relationship patterns in the graph",
                query="""
                MATCH (a:Content)-[r1]->(b:Content)-[r2]->(c:Content)
                WHERE a.id <> c.id
                WITH type(r1) as rel1_type, type(r2) as rel2_type, count(*) as pattern_count
                WHERE pattern_count >= $min_occurrences
                RETURN 
                    rel1_type + " -> " + rel2_type as pattern,
                    pattern_count,
                    pattern_count * 100.0 / (SELECT count(*) FROM (MATCH ()-[r]->() RETURN r)) as percentage
                ORDER BY pattern_count DESC
                LIMIT $limit
                """,
                parameters=["min_occurrences", "limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"min_occurrences": 5, "limit": 20},
                expected_results="Common relationship patterns with frequencies"
            ),
            
            "find_knowledge_gaps": QueryTemplate(
                name="find_knowledge_gaps",
                description="Find nodes that should be connected but aren't",
                query="""
                MATCH (a:Content)-[:RELATED]->(intermediate:Content)-[:RELATED]->(b:Content)
                WHERE a.id <> b.id
                AND NOT (a)-[:RELATED]-(b)
                AND a.content_type = $content_type
                AND b.content_type = $content_type
                WITH a, b, count(intermediate) as common_connections
                WHERE common_connections >= $min_common
                RETURN 
                    a.id as node1_id,
                    a.title as node1_title,
                    b.id as node2_id,
                    b.title as node2_title,
                    common_connections,
                    common_connections * 100.0 / (SELECT count(*) FROM (MATCH (a)-[:RELATED]->() RETURN a)) as connection_strength
                ORDER BY common_connections DESC
                LIMIT $limit
                """,
                parameters=["content_type", "min_common", "limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"content_type": "item", "min_common": 2, "limit": 30},
                expected_results="Potential missing connections with strength scores"
            ),
            
            # Clustering and Community Templates
            "find_dense_clusters": QueryTemplate(
                name="find_dense_clusters",
                description="Find densely connected clusters of nodes",
                query="""
                MATCH (n:Content)
                WITH n, [(n)-[r]-(m:Content) | {node: m, weight: r.weight}] as connections
                WHERE size(connections) >= $min_cluster_size
                UNWIND connections as conn
                WITH n, conn.node as connected_node, conn.weight as weight
                MATCH (connected_node)-[r2]-(other:Content)
                WHERE other IN [c.node FOR c IN connections]
                WITH n, connected_node, count(other) as internal_connections, avg(weight) as avg_weight
                WHERE internal_connections >= $min_internal_connections
                RETURN 
                    n.id as cluster_center,
                    n.title as center_title,
                    collect({id: connected_node.id, title: connected_node.title, internal_connections: internal_connections}) as cluster_members,
                    avg_weight as cluster_strength,
                    size(cluster_members) as cluster_size
                ORDER BY cluster_size DESC, cluster_strength DESC
                LIMIT $limit
                """,
                parameters=["min_cluster_size", "min_internal_connections", "limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"min_cluster_size": 4, "min_internal_connections": 2, "limit": 15},
                expected_results="Dense clusters with member information"
            ),
            
            # Temporal Analysis Templates
            "analyze_growth_patterns": QueryTemplate(
                name="analyze_growth_patterns",
                description="Analyze how the graph has grown over time",
                query="""
                MATCH (n:Content)
                WITH n, datetime(n.created_at) as creation_date
                WITH date(creation_date) as creation_day, count(n) as nodes_created
                ORDER BY creation_day
                WITH collect({day: creation_day, count: nodes_created}) as daily_growth
                UNWIND range(0, size(daily_growth)-1) as i
                WITH daily_growth[i] as current_day, 
                     reduce(total = 0, j in range(0, i) | total + daily_growth[j].count) as cumulative_nodes
                RETURN 
                    current_day.day as date,
                    current_day.count as new_nodes,
                    cumulative_nodes as total_nodes,
                    CASE 
                        WHEN i > 0 THEN (current_day.count - daily_growth[i-1].count) * 100.0 / daily_growth[i-1].count 
                        ELSE 0 
                    END as growth_rate
                ORDER BY date DESC
                LIMIT $limit
                """,
                parameters=["limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"limit": 30},
                expected_results="Growth patterns over time"
            ),
            
            # Recommendation Templates
            "content_recommendations": QueryTemplate(
                name="content_recommendations",
                description="Generate content recommendations based on user interaction patterns",
                query="""
                MATCH (user_content:Content {id: $user_id})
                MATCH (user_content)-[r1:RELATED|REFERENCES]->(related:Content)
                MATCH (related)-[r2:RELATED|REFERENCES]->(recommended:Content)
                WHERE NOT (user_content)-[:RELATED|REFERENCES]-(recommended)
                AND recommended.content_type = $content_type
                WITH recommended, 
                     count(DISTINCT related) as common_connections,
                     avg(r1.weight + r2.weight) as avg_path_weight
                WHERE common_connections >= $min_common
                RETURN 
                    recommended.id as id,
                    recommended.title as title,
                    recommended.content_type as content_type,
                    common_connections,
                    avg_path_weight,
                    (common_connections * avg_path_weight) as recommendation_score
                ORDER BY recommendation_score DESC
                LIMIT $limit
                """,
                parameters=["user_id", "content_type", "min_common", "limit"],
                query_type=QueryType.ANALYSIS,
                security_level=SecurityLevel.SAFE,
                example_params={"user_id": "user123", "content_type": "item", "min_common": 2, "limit": 10},
                expected_results="Recommended content with scores"
            )
        }
    
    async def execute_template(
        self,
        template_name: str,
        parameters: Dict[str, Any],
        user_id: str = None
    ) -> QueryResult:
        """
        Execute a predefined query template with parameters
        
        Args:
            template_name: Name of the template to execute
            parameters: Parameters for the template
            user_id: User ID for access control
            
        Returns:
            Query execution results
        """
        if template_name not in self.query_templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.query_templates[template_name]
        
        # Validate parameters
        missing_params = [p for p in template.parameters if p not in parameters]
        if missing_params:
            raise ValueError(f"Missing parameters: {missing_params}")
        
        # Format query with parameters
        formatted_query = template.query.format(**parameters)
        
        return await self.execute_query(
            query=formatted_query,
            parameters=parameters,
            query_type=template.query_type,
            security_level=template.security_level,
            user_id=user_id
        )
    
    async def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        query_type: QueryType = QueryType.READ,
        security_level: SecurityLevel = SecurityLevel.RESTRICTED,
        user_id: str = None
    ) -> QueryResult:
        """
        Execute a raw Cypher query with security validation
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            query_type: Type of query (read/write/analysis)
            security_level: Security level for execution
            user_id: User ID for access control
            
        Returns:
            Query execution results
        """
        start_time = datetime.utcnow()
        
        # Validate query security
        await self._validate_query_security(query, query_type, security_level)
        
        # Check cache for read queries
        if query_type == QueryType.READ:
            cache_key = self._generate_cache_key(query, parameters)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
        
        try:
            # Execute query
            async with neo4j_graph_service.driver.session() as session:
                result = await session.run(query, parameters or {})
                
                # Collect results
                records = []
                async for record in result:
                    records.append(dict(record))
                
                # Limit results
                if len(records) > self.max_results:
                    records = records[:self.max_results]
                    warnings = [f"Results limited to {self.max_results} records"]
                else:
                    warnings = []
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                query_result = QueryResult(
                    query=query,
                    parameters=parameters or {},
                    results=records,
                    execution_time=execution_time,
                    record_count=len(records),
                    query_type=query_type,
                    timestamp=datetime.utcnow(),
                    warnings=warnings
                )
                
                # Cache read queries
                if query_type == QueryType.READ:
                    self._cache_result(cache_key, query_result)
                
                return query_result
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def _validate_query_security(
        self,
        query: str,
        query_type: QueryType,
        security_level: SecurityLevel
    ):
        """Validate query for security concerns"""
        
        # Convert to lowercase for analysis
        query_lower = query.lower()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'drop', 'delete', 'remove', 'detach delete',
            'create constraint', 'drop constraint',
            'create index', 'drop index',
            'call apoc.', 'call gds.'
        ]
        
        if security_level == SecurityLevel.SAFE:
            # Only allow if it's a known template
            return
        
        if security_level == SecurityLevel.RESTRICTED:
            # Check for dangerous operations
            for keyword in dangerous_keywords:
                if keyword in query_lower:
                    raise ValueError(f"Dangerous operation '{keyword}' not allowed in restricted mode")
            
            # Limit query complexity
            if query_lower.count('match') > 5:
                raise ValueError("Query too complex for restricted mode")
        
        # ADVANCED level allows most operations but with logging
        if security_level == SecurityLevel.ADVANCED:
            logger.warning(f"Advanced query executed: {query[:100]}...")
    
    def _generate_cache_key(self, query: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for query and parameters"""
        import hashlib
        import json
        
        query_hash = hashlib.md5(query.encode()).hexdigest()
        params_hash = hashlib.md5(json.dumps(parameters or {}, sort_keys=True).encode()).hexdigest()
        
        return f"{query_hash}_{params_hash}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[QueryResult]:
        """Get cached query result if valid"""
        if cache_key in self.query_cache:
            cached_item = self.query_cache[cache_key]
            if (datetime.utcnow() - cached_item['timestamp']).total_seconds() < self.cache_ttl:
                return cached_item['result']
            else:
                # Remove expired cache
                del self.query_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: QueryResult):
        """Cache query result"""
        self.query_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }
        
        # Limit cache size
        if len(self.query_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.query_cache.keys(), 
                           key=lambda k: self.query_cache[k]['timestamp'])
            del self.query_cache[oldest_key]
    
    def get_template_list(self) -> List[Dict[str, Any]]:
        """Get list of available query templates"""
        return [
            {
                "name": template.name,
                "description": template.description,
                "parameters": template.parameters,
                "query_type": template.query_type.value,
                "security_level": template.security_level.value,
                "example_params": template.example_params,
                "expected_results": template.expected_results
            }
            for template in self.query_templates.values()
        ]
    
    def get_template_details(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific template"""
        if template_name not in self.query_templates:
            return None
        
        template = self.query_templates[template_name]
        return {
            "name": template.name,
            "description": template.description,
            "query": template.query,
            "parameters": template.parameters,
            "query_type": template.query_type.value,
            "security_level": template.security_level.value,
            "example_params": template.example_params,
            "expected_results": template.expected_results
        }
    
    async def analyze_query_performance(self, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze query performance without executing"""
        try:
            async with neo4j_graph_service.driver.session() as session:
                # Use EXPLAIN to get query plan
                explain_query = f"EXPLAIN {query}"
                result = await session.run(explain_query, parameters or {})
                
                plan = await result.single()
                
                return {
                    "query": query,
                    "estimated_cost": "Analysis not available in community edition",
                    "query_plan": str(plan) if plan else "No plan available",
                    "recommendations": [
                        "Consider adding indexes on frequently queried properties",
                        "Use LIMIT to restrict result size",
                        "Avoid Cartesian products in MATCH clauses"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "recommendations": [
                    "Check query syntax",
                    "Verify parameter names match query placeholders"
                ]
            }
    
    def clear_cache(self):
        """Clear query result cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.query_cache),
            "cache_ttl": self.cache_ttl,
            "max_results": self.max_results,
            "query_timeout": self.query_timeout
        }


# Singleton instance
neo4j_cypher_service = Neo4jCypherService()