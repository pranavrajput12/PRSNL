"""
Second Brain Chat Service - Conversational interface for knowledge base
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Item, ItemTag, Tag
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)

class SecondBrainService:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.embedding_service = EmbeddingService()
        self.knowledge_graph = KnowledgeGraphService()
        
        # Conversation context window
        self.context_window_size = 10
        
        # System prompts for different chat modes
        self.system_prompts = {
            "general": """You are an AI assistant helping users explore their personal knowledge base. 
You have access to all their saved content including articles, videos, notes, and insights.
Be helpful, concise, and cite specific items when relevant. Use the user's content to provide 
personalized and contextual responses.""",
            
            "research": """You are a research assistant helping users dive deep into topics from their knowledge base.
Connect related concepts, identify patterns, and suggest new perspectives based on their saved content.
Always cite sources and suggest related items for further exploration.""",
            
            "learning": """You are a learning companion helping users understand and retain information from their knowledge base.
Break down complex topics, create summaries, and suggest learning paths based on their saved content.
Adapt your explanations to their apparent level of understanding.""",
            
            "creative": """You are a creative thinking partner helping users generate new ideas from their knowledge base.
Make unexpected connections, suggest novel applications, and help synthesize information in creative ways.
Encourage exploration and 'what if' thinking."""
        }
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        chat_mode: str = "general",
        context_items: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return a response with relevant context
        """
        try:
            # Get conversation history if conversation_id provided
            conversation_history = []
            if conversation_id:
                # In a real implementation, we'd fetch from a conversations table
                pass
            
            # Search for relevant items based on the message
            relevant_items = await self._find_relevant_items(message, db)
            
            # Get knowledge graph connections if items found
            connections = []
            if relevant_items:
                for item in relevant_items[:3]:  # Top 3 items
                    item_connections = await self.knowledge_graph.get_item_relationships(
                        item['id'], 
                        db=db
                    )
                    connections.extend(item_connections['relationships'][:2])
            
            # Build context for the LLM
            context = self._build_context(
                message=message,
                relevant_items=relevant_items,
                connections=connections,
                conversation_history=conversation_history,
                context_items=context_items
            )
            
            # Generate response
            system_prompt = self.system_prompts.get(chat_mode, self.system_prompts["general"])
            
            response = await self.llm_processor.process_with_llm(
                prompt=context,
                system_message=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract citations and suggested items
            citations = self._extract_citations(response, relevant_items)
            suggested_items = await self._get_suggested_items(message, relevant_items, db)
            
            # Analyze conversation for insights
            insights = await self._analyze_conversation(
                message=message,
                response=response,
                relevant_items=relevant_items
            )
            
            return {
                "response": response,
                "citations": citations,
                "suggested_items": suggested_items,
                "insights": insights,
                "chat_mode": chat_mode,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise
    
    async def _find_relevant_items(
        self, 
        message: str, 
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find items relevant to the chat message
        """
        try:
            # Generate embedding for the message
            message_embedding = await self.embedding_service.generate_embedding(message)
            
            # Semantic search
            semantic_results = await self.embedding_service.search_similar(
                embedding=message_embedding,
                limit=limit,
                db=db
            )
            
            # Also do keyword search for better coverage
            keywords = self._extract_keywords(message)
            
            keyword_query = select(Item).where(
                or_(*[Item.search_vector.match(keyword) for keyword in keywords])
            ).limit(limit)
            
            keyword_results = await db.execute(keyword_query)
            keyword_items = keyword_results.scalars().all()
            
            # Combine and deduplicate results
            all_items = {}
            
            # Add semantic results with scores
            for item, score in semantic_results:
                all_items[item.id] = {
                    "id": str(item.id),
                    "title": item.title,
                    "summary": item.summary,
                    "url": item.url,
                    "created_at": item.created_at.isoformat(),
                    "relevance_score": float(score),
                    "match_type": "semantic"
                }
            
            # Add keyword results
            for item in keyword_items:
                if item.id not in all_items:
                    all_items[item.id] = {
                        "id": str(item.id),
                        "title": item.title,
                        "summary": item.summary,
                        "url": item.url,
                        "created_at": item.created_at.isoformat(),
                        "relevance_score": 0.5,  # Lower score for keyword matches
                        "match_type": "keyword"
                    }
            
            # Sort by relevance score
            sorted_items = sorted(
                all_items.values(), 
                key=lambda x: x['relevance_score'], 
                reverse=True
            )
            
            return sorted_items[:limit]
            
        except Exception as e:
            logger.error(f"Error finding relevant items: {str(e)}")
            return []
    
    def _extract_keywords(self, message: str) -> List[str]:
        """
        Extract keywords from message for search
        """
        # Simple keyword extraction - in production, use NLP
        import re

        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'how', 'when', 'where', 'what', 'which', 'who', 'why', 'can', 'could',
            'should', 'would', 'is', 'are', 'was', 'were', 'been', 'be', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'shall', 'may', 'might'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', message.lower())
        
        # Filter out stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)
        
        return unique_keywords[:5]  # Top 5 keywords
    
    def _build_context(
        self,
        message: str,
        relevant_items: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        context_items: Optional[List[str]] = None
    ) -> str:
        """
        Build context for the LLM
        """
        context_parts = []
        
        # Add conversation history
        if conversation_history:
            context_parts.append("Previous conversation:")
            for entry in conversation_history[-self.context_window_size:]:
                context_parts.append(f"User: {entry['user_message']}")
                context_parts.append(f"Assistant: {entry['assistant_response']}")
            context_parts.append("")
        
        # Add relevant items from knowledge base
        if relevant_items:
            context_parts.append("Relevant items from knowledge base:")
            for i, item in enumerate(relevant_items[:5], 1):
                context_parts.append(f"{i}. [{item['title']}] - {item['summary']}")
                if item.get('match_type') == 'semantic':
                    context_parts.append(f"   Relevance: {item['relevance_score']:.2f}")
            context_parts.append("")
        
        # Add knowledge graph connections
        if connections:
            context_parts.append("Related concepts and connections:")
            for conn in connections[:5]:
                context_parts.append(
                    f"- {conn['from_title']} → {conn['relationship_type']} → {conn['to_title']}"
                )
            context_parts.append("")
        
        # Add specific context items if provided
        if context_items:
            context_parts.append("Specific context provided:")
            for item_id in context_items:
                # Would fetch actual item content here
                context_parts.append(f"- Item {item_id}")
            context_parts.append("")
        
        # Add the current message
        context_parts.append(f"Current question: {message}")
        context_parts.append("")
        context_parts.append("Please provide a helpful response based on the user's knowledge base. Cite specific items when relevant using [Item Title] format.")
        
        return "\n".join(context_parts)
    
    def _extract_citations(
        self, 
        response: str, 
        relevant_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract citations from the response
        """
        import re
        
        citations = []
        
        # Find all [Title] patterns in response
        citation_pattern = r'\[([^\]]+)\]'
        matches = re.findall(citation_pattern, response)
        
        for match in matches:
            # Find corresponding item
            for item in relevant_items:
                if match.lower() in item['title'].lower() or item['title'].lower() in match.lower():
                    citations.append({
                        "text": match,
                        "item_id": item['id'],
                        "title": item['title'],
                        "url": item['url']
                    })
                    break
        
        return citations
    
    async def _get_suggested_items(
        self,
        message: str,
        relevant_items: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get suggested items for further exploration
        """
        suggested = []
        
        # Get items related to the most relevant items
        if relevant_items:
            top_item_id = relevant_items[0]['id']
            
            # Get knowledge graph connections
            connections = await self.knowledge_graph.get_item_relationships(
                top_item_id,
                db=db
            )
            
            for rel in connections['relationships'][:3]:
                if rel['to_item']['id'] not in [item['id'] for item in relevant_items]:
                    suggested.append({
                        "id": rel['to_item']['id'],
                        "title": rel['to_item']['title'],
                        "reason": f"{rel['relationship_type']} to '{relevant_items[0]['title']}'"
                    })
        
        return suggested
    
    async def _analyze_conversation(
        self,
        message: str,
        response: str,
        relevant_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze the conversation for insights
        """
        insights = {
            "topics_discussed": [],
            "knowledge_gaps": [],
            "exploration_suggestions": []
        }
        
        # Extract main topics
        if relevant_items:
            # Get unique topics from relevant items
            topics = set()
            for item in relevant_items[:5]:
                # In real implementation, would extract from item tags/categories
                topics.add(item['title'].split()[0])  # Simple approach
            
            insights["topics_discussed"] = list(topics)
        
        # Identify potential knowledge gaps
        question_words = ['how', 'why', 'what', 'when', 'where', 'which']
        if any(word in message.lower() for word in question_words):
            if len(relevant_items) < 3:
                insights["knowledge_gaps"].append({
                    "topic": message.split()[-1],  # Simple approach
                    "suggestion": "Consider saving more content about this topic"
                })
        
        # Suggest exploration paths
        if relevant_items:
            insights["exploration_suggestions"].append({
                "action": "deep_dive",
                "topic": relevant_items[0]['title'],
                "reason": "Most relevant to your question"
            })
        
        return insights
    
    async def get_conversation_summary(
        self,
        conversation_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get a summary of a conversation
        """
        # In real implementation, would fetch from conversations table
        # For now, return a placeholder
        return {
            "conversation_id": conversation_id,
            "summary": "Conversation summary would go here",
            "main_topics": [],
            "items_referenced": [],
            "insights_generated": []
        }
    
    async def suggest_questions(
        self,
        context_items: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> List[str]:
        """
        Suggest interesting questions based on user's knowledge base
        """
        suggestions = []
        
        try:
            # Get recent items
            recent_query = select(Item).order_by(
                Item.created_at.desc()
            ).limit(10)
            
            result = await db.execute(recent_query)
            recent_items = result.scalars().all()
            
            if recent_items:
                # Generate questions based on recent content
                recent_titles = [item.title for item in recent_items[:3]]
                
                prompt = f"""Based on these recent items from a knowledge base:
{', '.join(recent_titles)}

Suggest 5 interesting questions the user might want to explore about their saved content.
Questions should be thought-provoking and help discover connections or insights.
Format: One question per line, no numbering."""

                questions_text = await self.llm_processor.process_with_llm(
                    prompt=prompt,
                    temperature=0.8,
                    max_tokens=200
                )
                
                suggestions = [q.strip() for q in questions_text.split('\n') if q.strip()][:5]
            
            # Add some default questions if needed
            if len(suggestions) < 3:
                defaults = [
                    "What patterns do you see in my recent saves?",
                    "How do my interests connect to each other?",
                    "What am I learning about lately?",
                    "Show me connections I might have missed",
                    "What should I explore next based on my interests?"
                ]
                suggestions.extend(defaults[:5-len(suggestions)])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting questions: {str(e)}")
            return [
                "What have I been learning about recently?",
                "Show me connections between my saved items",
                "What patterns exist in my knowledge base?"
            ]