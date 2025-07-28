"""
AI Processing Celery Tasks

Distributed tasks for AI-powered content analysis, embedding generation,
and LLM processing to eliminate blocking operations.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.embedding_service import EmbeddingService
from app.services.llm_processor import LLMProcessor
from app.services.realtime_progress_service import send_task_progress

logger = logging.getLogger(__name__)


@celery_app.task(name="ai.analyze_content", bind=True, max_retries=3)
def analyze_content_task(self, content_id: str, content: str, options: Dict[str, Any] = None):
    """
    Analyze content with AI in background.
    
    Args:
        content_id: ID of the content item
        content: Text content to analyze
        options: Analysis options (summarize, categorize, extract_entities, etc.)
    
    Returns:
        Analysis results with summary, tags, insights
    """
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _analyze_content_async(self.request.id, content_id, content, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Content analysis failed: {e}", exc_info=True)
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_analyze_content")
async def _analyze_content_async(task_id: str, content_id: str, content: str, options: Dict[str, Any]):
    """Async implementation of content analysis"""
    
    try:
        await _send_progress_update(task_id, content_id, "ai_analysis", 0, 4, "Starting AI analysis")
        
        ai_service = UnifiedAIService()
        analysis_results = {}
        
        # 1. Generate summary if requested
        if options.get("summarize", True):
            await _send_progress_update(task_id, content_id, "ai_analysis", 1, 4, "Generating summary")
            
            summary = await ai_service.generate_summary(
                content=content,
                max_length=options.get("summary_length", 200)
            )
            analysis_results["summary"] = summary
        
        # 2. Extract entities and tags
        if options.get("extract_entities", True):
            await _send_progress_update(task_id, content_id, "ai_analysis", 2, 4, "Extracting entities")
            
            entities = await ai_service.extract_entities(content)
            analysis_results["entities"] = entities
            
            # Generate tags from entities
            tags = await ai_service.generate_tags(content, entities)
            analysis_results["tags"] = tags
        
        # 3. Categorize content
        if options.get("categorize", True):
            await _send_progress_update(task_id, content_id, "ai_analysis", 3, 4, "Categorizing content")
            
            category = await ai_service.categorize_content(content)
            analysis_results["category"] = category
        
        # 4. Store results in database
        await _send_progress_update(task_id, content_id, "ai_analysis", 4, 4, "Storing results")
        
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE items 
                SET 
                    summary = COALESCE($2, summary),
                    processed_content = $3,
                    status = 'completed',
                    last_processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, 
                UUID(content_id), 
                analysis_results.get("summary"),
                analysis_results
            )
            
            # Store tags
            if "tags" in analysis_results:
                for tag in analysis_results["tags"]:
                    await db.execute("""
                        INSERT INTO item_tags (item_id, tag, confidence_score)
                        VALUES ($1, $2, $3)
                        ON CONFLICT DO NOTHING
                    """, UUID(content_id), tag.get("name"), tag.get("confidence", 0.8))
        
        return {
            "status": "completed",
            "content_id": content_id,
            "analysis_results": analysis_results,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Content analysis async failed: {e}", exc_info=True)
        await _send_progress_update(task_id, content_id, "ai_analysis", 0, 4, f"Analysis failed: {str(e)}")
        raise


@celery_app.task(name="ai.generate_embeddings_batch", bind=True, max_retries=2)
def generate_embeddings_batch_task(self, items: List[Dict[str, Any]], cache_prefix: str = ""):
    """
    Generate embeddings for multiple items in batch for cost efficiency.
    
    Args:
        items: List of {"id": str, "content": str, "type": str} items
        cache_prefix: Cache key prefix for organization
    
    Returns:
        Batch processing results with embeddings
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _generate_embeddings_batch_async(self.request.id, items, cache_prefix)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_generate_embeddings_batch")
async def _generate_embeddings_batch_async(task_id: str, items: List[Dict[str, Any]], cache_prefix: str):
    """Async implementation of batch embedding generation"""
    
    try:
        await _send_progress_update(task_id, "batch", "embeddings", 0, len(items), f"Starting batch embedding for {len(items)} items")
        
        embedding_service = EmbeddingService()
        results = []
        
        # Process in batches to optimize API calls
        batch_size = 10  # Optimize based on OpenAI rate limits
        
        for i in range(0, len(items), batch_size):
            batch_items = items[i:i + batch_size]
            batch_texts = [item["content"] for item in batch_items]
            
            await _send_progress_update(
                task_id, "batch", "embeddings", 
                i, len(items), f"Processing batch {i//batch_size + 1}"
            )
            
            # Generate embeddings for batch
            embeddings = await embedding_service.generate_embeddings_batch(batch_texts)
            
            # Store results in database
            async with get_db_connection() as db:
                for j, item in enumerate(batch_items):
                    if j < len(embeddings):
                        # Store embedding
                        await db.execute("""
                            INSERT INTO embeddings (item_id, embedding_vector, model_name, created_at)
                            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                            ON CONFLICT (item_id) DO UPDATE SET
                                embedding_vector = EXCLUDED.embedding_vector,
                                model_name = EXCLUDED.model_name,
                                created_at = CURRENT_TIMESTAMP
                        """, 
                            UUID(item["id"]), 
                            embeddings[j], 
                            embedding_service.model_name
                        )
                        
                        results.append({
                            "id": item["id"],
                            "status": "success",
                            "embedding_dimensions": len(embeddings[j])
                        })
                    else:
                        results.append({
                            "id": item["id"],
                            "status": "failed",
                            "error": "Embedding generation failed"
                        })
        
        await _send_progress_update(task_id, "batch", "embeddings", len(items), len(items), "Batch embedding completed")
        
        return {
            "status": "completed",
            "processed_count": len(results),
            "successful_count": len([r for r in results if r["status"] == "success"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch embedding generation async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="ai.process_with_llm", bind=True, max_retries=3)
def process_with_llm_task(self, content: str, prompt_type: str, options: Dict[str, Any] = None):
    """
    Process content with LLM for specific tasks.
    
    Args:
        content: Content to process
        prompt_type: Type of processing (summarize, analyze, categorize, etc.)
        options: Processing options and parameters
    
    Returns:
        LLM processing results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _process_with_llm_async(self.request.id, content, prompt_type, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"LLM processing failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_process_with_llm")
async def _process_with_llm_async(task_id: str, content: str, prompt_type: str, options: Dict[str, Any]):
    """Async implementation of LLM processing"""
    
    try:
        await _send_progress_update(task_id, "llm", "processing", 0, 2, f"Starting {prompt_type} processing")
        
        llm_processor = LLMProcessor()
        
        # Process based on prompt type
        if prompt_type == "summarize":
            result = await llm_processor.summarize(
                content=content,
                max_length=options.get("max_length", 200),
                style=options.get("style", "concise")
            )
        elif prompt_type == "analyze":
            result = await llm_processor.analyze_content(
                content=content,
                analysis_type=options.get("analysis_type", "general")
            )
        elif prompt_type == "categorize":
            result = await llm_processor.categorize(
                content=content,
                categories=options.get("categories", [])
            )
        elif prompt_type == "extract_insights":
            result = await llm_processor.extract_insights(
                content=content,
                focus_areas=options.get("focus_areas", [])
            )
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        await _send_progress_update(task_id, "llm", "processing", 2, 2, f"{prompt_type} processing completed")
        
        return {
            "status": "completed",
            "prompt_type": prompt_type,
            "result": result,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"LLM processing async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="ai.smart_categorization", bind=True)
def smart_categorization_task(self, content_items: List[Dict[str, Any]]):
    """
    Perform smart categorization for multiple content items.
    
    Args:
        content_items: List of content items to categorize
    
    Returns:
        Categorization results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _smart_categorization_async(self.request.id, content_items)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Smart categorization failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_smart_categorization")
async def _smart_categorization_async(task_id: str, content_items: List[Dict[str, Any]]):
    """Async implementation of smart categorization"""
    
    try:
        await _send_progress_update(
            task_id, "categorization", "processing", 
            0, len(content_items), "Starting smart categorization"
        )
        
        ai_service = UnifiedAIService()
        results = []
        
        for i, item in enumerate(content_items):
            category_result = await ai_service.smart_categorize(
                content=item["content"],
                existing_categories=item.get("existing_categories", []),
                context=item.get("context", {})
            )
            
            # Update database
            async with get_db_connection() as db:
                await db.execute("""
                    UPDATE items 
                    SET category = $2, subcategory = $3
                    WHERE id = $1
                """, 
                    UUID(item["id"]), 
                    category_result.get("category"),
                    category_result.get("subcategory")
                )
            
            results.append({
                "id": item["id"],
                "category": category_result.get("category"),
                "subcategory": category_result.get("subcategory"),
                "confidence": category_result.get("confidence", 0.0)
            })
            
            await _send_progress_update(
                task_id, "categorization", "processing",
                i + 1, len(content_items), f"Categorized {i + 1}/{len(content_items)} items"
            )
        
        return {
            "status": "completed",
            "categorized_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Smart categorization async failed: {e}", exc_info=True)
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
            metadata={"task_type": "ai_processing"}
        )
        logger.info(f"Progress update: {task_id} - {progress_type} - {current_value}/{total_value} - {message}")
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")