"""
Floating Chat Service - Handles floating chat interactions using CrewAI

This service provides intelligent, context-aware responses for the floating chat
component using specialized CrewAI crews optimized for speed and relevance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from app.crews.floating_chat_crew import (
    FloatingChatCrew,
    FloatingChatSimpleCrew,
    FloatingChatContextualCrew
)
from app.services.crew_service import CrewService
from app.db.database import get_db_pool
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class FloatingChatService:
    """Service for handling floating chat interactions with CrewAI intelligence"""
    
    def __init__(self):
        self.crew_service = CrewService()
        self.ai_service = UnifiedAIService()
        
        # Available crew types for different response needs
        self.crew_types = {
            "simple": "floating_chat_simple",      # Ultra-fast, single agent
            "standard": "floating_chat",           # Balanced speed and intelligence  
            "contextual": "floating_chat_contextual"  # Deep context analysis
        }
    
    async def get_contextual_response(
        self,
        message: str,
        page_context: Dict[str, Any],
        user_id: str,
        crew_type: str = "standard",
        max_knowledge_items: int = 5
    ) -> Dict[str, Any]:
        """
        Get a contextual response using CrewAI for the floating chat
        
        Args:
            message: User's message/question
            page_context: Current page context information
            user_id: User identifier
            crew_type: Type of crew to use (simple, standard, contextual)
            max_knowledge_items: Maximum number of knowledge base items to include
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Get relevant knowledge base items
            knowledge_items = await self._get_relevant_knowledge(
                message, user_id, page_context, max_knowledge_items
            )
            
            # Prepare inputs for the crew
            crew_inputs = {
                "user_message": message,
                "page_type": page_context.get("pageType", "unknown"),
                "page_url": page_context.get("url", ""),
                "page_title": page_context.get("pageTitle", ""),
                "context_info": self._format_context_info(page_context),
                "knowledge_items": self._format_knowledge_items(knowledge_items)
            }
            
            # Select and execute crew
            crew_name = self.crew_types.get(crew_type, "floating_chat")
            
            start_time = datetime.utcnow()
            
            # Execute crew asynchronously
            result = await self._execute_crew_async(crew_name, crew_inputs)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Extract response from crew output
            response_text = self._extract_response_text(result, crew_type)
            
            return {
                "response": response_text,
                "context_used": page_context,
                "knowledge_items_used": len(knowledge_items),
                "crew_type": crew_type,
                "response_time_seconds": response_time,
                "citations": self._extract_citations(knowledge_items),
                "metadata": {
                    "page_type": page_context.get("pageType"),
                    "has_context": bool(page_context.get("pageType") != "unknown"),
                    "knowledge_match_count": len(knowledge_items)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in floating chat response: {e}", exc_info=True)
            
            # Fallback to simple AI service response
            return await self._fallback_response(message, page_context, knowledge_items)
    
    async def stream_contextual_response(
        self,
        message: str,
        page_context: Dict[str, Any],
        user_id: str,
        crew_type: str = "simple"
    ) -> AsyncGenerator[str, None]:
        """
        Stream a contextual response for real-time floating chat
        
        Note: CrewAI doesn't natively support streaming, so we use the simple AI service
        with enhanced context for streaming responses.
        """
        try:
            # For streaming, use the AI service with enhanced context
            knowledge_items = await self._get_relevant_knowledge(
                message, user_id, page_context, max_items=3
            )
            
            # Build enhanced context prompt
            context_prompt = self._build_context_prompt(message, page_context, knowledge_items)
            
            # Stream response using AI service
            async for chunk in self.ai_service.stream_chat_response(
                system_prompt=self._get_floating_chat_system_prompt(),
                user_prompt=context_prompt,
                history=[]  # Floating chat is stateless
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming floating chat: {e}", exc_info=True)
            yield f"Sorry, I encountered an error processing your request: {str(e)}"
    
    async def get_quick_actions(
        self,
        page_context: Dict[str, Any],
        user_id: str
    ) -> List[str]:
        """Get contextual quick actions for the current page"""
        page_type = page_context.get("pageType", "unknown")
        
        # Base actions
        actions = {
            "dashboard": [
                "What did I save today?",
                "Show my recent activity",
                "Find trending topics",
                "Summarize this week"
            ],
            "item-detail": [
                "Summarize this content",
                "Find similar items",
                "Extract key insights",
                "Generate tags"
            ],
            "timeline": [
                "What happened this week?",
                "Show productivity patterns",
                "Find knowledge gaps",
                "Weekly summary"
            ],
            "code-cortex": [
                "Analyze this repository",
                "Find security issues",
                "Suggest improvements",
                "Generate documentation"
            ],
            "development": [
                "Debug this error",
                "Best practices for...",
                "Generate code snippet",
                "Explain architecture"
            ],
            "search": [
                "Refine my search",
                "Related topics",
                "Filter by date",
                "Save this search"
            ]
        }
        
        default_actions = [
            "Help me understand this",
            "What should I know?",
            "Quick summary",
            "Related content"
        ]
        
        return actions.get(page_type, default_actions)
    
    async def _get_relevant_knowledge(
        self,
        message: str,
        user_id: str,
        page_context: Dict[str, Any],
        max_items: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant knowledge base items for the query"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                
                # Enhanced search query that considers page context
                search_query = message
                
                # Add page-specific context to search
                if page_context.get("pageType") == "item-detail" and page_context.get("itemId"):
                    # If user is on an item page, that item is highly relevant
                    item_query = """
                        SELECT id, title, url, summary, content_type
                        FROM items 
                        WHERE id = $1 AND user_id = $2
                    """
                    item_result = await conn.fetchrow(item_query, page_context["itemId"], user_id)
                    if item_result:
                        return [dict(item_result)]
                
                # General semantic search
                if self.ai_service.embedding_available:
                    try:
                        query_embedding = (await self.ai_service.generate_embeddings([search_query]))[0]
                        
                        semantic_query = """
                            SELECT id, title, url, summary, content_type,
                                   1 - (embedding <=> $1::vector) as similarity
                            FROM items
                            WHERE user_id = $2 AND embedding IS NOT NULL
                            ORDER BY embedding <=> $1::vector
                            LIMIT $3
                        """
                        results = await conn.fetch(semantic_query, query_embedding, user_id, max_items)
                        return [dict(row) for row in results]
                        
                    except Exception as e:
                        logger.warning(f"Semantic search failed: {e}")
                
                # Fallback to text search
                text_query = """
                    SELECT id, title, url, summary, content_type,
                           ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
                    FROM items
                    WHERE user_id = $2
                      AND search_vector @@ plainto_tsquery('english', $1)
                    ORDER BY rank DESC
                    LIMIT $3
                """
                results = await conn.fetch(text_query, search_query, user_id, max_items)
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            return []
    
    def _format_context_info(self, page_context: Dict[str, Any]) -> str:
        """Format page context information for crew input"""
        context_parts = []
        
        if page_context.get("pageType"):
            context_parts.append(f"Page type: {page_context['pageType']}")
        
        if page_context.get("itemId"):
            context_parts.append(f"Viewing item: {page_context['itemId']}")
        
        if page_context.get("searchQuery"):
            context_parts.append(f"Search query: {page_context['searchQuery']}")
        
        return " | ".join(context_parts) if context_parts else "No specific context"
    
    def _format_knowledge_items(self, items: List[Dict[str, Any]]) -> str:
        """Format knowledge base items for crew input"""
        if not items:
            return "No relevant knowledge base items found."
        
        formatted_items = []
        for item in items:
            item_text = f"• {item['title']}"
            if item.get('summary'):
                item_text += f": {item['summary'][:100]}..."
            formatted_items.append(item_text)
        
        return "\n".join(formatted_items)
    
    async def _execute_crew_async(self, crew_name: str, inputs: Dict[str, Any]) -> Any:
        """Execute crew asynchronously"""
        # Run crew in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.crew_service.run_crew(crew_name, inputs)
        )
    
    def _extract_response_text(self, crew_result: Any, crew_type: str) -> str:
        """Extract response text from crew result"""
        try:
            if hasattr(crew_result, 'raw'):
                return crew_result.raw
            elif isinstance(crew_result, str):
                return crew_result
            elif isinstance(crew_result, dict):
                # Try common response keys
                for key in ['response', 'output', 'result', 'text']:
                    if key in crew_result:
                        return crew_result[key]
            return str(crew_result)
        except Exception:
            return "I'm here to help! Could you please rephrase your question?"
    
    def _extract_citations(self, knowledge_items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract citations from knowledge items"""
        citations = []
        for item in knowledge_items:
            if item.get('url') and item.get('title'):
                citations.append({
                    "title": item['title'],
                    "url": item['url']
                })
        return citations
    
    def _build_context_prompt(
        self,
        message: str,
        page_context: Dict[str, Any],
        knowledge_items: List[Dict[str, Any]]
    ) -> str:
        """Build enhanced context prompt for streaming"""
        context_parts = []
        
        # Page context
        if page_context.get("pageType") and page_context["pageType"] != "unknown":
            context_parts.append(f"User is currently on: {page_context['pageType']} page")
            
            if page_context.get("pageTitle"):
                context_parts.append(f"Page title: {page_context['pageTitle']}")
        
        # Knowledge items
        if knowledge_items:
            context_parts.append("Relevant knowledge base items:")
            for item in knowledge_items[:3]:  # Limit for streaming
                context_parts.append(f"- {item['title']}: {item.get('summary', '')[:100]}...")
        
        context_str = "\n".join(context_parts) if context_parts else "No specific context available."
        
        return f"""Context: {context_str}

User question: {message}

Please provide a helpful, contextual response based on the available information."""
    
    def _get_floating_chat_system_prompt(self) -> str:
        """Get system prompt for floating chat"""
        return """You are PRSNL's floating chat assistant. You provide quick, helpful responses based on the user's current context and knowledge base.

Guidelines:
- Be concise and helpful (2-3 sentences max unless complex topic)
- Acknowledge the user's current context when relevant
- Use knowledge base information when available
- Suggest next steps when appropriate
- Maintain a friendly, assistant-like tone
- If you don't have relevant information, say so clearly"""
    
    async def _fallback_response(
        self,
        message: str,
        page_context: Dict[str, Any],
        knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback response when crew fails"""
        context_prompt = self._build_context_prompt(message, page_context, knowledge_items)
        
        try:
            # Simple AI service response
            response = await self.ai_service.generate_response(
                prompt=context_prompt,
                system_prompt=self._get_floating_chat_system_prompt()
            )
            
            return {
                "response": response.get("content", "I'm here to help! Could you please rephrase your question?"),
                "context_used": page_context,
                "knowledge_items_used": len(knowledge_items),
                "crew_type": "fallback",
                "response_time_seconds": 0,
                "citations": self._extract_citations(knowledge_items),
                "metadata": {
                    "fallback_used": True,
                    "page_type": page_context.get("pageType"),
                    "has_context": bool(page_context.get("pageType") != "unknown")
                }
            }
        except Exception as e:
            logger.error(f"Fallback response failed: {e}")
            return {
                "response": "I'm experiencing some technical difficulties. Please try again in a moment.",
                "context_used": page_context,
                "knowledge_items_used": 0,
                "crew_type": "error",
                "response_time_seconds": 0,
                "citations": [],
                "metadata": {"error": True}
            }