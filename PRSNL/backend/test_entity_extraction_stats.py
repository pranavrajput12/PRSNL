#!/usr/bin/env python3
"""
Test the entity extraction stats endpoint
"""
import asyncio
import logging
from app.services.entity_extraction_service import entity_extraction_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_entity_stats():
    """Test the entity extraction statistics endpoint"""
    try:
        logger.info("Testing entity extraction statistics...")
        
        # Call the service method that the API uses
        stats = await entity_extraction_service.get_entity_statistics()
        
        logger.info("✅ Entity extraction statistics retrieved successfully!")
        logger.info(f"Stats keys: {list(stats.keys())}")
        
        # Print the statistics
        if "entity_statistics" in stats:
            logger.info(f"Entity statistics count: {len(stats['entity_statistics'])}")
            for stat in stats['entity_statistics']:
                logger.info(f"  Entity type: {stat.get('entity_type', 'unknown')} - Count: {stat.get('total_entities', 0)}")
        
        if "relationship_statistics" in stats:
            logger.info(f"Relationship statistics count: {len(stats['relationship_statistics'])}")
            for stat in stats['relationship_statistics']:
                logger.info(f"  Relationship type: {stat.get('relationship_type', 'unknown')} - Count: {stat.get('total_relationships', 0)}")
        
        logger.info(f"Total entities: {stats.get('total_entities', 0)}")
        logger.info(f"Total relationships: {stats.get('total_relationships', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Entity extraction statistics test failed: {e}")
        return False


async def main():
    """Main function"""
    success = await test_entity_stats()
    if success:
        logger.info("🎉 Entity extraction stats test completed successfully!")
        exit(0)
    else:
        logger.error("💥 Entity extraction stats test failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())