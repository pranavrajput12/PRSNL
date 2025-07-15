"""
Neo4j Sync API endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.neo4j_sync_service import neo4j_sync_service

router = APIRouter()


class SyncRequest(BaseModel):
    """Request model for sync operations"""
    force_resync: bool = Field(default=False, description="Force resync of all data")
    tables: List[str] = Field(default_factory=list, description="Specific tables to sync")
    source_id: Optional[str] = Field(default=None, description="Specific record ID to sync")


class RollbackRequest(BaseModel):
    """Request model for rollback operations"""
    source_table: Optional[str] = Field(default=None, description="Table to rollback")
    source_id: Optional[str] = Field(default=None, description="Specific record ID to rollback")
    confirm: bool = Field(default=False, description="Confirmation required for rollback")


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_sync_service(
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize the Neo4j sync service and create necessary infrastructure
    """
    try:
        await neo4j_sync_service.initialize()
        return {
            "status": "success",
            "message": "Neo4j sync service initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post("/sync/all", response_model=Dict[str, Any])
async def sync_all_data(
    request: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Perform complete data synchronization from PostgreSQL to Neo4j
    
    Args:
        request: Sync configuration
        
    Returns:
        Comprehensive sync results
    """
    try:
        results = await neo4j_sync_service.sync_all_data(
            force_resync=request.force_resync
        )
        
        return {
            "status": "success",
            "sync_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full sync failed: {str(e)}")


@router.post("/sync/table/{table_name}", response_model=Dict[str, Any])
async def sync_table_data(
    table_name: str,
    force_resync: bool = Query(default=False, description="Force resync of table data"),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync data from a specific PostgreSQL table to Neo4j
    
    Args:
        table_name: Name of the table to sync
        force_resync: Force resync of all data
        
    Returns:
        Table sync results
    """
    try:
        # Validate table name
        valid_tables = ['items', 'repositories', 'documents']
        if table_name not in valid_tables:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name '{table_name}'. Valid tables: {valid_tables}"
            )
        
        # Initialize service
        await neo4j_sync_service.initialize()
        
        # Sync table nodes
        table_results = await neo4j_sync_service._sync_table_nodes(table_name, force_resync)
        
        # Sync relationships if parser exists
        if table_name in neo4j_sync_service.relationship_parsers:
            parser = neo4j_sync_service.relationship_parsers[table_name]
            relationship_results = await neo4j_sync_service._sync_table_relationships(
                table_name, parser, force_resync
            )
        else:
            relationship_results = {"relationships_created": 0}
        
        return {
            "status": "success",
            "table": table_name,
            "nodes_results": table_results,
            "relationships_results": relationship_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table sync failed: {str(e)}")


@router.post("/sync/record/{table_name}/{record_id}", response_model=Dict[str, Any])
async def sync_specific_record(
    table_name: str,
    record_id: str,
    force_resync: bool = Query(default=False, description="Force resync of record"),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync a specific record from PostgreSQL to Neo4j
    
    Args:
        table_name: Name of the table
        record_id: ID of the record to sync
        force_resync: Force resync of the record
        
    Returns:
        Record sync results
    """
    try:
        # Validate table name
        valid_tables = ['items', 'repositories', 'documents']
        if table_name not in valid_tables:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name '{table_name}'. Valid tables: {valid_tables}"
            )
        
        await neo4j_sync_service.initialize()
        
        # Get record from PostgreSQL
        async with neo4j_sync_service.db_pool.acquire() as conn:
            query = f"""
            SELECT id, title, created_at, updated_at, metadata
            FROM {table_name}
            WHERE id = $1
            """
            
            record = await conn.fetchrow(query, record_id)
            
            if not record:
                raise HTTPException(
                    status_code=404,
                    detail=f"Record {record_id} not found in {table_name}"
                )
        
        # Create Neo4j node
        from app.services.neo4j_graph_service import GraphNode
        from datetime import datetime
        
        node = GraphNode(
            id=str(record['id']),
            title=record['title'] or f"{table_name.capitalize()} {record['id']}",
            content_type=table_name.rstrip('s'),
            created_at=record['created_at'],
            updated_at=record['updated_at'],
            tags=await neo4j_sync_service._extract_tags_from_metadata(record['metadata']),
            metadata=dict(record['metadata']) if record['metadata'] else {}
        )
        
        from app.services.neo4j_graph_service import neo4j_graph_service
        node_success = await neo4j_graph_service.create_node(node)
        
        # Sync relationships if metadata exists
        relationships_created = 0
        if record['metadata'] and table_name in neo4j_sync_service.relationship_parsers:
            parser = neo4j_sync_service.relationship_parsers[table_name]
            relationships = await parser(record['id'], record['metadata'])
            
            for relationship in relationships:
                success = await neo4j_graph_service.create_relationship(relationship)
                if success:
                    relationships_created += 1
        
        # Track sync operation
        from app.services.neo4j_sync_service import SyncStatus
        await neo4j_sync_service._track_sync_operation(
            operation_type="sync_record",
            source_table=table_name,
            source_id=str(record['id']),
            target_node_id=str(record['id']),
            status=SyncStatus.COMPLETED,
            metadata={"relationships_created": relationships_created}
        )
        
        return {
            "status": "success",
            "record": {
                "table": table_name,
                "id": record_id,
                "title": record['title']
            },
            "node_created": node_success,
            "relationships_created": relationships_created
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Record sync failed: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive sync status and statistics
    
    Returns:
        Sync status including PostgreSQL and Neo4j statistics
    """
    try:
        status = await neo4j_sync_service.get_sync_status()
        
        return {
            "status": "success",
            "sync_status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/rollback", response_model=Dict[str, Any])
async def rollback_sync(
    request: RollbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rollback sync operations by removing Neo4j data
    
    Args:
        request: Rollback configuration
        
    Returns:
        Rollback results
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400,
                detail="Rollback requires confirmation. Set 'confirm': true"
            )
        
        results = await neo4j_sync_service.rollback_sync(
            source_table=request.source_table,
            source_id=request.source_id
        )
        
        return {
            "status": "success",
            "rollback_results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def sync_service_health():
    """
    Health check for Neo4j sync service
    
    Returns:
        Health status of PostgreSQL and Neo4j connections
    """
    try:
        health_status = await neo4j_sync_service.health_check()
        
        return {
            "status": "success",
            "health": health_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/tables", response_model=Dict[str, Any])
async def get_syncable_tables():
    """
    Get list of tables that can be synced to Neo4j
    
    Returns:
        List of tables with their sync capabilities
    """
    try:
        tables = [
            {
                "name": "items",
                "description": "Knowledge base items",
                "content_type": "item",
                "has_relationship_parser": True,
                "relationship_types": ["RELATED", "REFERENCES", "PREREQUISITE"]
            },
            {
                "name": "repositories",
                "description": "Code repositories",
                "content_type": "repository",
                "has_relationship_parser": True,
                "relationship_types": ["DEPENDS_ON", "SIMILAR_TO", "RELATED"]
            },
            {
                "name": "documents",
                "description": "Documents and files",
                "content_type": "document",
                "has_relationship_parser": True,
                "relationship_types": ["REFERENCES", "RELATED", "PART_OF"]
            }
        ]
        
        return {
            "status": "success",
            "syncable_tables": tables
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


@router.get("/operations", response_model=Dict[str, Any])
async def get_sync_operations(
    status: Optional[str] = Query(default=None, description="Filter by operation status"),
    source_table: Optional[str] = Query(default=None, description="Filter by source table"),
    limit: int = Query(default=100, description="Maximum number of operations to return"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get sync operation history
    
    Args:
        status: Filter by operation status
        source_table: Filter by source table
        limit: Maximum number of operations
        
    Returns:
        List of sync operations
    """
    try:
        await neo4j_sync_service.initialize()
        
        async with neo4j_sync_service.db_pool.acquire() as conn:
            # Build query with filters
            where_conditions = []
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                where_conditions.append(f"status = ${param_count}")
                params.append(status)
            
            if source_table:
                param_count += 1
                where_conditions.append(f"source_table = ${param_count}")
                params.append(source_table)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            param_count += 1
            params.append(limit)
            
            query = f"""
            SELECT 
                id, operation_type, source_table, source_id, target_node_id,
                status, created_at, completed_at, error_message, metadata
            FROM neo4j_sync_operations
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count}
            """
            
            operations = await conn.fetch(query, *params)
            
            return {
                "status": "success",
                "operations": [dict(op) for op in operations],
                "count": len(operations)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get operations: {str(e)}")


@router.delete("/operations/{operation_id}", response_model=Dict[str, Any])
async def delete_sync_operation(
    operation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific sync operation record
    
    Args:
        operation_id: ID of the operation to delete
        
    Returns:
        Deletion result
    """
    try:
        await neo4j_sync_service.initialize()
        
        async with neo4j_sync_service.db_pool.acquire() as conn:
            query = """
            DELETE FROM neo4j_sync_operations
            WHERE id = $1
            RETURNING operation_type, source_table, source_id
            """
            
            result = await conn.fetchrow(query, operation_id)
            
            if result:
                return {
                    "status": "success",
                    "operation_id": operation_id,
                    "deleted_operation": dict(result),
                    "message": "Sync operation deleted successfully"
                }
            else:
                return {
                    "status": "not_found",
                    "operation_id": operation_id,
                    "message": "Sync operation not found"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operation deletion failed: {str(e)}")


# Add to main router
def include_neo4j_sync_routes(main_router):
    """Include Neo4j sync routes in main router"""
    main_router.include_router(
        router,
        prefix="/api/sync",
        tags=["neo4j_sync"]
    )