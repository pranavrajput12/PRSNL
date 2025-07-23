"""
Knowledge Graph Celery Tasks

Phase 2: Optimize Knowledge Graph operations with background processing
for semantic search, entity linking, and graph construction.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from celery import group, chord
from app.workers.celery_app import celery_app
from app.workers.retry_strategies import IntelligentRetryTask
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.embedding_manager import embedding_manager
from app.services.realtime_progress_service import send_task_progress

logger = logging.getLogger(__name__)


@celery_app.task(name="knowledge_graph.build_distributed", base=IntelligentRetryTask, bind=True, agent_type="knowledge_graph")
def build_knowledge_graph_distributed(self, entity_ids: List[str], user_id: str, options: Dict[str, Any] = None):
    """
    Orchestrate distributed knowledge graph construction using Celery coordination.
    
    Uses parallel entity processing with intelligent graph assembly.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _build_knowledge_graph_distributed_async(self.request.id, entity_ids, user_id, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Distributed knowledge graph construction failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _build_knowledge_graph_distributed_async(task_id: str, entity_ids: List[str], user_id: str, options: Dict[str, Any]):
    """Async implementation of distributed knowledge graph construction"""
    
    try:
        await _send_progress_update(task_id, user_id, "knowledge_graph_construction", 0, 4, "Starting distributed graph construction")
        
        # Create parallel entity processing group
        entity_processing_group = group([
            extract_entity_relationships_task.s(entity_id, user_id, options)
            for entity_id in entity_ids
        ])
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_construction", 1, 4, f"Processing {len(entity_ids)} entities in parallel")
        
        # Execute entity processing and aggregate with Chord
        workflow = chord(entity_processing_group)(
            assemble_knowledge_graph_task.s(user_id, options)
        )
        
        # Start workflow
        workflow_result = workflow.apply_async()
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_construction", 2, 4, "Entity processing initiated")
        
        return {
            "status": "workflow_initiated",
            "user_id": user_id,
            "workflow_id": workflow_result.id,
            "entities_count": len(entity_ids),
            "initiated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Distributed knowledge graph construction async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="knowledge_graph.extract_relationships", bind=True, max_retries=2, queue="ai_analysis")
def extract_entity_relationships_task(self, entity_id: str, user_id: str, options: Dict[str, Any]):
    """Extract relationships and connections for a specific entity"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _extract_entity_relationships_async(self.request.id, entity_id, user_id, options)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Entity relationship extraction failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"entity_id": entity_id, "error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _extract_entity_relationships_async(task_id: str, entity_id: str, user_id: str, options: Dict[str, Any]):
    """Entity relationship extraction implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Load entity data from knowledge base
        async with get_db_connection() as db:
            entity = await db.fetchrow("""
                SELECT * FROM knowledge_entities 
                WHERE id = $1 AND user_id = $2
            """, UUID(entity_id), UUID(user_id))
            
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # Get related content for context
            related_content = await db.fetch("""
                SELECT * FROM embeddings 
                WHERE user_id = $1 
                AND content_type = 'entity_context'
                AND metadata->>'entity_id' = $2
                LIMIT 10
            """, UUID(user_id), entity_id)
        
        # Extract relationships using AI
        relationships = await ai_service.extract_entity_relationships(
            entity_data=dict(entity),
            related_content=[dict(content) for content in related_content],
            extract_semantic_links=True,
            identify_hierarchies=True,
            find_cross_references=True
        )
        
        # Generate embeddings for discovered relationships
        relationship_embeddings = []
        for relationship in relationships.get("relationships", []):
            embedding = await embedding_manager.generate_embedding(
                text=f"{relationship.get('source')} {relationship.get('relation')} {relationship.get('target')}",
                content_type="relationship"
            )
            relationship_embeddings.append({
                "relationship": relationship,
                "embedding": embedding
            })
        
        return {
            "entity_id": entity_id,
            "status": "completed",
            "relationships": relationships,
            "relationship_embeddings": relationship_embeddings,
            "relationships_count": len(relationships.get("relationships", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Entity relationship extraction async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="knowledge_graph.semantic_search", bind=True, max_retries=2, queue="ai_analysis")
def semantic_search_distributed_task(self, query: str, user_id: str, search_options: Dict[str, Any]):
    """Perform distributed semantic search across knowledge graph"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _semantic_search_distributed_async(self.request.id, query, user_id, search_options)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Distributed semantic search failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _semantic_search_distributed_async(task_id: str, query: str, user_id: str, search_options: Dict[str, Any]):
    """Distributed semantic search implementation"""
    
    try:
        # Generate query embedding
        query_embedding = await embedding_manager.generate_embedding(query, "query")
        
        # Parallel search across different content types
        search_tasks = []
        content_types = search_options.get("content_types", ["text", "code", "conversation", "entity"])
        
        for content_type in content_types:
            search_tasks.append(
                _search_content_type_async(query_embedding, user_id, content_type, search_options)
            )
        
        # Execute searches in parallel
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for content type {content_types[i]}: {result}")
            else:
                successful_results.extend(result)
        
        # Rank and deduplicate results
        ranked_results = await _rank_search_results(successful_results, query, search_options)
        
        return {
            "status": "completed",
            "query": query,
            "results": ranked_results[:search_options.get("limit", 20)],
            "total_found": len(successful_results),
            "content_types_searched": content_types,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Semantic search distributed async failed: {e}", exc_info=True)
        raise


async def _search_content_type_async(query_embedding: List[float], user_id: str, content_type: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search within a specific content type"""
    
    try:
        async with get_db_connection() as db:
            # Use pgvector similarity search
            results = await db.fetch("""
                SELECT 
                    content,
                    metadata,
                    content_type,
                    1 - (embedding <=> $1::vector) as similarity
                FROM embeddings 
                WHERE user_id = $2 
                AND content_type = $3
                AND 1 - (embedding <=> $1::vector) > $4
                ORDER BY embedding <=> $1::vector
                LIMIT $5
            """, 
                query_embedding,
                UUID(user_id),
                content_type,
                options.get("similarity_threshold", 0.7),
                options.get("per_type_limit", 10)
            )
            
            return [dict(result) for result in results]
            
    except Exception as e:
        logger.error(f"Content type search failed for {content_type}: {e}")
        return []


async def _rank_search_results(results: List[Dict[str, Any]], query: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Use AI to re-rank search results for relevance"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Use AI to analyze relevance and re-rank
        ranking_analysis = await ai_service.rank_search_results(
            query=query,
            results=results,
            ranking_criteria=options.get("ranking_criteria", ["relevance", "recency", "completeness"])
        )
        
        return ranking_analysis.get("ranked_results", results)
        
    except Exception as e:
        logger.error(f"AI ranking failed, using similarity order: {e}")
        # Fallback to similarity-based ranking
        return sorted(results, key=lambda x: x.get("similarity", 0), reverse=True)


@celery_app.task(name="knowledge_graph.assemble_graph", bind=True, max_retries=2, queue="ai_synthesis")
def assemble_knowledge_graph_task(self, entity_results: List[Dict[str, Any]], user_id: str, options: Dict[str, Any]):
    """
    Intelligent assembly of knowledge graph from parallel entity processing results.
    
    This Chord callback task receives results from all parallel entity processors and creates
    a comprehensive knowledge graph with AI-enhanced connections.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _assemble_knowledge_graph_async(self.request.id, entity_results, user_id, options)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Knowledge graph assembly failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _assemble_knowledge_graph_async(task_id: str, entity_results: List[Dict[str, Any]], user_id: str, options: Dict[str, Any]):
    """Intelligent knowledge graph assembly implementation"""
    
    try:
        await _send_progress_update(task_id, user_id, "knowledge_graph_assembly", 0, 4, "Starting graph assembly")
        
        # Filter successful entity results
        successful_results = [result for result in entity_results if result.get("status") == "completed"]
        failed_entities = [result.get("entity_id", "unknown") for result in entity_results if result.get("status") == "failed"]
        
        logger.info(f"Graph assembly: {len(successful_results)} successful, {len(failed_entities)} failed entities")
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_assembly", 1, 4, "Aggregating relationships")
        
        # Aggregate all relationships
        all_relationships = []
        all_entities = {}
        
        for result in successful_results:
            entity_id = result.get("entity_id")
            relationships = result.get("relationships", {}).get("relationships", [])
            
            all_relationships.extend(relationships)
            all_entities[entity_id] = result
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_assembly", 2, 4, "Creating graph structure")
        
        # Use AI to enhance graph structure
        ai_service = UnifiedAIService()
        
        enhanced_graph = await ai_service.synthesize_knowledge_graph(
            entities=all_entities,
            relationships=all_relationships,
            enhancement_options={
                "infer_missing_connections": True,
                "identify_clusters": True,
                "calculate_centrality": True,
                "detect_communities": True,
                **options.get("graph_enhancement", {})
            }
        )
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_assembly", 3, 4, "Storing graph structure")
        
        # Store enhanced knowledge graph
        async with get_db_connection() as db:
            graph_id = await db.fetchval("""
                INSERT INTO knowledge_graphs (
                    user_id, graph_name, graph_structure, entities_count,
                    relationships_count, enhancement_metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                RETURNING id
            """,
                UUID(user_id),
                options.get("graph_name", f"Graph_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                enhanced_graph,
                len(all_entities),
                len(all_relationships),
                {
                    "successful_entities": len(successful_results),
                    "failed_entities": failed_entities,
                    "assembly_options": options
                }
            )
            
            # Store individual relationships with enhanced data
            for relationship in enhanced_graph.get("relationships", []):
                await db.execute("""
                    INSERT INTO knowledge_relationships (
                        graph_id, source_entity, target_entity, relation_type,
                        confidence_score, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    graph_id,
                    relationship.get("source"),
                    relationship.get("target"),
                    relationship.get("relation_type"),
                    relationship.get("confidence", 0.8),
                    relationship.get("metadata", {})
                )
        
        await _send_progress_update(task_id, user_id, "knowledge_graph_assembly", 4, 4, "Graph assembly completed")
        
        return {
            "status": "completed",
            "graph_id": str(graph_id),
            "user_id": user_id,
            "entities_processed": len(successful_results),
            "relationships_created": len(enhanced_graph.get("relationships", [])),
            "failed_entities": failed_entities,
            "enhancement_applied": True,
            "graph_metrics": enhanced_graph.get("metrics", {}),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Knowledge graph assembly async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="knowledge_graph.entity_linking", bind=True, max_retries=2, queue="ai_analysis")
def entity_linking_task(self, content_id: str, user_id: str, linking_options: Dict[str, Any]):
    """Link entities within content to existing knowledge graph"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _entity_linking_async(self.request.id, content_id, user_id, linking_options)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Entity linking failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _entity_linking_async(task_id: str, content_id: str, user_id: str, linking_options: Dict[str, Any]):
    """Entity linking implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Load content to analyze
        async with get_db_connection() as db:
            content = await db.fetchrow("""
                SELECT * FROM embeddings 
                WHERE id = $1 AND user_id = $2
            """, UUID(content_id), UUID(user_id))
            
            if not content:
                raise ValueError(f"Content {content_id} not found")
            
            # Get existing entities for linking
            existing_entities = await db.fetch("""
                SELECT * FROM knowledge_entities 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 200
            """, UUID(user_id))
        
        # Use AI to identify and link entities
        linking_results = await ai_service.link_entities_in_content(
            content_text=content["content"],
            content_metadata=content["metadata"],
            existing_entities=[dict(entity) for entity in existing_entities],
            linking_options=linking_options
        )
        
        # Store entity links
        links_created = 0
        for link in linking_results.get("entity_links", []):
            await db.execute("""
                INSERT INTO content_entity_links (
                    content_id, entity_id, link_type, confidence_score,
                    context_text, position_start, position_end
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                UUID(content_id),
                UUID(link["entity_id"]),
                link.get("link_type", "mention"),
                link.get("confidence", 0.8),
                link.get("context", ""),
                link.get("start_pos", 0),
                link.get("end_pos", 0)
            )
            links_created += 1
        
        return {
            "status": "completed",
            "content_id": content_id,
            "entities_linked": linking_results.get("entities_count", 0),
            "links_created": links_created,
            "linking_confidence": linking_results.get("overall_confidence", 0.8),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Entity linking async failed: {e}", exc_info=True)
        raise


async def _send_progress_update(
    task_id: str,
    entity_id: str,
    progress_type: str,
    current_value: int,
    total_value: Optional[int] = None,
    message: Optional[str] = None
):
    """Send progress update to database and WebSocket"""
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO task_progress (
                    task_id, entity_id, progress_type, current_value,
                    total_value, message, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                ON CONFLICT (task_id) DO UPDATE SET
                    current_value = EXCLUDED.current_value,
                    total_value = EXCLUDED.total_value,
                    message = EXCLUDED.message,
                    updated_at = CURRENT_TIMESTAMP
            """,
                task_id, entity_id, progress_type, current_value,
                total_value, message
            )
            
        # Send WebSocket update for real-time progress
        await send_task_progress(
            task_id=task_id,
            progress_type=progress_type,
            current_value=current_value,
            total_value=total_value,
            message=message,
            entity_id=entity_id,
            metadata={"task_type": "knowledge_graph"}
        )
        logger.info(f"Progress update: {task_id} - {progress_type} - {current_value}/{total_value} - {message}")
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")