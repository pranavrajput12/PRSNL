from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.llm_processor import LLMProcessor
from app.core.websocket_manager import manager
from app.services.unified_ai_service import UnifiedAIService
from app.db.database import get_db_pool
import logging
import json
import uuid
import asyncio
import random
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
            
            # Check for common greetings and conversational patterns
            greetings = ['hi', 'hello', 'hey', 'hii', 'hiii', 'hiiii', 'good morning', 'good afternoon', 'good evening', 'greetings', 'howdy', 'sup', "what's up", 'yo']
            small_talk = ['how are you', "how's it going", 'how do you do', 'what can you do', 'who are you', 'what are you']
            thanks = ['thanks', 'thank you', 'thx', 'ty', 'appreciated']
            
            message_lower = message.lower().strip().rstrip('?!.')
            
            # If it's just a greeting, respond conversationally
            if message_lower in greetings or any(message_lower.startswith(g) for g in greetings):
                greeting_responses = [
                    "Hello! I'm here to help you explore your knowledge base. What would you like to know about?",
                    "Hi there! I can help you search through your saved content. What are you looking for today?",
                    "Hello! How can I assist you with your knowledge base today?",
                    "Hi! I'm ready to help you find information from your saved content. What interests you?",
                    "Greetings! What would you like to explore in your knowledge base?"
                ]
                import random
                response = random.choice(greeting_responses)
                
                # Send the greeting response
                for char in response:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": char
                    })
                    await asyncio.sleep(0.01)  # Small delay for character streaming
                
                await websocket.send_json({
                    "type": "complete",
                    "citations": [],
                    "context_count": 0
                })
                continue
            
            # Handle small talk
            elif message_lower in small_talk or any(phrase in message_lower for phrase in small_talk):
                if 'how are you' in message_lower or "how's it going" in message_lower:
                    responses = [
                        "I'm doing well, thank you! Ready to help you explore your knowledge base. What would you like to search for?",
                        "I'm great! Here to assist you with finding information from your saved content. What interests you today?",
                        "Doing well! I'm here to help you navigate your knowledge base. What can I find for you?"
                    ]
                elif 'what can you do' in message_lower or 'who are you' in message_lower or 'what are you' in message_lower:
                    responses = [
                        "I'm your Second Brain assistant! I can help you search through your saved content, find connections between ideas, and answer questions based on your knowledge base. What would you like to explore?",
                        "I'm PRSNL, your AI-powered knowledge assistant. I can search your saved articles, videos, and notes to help you find exactly what you're looking for. What can I help you with?",
                        "I'm here to help you navigate your personal knowledge base. I can search for specific topics, find related content, and help you discover insights from your saved information. What would you like to know?"
                    ]
                else:
                    responses = [
                        "I'm here to help you with your knowledge base. What would you like to know?",
                        "Ready to assist! What information are you looking for?",
                        "I can help you search your saved content. What interests you?"
                    ]
                
                response = random.choice(responses)
                for char in response:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": char
                    })
                    await asyncio.sleep(0.01)
                
                await websocket.send_json({
                    "type": "complete",
                    "citations": [],
                    "context_count": 0
                })
                continue
            
            # Handle thanks
            elif message_lower in thanks or any(t in message_lower for t in thanks):
                thank_responses = [
                    "You're welcome! Feel free to ask me anything else about your knowledge base.",
                    "Happy to help! Let me know if you need anything else.",
                    "You're welcome! Is there anything else you'd like to explore?",
                    "My pleasure! Don't hesitate to ask if you have more questions."
                ]
                response = random.choice(thank_responses)
                for char in response:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": char
                    })
                    await asyncio.sleep(0.01)
                
                await websocket.send_json({
                    "type": "complete",
                    "citations": [],
                    "context_count": 0
                })
                continue
            
            # Send typing indicator for knowledge base search
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
                
                # Extract meaningful words and perform basic query expansion
                words = [word.lower().strip('?,.') for word in message.split() if word.strip('?,.')]
                
                # Filter out common question words and short words
                filtered_words = [word for word in words if word not in question_words and len(word) > 2]
                
                # Basic query expansion (can be expanded with a more comprehensive synonym list)
                expanded_keywords = set(filtered_words)
                synonym_map = {
                    'save': 'capture',
                    'show': 'display',
                    'find': 'locate',
                    'tell': 'explain',
                    'list': 'enumerate',
                    'display': 'show'
                }
                for word in filtered_words:
                    if word in synonym_map:
                        expanded_keywords.add(synonym_map[word])
                
                keywords = list(expanded_keywords)
                
                # Detect date-based queries
                date_filter_sql = ""
                date_keywords_map = {
                    'today': "DATE(created_at) = CURRENT_DATE",
                    'yesterday': "DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'",
                    'this week': "created_at >= date_trunc('week', CURRENT_DATE)",
                    'last week': "created_at >= date_trunc('week', CURRENT_DATE - INTERVAL '1 week') AND created_at < date_trunc('week', CURRENT_DATE)",
                    'this month': "created_at >= date_trunc('month', CURRENT_DATE)",
                    'last month': "created_at >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') AND created_at < date_trunc('month', CURRENT_DATE)"
                }
                
                for keyword, sql_condition in date_keywords_map.items():
                    if keyword in message_lower:
                        date_filter_sql = f"AND {sql_condition}"
                        # Remove date keyword from message to refine search query
                        message = message_lower.replace(keyword, "").strip()
                        break # Only apply one date filter
                
                # Create search query from keywords
                search_query = ' '.join(keywords) if keywords else message
                logger.debug(f"Original message: {message}")
                logger.debug(f"Search query: {search_query}")
                logger.debug(f"Date filter SQL: {date_filter_sql}")
                
                # Search for relevant content from the knowledge base
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    # First, try semantic search if embeddings are available
                    # Generate embedding for the search query
                    query_embedding = None
                    if ai_service.embedding_available and search_query:
                        try:
                            query_embedding = (await ai_service.generate_embeddings([search_query]))[0]
                        except Exception as e:
                            logger.warning(f"Could not generate embedding for search query: {e}")

                    # Perform hybrid search: full-text search + semantic search
                    # Combine results and re-rank
                    relevant_items = []
                    if search_query:
                        # Full-text search
                        text_search_query = """
                            SELECT 
                                id, title, 
                                COALESCE(processed_content, raw_content) as content, 
                                url, 
                                metadata->>'tags' as tags,
                                created_at, 
                                summary,
                                metadata->>'category' as category,
                                ts_rank(search_vector, plainto_tsquery('english', $1)) as rank_score
                            FROM items
                            WHERE 
                                search_vector @@ plainto_tsquery('english', $1)
                                OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                                OR $1 = ANY(string_to_array(metadata->>'tags', ','))
                                {date_filter_sql}
                            ORDER BY rank_score DESC
                            LIMIT 10
                        """.format(date_filter_sql=date_filter_sql)
                        text_results = await conn.fetch(text_search_query, search_query)
                        relevant_items.extend(text_results)

                    if query_embedding is not None:
                        # Semantic search - match the query structure from database.py
                        semantic_search_query = """
                            SELECT 
                                id, title, 
                                COALESCE(processed_content, raw_content) as content, 
                                url, 
                                metadata->>'tags' as tags,
                                created_at, 
                                summary,
                                metadata->>'category' as category,
                                1 - (embedding <=> $1::vector) as similarity_score
                            FROM items
                            WHERE embedding IS NOT NULL
                                {date_filter_sql}
                            ORDER BY embedding <=> $1::vector
                            LIMIT 10
                        """.format(date_filter_sql=date_filter_sql)
                        # Pass embedding directly - pgvector handles conversion
                        semantic_results = await conn.fetch(semantic_search_query, query_embedding)
                        
                        # Combine and deduplicate results
                        combined_results = {}
                        for row in relevant_items + semantic_results:
                            if row['id'] not in combined_results:
                                combined_results[row['id']] = dict(row)
                                combined_results[row['id']]['score'] = row.get('rank_score', 0) + row.get('similarity_score', 0)
                            else:
                                # Update score if a better one is found
                                combined_results[row['id']]['score'] += row.get('rank_score', 0) + row.get('similarity_score', 0)
                        
                        # Sort by combined score and take top 5
                        relevant_items = sorted(combined_results.values(), key=lambda x: x['score'], reverse=True)[:5]
                    else:
                        # If no embedding, just use text search results (already limited to 5)
                        relevant_items = relevant_items[:5]
                    
                    logger.debug(f"Found {len(relevant_items)} relevant items")
                
                # Build context from search results
                context_items_formatted = []
                for item in relevant_items:
                    # Parse tags from string
                    tags = item['tags'].split(',') if item['tags'] else []
                    
                    # Generate a brief summary of the item relevant to the query
                    item_summary = await ai_service.generate_summary(
                        content=item['content'],
                        summary_type="brief",
                        context={'query': message} # Provide query as context for summary
                    )

                    context_items_formatted.append(
                        f"Source Title: {item['title']}\n"
                        f"Source URL: {item['url']}\n"
                        f"Summary: {item_summary}\n"
                        f"Category: {item['category']}\n"
                        f"Tags: {tags}\n"
                        f"---"
                    )
                
                knowledge_base_context = "\n".join(context_items_formatted)

                # Generate response using AI with context
                system_prompt = """You are PRSNL, a personal knowledge base assistant. 
                You can ONLY answer based on the information provided in the user's knowledge base.
                If the information is not in the provided context, say so clearly.
                Always cite the sources you're using from the knowledge base.
                Be helpful, concise, and accurate."""
                
                user_prompt = f"""Based on the following items from the knowledge base, answer the user's question.
                
                Knowledge Base Items:
                {knowledge_base_context}
                
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
                # Don't send the message content again - frontend already has it from chunks
                citations = [{"title": item["title"], "url": item["url"]} 
                           for item in relevant_items if item["url"]]
                
                await websocket.send_json({
                    "type": "complete",
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