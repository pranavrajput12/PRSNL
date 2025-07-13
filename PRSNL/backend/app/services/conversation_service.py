"""
Conversation Service - Business logic for AI chat conversations

Handles importing, processing, and categorizing conversations from various AI platforms.
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import uuid as uuid_lib

from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.multimodal_embedding_service import multimodal_embedding_service
from app.services.slug_generator import SmartSlugGenerator

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing AI chat conversations"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
    
    async def import_conversation(
        self,
        extension_id: str,
        platform: str,
        source_url: str,
        title: str,
        timestamp: datetime,
        messages: List[Dict[str, Any]],
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Import and process a conversation.
        
        Steps:
        1. Check for duplicates
        2. Generate slug and permalink
        3. Store conversation and messages
        4. Apply neural categorization
        5. Create item for unified search
        6. Apply tags if provided
        """
        try:
            async for conn in get_db_connection():
                # Check for duplicate using extension_id
                existing = await conn.fetchval("""
                    SELECT id FROM ai_conversation_imports 
                    WHERE platform = $1 AND extension_id = $2
                """, platform, extension_id)
                
                if existing:
                    logger.info(f"Conversation already exists: {existing}")
                    # Return existing conversation
                    return await self._get_conversation_details(existing)
                
                # Generate slug
                base_slug = SmartSlugGenerator._generate_base_slug(title)
                slug = f"{base_slug}-{timestamp.strftime('%Y%m')}"
                
                # Ensure slug is unique
                slug_exists = await conn.fetchval(
                    "SELECT 1 FROM ai_conversation_imports WHERE slug = $1",
                    slug
                )
                if slug_exists:
                    slug = f"{slug}-{uuid_lib.uuid4().hex[:6]}"
                
                # Generate permalink using simple /conversations format
                permalink = f"/conversations/{platform}/{slug}"
                
                # Create conversation
                conversation_id = await conn.fetchval("""
                    INSERT INTO ai_conversation_imports (
                        platform, source_url, extension_id, title, slug, 
                        conversation_date, message_count, permalink
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """, platform, source_url, extension_id, title, slug, timestamp, len(messages), permalink)
                
                # Store messages
                for idx, msg in enumerate(messages):
                    content = msg.get('content', {})
                    
                    # Calculate approximate token count (rough estimate)
                    text_content = content.get('text', '')
                    token_count = len(text_content.split()) * 1.3  # Rough approximation
                    
                    await conn.execute("""
                        INSERT INTO ai_conversation_messages (
                            conversation_id, original_message_id, role, content_text,
                            content_html, content_markdown, timestamp,
                            sequence_number, token_count, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """, 
                        conversation_id,
                        msg['id'],
                        msg['role'],
                        content.get('text', ''),
                        content.get('html'),
                        content.get('markdown', content.get('text', '')),
                        datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')),
                        idx,
                        int(token_count),
                        json.dumps(msg.get('metadata', {}))
                    )
                
                # Apply neural categorization
                categorization = await self._categorize_conversation(
                    title, messages, platform
                )
                
                # Update conversation with categorization
                await conn.execute("""
                    UPDATE ai_conversation_imports 
                    SET neural_category = $1, 
                        neural_subcategory = $2,
                        categorization_confidence = $3,
                        metadata = $4,
                        processing_status = 'completed'
                    WHERE id = $5
                """, 
                    categorization['category'],
                    categorization['subcategory'],
                    categorization['confidence'],
                    json.dumps(categorization.get('metadata', {})),
                    conversation_id
                )
                
                # Create item for unified search
                item_id = await self._create_search_item(
                    conversation_id, title, messages, permalink, tags
                )
                
                # Link conversation to item for search
                await conn.execute("""
                    INSERT INTO ai_conversation_search_items (conversation_id, item_id)
                    VALUES ($1, $2)
                """, conversation_id, item_id)
                
                # Return conversation details
                return await self._get_conversation_details(conversation_id)
                
        except Exception as e:
            logger.error(f"Error importing conversation: {e}")
            raise
    
    async def _categorize_conversation(
        self, 
        title: str, 
        messages: List[Dict[str, Any]], 
        platform: str
    ) -> Dict[str, Any]:
        """
        Use AI to categorize the conversation into PRSNL's neural categories.
        """
        try:
            # Extract key topics from conversation
            conversation_summary = self._summarize_conversation(messages[:10])  # First 10 messages
            
            prompt = f"""
            Analyze this AI conversation and categorize it for a personal knowledge system.
            
            Title: {title}
            Platform: {platform}
            Summary: {conversation_summary}
            
            Categories available:
            - learning: Educational content, tutorials, explanations
            - development: Programming, code, technical discussions
            - thoughts: Personal reflections, ideas, brainstorming
            - reference: Facts, documentation, how-to guides
            - creative: Creative writing, storytelling, artistic discussions
            - problem-solving: Debugging, troubleshooting, solution finding
            
            Based on the content, choose the most appropriate category and subcategory.
            
            Respond with JSON only:
            {{"category": "learning", "subcategory": "tutorial", "confidence": 0.85, "topics": ["fastapi", "python"]}}
            """
            
            response = await self.ai_service.complete(
                prompt=prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            try:
                # Parse AI response
                result = json.loads(response.strip())
                
                # Validate category
                valid_categories = ['learning', 'development', 'thoughts', 'reference', 'creative', 'problem-solving']
                if result.get('category') not in valid_categories:
                    result['category'] = 'thoughts'  # Default
                
                return {
                    'category': result.get('category', 'thoughts'),
                    'subcategory': result.get('subcategory', 'general'),
                    'confidence': float(result.get('confidence', 0.5)),
                    'metadata': {
                        'topics': result.get('topics', []),
                        'ai_analysis': result
                    }
                }
            except:
                # Fallback categorization based on keywords
                return self._fallback_categorization(title, conversation_summary)
                
        except Exception as e:
            logger.error(f"Error categorizing conversation: {e}")
            return self._fallback_categorization(title, "")
    
    def _fallback_categorization(self, title: str, summary: str) -> Dict[str, Any]:
        """
        Simple keyword-based categorization as fallback.
        """
        text = f"{title} {summary}".lower()
        
        # Development keywords
        dev_keywords = ['code', 'programming', 'python', 'javascript', 'api', 'debug', 'function', 'class']
        if any(keyword in text for keyword in dev_keywords):
            return {
                'category': 'development',
                'subcategory': 'programming',
                'confidence': 0.7,
                'metadata': {'method': 'keyword_fallback'}
            }
        
        # Learning keywords
        learn_keywords = ['learn', 'tutorial', 'explain', 'how to', 'understand', 'course']
        if any(keyword in text for keyword in learn_keywords):
            return {
                'category': 'learning',
                'subcategory': 'tutorial',
                'confidence': 0.7,
                'metadata': {'method': 'keyword_fallback'}
            }
        
        # Creative keywords
        creative_keywords = ['story', 'write', 'creative', 'imagine', 'design', 'art']
        if any(keyword in text for keyword in creative_keywords):
            return {
                'category': 'creative',
                'subcategory': 'writing',
                'confidence': 0.6,
                'metadata': {'method': 'keyword_fallback'}
            }
        
        # Default to thoughts
        return {
            'category': 'thoughts',
            'subcategory': 'conversation',
            'confidence': 0.5,
            'metadata': {'method': 'default_fallback'}
        }
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Create a brief summary of the conversation for categorization.
        """
        summary_parts = []
        
        for msg in messages[:10]:  # First 10 messages
            content = msg.get('content', {})
            text = content.get('text', '')[:200]  # First 200 chars
            
            if msg['role'] == 'user' and text:
                summary_parts.append(f"User asks: {text}")
            elif msg['role'] == 'assistant' and text:
                summary_parts.append(f"AI discusses: {text}")
        
        return " ".join(summary_parts)[:500]
    
    async def _create_search_item(
        self,
        conversation_id: UUID,
        title: str,
        messages: List[Dict[str, Any]],
        permalink: str,
        tags: Optional[List[str]] = None
    ) -> UUID:
        """
        Create an item in the main items table for unified search.
        """
        try:
            # Create a summary from first few messages
            summary = self._create_item_summary(messages[:5])
            
            # Combine all message text for content
            content_parts = []
            for msg in messages:
                text = msg.get('content', {}).get('text', '')
                if text:
                    content_parts.append(f"{msg['role'].upper()}: {text}")
            
            content = "\n\n".join(content_parts)[:10000]  # Limit content size
            
            async for conn in get_db_connection():
                # Create item
                item_id = await conn.fetchval("""
                    INSERT INTO items (
                        url, title, summary, content, type, status,
                        content_type, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """,
                    permalink,  # Use permalink as URL
                    title,
                    summary,
                    content,
                    'conversation',  # New item type
                    'completed',
                    'conversation',
                    json.dumps({
                        'conversation_id': str(conversation_id),
                        'message_count': len(messages)
                    })
                )
                
                # Apply tags if provided
                if tags:
                    for tag_name in tags:
                        # Get or create tag
                        tag_id = await conn.fetchval("""
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id
                        """, tag_name.lower())
                        
                        # Link tag to item
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id, confidence)
                            VALUES ($1, $2, $3)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id, 1.0)
                
                # Create embedding for search
                await self._create_conversation_embedding(item_id, title, summary)
                
                return item_id
                
        except Exception as e:
            logger.error(f"Error creating search item: {e}")
            raise
    
    def _create_item_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        Create a summary from the first few messages.
        """
        summary_parts = []
        
        for msg in messages:
            text = msg.get('content', {}).get('text', '')[:150]
            if text and len(summary_parts) < 3:
                role = "Question" if msg['role'] == 'user' else "Answer"
                summary_parts.append(f"{role}: {text}")
        
        return " | ".join(summary_parts)[:500]
    
    async def _create_conversation_embedding(
        self, 
        item_id: UUID, 
        title: str, 
        summary: str
    ):
        """
        Create embedding for the conversation.
        """
        try:
            # Initialize embedding service
            await multimodal_embedding_service.initialize()
            
            # Create text embedding
            embedding_text = f"{title}\n\n{summary}"
            embedding_data = await multimodal_embedding_service.create_text_embedding(
                embedding_text
            )
            
            # Store embedding
            await multimodal_embedding_service.store_embedding(
                str(item_id),
                embedding_data
            )
            
        except Exception as e:
            logger.error(f"Error creating conversation embedding: {e}")
            # Don't fail the import if embedding fails
    
    async def _get_conversation_details(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Get conversation details for response.
        """
        async for conn in get_db_connection():
            conv = await conn.fetchrow("""
                SELECT * FROM ai_conversation_imports WHERE id = $1
            """, conversation_id)
            
            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            return {
                'id': conv['id'],
                'platform': conv['platform'],
                'title': conv['title'],
                'slug': conv['slug'],
                'permalink': conv['permalink'],
                'message_count': conv['message_count'],
                'neural_category': conv['neural_category'],
                'neural_subcategory': conv['neural_subcategory'],
                'imported_at': conv['imported_at'],
                'source_url': conv['source_url'],
                'processing_status': conv['processing_status']
            }