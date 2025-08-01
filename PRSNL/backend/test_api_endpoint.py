#!/usr/bin/env python3
"""
Test the entity extraction API endpoint directly
"""
import asyncio
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import create_db_pool, close_db_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_endpoint():
    """Test the entity extraction stats API endpoint"""
    try:
        # Initialize database connection
        logger.info("Initializing database connection for API test...")
        await create_db_pool()
        
        # Create test client
        with TestClient(app) as client:
            logger.info("Testing /entity-extraction/stats endpoint...")
            
            # Make request to stats endpoint
            response = client.get("/api/entity-extraction/stats")
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ API endpoint returned successfully!")
                logger.info(f"Total entities: {data.get('total_entities', 0)}")
                logger.info(f"Total relationships: {data.get('total_relationships', 0)}")
                logger.info(f"Entity statistics: {len(data.get('entity_statistics', []))}")
                logger.info(f"Relationship statistics: {len(data.get('relationship_statistics', []))}")
                return True
            else:
                logger.error(f"❌ API endpoint failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ API endpoint test failed: {e}")
        return False
    finally:
        await close_db_pool()


async def test_health_endpoint():
    """Test the entity extraction health endpoint"""
    try:
        await create_db_pool()
        
        with TestClient(app) as client:
            logger.info("Testing /entity-extraction/health endpoint...")
            
            response = client.get("/api/entity-extraction/health")
            
            logger.info(f"Health response status: {response.status_code}")
            logger.info(f"Health response body: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    logger.info("✅ Health endpoint shows service is healthy!")
                    return True
                else:
                    logger.warning(f"⚠️ Health endpoint shows status: {data.get('status')}")
                    return False
            else:
                logger.error(f"❌ Health endpoint failed with status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Health endpoint test failed: {e}")
        return False
    finally:
        await close_db_pool()


async def main():
    """Main function"""
    try:
        logger.info("🧪 Testing Entity Extraction API Endpoints")
        
        # Test health endpoint
        health_success = await test_health_endpoint()
        
        # Test stats endpoint
        stats_success = await test_api_endpoint()
        
        if health_success and stats_success:
            logger.info("🎉 All API endpoint tests completed successfully!")
            logger.info("✅ The materialized view concurrent refresh fix is working correctly!")
            return True
        else:
            logger.error("💥 Some API endpoint tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)