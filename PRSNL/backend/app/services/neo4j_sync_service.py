"""
Neo4j Sync Service - Hybrid PostgreSQL + Neo4j data synchronization
Handles incremental migration from JSONB metadata to graph relationships
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from app.config import settings
from app.db.database import get_db_pool
from app.services.neo4j_graph_service import (
    neo4j_graph_service,
    GraphNode,
    GraphRelationship,
    RelationshipType
)

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Status of synchronization operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SyncOperation:
    """Represents a synchronization operation"""
    operation_type: str
    source_table: str
    source_id: str
    target_node_id: str
    status: SyncStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class Neo4jSyncService:
    """
    Service for synchronizing data between PostgreSQL and Neo4j
    
    Features:
    - Incremental sync from JSONB metadata to graph relationships
    - Bidirectional sync for nodes and relationships
    - Conflict resolution and data validation
    - Batch processing for large datasets
    - Rollback and recovery mechanisms
    """
    
    def __init__(self):
        self.db_pool = None
        self.sync_batch_size = 100
        self.sync_delay = 0.1  # seconds between batches
        self.relationship_parsers = {
            'items': self._parse_item_relationships,
            'repositories': self._parse_repository_relationships,
            'documents': self._parse_document_relationships
        }
        
    async def initialize(self):
        """Initialize database connections and sync infrastructure"""
        if not self.db_pool:
            self.db_pool = await get_db_pool()
        
        # Initialize Neo4j service
        await neo4j_graph_service.initialize()
        
        # Create sync tracking table
        await self._create_sync_tracking_table()
        
        logger.info("Neo4j Sync Service initialized successfully")
    
    async def _create_sync_tracking_table(self):
        """Create table for tracking sync operations"""
        async with self.db_pool.acquire() as conn:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS neo4j_sync_operations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                operation_type VARCHAR(50) NOT NULL,
                source_table VARCHAR(100) NOT NULL,
                source_id VARCHAR(255) NOT NULL,
                target_node_id VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                
                UNIQUE(source_table, source_id, operation_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_sync_operations_status 
                ON neo4j_sync_operations(status);
            CREATE INDEX IF NOT EXISTS idx_sync_operations_source 
                ON neo4j_sync_operations(source_table, source_id);
            """
            
            await conn.execute(create_table_query)
    
    async def sync_all_data(self, force_resync: bool = False) -> Dict[str, Any]:
        """
        Perform complete data synchronization from PostgreSQL to Neo4j
        
        Args:
            force_resync: If True, resync all data regardless of sync status
            
        Returns:
            Sync results summary
        """
        await self.initialize()
        
        sync_results = {
            "started_at": datetime.utcnow().isoformat(),
            "status": "in_progress",
            "tables_synced": {},
            "total_nodes_created": 0,
            "total_relationships_created": 0,
            "errors": []
        }
        
        try:
            # Sync nodes from each table
            for table_name in ['items', 'repositories', 'documents']:
                table_results = await self._sync_table_nodes(table_name, force_resync)
                sync_results["tables_synced"][table_name] = table_results
                sync_results["total_nodes_created"] += table_results.get("nodes_created", 0)
            
            # Sync relationships from JSONB metadata
            relationship_results = await self._sync_relationships_from_jsonb(force_resync)
            sync_results["total_relationships_created"] = relationship_results.get("relationships_created", 0)
            
            # Update sync status
            sync_results["status"] = "completed"
            sync_results["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Full sync completed: {sync_results['total_nodes_created']} nodes, {sync_results['total_relationships_created']} relationships")
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            sync_results["status"] = "failed"
            sync_results["errors"].append(str(e))
        
        return sync_results
    
    async def _sync_table_nodes(self, table_name: str, force_resync: bool = False) -> Dict[str, Any]:
        """Sync nodes from a specific PostgreSQL table to Neo4j"""
        results = {
            "table": table_name,
            "nodes_processed": 0,
            "nodes_created": 0,
            "nodes_updated": 0,
            "errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get records that need syncing
                if force_resync:
                    # Sync all records
                    query = f"""
                    SELECT id, title, created_at, updated_at, metadata
                    FROM {table_name}
                    ORDER BY created_at DESC
                    """
                    records = await conn.fetch(query)
                else:
                    # Sync only unsynced records
                    query = f"""
                    SELECT i.id, i.title, i.created_at, i.updated_at, i.metadata
                    FROM {table_name} i
                    LEFT JOIN neo4j_sync_operations s ON (
                        s.source_table = $1 AND 
                        s.source_id = i.id::text AND 
                        s.operation_type = 'create_node' AND
                        s.status = 'completed'
                    )
                    WHERE s.id IS NULL
                    ORDER BY i.created_at DESC
                    """
                    records = await conn.fetch(query, table_name)
                
                # Process records in batches
                for i in range(0, len(records), self.sync_batch_size):
                    batch = records[i:i + self.sync_batch_size]
                    
                    for record in batch:
                        try:
                            # Create Neo4j node
                            node = GraphNode(
                                id=str(record['id']),
                                title=record['title'] or f"{table_name.capitalize()} {record['id']}",
                                content_type=table_name.rstrip('s'),  # items -> item
                                created_at=record['created_at'],
                                updated_at=record['updated_at'],
                                tags=self._extract_tags_from_metadata(record['metadata']),
                                metadata=dict(record['metadata']) if record['metadata'] else {}
                            )
                            
                            success = await neo4j_graph_service.create_node(node)
                            
                            if success:
                                results["nodes_created"] += 1
                                
                                # Track sync operation
                                await self._track_sync_operation(
                                    operation_type="create_node",
                                    source_table=table_name,
                                    source_id=str(record['id']),
                                    target_node_id=str(record['id']),
                                    status=SyncStatus.COMPLETED
                                )
                            else:
                                results["errors"].append(f"Failed to create node for {table_name} {record['id']}")
                                
                        except Exception as e:
                            logger.error(f"Error syncing {table_name} {record['id']}: {e}")
                            results["errors"].append(f"{table_name} {record['id']}: {str(e)}")
                        
                        results["nodes_processed"] += 1
                    
                    # Small delay to avoid overwhelming the databases
                    await asyncio.sleep(self.sync_delay)
                
        except Exception as e:
            logger.error(f"Error syncing {table_name} table: {e}")
            results["errors"].append(f"Table sync error: {str(e)}")
        
        return results
    
    async def _sync_relationships_from_jsonb(self, force_resync: bool = False) -> Dict[str, Any]:
        """Extract and sync relationships from JSONB metadata fields"""
        results = {
            "relationships_processed": 0,
            "relationships_created": 0,
            "parsing_errors": []
        }
        
        try:
            for table_name, parser in self.relationship_parsers.items():
                table_results = await self._sync_table_relationships(table_name, parser, force_resync)
                results["relationships_processed"] += table_results.get("relationships_processed", 0)
                results["relationships_created"] += table_results.get("relationships_created", 0)
                results["parsing_errors"].extend(table_results.get("parsing_errors", []))
                
        except Exception as e:
            logger.error(f"Error syncing relationships from JSONB: {e}")
            results["parsing_errors"].append(f"General error: {str(e)}")
        
        return results
    
    async def _sync_table_relationships(self, table_name: str, parser_func, force_resync: bool = False) -> Dict[str, Any]:
        """Sync relationships from a specific table's JSONB metadata"""
        results = {
            "table": table_name,
            "relationships_processed": 0,
            "relationships_created": 0,
            "parsing_errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get records with metadata
                if force_resync:
                    query = f"""
                    SELECT id, metadata
                    FROM {table_name}
                    WHERE metadata IS NOT NULL AND metadata != '{{}}'::jsonb
                    ORDER BY updated_at DESC
                    """
                    records = await conn.fetch(query)
                else:
                    query = f"""
                    SELECT i.id, i.metadata
                    FROM {table_name} i
                    LEFT JOIN neo4j_sync_operations s ON (
                        s.source_table = $1 AND 
                        s.source_id = i.id::text AND 
                        s.operation_type = 'sync_relationships' AND
                        s.status = 'completed'
                    )
                    WHERE s.id IS NULL 
                    AND i.metadata IS NOT NULL 
                    AND i.metadata != '{{}}'::jsonb
                    ORDER BY i.updated_at DESC
                    """
                    records = await conn.fetch(query, table_name)
                
                # Process relationships for each record
                for record in records:
                    try:
                        relationships = await parser_func(record['id'], record['metadata'])
                        
                        for relationship in relationships:
                            try:
                                success = await neo4j_graph_service.create_relationship(relationship)
                                if success:
                                    results["relationships_created"] += 1
                                    
                                results["relationships_processed"] += 1
                                
                            except Exception as e:
                                logger.error(f"Error creating relationship: {e}")
                                results["parsing_errors"].append(f"Relationship creation error: {str(e)}")
                        
                        # Track sync operation
                        await self._track_sync_operation(
                            operation_type="sync_relationships",
                            source_table=table_name,
                            source_id=str(record['id']),
                            target_node_id=str(record['id']),
                            status=SyncStatus.COMPLETED,
                            metadata={"relationships_count": len(relationships)}
                        )
                        
                    except Exception as e:
                        logger.error(f"Error parsing relationships for {table_name} {record['id']}: {e}")
                        results["parsing_errors"].append(f"{table_name} {record['id']}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error syncing relationships from {table_name}: {e}")
            results["parsing_errors"].append(f"Table relationship sync error: {str(e)}")
        
        return results
    
    async def _parse_item_relationships(self, item_id: str, metadata: Dict[str, Any]) -> List[GraphRelationship]:
        """Parse relationships from items metadata"""
        relationships = []
        
        try:
            # Extract relationships from metadata
            if 'related_items' in metadata:
                for related_id in metadata['related_items']:
                    relationships.append(GraphRelationship(
                        from_node=str(item_id),
                        to_node=str(related_id),
                        relationship_type=RelationshipType.RELATED,
                        weight=0.8,
                        confidence=0.7,
                        metadata={"source": "items_metadata"}
                    ))
            
            if 'references' in metadata:
                for ref_id in metadata['references']:
                    relationships.append(GraphRelationship(
                        from_node=str(item_id),
                        to_node=str(ref_id),
                        relationship_type=RelationshipType.REFERENCES,
                        weight=0.6,
                        confidence=0.8,
                        metadata={"source": "items_metadata"}
                    ))
            
            if 'prerequisites' in metadata:
                for prereq_id in metadata['prerequisites']:
                    relationships.append(GraphRelationship(
                        from_node=str(item_id),
                        to_node=str(prereq_id),
                        relationship_type=RelationshipType.PREREQUISITE,
                        weight=0.9,
                        confidence=0.9,
                        metadata={"source": "items_metadata"}
                    ))
            
        except Exception as e:
            logger.error(f"Error parsing item relationships for {item_id}: {e}")
        
        return relationships
    
    async def _parse_repository_relationships(self, repo_id: str, metadata: Dict[str, Any]) -> List[GraphRelationship]:
        """Parse relationships from repositories metadata"""
        relationships = []
        
        try:
            # Extract dependencies
            if 'dependencies' in metadata:
                for dep_id in metadata['dependencies']:
                    relationships.append(GraphRelationship(
                        from_node=str(repo_id),
                        to_node=str(dep_id),
                        relationship_type=RelationshipType.DEPENDS_ON,
                        weight=0.7,
                        confidence=0.8,
                        metadata={"source": "repositories_metadata"}
                    ))
            
            # Extract similar repositories
            if 'similar_repos' in metadata:
                for similar_id in metadata['similar_repos']:
                    relationships.append(GraphRelationship(
                        from_node=str(repo_id),
                        to_node=str(similar_id),
                        relationship_type=RelationshipType.SIMILAR_TO,
                        weight=0.6,
                        confidence=0.7,
                        metadata={"source": "repositories_metadata"}
                    ))
            
            # Extract tech stack relationships
            if 'tech_stack' in metadata:
                for tech in metadata['tech_stack']:
                    if isinstance(tech, dict) and 'related_repos' in tech:
                        for related_id in tech['related_repos']:
                            relationships.append(GraphRelationship(
                                from_node=str(repo_id),
                                to_node=str(related_id),
                                relationship_type=RelationshipType.RELATED,
                                weight=0.5,
                                confidence=0.6,
                                metadata={"source": "repositories_metadata", "tech_stack": tech.get('name')}
                            ))
            
        except Exception as e:
            logger.error(f"Error parsing repository relationships for {repo_id}: {e}")
        
        return relationships
    
    async def _parse_document_relationships(self, doc_id: str, metadata: Dict[str, Any]) -> List[GraphRelationship]:
        """Parse relationships from documents metadata"""
        relationships = []
        
        try:
            # Extract document references
            if 'cited_documents' in metadata:
                for cited_id in metadata['cited_documents']:
                    relationships.append(GraphRelationship(
                        from_node=str(doc_id),
                        to_node=str(cited_id),
                        relationship_type=RelationshipType.REFERENCES,
                        weight=0.7,
                        confidence=0.8,
                        metadata={"source": "documents_metadata"}
                    ))
            
            # Extract related documents
            if 'related_documents' in metadata:
                for related_id in metadata['related_documents']:
                    relationships.append(GraphRelationship(
                        from_node=str(doc_id),
                        to_node=str(related_id),
                        relationship_type=RelationshipType.RELATED,
                        weight=0.6,
                        confidence=0.7,
                        metadata={"source": "documents_metadata"}
                    ))
            
            # Extract document hierarchy
            if 'parent_document' in metadata:
                parent_id = metadata['parent_document']
                relationships.append(GraphRelationship(
                    from_node=str(doc_id),
                    to_node=str(parent_id),
                    relationship_type=RelationshipType.PART_OF,
                    weight=0.9,
                    confidence=0.9,
                    metadata={"source": "documents_metadata"}
                ))
            
        except Exception as e:
            logger.error(f"Error parsing document relationships for {doc_id}: {e}")
        
        return relationships
    
    async def _extract_tags_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract tags from metadata for Neo4j node creation"""
        tags = []
        
        if not metadata:
            return tags
        
        # Common tag fields
        tag_fields = ['tags', 'categories', 'labels', 'keywords', 'topics']
        
        for field in tag_fields:
            if field in metadata:
                field_value = metadata[field]
                if isinstance(field_value, list):
                    tags.extend([str(tag) for tag in field_value])
                elif isinstance(field_value, str):
                    tags.append(field_value)
        
        return list(set(tags))  # Remove duplicates
    
    async def _track_sync_operation(
        self,
        operation_type: str,
        source_table: str,
        source_id: str,
        target_node_id: str,
        status: SyncStatus,
        metadata: Dict[str, Any] = None
    ):
        """Track a sync operation in the database"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                INSERT INTO neo4j_sync_operations (
                    operation_type, source_table, source_id, target_node_id, 
                    status, completed_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (source_table, source_id, operation_type)
                DO UPDATE SET
                    status = $5,
                    completed_at = $6,
                    metadata = $7
                """
                
                await conn.execute(
                    query,
                    operation_type,
                    source_table,
                    source_id,
                    target_node_id,
                    status.value,
                    datetime.utcnow() if status == SyncStatus.COMPLETED else None,
                    json.dumps(metadata or {})
                )
                
        except Exception as e:
            logger.error(f"Error tracking sync operation: {e}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get comprehensive sync status and statistics"""
        await self.initialize()
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get sync operation statistics
                stats_query = """
                SELECT 
                    operation_type,
                    source_table,
                    status,
                    COUNT(*) as count,
                    MAX(completed_at) as last_completed
                FROM neo4j_sync_operations
                GROUP BY operation_type, source_table, status
                ORDER BY source_table, operation_type, status
                """
                
                stats = await conn.fetch(stats_query)
                
                # Get pending operations
                pending_query = """
                SELECT source_table, COUNT(*) as pending_count
                FROM neo4j_sync_operations
                WHERE status = 'pending'
                GROUP BY source_table
                """
                
                pending_stats = await conn.fetch(pending_query)
                
                # Get Neo4j graph statistics
                graph_stats = await neo4j_graph_service.get_graph_statistics()
                
                return {
                    "sync_statistics": [dict(row) for row in stats],
                    "pending_operations": [dict(row) for row in pending_stats],
                    "graph_statistics": graph_stats,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"error": str(e)}
    
    async def rollback_sync(self, source_table: str = None, source_id: str = None) -> Dict[str, Any]:
        """Rollback sync operations by removing Neo4j data"""
        rollback_results = {
            "started_at": datetime.utcnow().isoformat(),
            "status": "in_progress",
            "nodes_deleted": 0,
            "relationships_deleted": 0,
            "errors": []
        }
        
        try:
            async with neo4j_graph_service.driver.session() as session:
                if source_table and source_id:
                    # Rollback specific item
                    delete_query = """
                    MATCH (n:Content {id: $node_id})
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                    """
                    
                    result = await session.run(delete_query, node_id=source_id)
                    record = await result.single()
                    rollback_results["nodes_deleted"] = record["deleted_count"]
                    
                    # Update sync tracking
                    await self._remove_sync_tracking(source_table, source_id)
                    
                elif source_table:
                    # Rollback entire table
                    delete_query = """
                    MATCH (n:Content)
                    WHERE n.content_type = $content_type
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                    """
                    
                    content_type = source_table.rstrip('s')  # items -> item
                    result = await session.run(delete_query, content_type=content_type)
                    record = await result.single()
                    rollback_results["nodes_deleted"] = record["deleted_count"]
                    
                    # Update sync tracking
                    await self._remove_sync_tracking(source_table)
                    
                else:
                    # Rollback everything
                    delete_query = """
                    MATCH (n)
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                    """
                    
                    result = await session.run(delete_query)
                    record = await result.single()
                    rollback_results["nodes_deleted"] = record["deleted_count"]
                    
                    # Clear all sync tracking
                    await self._clear_sync_tracking()
                
                rollback_results["status"] = "completed"
                rollback_results["completed_at"] = datetime.utcnow().isoformat()
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_results["status"] = "failed"
            rollback_results["errors"].append(str(e))
        
        return rollback_results
    
    async def _remove_sync_tracking(self, source_table: str, source_id: str = None):
        """Remove sync tracking records"""
        async with self.db_pool.acquire() as conn:
            if source_id:
                query = """
                DELETE FROM neo4j_sync_operations 
                WHERE source_table = $1 AND source_id = $2
                """
                await conn.execute(query, source_table, source_id)
            else:
                query = """
                DELETE FROM neo4j_sync_operations 
                WHERE source_table = $1
                """
                await conn.execute(query, source_table)
    
    async def _clear_sync_tracking(self):
        """Clear all sync tracking records"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM neo4j_sync_operations")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of sync service"""
        try:
            await self.initialize()
            
            # Check PostgreSQL connection
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            # Check Neo4j connection
            neo4j_health = await neo4j_graph_service.health_check()
            
            # Get sync status
            sync_status = await self.get_sync_status()
            
            return {
                "status": "healthy",
                "postgresql_connection": True,
                "neo4j_connection": neo4j_health.get("connectivity", False),
                "sync_status": sync_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
neo4j_sync_service = Neo4jSyncService()