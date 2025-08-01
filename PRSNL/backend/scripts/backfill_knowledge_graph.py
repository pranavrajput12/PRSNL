#!/usr/bin/env python3
"""
Knowledge Graph Backfill Script
Processes existing content items through entity extraction to populate the knowledge graph
"""
import asyncio
import asyncpg
import json
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.entity_extraction_service import entity_extraction_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeGraphBackfill:
    """Backfill existing content items with entity extraction"""
    
    def __init__(self):
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        
    async def get_existing_items(self) -> List[Dict]:
        """Get all existing content items that haven't been processed for entity extraction"""
        
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL)
            
            # Get items that don't have entity extraction metadata
            items = await conn.fetch("""
                SELECT 
                    id, 
                    title, 
                    raw_content, 
                    url,
                    content_type,
                    created_at,
                    metadata
                FROM items 
                WHERE 
                    raw_content IS NOT NULL 
                    AND length(raw_content) > 50
                    AND (
                        metadata->>'auto_processing' IS NULL 
                        OR metadata->'auto_processing'->>'entity_extraction' IS NULL
                    )
                ORDER BY created_at DESC
                LIMIT 100  -- Process in batches
            """)
            
            await conn.close()
            
            logger.info(f"Found {len(items)} items to process for entity extraction")
            return [dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting existing items: {e}")
            return []
    
    async def process_item_entities(self, item: Dict) -> Dict:
        """Process a single item through entity extraction"""
        
        item_id = item['id']
        title = item.get('title', 'Untitled')
        content = item.get('raw_content', '')
        content_type = item.get('content_type', 'article')
        
        try:
            logger.info(f"Processing item {item_id}: {title[:50]}...")
            
            # Extract entities from the content
            result = await entity_extraction_service.extract_entities_from_content(
                content_id=item_id,
                content_type=content_type,
                content_text=content[:5000],  # Limit content for extraction
                metadata={
                    "processing_context": "backfill_script",
                    "original_title": title,
                    "backfill_timestamp": datetime.now().isoformat()
                }
            )
            
            # Update item metadata with extraction results
            if result.get('success'):
                await self.update_item_metadata(item_id, result)
                logger.info(f"✅ Processed {item_id}: {len(result['entities_created'])} entities, {len(result['relationships_created'])} relationships")
                self.success_count += 1
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ Failed to process {item_id}: {error_msg}")
                self.errors.append(f"{item_id}: {error_msg}")
                self.error_count += 1
            
            self.processed_count += 1
            return result
            
        except Exception as e:
            logger.error(f"❌ Exception processing item {item_id}: {e}")
            self.errors.append(f"{item_id}: {str(e)}")
            self.error_count += 1
            self.processed_count += 1
            return {"success": False, "error": str(e)}
    
    async def update_item_metadata(self, item_id: UUID, extraction_result: Dict):
        """Update item metadata with entity extraction results"""
        
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL)
            
            # Update the item's metadata with extraction results
            metadata_update = {
                "entity_extraction": {
                    "processed_at": datetime.now().isoformat(),
                    "entities_created": len(extraction_result.get('entities_created', [])),
                    "relationships_created": len(extraction_result.get('relationships_created', [])),
                    "extraction_method": extraction_result.get('extraction_method', 'ai_extracted'),
                    "processing_context": "backfill_script"
                }
            }
            
            await conn.execute("""
                UPDATE items 
                SET 
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{entity_extraction}', 
                        $2::jsonb, 
                        true
                    ),
                    updated_at = NOW()
                WHERE id = $1
            """, item_id, json.dumps(metadata_update["entity_extraction"]))
            
            await conn.close()
            logger.debug(f"Updated metadata for item {item_id}")
            
        except Exception as e:
            logger.error(f"Error updating metadata for item {item_id}: {e}")
    
    async def run_backfill(self, batch_size: int = 5, delay_seconds: float = 1.0):
        """Run the complete backfill process"""
        
        logger.info("🚀 Starting Knowledge Graph Backfill Process")
        start_time = datetime.now()
        
        # Get items to process
        items = await self.get_existing_items()
        
        if not items:
            logger.info("✅ No items found that need entity extraction processing")
            return
        
        logger.info(f"📊 Processing {len(items)} items in batches of {batch_size}")
        
        # Process items in batches to avoid overwhelming the system
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} items)")
            
            # Process batch concurrently
            tasks = [self.process_item_entities(item) for item in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add delay between batches
            if i + batch_size < len(items):
                logger.info(f"⏳ Waiting {delay_seconds}s before next batch...")
                await asyncio.sleep(delay_seconds)
        
        # Final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("📈 BACKFILL COMPLETE - Final Statistics:")
        logger.info(f"   📊 Total Items Processed: {self.processed_count}")
        logger.info(f"   ✅ Successful Extractions: {self.success_count}")
        logger.info(f"   ❌ Failed Extractions: {self.error_count}")
        logger.info(f"   ⏱️  Total Duration: {duration}")
        logger.info(f"   🚀 Processing Rate: {self.processed_count / duration.total_seconds():.2f} items/second")
        
        if self.errors:
            logger.warning("⚠️  Errors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.warning(f"   - {error}")
            if len(self.errors) > 10:
                logger.warning(f"   ... and {len(self.errors) - 10} more errors")
        
        # Get final knowledge graph statistics
        await self.print_knowledge_graph_stats()
    
    async def print_knowledge_graph_stats(self):
        """Print final knowledge graph statistics"""
        
        try:
            stats = await entity_extraction_service.get_entity_statistics()
            
            if 'error' not in stats:
                logger.info("🧠 Knowledge Graph Statistics:")
                logger.info(f"   📈 Total Entities: {stats.get('total_entities', 0)}")
                logger.info(f"   🔗 Total Relationships: {stats.get('total_relationships', 0)}")
                
                entity_stats = stats.get('entity_statistics', [])
                if entity_stats:
                    logger.info("   📊 Entity Types:")
                    for stat in entity_stats:
                        logger.info(f"      - {stat.get('entity_type', 'unknown')}: {stat.get('total_entities', 0)}")
                
                relationship_stats = stats.get('relationship_statistics', [])
                if relationship_stats:
                    logger.info("   🔗 Relationship Types:")
                    for stat in relationship_stats:
                        logger.info(f"      - {stat.get('relationship_type', 'unknown')}: {stat.get('total_relationships', 0)}")
            else:
                logger.warning(f"Could not retrieve knowledge graph statistics: {stats['error']}")
                
        except Exception as e:
            logger.error(f"Error getting knowledge graph statistics: {e}")


async def main():
    """Main function to run the backfill script"""
    
    logger.info("🧠 Knowledge Graph Backfill Script Starting...")
    
    # Initialize backfill processor
    backfill_processor = KnowledgeGraphBackfill()
    
    try:
        # Run the backfill process
        await backfill_processor.run_backfill(
            batch_size=3,      # Process 3 items at a time to avoid overwhelming AI service
            delay_seconds=2.0  # 2 second delay between batches
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️  Backfill process interrupted by user")
    except Exception as e:
        logger.error(f"💥 Backfill process failed: {e}")
        raise
    
    logger.info("🏁 Knowledge Graph Backfill Script Complete")


if __name__ == "__main__":
    asyncio.run(main())