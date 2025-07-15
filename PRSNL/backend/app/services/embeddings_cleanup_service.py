"""
Embeddings Cleanup Service
Handles cleanup of orphaned embeddings and database maintenance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from app.config import settings
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)


class EmbeddingsCleanupService:
    """
    Service for cleaning up orphaned embeddings and maintaining database health
    
    Features:
    - Identifies orphaned embeddings not linked to existing items
    - Coordinates with CodeMirror analysis to avoid disrupting active sessions
    - Provides cleanup statistics and monitoring
    - Supports incremental cleanup to avoid database locks
    """
    
    def __init__(self):
        self.db_pool = None
        self.cleanup_batch_size = 1000
        self.cleanup_delay = 0.1  # seconds between batches
        
    async def initialize(self):
        """Initialize database connection pool"""
        if not self.db_pool:
            self.db_pool = await get_db_pool()
    
    async def analyze_orphaned_embeddings(self) -> Dict[str, Any]:
        """
        Analyze orphaned embeddings without deleting them
        
        Returns:
            Dictionary with analysis results
        """
        await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            # Check embeddings table schema
            schema_query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(schema_query)
            logger.info(f"Embeddings table columns: {[row['column_name'] for row in columns]}")
            
            # Count total embeddings
            total_embeddings = await conn.fetchval("SELECT COUNT(*) FROM embeddings")
            
            # Find orphaned embeddings (embeddings with no corresponding items)
            orphaned_query = """
            SELECT 
                e.id,
                e.item_id,
                e.created_at,
                e.embedding_type,
                CASE 
                    WHEN i.id IS NULL THEN 'orphaned_item'
                    ELSE 'valid'
                END as status
            FROM embeddings e
            LEFT JOIN items i ON e.item_id = i.id
            WHERE i.id IS NULL;
            """
            
            orphaned_embeddings = await conn.fetch(orphaned_query)
            orphaned_count = len(orphaned_embeddings)
            
            # Find old embeddings (older than 30 days with no recent activity)
            old_embeddings_query = """
            SELECT COUNT(*) as count
            FROM embeddings e
            LEFT JOIN items i ON e.item_id = i.id
            WHERE e.created_at < NOW() - INTERVAL '30 days'
            AND (i.updated_at IS NULL OR i.updated_at < NOW() - INTERVAL '30 days');
            """
            
            old_embeddings_count = await conn.fetchval(old_embeddings_query)
            
            # Check for CodeMirror analysis embeddings
            codemirror_embeddings_query = """
            SELECT COUNT(*) as count
            FROM embeddings e
            WHERE e.item_id IN (
                SELECT DISTINCT repo_id::text 
                FROM codemirror_analyses 
                WHERE status = 'in_progress'
            );
            """
            
            active_codemirror_count = await conn.fetchval(codemirror_embeddings_query) or 0
            
            # Get embedding types distribution
            types_query = """
            SELECT 
                embedding_type,
                COUNT(*) as count
            FROM embeddings
            GROUP BY embedding_type
            ORDER BY count DESC;
            """
            
            embedding_types = await conn.fetch(types_query)
            
            # Get database size statistics
            size_query = """
            SELECT 
                pg_size_pretty(pg_total_relation_size('embeddings')) as table_size,
                pg_size_pretty(pg_indexes_size('embeddings')) as index_size
            """
            
            size_stats = await conn.fetchrow(size_query)
            
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_embeddings": total_embeddings,
                "orphaned_embeddings": orphaned_count,
                "old_embeddings": old_embeddings_count,
                "active_codemirror_embeddings": active_codemirror_count,
                "embedding_types": [dict(row) for row in embedding_types],
                "database_size": dict(size_stats) if size_stats else {},
                "cleanup_recommendation": {
                    "safe_to_cleanup": orphaned_count > 0 and active_codemirror_count == 0,
                    "estimated_cleanup_count": orphaned_count,
                    "potential_space_savings": f"{orphaned_count * 0.05:.1f}MB"  # Rough estimate
                }
            }
    
    async def check_active_codemirror_sessions(self) -> List[str]:
        """
        Check for active CodeMirror analysis sessions
        
        Returns:
            List of active session IDs
        """
        await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            active_sessions_query = """
            SELECT 
                id,
                repo_id,
                status,
                started_at,
                updated_at
            FROM codemirror_analyses
            WHERE status IN ('in_progress', 'starting', 'analyzing')
            AND updated_at > NOW() - INTERVAL '1 hour';
            """
            
            active_sessions = await conn.fetch(active_sessions_query)
            return [row['id'] for row in active_sessions]
    
    async def cleanup_orphaned_embeddings(
        self,
        dry_run: bool = True,
        max_deletions: int = 5000
    ) -> Dict[str, Any]:
        """
        Clean up orphaned embeddings
        
        Args:
            dry_run: If True, only analyze without deleting
            max_deletions: Maximum number of embeddings to delete in one run
            
        Returns:
            Cleanup results
        """
        await self.initialize()
        
        # Check for active CodeMirror sessions
        active_sessions = await self.check_active_codemirror_sessions()
        if active_sessions:
            logger.warning(f"Active CodeMirror sessions detected: {active_sessions}")
            if not dry_run:
                return {
                    "status": "aborted",
                    "reason": "Active CodeMirror sessions detected",
                    "active_sessions": active_sessions
                }
        
        cleanup_results = {
            "status": "dry_run" if dry_run else "executed",
            "started_at": datetime.utcnow().isoformat(),
            "deletions_performed": 0,
            "space_freed": "0MB",
            "errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Find orphaned embeddings
                    find_orphaned_query = """
                    SELECT e.id, e.item_id, e.created_at
                    FROM embeddings e
                    LEFT JOIN items i ON e.item_id = i.id
                    WHERE i.id IS NULL
                    ORDER BY e.created_at ASC
                    LIMIT $1;
                    """
                    
                    orphaned_embeddings = await conn.fetch(find_orphaned_query, max_deletions)
                    
                    if not orphaned_embeddings:
                        cleanup_results["status"] = "no_orphans_found"
                        return cleanup_results
                    
                    orphaned_ids = [row['id'] for row in orphaned_embeddings]
                    
                    if dry_run:
                        cleanup_results.update({
                            "orphaned_embeddings_found": len(orphaned_ids),
                            "would_delete_ids": orphaned_ids[:10],  # First 10 for reference
                            "total_would_delete": len(orphaned_ids)
                        })
                    else:
                        # Delete in batches to avoid long locks
                        deleted_count = 0
                        batch_size = self.cleanup_batch_size
                        
                        for i in range(0, len(orphaned_ids), batch_size):
                            batch_ids = orphaned_ids[i:i + batch_size]
                            
                            delete_query = """
                            DELETE FROM embeddings 
                            WHERE id = ANY($1::uuid[])
                            """
                            
                            result = await conn.execute(delete_query, batch_ids)
                            batch_deleted = int(result.split()[-1])
                            deleted_count += batch_deleted
                            
                            logger.info(f"Deleted batch of {batch_deleted} embeddings")
                            
                            # Small delay to avoid overwhelming the database
                            await asyncio.sleep(self.cleanup_delay)
                        
                        cleanup_results.update({
                            "deletions_performed": deleted_count,
                            "orphaned_embeddings_found": len(orphaned_ids),
                            "space_freed": f"{deleted_count * 0.05:.1f}MB"  # Rough estimate
                        })
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            cleanup_results["errors"].append(str(e))
            cleanup_results["status"] = "failed"
        
        cleanup_results["completed_at"] = datetime.utcnow().isoformat()
        return cleanup_results
    
    async def cleanup_old_embeddings(
        self,
        days_old: int = 90,
        dry_run: bool = True,
        max_deletions: int = 10000
    ) -> Dict[str, Any]:
        """
        Clean up old embeddings from inactive items
        
        Args:
            days_old: Delete embeddings older than this many days
            dry_run: If True, only analyze without deleting
            max_deletions: Maximum number of embeddings to delete
            
        Returns:
            Cleanup results
        """
        await self.initialize()
        
        cleanup_results = {
            "status": "dry_run" if dry_run else "executed",
            "started_at": datetime.utcnow().isoformat(),
            "deletions_performed": 0,
            "criteria": f"older_than_{days_old}_days",
            "errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Find old embeddings
                find_old_query = """
                SELECT e.id, e.item_id, e.created_at
                FROM embeddings e
                LEFT JOIN items i ON e.item_id = i.id
                WHERE e.created_at < NOW() - INTERVAL '%s days'
                AND (i.updated_at IS NULL OR i.updated_at < NOW() - INTERVAL '%s days')
                ORDER BY e.created_at ASC
                LIMIT $1;
                """ % (days_old, days_old)
                
                old_embeddings = await conn.fetch(find_old_query, max_deletions)
                
                if not old_embeddings:
                    cleanup_results["status"] = "no_old_embeddings_found"
                    return cleanup_results
                
                old_ids = [row['id'] for row in old_embeddings]
                
                if dry_run:
                    cleanup_results.update({
                        "old_embeddings_found": len(old_ids),
                        "would_delete_ids": old_ids[:10],  # First 10 for reference
                        "total_would_delete": len(old_ids)
                    })
                else:
                    # Delete in transaction
                    async with conn.transaction():
                        delete_query = """
                        DELETE FROM embeddings 
                        WHERE id = ANY($1::uuid[])
                        """
                        
                        result = await conn.execute(delete_query, old_ids)
                        deleted_count = int(result.split()[-1])
                        
                        cleanup_results.update({
                            "deletions_performed": deleted_count,
                            "old_embeddings_found": len(old_ids),
                            "space_freed": f"{deleted_count * 0.05:.1f}MB"
                        })
        
        except Exception as e:
            logger.error(f"Old embeddings cleanup failed: {e}")
            cleanup_results["errors"].append(str(e))
            cleanup_results["status"] = "failed"
        
        cleanup_results["completed_at"] = datetime.utcnow().isoformat()
        return cleanup_results
    
    async def add_cascade_constraints(self) -> Dict[str, Any]:
        """
        Add CASCADE delete constraints to prevent orphaned embeddings
        
        Returns:
            Results of constraint additions
        """
        await self.initialize()
        
        results = {
            "status": "completed",
            "constraints_added": [],
            "errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check existing constraints
                check_constraints_query = """
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'embeddings';
                """
                
                existing_constraints = await conn.fetch(check_constraints_query)
                
                # Check if CASCADE constraint already exists
                has_cascade = any(
                    constraint['delete_rule'] == 'CASCADE' 
                    for constraint in existing_constraints
                )
                
                if has_cascade:
                    results["status"] = "already_exists"
                    results["message"] = "CASCADE constraints already exist"
                    return results
                
                # Add CASCADE constraint for embeddings -> items
                async with conn.transaction():
                    # Drop existing constraint if it exists
                    drop_constraint_query = """
                    ALTER TABLE embeddings 
                    DROP CONSTRAINT IF EXISTS embeddings_item_id_fkey;
                    """
                    
                    await conn.execute(drop_constraint_query)
                    
                    # Add new CASCADE constraint
                    add_constraint_query = """
                    ALTER TABLE embeddings 
                    ADD CONSTRAINT embeddings_item_id_fkey 
                    FOREIGN KEY (item_id) 
                    REFERENCES items(id) 
                    ON DELETE CASCADE;
                    """
                    
                    await conn.execute(add_constraint_query)
                    
                    results["constraints_added"].append({
                        "table": "embeddings",
                        "constraint": "embeddings_item_id_fkey",
                        "type": "FOREIGN KEY CASCADE"
                    })
                
                logger.info("CASCADE constraints added successfully")
                
        except Exception as e:
            logger.error(f"Failed to add CASCADE constraints: {e}")
            results["errors"].append(str(e))
            results["status"] = "failed"
        
        return results
    
    async def get_cleanup_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cleanup statistics
        
        Returns:
            Statistical analysis of embeddings cleanup needs
        """
        await self.initialize()
        
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_health": {},
            "cleanup_recommendations": {},
            "maintenance_schedule": {}
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Database health metrics
                health_query = """
                SELECT 
                    COUNT(*) as total_embeddings,
                    COUNT(DISTINCT item_id) as unique_items,
                    AVG(pg_column_size(embedding)) as avg_embedding_size,
                    MIN(created_at) as oldest_embedding,
                    MAX(created_at) as newest_embedding
                FROM embeddings;
                """
                
                health_stats = await conn.fetchrow(health_query)
                
                # Orphaned embeddings count
                orphaned_count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM embeddings e
                    LEFT JOIN items i ON e.item_id = i.id
                    WHERE i.id IS NULL;
                """)
                
                # Old embeddings count
                old_count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM embeddings e
                    LEFT JOIN items i ON e.item_id = i.id
                    WHERE e.created_at < NOW() - INTERVAL '30 days'
                    AND (i.updated_at IS NULL OR i.updated_at < NOW() - INTERVAL '30 days');
                """)
                
                stats["database_health"] = {
                    "total_embeddings": health_stats['total_embeddings'],
                    "unique_items": health_stats['unique_items'],
                    "avg_embedding_size_bytes": int(health_stats['avg_embedding_size'] or 0),
                    "oldest_embedding": health_stats['oldest_embedding'].isoformat() if health_stats['oldest_embedding'] else None,
                    "newest_embedding": health_stats['newest_embedding'].isoformat() if health_stats['newest_embedding'] else None,
                    "orphaned_count": orphaned_count,
                    "old_count": old_count
                }
                
                # Cleanup recommendations
                total_cleanup_potential = orphaned_count + old_count
                
                stats["cleanup_recommendations"] = {
                    "immediate_cleanup_needed": orphaned_count > 1000,
                    "routine_cleanup_needed": old_count > 5000,
                    "total_cleanup_potential": total_cleanup_potential,
                    "estimated_space_savings_mb": round(total_cleanup_potential * 0.05, 1),
                    "recommended_action": (
                        "immediate_cleanup" if orphaned_count > 1000 else
                        "routine_cleanup" if old_count > 5000 else
                        "no_action_needed"
                    )
                }
                
                # Maintenance schedule
                stats["maintenance_schedule"] = {
                    "next_orphaned_cleanup": "daily" if orphaned_count > 500 else "weekly",
                    "next_old_cleanup": "weekly" if old_count > 2000 else "monthly",
                    "constraint_check": "monthly",
                    "index_maintenance": "quarterly"
                }
                
        except Exception as e:
            logger.error(f"Failed to get cleanup statistics: {e}")
            stats["error"] = str(e)
        
        return stats


# Singleton instance
embeddings_cleanup_service = EmbeddingsCleanupService()