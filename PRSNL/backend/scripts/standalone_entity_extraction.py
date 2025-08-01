#!/usr/bin/env python3
"""
Standalone Entity Extraction for Knowledge Graph Backfill
Processes existing content items through entity extraction without FastAPI context
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
from app.services.unified_ai_service import unified_ai_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandaloneEntityExtractor:
    """Standalone entity extraction service that doesn't depend on FastAPI"""
    
    def __init__(self):
        self.ai_service = unified_ai_service
        self.db_pool = None
        
        # Entity type mappings for different content types
        self.content_type_mappings = {
            'conversation': ['conversation_turn', 'text_entity', 'knowledge_concept'],
            'video': ['video_segment', 'audio_entity', 'knowledge_concept'],
            'code': ['code_function', 'code_class', 'code_module', 'text_entity'],
            'github_repo': ['code_function', 'code_class', 'code_module'],
            'github_document': ['text_entity', 'knowledge_concept'],
            'article': ['text_entity', 'knowledge_concept'],
            'note': ['text_entity', 'knowledge_concept'],
            'tutorial': ['text_entity', 'knowledge_concept'],
            'document': ['text_entity', 'knowledge_concept'],
            'auto': ['text_entity', 'knowledge_concept'],
            'link': ['text_entity', 'knowledge_concept'],
            'timeline': ['timeline_event', 'knowledge_concept']
        }
    
    async def initialize_db(self):
        """Initialize database connection"""
        try:
            self.db_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=5
            )
            logger.info("✅ Database pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def close_db(self):
        """Close database connection"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Database pool closed")
    
    async def extract_entities_simple(self, content_text: str, content_type: str) -> List[Dict]:
        """Simple entity extraction using AI"""
        entities = []
        
        try:
            # Create a simple prompt for entity extraction
            analysis_prompt = f"""
            Analyze this {content_type} content and extract 3-5 key entities:
            
            Content: {content_text[:2000]}
            
            Extract entities with these types:
            - knowledge_concept: Main topics, technologies, concepts
            - text_entity: People, tools, products, specific items mentioned
            
            Return ONLY a JSON array like this:
            [
                {{"name": "React", "entity_type": "knowledge_concept", "description": "JavaScript library", "confidence": 0.9}},
                {{"name": "useEffect", "entity_type": "text_entity", "description": "React hook", "confidence": 0.8}}
            ]
            """
            
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse AI response
            try:
                ai_entities = json.loads(response)
                if isinstance(ai_entities, list):
                    for entity in ai_entities:
                        if all(key in entity for key in ['name', 'entity_type']):
                            entities.append({
                                "name": entity["name"],
                                "entity_type": entity["entity_type"],
                                "description": entity.get("description", ""),
                                "confidence": entity.get("confidence", 0.8),
                                "metadata": {"source": "simple_extraction"}
                            })
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI entity extraction response")
            
        except Exception as e:
            logger.error(f"Error in simple entity extraction: {e}")
        
        return entities
    
    async def create_unified_entity(self, content_id: UUID, entity_data: Dict) -> Optional[UUID]:
        """Create a unified entity in the database"""
        try:
            async with self.db_pool.acquire() as conn:
                entity_id = await conn.fetchval("""
                    INSERT INTO unified_entities (
                        entity_type, source_content_id, name, description, metadata,
                        confidence_score, extraction_method
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    entity_data["entity_type"],
                    content_id,
                    entity_data["name"],
                    entity_data.get("description", ""),
                    json.dumps(entity_data.get("metadata", {})),
                    entity_data.get("confidence", 1.0),
                    "standalone_extraction"
                )
                
                return entity_id
                
        except Exception as e:
            logger.error(f"Error creating unified entity: {e}")
            return None
    
    async def create_simple_relationships(self, entities: List[Dict]) -> List[Dict]:
        """Create simple relationships between entities"""
        relationships = []
        
        if len(entities) < 2:
            return relationships
        
        # Create "related_to" relationships between entities
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                try:
                    async with self.db_pool.acquire() as conn:
                        relationship_id = await conn.fetchval("""
                            INSERT INTO unified_relationships (
                                source_entity_id, target_entity_id, relationship_type,
                                confidence_score, context, extraction_method
                            )
                            VALUES ($1, $2, $3, $4, $5, $6)
                            RETURNING id
                        """,
                            UUID(entity1["entity_id"]),
                            UUID(entity2["entity_id"]),
                            "related_to",
                            0.7,
                            "Co-occurring in same content",
                            "standalone_inference"
                        )
                        
                        if relationship_id:
                            relationships.append({
                                "relationship_id": str(relationship_id),
                                "source_entity": entity1["name"],
                                "target_entity": entity2["name"],
                                "relationship_type": "related_to",
                                "confidence": 0.7
                            })
                            
                except Exception as e:
                    logger.error(f"Error creating relationship: {e}")
        
        return relationships
    
    async def process_item(self, item: Dict) -> Dict:
        """Process a single item through entity extraction"""
        
        item_id = item['id']
        title = item.get('title', 'Untitled')
        content = item.get('raw_content', '')
        content_type = item.get('content_type', 'article')
        
        try:
            logger.info(f"🔍 Processing item {item_id}: {title[:50]}...")
            
            if len(content) < 50:
                logger.info(f"⏭️  Skipping {item_id}: Content too short")
                return {"success": True, "entities_created": [], "relationships_created": [], "reason": "content_too_short"}
            
            # Extract entities from the content
            entities = await self.extract_entities_simple(content, content_type)
            
            # Create unified entities in database
            created_entities = []
            for entity_data in entities:
                entity_id = await self.create_unified_entity(item_id, entity_data)
                if entity_id:
                    created_entities.append({
                        "entity_id": str(entity_id),
                        "name": entity_data["name"],
                        "entity_type": entity_data["entity_type"],
                        "confidence": entity_data.get("confidence", 1.0)
                    })
            
            # Create relationships between entities
            relationships = await self.create_simple_relationships(created_entities)
            
            # Update item metadata
            await self.update_item_metadata(item_id, {
                "entities_created": created_entities,
                "relationships_created": relationships,
                "extraction_method": "standalone_extraction"
            })
            
            logger.info(f"✅ Processed {item_id}: {len(created_entities)} entities, {len(relationships)} relationships")
            
            return {
                "success": True,
                "entities_created": created_entities,
                "relationships_created": relationships,
                "extraction_method": "standalone_extraction"
            }
            
        except Exception as e:
            logger.error(f"❌ Exception processing item {item_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_item_metadata(self, item_id: UUID, extraction_result: Dict):
        """Update item metadata with entity extraction results"""
        
        try:
            async with self.db_pool.acquire() as conn:
                metadata_update = {
                    "entity_extraction": {
                        "processed_at": datetime.now().isoformat(),
                        "entities_created": len(extraction_result.get('entities_created', [])),
                        "relationships_created": len(extraction_result.get('relationships_created', [])),
                        "extraction_method": extraction_result.get('extraction_method', 'standalone_extraction'),
                        "processing_context": "standalone_backfill"
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
                
                logger.debug(f"Updated metadata for item {item_id}")
                
        except Exception as e:
            logger.error(f"Error updating metadata for item {item_id}: {e}")
    
    async def get_items_to_process(self, limit: int = 10) -> List[Dict]:
        """Get items that need entity extraction"""
        
        try:
            async with self.db_pool.acquire() as conn:
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
                            metadata->>'entity_extraction' IS NULL
                            OR NOT EXISTS (
                                SELECT 1 FROM unified_entities WHERE source_content_id = items.id
                            )
                        )
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
                
                logger.info(f"Found {len(items)} items to process for entity extraction")
                return [dict(item) for item in items]
                
        except Exception as e:
            logger.error(f"Error getting items to process: {e}")
            return []
    
    async def get_knowledge_graph_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get entity counts
                entity_count = await conn.fetchval("SELECT COUNT(*) FROM unified_entities")
                relationship_count = await conn.fetchval("SELECT COUNT(*) FROM unified_relationships")
                
                # Get entity types
                entity_types = await conn.fetch("""
                    SELECT entity_type, COUNT(*) as count 
                    FROM unified_entities 
                    GROUP BY entity_type 
                    ORDER BY count DESC
                """)
                
                return {
                    "total_entities": entity_count,
                    "total_relationships": relationship_count,
                    "entity_types": [{"type": row["entity_type"], "count": row["count"]} for row in entity_types]
                }
                
        except Exception as e:
            logger.error(f"Error getting knowledge graph stats: {e}")
            return {"error": str(e)}


async def main():
    """Main function to run standalone entity extraction"""
    
    logger.info("🧠 Standalone Knowledge Graph Entity Extraction Starting...")
    
    extractor = StandaloneEntityExtractor()
    
    try:
        # Initialize database
        await extractor.initialize_db()
        
        # Get items to process
        items = await extractor.get_items_to_process(limit=10)  # Process 10 items as a test
        
        if not items:
            logger.info("✅ No items found that need entity extraction processing")
            return
        
        logger.info(f"📊 Processing {len(items)} items...")
        
        success_count = 0
        error_count = 0
        
        # Process items one by one
        for i, item in enumerate(items):
            logger.info(f"🔄 Processing item {i+1}/{len(items)}")
            
            result = await extractor.process_item(item)
            
            if result.get("success"):
                success_count += 1
            else:
                error_count += 1
            
            # Small delay between items
            await asyncio.sleep(1)
        
        # Final statistics
        logger.info("📈 PROCESSING COMPLETE - Final Statistics:")
        logger.info(f"   ✅ Successful Extractions: {success_count}")
        logger.info(f"   ❌ Failed Extractions: {error_count}")
        
        # Get final knowledge graph statistics
        stats = await extractor.get_knowledge_graph_stats()
        if 'error' not in stats:
            logger.info("🧠 Knowledge Graph Statistics:")
            logger.info(f"   📈 Total Entities: {stats['total_entities']}")
            logger.info(f"   🔗 Total Relationships: {stats['total_relationships']}")
            
            if stats['entity_types']:
                logger.info("   📊 Entity Types:")
                for entity_type in stats['entity_types']:
                    logger.info(f"      - {entity_type['type']}: {entity_type['count']}")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"💥 Process failed: {e}")
        raise
    finally:
        await extractor.close_db()
    
    logger.info("🏁 Standalone Entity Extraction Complete")


if __name__ == "__main__":
    asyncio.run(main())