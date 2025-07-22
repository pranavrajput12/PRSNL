import asyncio
import json
import logging
import random
import uuid
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import manager
from app.db.database import get_db_pool
from app.services.llm_processor import LLMProcessor
from app.services.unified_ai_service import UnifiedAIService

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Enable debug logging for chat

def diversify_search_results(results, max_results=20):
    """
    Diversify search results to show different content types
    Ensures we don't show only one type of content (e.g., all websites)
    """
    if not results:
        return results
    
    # Group by content type and source type
    type_groups = {}
    for item in results:
        content_type = item.get('source_type', 'unknown')
        item_type = item.get('type', 'unknown') 
        
        # Use more specific grouping
        group_key = f"{content_type}_{item_type}"
        if group_key not in type_groups:
            type_groups[group_key] = []
        type_groups[group_key].append(item)
    
    # Select diverse results - max 5 per type group
    diversified = []
    for group_key, group_items in type_groups.items():
        # Sort by score within each group and take top 5
        group_items.sort(key=lambda x: x.get('rank_score', 0), reverse=True)
        diversified.extend(group_items[:5])
    
    # Sort final results by score and limit
    diversified.sort(key=lambda x: x.get('rank_score', 0), reverse=True)
    return diversified[:max_results]

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
    
    # NO AUTHENTICATION - DEVELOPMENT MODE ONLY
    logger.debug(f"Chat connection established for client: {client_id} - NO AUTH MODE")
    
    
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
            context = data.get("context", {})
            
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "No message provided"
                })
                continue
            
            logger.debug(f"🔍 RECEIVED MESSAGE from {client_id}: '{message}'")
            logger.debug(f"📝 Conversation history items: {len(conversation_history)}")
            logger.debug(f"🎯 Context data: {context}")
            
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
                
                # Special handling for bookmark queries
                if any(word in message_lower for word in ['bookmark', 'bookmarks', 'saved', 'links']):
                    # For bookmark queries, search by type
                    search_query = 'bookmark'
                    logger.debug(f"Detected bookmark query, using type search")
                
                # Filter out common question words but keep important short words
                # Allow important technical terms even if short (ai, ml, js, py, etc.)
                important_short_words = ['ai', 'ml', 'js', 'py', 'go', 'r', 'c', 'qt', 'ui', 'ux', 'db', 'os', 'vm', 'cd', 'ci', 'cd', 'qa', 'hr', 'pr', 'id', 'ip', 'tv', 'vr', 'ar', 'iot', 'api', 'sql', 'css', 'xml', 'rss', 'cms', 'seo', 'roi', 'kpi', 'crm', 'erp', 'etl', 'aws', 'gcp']
                filtered_words = [word for word in words if word not in question_words and (len(word) > 2 or word.lower() in important_short_words)]
                
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
                
                # Create search query from keywords - use first meaningful keyword
                if keywords:
                    # Use the most specific/shortest keyword for better matching
                    # Sort by length and take the shortest (usually most specific)
                    search_query = min(keywords, key=len) if keywords else keywords[0]
                else:
                    search_query = message
                logger.debug(f"🔍 SEARCH PROCESSING:")
                logger.debug(f"  📄 Original message: '{message}'")
                logger.debug(f"  🔎 Final search query: '{search_query}'")
                logger.debug(f"  📅 Date filter SQL: '{date_filter_sql}'")
                logger.debug(f"  🚫 NO USER FILTERING - SEARCHING ALL DATA")
                
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
                    # Include both items and conversations
                    relevant_items = []
                    if search_query:
                        # Combined search for items and conversations
                        combined_search_query = """
                            WITH item_results AS (
                                SELECT 
                                    id, title, 
                                    type,  -- Added type field
                                    COALESCE(processed_content, raw_content) as content, 
                                    url, 
                                    metadata->>'tags' as tags,
                                    created_at, 
                                    summary,
                                    metadata->>'category' as category,
                                    CASE 
                                        WHEN search_vector IS NOT NULL THEN ts_rank(search_vector, plainto_tsquery('english', $1))
                                        ELSE 0.1
                                    END as rank_score,
                                    'item' as source_type,
                                    NULL as platform,
                                    NULL as slug
                                FROM items
                                WHERE (
                                    (search_vector IS NOT NULL AND search_vector @@ plainto_tsquery('english', $1))
                                    OR to_tsvector('english', COALESCE(title, '')) @@ plainto_tsquery('english', $1)
                                    OR to_tsvector('english', COALESCE(raw_content, '')) @@ plainto_tsquery('english', $1)
                                    OR $1 = ANY(string_to_array(COALESCE(metadata->>'tags', ''), ','))
                                    OR type = $1  -- Search by type (e.g., 'bookmark')
                                    OR title ILIKE '%' || $1 || '%'  -- Simple text match
                                    OR raw_content ILIKE '%' || $1 || '%'  -- Content text match
                                )
                                {date_filter_sql}
                            ),
                            conversation_results AS (
                                SELECT 
                                    id, title,
                                    'conversation' as type,  -- Added type field for conversations
                                    COALESCE(summary, '') as content,
                                    source_url as url,
                                    array_to_string(COALESCE(key_topics, ARRAY[]::text[]), ',') as tags,
                                    created_at,
                                    summary,
                                    'conversation' as category,
                                    ts_rank(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(summary, '') || ' ' || array_to_string(COALESCE(key_topics, ARRAY[]::text[]), ' ')), plainto_tsquery('english', $1)) as rank_score,
                                    'conversation' as source_type,
                                    platform,
                                    slug
                                FROM ai_conversation_imports
                                WHERE to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(summary, '') || ' ' || array_to_string(COALESCE(key_topics, ARRAY[]::text[]), ' ')) @@ plainto_tsquery('english', $1)
                                    {date_filter_sql}
                            )
                            SELECT * FROM (
                                SELECT * FROM item_results
                                UNION ALL
                                SELECT * FROM conversation_results
                            ) combined_results
                            ORDER BY rank_score DESC
                            LIMIT 20
                        """.format(date_filter_sql=date_filter_sql)
                        logger.debug(f"🔍 EXECUTING COMBINED SEARCH SQL:")
                        logger.debug(f"📝 Query: {combined_search_query[:200]}...")
                        logger.debug(f"🔎 Search term: '{search_query}'")
                        
                        text_results = await conn.fetch(combined_search_query, search_query)
                        
                        logger.debug(f"✅ COMBINED SEARCH RESULTS:")
                        logger.debug(f"  📊 Total results found: {len(text_results)}")
                        for i, result in enumerate(text_results[:5]):  # Log first 5 results
                            logger.debug(f"  📄 Result {i+1}: '{result.get('title', 'NO TITLE')}' (type: {result.get('type', 'unknown')}, source: {result.get('source_type', 'unknown')})")
                        
                        relevant_items.extend(text_results)

                    # TEMPORARY: Disable semantic search to prioritize conversation text search
                    if False and query_embedding is not None:
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
                        
                        # Sort by combined score and take top 8 with diversity
                        relevant_items = sorted(combined_results.values(), key=lambda x: x['score'], reverse=True)[:8]
                    else:
                        # Apply content type diversity - show different types of content
                        relevant_items = diversify_search_results(relevant_items[:30], max_results=20)  # Get more results first, then diversify
                    
                    logger.debug(f"🎯 FINAL RESULTS SUMMARY:")
                    logger.debug(f"  📊 Total relevant items: {len(relevant_items)}")
                    logger.debug(f"  🔍 Search query was: '{search_query}'")
                
                # Build context from search results
                context_items_formatted = []
                for item in relevant_items:
                    # Parse tags from string
                    tags = item.get('tags', '').split(',') if item.get('tags') else []
                    
                    # Get content safely
                    content = item.get('content', '')
                    if not content:
                        content = item.get('title', '') + ' ' + item.get('url', '')
                    
                    # Generate a brief summary of the item relevant to the query
                    if content:
                        try:
                            item_summary = await ai_service.generate_summary(
                                content=content,
                                summary_type="brief",
                                context={'query': message} # Provide query as context for summary
                            )
                        except Exception as e:
                            logger.warning(f"Failed to generate summary: {e}")
                            item_summary = content[:200] + "..." if len(content) > 200 else content
                    else:
                        item_summary = "No content available"

                    context_items_formatted.append(
                        f"Source Title: {item.get('title', 'Untitled')}\n"
                        f"Source URL: {item.get('url', 'No URL')}\n"
                        f"Summary: {item_summary}\n"
                        f"Category: {item.get('category', 'Uncategorized')}\n"
                        f"Tags: {', '.join(tags) if tags else 'No tags'}\n"
                        f"---"
                    )
                
                knowledge_base_context = "\n".join(context_items_formatted)
                

                # Generate response using AI with context
                system_prompt = """You are PRSNL, a personal knowledge base assistant. 
                You can ONLY answer based on the information provided in the user's knowledge base.
                If the information is not in the provided context, say so clearly.
                Always cite the sources you're using from the knowledge base.
                Be helpful, concise, and accurate."""
                
                # If no relevant items found, adjust the prompt
                if not relevant_items:
                    logger.debug(f"No relevant items found for query: {message}")
                    knowledge_base_context = "No relevant items found in the knowledge base for this query."
                
                # Add page context if available
                page_context_prompt = ""
                if context and context.get("page"):
                    page_info = context["page"]
                    page_context_prompt = f"\n\nUser Context:\n"
                    page_context_prompt += f"- Current page: {page_info.get('pageTitle', page_info.get('url', 'Unknown'))}\n"
                    page_context_prompt += f"- Page type: {page_info.get('pageType', 'unknown')}\n"
                    
                    if page_info.get("itemId"):
                        page_context_prompt += f"- Viewing item ID: {page_info['itemId']}\n"
                    
                    if page_info.get("searchQuery"):
                        page_context_prompt += f"- Search query: {page_info['searchQuery']}\n"
                
                user_prompt = f"""Based on the following items from the knowledge base, answer the user's question.
                {page_context_prompt}
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
                citations = []
                for item in relevant_items:
                    if item.get("source_type") == "conversation":
                        # Build conversation URL: /conversations/{platform}/{slug}
                        platform = item.get("platform", "")
                        slug = item.get("slug", "")
                        if platform and slug:
                            conversation_url = f"/conversations/{platform}/{slug}"
                            citations.append({
                                "title": item.get("title", "Untitled"),
                                "url": conversation_url,
                                "item_id": str(item.get("id", "")),
                                "permalink": conversation_url,
                                "type": "conversation",
                                "format_label": "💬 Conversation"
                            })
                    else:
                        # Regular items - determine URL based on type
                        item_id = str(item.get("id", ""))
                        item_type = item.get("type", "")
                        
                        # Generate type-specific internal URL
                        if item_type == "video":
                            internal_url = f"/videos/{item_id}"
                        elif item_type == "development":
                            # Only actual development projects go to Code Cortex
                            # Articles about development still go to items
                            internal_url = f"/code-cortex/links/{item_id}"
                        elif item_type == "conversation":
                            # This should have been handled above, but just in case
                            internal_url = f"/items/{item_id}"
                        else:
                            # Default for articles, bookmarks, etc. - go to timeline single item page
                            internal_url = f"/items/{item_id}"
                        
                        # Determine format label based on type
                        format_label = ""
                        if item_type == "video":
                            format_label = "🎥 Video"
                        elif item_type == "development":
                            format_label = "💻 Code"
                        elif item_type == "bookmark":
                            format_label = "🔖 Bookmark"
                        elif item_type == "article":
                            format_label = "📄 Article"
                        else:
                            format_label = "📎 Link"
                        
                        citations.append({
                            "title": item.get("title", "Untitled"),
                            "url": item.get("url", ""),  # Original external URL
                            "item_id": item_id,
                            "permalink": internal_url,  # Internal navigation URL
                            "type": item_type,
                            "format_label": format_label
                        })
                
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


