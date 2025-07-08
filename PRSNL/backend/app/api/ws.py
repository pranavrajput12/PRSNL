from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.llm_processor import LLMProcessor
from app.core.websocket_manager import manager
from app.services.unified_ai_service import UnifiedAIService
from app.db.database import get_db_pool
import logging
import json
import uuid
from typing import List, Dict

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Enable debug logging for chat

@router.websocket("/ws/ai/stream/{client_id}")
async def ai_stream(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    llm_processor = LLMProcessor()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                await websocket.send_json({"error": "No content provided"})
                continue

            logger.info(f"Streaming AI response for {client_id}")
            async for chunk in llm_processor.stream_content(content):
                await websocket.send_json({"chunk": chunk})

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected from AI stream")
    except Exception as e:
        logger.error(f"Error in AI stream for {client_id}: {e}")
        await websocket.send_json({"error": str(e)})
        manager.disconnect(client_id)

@router.websocket("/ws/ai/tags/{client_id}")
async def ai_tag_stream(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    llm_processor = LLMProcessor()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                await websocket.send_json({"error": "No content provided"})
                continue

            logger.info(f"Streaming tag suggestions for {client_id}")
            async for chunk in llm_processor.stream_tag_suggestions(content):
                await websocket.send_json({"chunk": chunk})

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected from AI tag stream")
    except Exception as e:
        logger.error(f"Error in AI tag stream for {client_id}: {e}")
        await websocket.send_json({"error": str(e)})
        manager.disconnect(client_id)


@router.websocket("/ws/chat/{client_id}")
async def chat_with_knowledge_base(websocket: WebSocket, client_id: str):
    """
    Chat endpoint that uses only the user's knowledge base data.
    Implements RAG (Retrieval Augmented Generation) to prevent hallucination.
    """
    await manager.connect(websocket, client_id)
    ai_service = UnifiedAIService()
    
    logger.debug(f"Chat connection established for client: {client_id}")
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to PRSNL knowledge base chat"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            conversation_history = data.get("history", [])
            
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "No message provided"
                })
                continue
            
            logger.debug(f"Received message from {client_id}: {message}")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "status",
                "message": "Searching your knowledge base..."
            })
            
            try:
                # Extract key terms from the user's message
                # Simple keyword extraction - in production, use NLP
                keywords = []
                message_lower = message.lower()
                
                # Common question patterns to remove
                question_words = ['what', 'have', 'i', 'saved', 'about', 'show', 'me', 'find', 
                                'my', 'all', 'the', 'is', 'are', 'was', 'were', 'been', 
                                'tell', 'give', 'list', 'display']
                
                # Extract meaningful words
                words = message.split()
                for word in words:
                    cleaned_word = word.lower().strip('?,.')
                    if cleaned_word and cleaned_word not in question_words and len(cleaned_word) > 2:
                        keywords.append(cleaned_word)
                
                # Create search query from keywords
                search_query = ' '.join(keywords) if keywords else message
                logger.debug(f"Original message: {message}")
                logger.debug(f"Search query: {search_query}")
                
                # Search for relevant content from the knowledge base
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    # First, try semantic search if embeddings are available
                    relevant_items = await conn.fetch("""
                        SELECT 
                            id, title, 
                            COALESCE(processed_content, raw_content) as content, 
                            url, 
                            metadata->>'tags' as tags,
                            created_at, 
                            summary,
                            metadata->>'category' as category
                        FROM items
                        WHERE 
                            search_vector @@ plainto_tsquery('english', $1)
                            OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                            OR $1 = ANY(string_to_array(metadata->>'tags', ','))
                        ORDER BY 
                            ts_rank(search_vector, plainto_tsquery('english', $1)) DESC,
                            created_at DESC
                        LIMIT 5
                    """, search_query)
                    
                    logger.debug(f"Found {len(relevant_items)} relevant items")
                
                # Build context from search results
                context_items = []
                for item in relevant_items:
                    # Parse tags from string
                    tags = item['tags'].split(',') if item['tags'] else []
                    
                    context_items.append({
                        "title": item['title'],
                        "content": item['content'][:500] if item['content'] else "",  # Limit content length
                        "url": item['url'],
                        "tags": tags,
                        "category": item['category']
                    })
                
                # Generate response using AI with context
                system_prompt = """You are PRSNL, a personal knowledge base assistant. 
                You can ONLY answer based on the information provided in the user's knowledge base.
                If the information is not in the provided context, say so clearly.
                Always cite the sources you're using from the knowledge base.
                Be helpful, concise, and accurate."""
                
                user_prompt = f"""Based on the following items from the knowledge base, answer the user's question.
                
                Knowledge Base Items:
                {json.dumps(context_items, indent=2)}
                
                User Question: {message}
                
                Remember: Only use information from the provided knowledge base items. If the answer isn't in the context, say so."""
                
                # Stream the response
                await websocket.send_json({
                    "type": "status",
                    "message": "Generating response..."
                })
                
                response_chunks = []
                async for chunk in ai_service.stream_chat_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=conversation_history
                ):
                    response_chunks.append(chunk)
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Send completion message with citations
                full_response = "".join(response_chunks)
                citations = [{"title": item["title"], "url": item["url"]} 
                           for item in context_items if item["url"]]
                
                await websocket.send_json({
                    "type": "complete",
                    "message": full_response,
                    "citations": citations,
                    "context_count": len(relevant_items)
                })
                
                logger.debug(f"Completed response for {client_id}")
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing your request: {str(e)}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected from chat")
    except Exception as e:
        logger.error(f"Error in chat for {client_id}: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"Connection error: {str(e)}"
        })
        manager.disconnect(client_id)