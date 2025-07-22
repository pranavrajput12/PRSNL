"""
Chat Service for PRSNL - Handles conversational AI interactions
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from app.services.ai_service import AIService
from app.services.embedding_manager import EmbeddingManager
from app.db.database import get_db_connection
from app.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions with context and knowledge base integration"""
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or AIService()
        self.embedding_manager = EmbeddingManager()
        self.conversation_cache = {}
        
    async def process_message(
        self, 
        message: str, 
        user_id: str,
        context_type: str = "chat",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message with knowledge base context
        
        Args:
            message: User's message
            user_id: User identifier
            context_type: Type of context (chat, voice, etc.)
            conversation_id: Optional conversation thread ID
            
        Returns:
            Response with content and metadata
        """
        try:
            # 1. Get relevant context from knowledge base
            context = await self._get_relevant_context(message, user_id)
            
            # 2. Get conversation history if available
            history = await self._get_conversation_history(conversation_id) if conversation_id else []
            
            # 3. Build enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(message, context, history)
            
            # 4. Get AI response
            system_prompt = self._get_system_prompt(context_type)
            
            response = await self.ai_service.generate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # 5. Extract and clean response
            ai_response = response.get("content", "I'm having trouble processing that request.")
            
            # 6. Store conversation turn
            if conversation_id:
                await self._store_conversation_turn(
                    conversation_id, 
                    user_id, 
                    message, 
                    ai_response
                )
            
            return {
                "content": ai_response,
                "context": {
                    "relevant_items": len(context.get("items", [])),
                    "knowledge_used": bool(context.get("items")),
                    "context_type": context_type
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your message. Please try again.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_relevant_context(self, message: str, user_id: str) -> Dict[str, Any]:
        """Get relevant context from user's knowledge base"""
        try:
            # Search for relevant items using embeddings
            search_results = await self.embedding_manager.search_similar_items(
                query=message,
                user_id=user_id,
                limit=5,
                threshold=0.7
            )
            
            context = {
                "items": [],
                "topics": set()
            }
            
            if search_results:
                for result in search_results:
                    context["items"].append({
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:500],  # Limit content length
                        "type": result.get("content_type", ""),
                        "relevance": result.get("similarity", 0)
                    })
                    
                    # Extract topics/tags
                    if result.get("tags"):
                        context["topics"].update(result["tags"])
            
            context["topics"] = list(context["topics"])
            return context
            
        except Exception as e:
            logger.warning(f"Failed to get context: {e}")
            return {"items": [], "topics": []}
    
    async def _get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        try:
            async for conn in get_db_connection():
                rows = await conn.fetch("""
                    SELECT role, content_text as content, created_at
                    FROM ai_conversation_messages
                    WHERE conversation_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, conversation_id, limit)
                
                # Reverse to get chronological order
                history = [
                    {
                        "role": row["role"],
                        "content": row["content"]
                    }
                    for row in reversed(rows)
                ]
                
                return history
                
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []
    
    def _build_enhanced_prompt(
        self, 
        message: str, 
        context: Dict[str, Any], 
        history: List[Dict[str, str]]
    ) -> str:
        """Build enhanced prompt with context"""
        prompt_parts = []
        
        # Add conversation history if available
        if history:
            prompt_parts.append("Previous conversation:")
            for turn in history[-4:]:  # Last 4 turns
                role = "User" if turn["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {turn['content']}")
            prompt_parts.append("")
        
        # Add relevant context if available
        if context.get("items"):
            prompt_parts.append("Relevant information from knowledge base:")
            for item in context["items"][:3]:  # Top 3 most relevant
                prompt_parts.append(f"- {item['title']}: {item['content']}")
            prompt_parts.append("")
        
        # Add current message
        prompt_parts.append(f"Current message: {message}")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self, context_type: str) -> str:
        """Get appropriate system prompt based on context"""
        base_prompt = """You are a helpful AI assistant integrated with the user's personal knowledge base. 
You have access to their saved information, notes, and insights. Use this context when relevant to provide 
more personalized and informed responses."""
        
        context_prompts = {
            "voice": """You are responding to a voice message. Keep your responses conversational, 
natural, and concise. Avoid overly long explanations unless specifically asked.""",
            
            "chat": """You are having a text-based conversation. Provide clear, well-structured 
responses with appropriate detail.""",
            
            "search": """You are helping the user search and understand their knowledge base. 
Focus on finding and explaining relevant information from their saved content."""
        }
        
        return f"{base_prompt}\n\n{context_prompts.get(context_type, context_prompts['chat'])}"
    
    async def _store_conversation_turn(
        self, 
        conversation_id: str, 
        user_id: str, 
        user_message: str, 
        ai_response: str
    ):
        """Store conversation turn in database"""
        try:
            async for conn in get_db_connection():
                # Store user message
                await conn.execute("""
                    INSERT INTO ai_conversation_messages 
                    (conversation_id, original_message_id, role, sequence_number, content_text, timestamp, created_at)
                    VALUES ($1, $2, 'user', 1, $3, NOW(), NOW())
                """, conversation_id, f"user_{conversation_id}_1", user_message)
                
                # Store AI response
                await conn.execute("""
                    INSERT INTO ai_conversation_messages 
                    (conversation_id, original_message_id, role, sequence_number, content_text, timestamp, created_at)
                    VALUES ($1, $2, 'assistant', 2, $3, NOW(), NOW())
                """, conversation_id, f"assistant_{conversation_id}_2", ai_response)
                
        except Exception as e:
            logger.error(f"Failed to store conversation turn: {e}")
    
    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new conversation thread"""
        try:
            async for conn in get_db_connection():
                conversation_id = await conn.fetchval("""
                    INSERT INTO ai_conversation_imports 
                    (platform, source_url, extension_id, title, slug, conversation_date, imported_at, message_count, created_at, updated_at)
                    VALUES ('chat', '', $1, $2, $3, NOW(), NOW(), 0, NOW(), NOW())
                    RETURNING id
                """, user_id, title or "New Conversation", title.lower().replace(" ", "-") if title else "new-conversation")
                
                return str(conversation_id)
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise


# Singleton instance
_chat_service_instance = None

def get_chat_service() -> ChatService:
    """Get singleton chat service instance"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance