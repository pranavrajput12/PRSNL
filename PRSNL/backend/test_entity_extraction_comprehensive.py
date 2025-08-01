#!/usr/bin/env python3
"""
Comprehensive test for the entity extraction stats after migration
"""
import asyncio
import logging
from app.db.database import create_db_pool, close_db_pool
from app.services.entity_extraction_service import entity_extraction_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_materialized_views_directly():
    """Test materialized views directly"""
    try:
        from app.db.database import get_db_pool
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            logger.info("Testing materialized views directly...")
            
            # Test entity_statistics view
            try:
                entity_stats = await conn.fetch("SELECT * FROM entity_statistics")
                logger.info(f"✅ entity_statistics view accessible - {len(entity_stats)} rows")
                for row in entity_stats:
                    logger.info(f"  {dict(row)}")
            except Exception as e:
                logger.error(f"❌ entity_statistics view error: {e}")
            
            # Test relationship_statistics view
            try:
                relationship_stats = await conn.fetch("SELECT * FROM relationship_statistics")
                logger.info(f"✅ relationship_statistics view accessible - {len(relationship_stats)} rows")
                for row in relationship_stats:
                    logger.info(f"  {dict(row)}")
            except Exception as e:
                logger.error(f"❌ relationship_statistics view error: {e}")
            
            # Test concurrent refresh
            try:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics")
                logger.info("✅ entity_statistics concurrent refresh successful")
            except Exception as e:
                logger.error(f"❌ entity_statistics concurrent refresh failed: {e}")
            
            try:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics")
                logger.info("✅ relationship_statistics concurrent refresh successful")
            except Exception as e:
                logger.error(f"❌ relationship_statistics concurrent refresh failed: {e}")
            
            # Test the refresh function
            try:
                await conn.execute("SELECT refresh_knowledge_graph_stats()")
                logger.info("✅ refresh_knowledge_graph_stats() function works")
            except Exception as e:
                logger.error(f"❌ refresh_knowledge_graph_stats() function failed: {e}")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct materialized view test failed: {e}")
        return False


async def test_entity_service():
    """Test entity extraction service"""
    try:
        logger.info("Testing entity extraction service...")
        
        # Call the service method that the API uses
        stats = await entity_extraction_service.get_entity_statistics()
        
        if "error" in stats:
            logger.error(f"❌ Service returned error: {stats['error']}")
            return False
        
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
        logger.error(f"❌ Entity extraction service test failed: {e}")
        return False


async def main():
    """Main function"""
    try:
        # Initialize database connection
        logger.info("Initializing database connection pool...")
        await create_db_pool()
        
        # Test materialized views directly
        direct_success = await test_materialized_views_directly()
        
        # Test entity service
        service_success = await test_entity_service()
        
        if direct_success and service_success:
            logger.info("🎉 All tests completed successfully!")
            return True
        else:
            logger.error("💥 Some tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"Test setup failed: {e}")
        return False
    finally:
        # Clean up database connection
        await close_db_pool()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)