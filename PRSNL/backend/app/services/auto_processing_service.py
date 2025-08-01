"""
Auto-Processing Service - Centralized AI processing coordinator for captured content
Automatically triggers AI analysis, summarization, categorization, and embedding generation
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.config import settings
from app.db.database import get_db_pool, update_item_embedding
from app.services.embedding_service import embedding_service
from app.services.llm_processor import llm_processor
from app.services.smart_categorization import smart_categorization
from app.services.content_summarization import ContentSummarizationService
from app.services.entity_extraction_service import entity_extraction_service

logger = logging.getLogger(__name__)

class AutoProcessingService:
    """
    Centralized service for automatic AI processing of captured content.
    Coordinates the AI pipeline: Processing → Categorization → Summarization → Embeddings
    """
    
    def __init__(self):
        self.summarization_service = ContentSummarizationService()
        self.processing_queue: Set[str] = set()  # Track items being processed
        
    async def process_captured_item(
        self, 
        item_id: UUID, 
        content: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        enable_ai_processing: bool = True
    ) -> Dict:
        """
        Automatically process a captured item through the complete AI pipeline.
        
        Args:
            item_id: Item UUID
            content: Raw content to process
            url: Source URL (if available)  
            title: Item title
            enable_ai_processing: Whether to run AI analysis
            
        Returns:
            Dict with processing results and status
        """
        item_id_str = str(item_id)
        
        # Prevent duplicate processing
        if item_id_str in self.processing_queue:
            logger.info(f"Item {item_id_str} already being processed, skipping")
            return {"status": "already_processing", "item_id": item_id_str}
            
        self.processing_queue.add(item_id_str)
        
        try:
            logger.info(f"🤖 Starting auto-processing for item {item_id_str}")
            
            # Get item data from database if not provided
            if not content:
                content, url, title = await self._get_item_data(item_id)
                
            if not content:
                logger.warning(f"No content available for item {item_id_str}, skipping AI processing")
                return {"status": "no_content", "item_id": item_id_str}
            
            processing_results = {
                "item_id": item_id_str,
                "status": "processing",
                "steps_completed": [],
                "errors": []
            }
            
            # Step 1: AI Content Analysis (if enabled)
            if enable_ai_processing and settings.AZURE_OPENAI_API_KEY:
                try:
                    logger.info(f"🔍 Running AI analysis for item {item_id_str}")
                    processed_content = await llm_processor.process_content(
                        content=content[:8000],  # Limit content length
                        url=url,
                        title=title
                    )
                    
                    # Update item with AI analysis results
                    await self._update_item_with_ai_analysis(item_id, processed_content)
                    processing_results["steps_completed"].append("ai_analysis")
                    processing_results["ai_analysis"] = {
                        "tags_generated": len(processed_content.tags),
                        "summary_length": len(processed_content.summary),
                        "key_points": len(processed_content.key_points),
                        "sentiment": processed_content.sentiment
                    }
                    
                except Exception as e:
                    logger.error(f"AI analysis failed for item {item_id_str}: {e}")
                    processing_results["errors"].append(f"ai_analysis: {str(e)}")
            
            # Step 2: Smart Categorization  
            try:
                logger.info(f"🏷️ Running categorization for item {item_id_str}")
                categorization_result = await smart_categorization.categorize_item(
                    title=title or "Untitled",
                    content=content[:4000],  # Limit for categorization
                    tags=None  # Fixed parameter name
                )
                
                # Update item with categorization
                await self._update_item_categorization(item_id, categorization_result)
                processing_results["steps_completed"].append("categorization")
                processing_results["categorization"] = {
                    "category": categorization_result.get("category"),
                    "subcategory": categorization_result.get("subcategory"),
                    "confidence": categorization_result.get("confidence"),
                    "suggested_tags": len(categorization_result.get("suggested_tags", []))
                }
                
            except Exception as e:
                logger.error(f"Categorization failed for item {item_id_str}: {e}")
                processing_results["errors"].append(f"categorization: {str(e)}")
            
            # Step 3: Generate Summary (if content is substantial)
            if len(content) > 500:  # Only summarize substantial content
                try:
                    logger.info(f"📝 Generating summary for item {item_id_str}")
                    summary_result = await self.summarization_service.summarize_item(
                        item_id=item_id_str,
                        summary_type="brief"
                    )
                    processing_results["steps_completed"].append("summarization")
                    processing_results["summarization"] = {
                        "summary_generated": bool(summary_result.get("summary"))
                    }
                    
                except Exception as e:
                    logger.error(f"Summarization failed for item {item_id_str}: {e}")
                    processing_results["errors"].append(f"summarization: {str(e)}")
            
            # Step 4: Entity Extraction & Knowledge Graph Integration
            try:
                logger.info(f"🧠 Extracting entities for knowledge graph integration - item {item_id_str}")
                
                # Get content type from database for proper entity extraction
                content_type = await self._get_item_content_type(item_id)
                
                entity_results = await entity_extraction_service.extract_entities_from_content(
                    content_id=item_id,
                    content_type=content_type or 'article',
                    content_text=content[:5000],  # Larger limit for entity extraction
                    metadata={"processing_context": "auto_processing"}
                )
                
                if entity_results.get("success"):
                    processing_results["steps_completed"].append("entity_extraction")
                    processing_results["entity_extraction"] = {
                        "entities_created": len(entity_results["entities_created"]),
                        "relationships_created": len(entity_results["relationships_created"]),
                        "extraction_method": entity_results["extraction_method"]
                    }
                else:
                    processing_results["errors"].append(f"entity_extraction: {entity_results.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Entity extraction failed for item {item_id_str}: {e}")
                processing_results["errors"].append(f"entity_extraction: {str(e)}")
            
            # Step 5: Generate Embeddings
            try:
                logger.info(f"🔢 Generating embeddings for item {item_id_str}")
                # Use summary if available, otherwise use truncated content
                embedding_text = content[:2000]  # Limit text for embedding
                
                embedding = await embedding_service.generate_embedding(embedding_text)
                if embedding:
                    await update_item_embedding(item_id_str, embedding)
                    processing_results["steps_completed"].append("embeddings")
                    processing_results["embeddings"] = {
                        "embedding_dimensions": len(embedding),
                        "text_length": len(embedding_text)
                    }
                    
            except Exception as e:
                logger.error(f"Embedding generation failed for item {item_id_str}: {e}")
                processing_results["errors"].append(f"embeddings: {str(e)}")
            
            # Step 6: Update item status to completed
            await self._mark_processing_complete(item_id, processing_results)
            
            processing_results["status"] = "completed"
            processing_results["total_steps"] = len(processing_results["steps_completed"])
            processing_results["success_rate"] = len(processing_results["steps_completed"]) / 5  # 5 total steps now
            
            logger.info(f"✅ Auto-processing completed for item {item_id_str}. "
                       f"Steps: {processing_results['steps_completed']}")
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Auto-processing failed for item {item_id_str}: {e}")
            processing_results["status"] = "failed"
            processing_results["errors"].append(f"general: {str(e)}")
            return processing_results
            
        finally:
            # Always remove from processing queue
            self.processing_queue.discard(item_id_str)
    
    async def batch_process_items(self, item_ids: List[UUID], max_concurrent: int = 3) -> Dict:
        """
        Process multiple items concurrently with rate limiting.
        
        Args:
            item_ids: List of item UUIDs to process
            max_concurrent: Maximum concurrent processing tasks
            
        Returns:
            Dict with batch processing results
        """
        logger.info(f"🚀 Starting batch processing for {len(item_ids)} items")
        
        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_limit(item_id: UUID):
            async with semaphore:
                return await self.process_captured_item(item_id)
        
        # Process all items concurrently with limit
        tasks = [process_with_limit(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile batch results
        batch_results = {
            "total_items": len(item_ids),
            "completed": 0,
            "failed": 0,
            "errors": [],
            "results": []
        }
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results["failed"] += 1
                batch_results["errors"].append(f"Item {item_ids[i]}: {str(result)}")
            else:
                batch_results["results"].append(result)
                if result.get("status") == "completed":
                    batch_results["completed"] += 1
                else:
                    batch_results["failed"] += 1
        
        logger.info(f"📊 Batch processing complete. Success: {batch_results['completed']}, "
                   f"Failed: {batch_results['failed']}")
        
        return batch_results
    
    async def get_processing_status(self, item_id: UUID) -> Dict:
        """Get current processing status for an item."""
        item_id_str = str(item_id)
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            item_data = await conn.fetchrow("""
                SELECT 
                    status,
                    metadata->>'auto_processing' as processing_data,
                    created_at,
                    updated_at
                FROM items 
                WHERE id = $1
            """, item_id)
            
            if not item_data:
                return {"error": "Item not found"}
            
            processing_data = {}
            if item_data['processing_data']:
                try:
                    processing_data = json.loads(item_data['processing_data'])
                except json.JSONDecodeError:
                    pass
            
            return {
                "item_id": item_id_str,
                "status": item_data['status'],
                "currently_processing": item_id_str in self.processing_queue,
                "processing_results": processing_data,
                "created_at": item_data['created_at'].isoformat() if item_data['created_at'] else None,
                "updated_at": item_data['updated_at'].isoformat() if item_data['updated_at'] else None
            }
    
    async def _get_item_data(self, item_id: UUID) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Retrieve item content, URL, and title from database."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            item_data = await conn.fetchrow("""
                SELECT raw_content, url, title 
                FROM items 
                WHERE id = $1
            """, item_id)
            
            if item_data:
                return item_data['raw_content'], item_data['url'], item_data['title']
            return None, None, None
    
    async def _get_item_content_type(self, item_id: UUID) -> Optional[str]:
        """Get the content type of an item from the database."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            content_type = await conn.fetchval("""
                SELECT content_type FROM items WHERE id = $1
            """, item_id)
            return content_type
    
    async def _update_item_with_ai_analysis(self, item_id: UUID, processed_content) -> None:
        """Update item with AI analysis results."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Add AI-generated tags
            if processed_content.tags:
                for tag_name in processed_content.tags:
                    # Get or create tag
                    tag_id = await conn.fetchval("""
                        SELECT id FROM tags WHERE name = $1
                    """, tag_name.lower())
                    
                    if not tag_id:
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            RETURNING id
                        """, tag_name.lower())
                    
                    # Link tag to item  
                    await conn.execute("""
                        INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, item_id, tag_id)
            
            # Update item with AI analysis metadata
            ai_metadata = {
                "ai_analysis": {
                    "tags": processed_content.tags,
                    "key_points": processed_content.key_points,
                    "sentiment": processed_content.sentiment,
                    "reading_time": processed_content.reading_time,
                    "entities": processed_content.entities,
                    "processed_at": asyncio.get_event_loop().time()
                }
            }
            
            await conn.execute("""
                UPDATE items
                SET 
                    summary = COALESCE($2, summary),
                    metadata = jsonb_set(COALESCE(metadata, '{}'), '{ai_analysis}', $3::jsonb, true),
                    updated_at = NOW()
                WHERE id = $1
            """, item_id, processed_content.summary, json.dumps(ai_metadata["ai_analysis"]))
    
    async def _update_item_categorization(self, item_id: UUID, categorization_result: Dict) -> None:
        """Update item with categorization results."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET 
                    category = $2,
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{categorization}', 
                        $3::jsonb, 
                        true
                    ),
                    updated_at = NOW()
                WHERE id = $1
            """, item_id, categorization_result.get("category"), json.dumps({
                "subcategory": categorization_result.get("subcategory"),
                "confidence": categorization_result.get("confidence"),
                "content_type": categorization_result.get("content_type"),
                "reasoning": categorization_result.get("reasoning"),
                "suggested_tags": categorization_result.get("suggested_tags", [])
            }))
    
    async def _mark_processing_complete(self, item_id: UUID, processing_results: Dict) -> None:
        """Mark item processing as complete and store results."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE items
                SET 
                    status = CASE 
                        WHEN status = 'pending' THEN 'completed'
                        ELSE status 
                    END,
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{auto_processing}', 
                        $2::jsonb, 
                        true
                    ),
                    updated_at = NOW()
                WHERE id = $1
            """, item_id, json.dumps({
                "steps_completed": processing_results["steps_completed"],
                "errors": processing_results["errors"],
                "processed_at": asyncio.get_event_loop().time(),
                "success_rate": processing_results.get("success_rate", 0)
            }))

# Create singleton instance
auto_processing_service = AutoProcessingService()