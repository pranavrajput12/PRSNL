#!/usr/bin/env python3
"""
Debug script for chat functionality
"""
import asyncio
import logging

from app.config import settings
from app.db.database import create_db_pool, get_db_pool
from app.services.unified_ai_service import UnifiedAIService

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_database_search():
    """Test database search functionality"""
    logger.info("Testing database search...")
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Test basic query
            result = await conn.fetch("SELECT COUNT(*) as count FROM items")
            logger.info(f"Total items in database: {result[0]['count']}")
            
            # Test search query
            search_term = "React"
            items = await conn.fetch("""
                SELECT id, title, 
                       COALESCE(processed_content, raw_content) as content, 
                       url, 
                       metadata->>'tags' as tags 
                FROM items
                WHERE 
                    search_vector @@ plainto_tsquery('english', $1)
                    OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                LIMIT 3
            """, search_term)
            
            logger.info(f"Found {len(items)} items for search term '{search_term}'")
            for item in items:
                logger.info(f"  - {item['title'][:50]}...")
                
    except Exception as e:
        logger.error(f"Database search error: {e}", exc_info=True)

async def test_azure_openai():
    """Test Azure OpenAI connection"""
    logger.info("Testing Azure OpenAI...")
    
    try:
        logger.info(f"API Key present: {settings.AZURE_OPENAI_API_KEY is not None}")
        logger.info(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        logger.info(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
        logger.info(f"API Version: {settings.AZURE_OPENAI_API_VERSION}")
        
        ai_service = UnifiedAIService()
        
        # Test simple completion
        response = await ai_service.complete(
            prompt="Say 'Hello, I am working!'",
            temperature=0.1,
            max_tokens=50
        )
        logger.info(f"Azure OpenAI response: {response}")
        
    except Exception as e:
        logger.error(f"Azure OpenAI error: {e}", exc_info=True)

async def test_chat_flow():
    """Test the complete chat flow"""
    logger.info("Testing complete chat flow...")
    
    try:
        ai_service = UnifiedAIService()
        
        # Simulate chat message
        message = "What have I saved about React?"
        
        # Search database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            items = await conn.fetch("""
                SELECT id, title, 
                       COALESCE(processed_content, raw_content) as content, 
                       url, 
                       metadata->>'tags' as tags,
                       metadata->>'category' as category
                FROM items
                WHERE 
                    search_vector @@ plainto_tsquery('english', $1)
                    OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                ORDER BY created_at DESC
                LIMIT 5
            """, message)
            
            logger.info(f"Found {len(items)} relevant items")
            
            if items:
                # Build context
                context_items = []
                for item in items:
                    tags = item['tags'].split(',') if item['tags'] else []
                    context_items.append({
                        "title": item['title'],
                        "content": item['content'][:500] if item['content'] else "",
                        "url": item['url'],
                        "tags": tags,
                        "category": item['category']
                    })
                
                # Test streaming response
                system_prompt = "You are PRSNL assistant. Only answer based on provided context."
                user_prompt = f"Context: {context_items}\n\nQuestion: {message}"
                
                logger.info("Generating AI response...")
                response_text = ""
                async for chunk in ai_service.stream_chat_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=[]
                ):
                    response_text += chunk
                    print(chunk, end='', flush=True)
                
                print()  # New line after streaming
                logger.info(f"Complete response: {response_text[:200]}...")
            else:
                logger.warning("No items found in database")
                
    except Exception as e:
        logger.error(f"Chat flow error: {e}", exc_info=True)

async def main():
    """Run all tests"""
    print("=" * 60)
    print("PRSNL Chat Debug Script")
    print("=" * 60)
    
    # Initialize database pool
    await create_db_pool()
    
    # Test each component
    await test_database_search()
    print("-" * 60)
    
    await test_azure_openai()
    print("-" * 60)
    
    await test_chat_flow()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())