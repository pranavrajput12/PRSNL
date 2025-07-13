"""
AI Chat Conversations API - Neural Echo

This module handles importing and managing AI chat conversations from various platforms
like ChatGPT, Claude, Perplexity, etc. Part of the Neural Echo feature.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid as uuid_lib

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator

from app.db.database import get_db_connection
from app.services.conversation_service import ConversationService
from app.core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations", "neural-echo"])

# Request/Response Models
class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    id: str = Field(..., description="Message ID from platform")
    role: str = Field(..., pattern="^(user|assistant|system)$")
    timestamp: str = Field(..., description="ISO timestamp")
    content: Dict[str, Any] = Field(..., description="Message content with text, html, markdown")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError('Role must be user, assistant, or system')
        return v

class ConversationImportRequest(BaseModel):
    """Request to import a conversation"""
    id: str = Field(..., description="Unique ID from Chrome extension")
    platform: str = Field(..., pattern="^(chatgpt|claude|perplexity|bard|gemini|other)$")
    source_url: str = Field(..., description="Original conversation URL")
    title: str = Field(..., min_length=1, max_length=500)
    timestamp: str = Field(..., description="ISO timestamp of conversation")
    messages: List[ConversationMessage]
    tags: Optional[List[str]] = Field(default=[], description="Optional tags to apply")
    
    @validator('messages')
    def validate_messages(cls, v):
        if len(v) == 0:
            raise ValueError('Conversation must have at least one message')
        if len(v) > 1000:
            raise ValueError('Conversation cannot exceed 1000 messages')
        return v

class ConversationResponse(BaseModel):
    """Response after importing conversation"""
    id: UUID
    platform: str
    title: str
    slug: str
    permalink: str
    message_count: int
    neural_category: Optional[str]
    neural_subcategory: Optional[str]
    imported_at: datetime
    source_url: str

class ConversationListItem(BaseModel):
    """Conversation item for listing"""
    id: UUID
    platform: str
    title: str
    slug: str
    permalink: str
    message_count: int
    timestamp: datetime
    imported_at: datetime
    neural_category: Optional[str]
    neural_subcategory: Optional[str]

class ConversationDetail(BaseModel):
    """Detailed conversation with messages"""
    id: UUID
    platform: str
    title: str
    slug: str
    permalink: str
    source_url: str
    timestamp: datetime
    imported_at: datetime
    message_count: int
    total_tokens: int
    neural_category: Optional[str]
    neural_subcategory: Optional[str]
    categorization_confidence: Optional[float]
    tags: List[str]
    messages: List[Dict[str, Any]]

# API Endpoints
@router.post("/import", response_model=ConversationResponse)
async def import_conversation(
    request: ConversationImportRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_optional)
):
    """
    Import an AI chat conversation from Chrome extension.
    
    This endpoint:
    1. Validates the conversation data
    2. Checks for duplicates
    3. Stores the conversation and messages
    4. Applies neural categorization
    5. Creates a PRSNL item for unified search
    6. Returns the permalink for viewing
    """
    logger.info(f"Importing conversation from {request.platform}: {request.title}")
    
    try:
        conversation_service = ConversationService()
        
        # Process and store the conversation
        result = await conversation_service.import_conversation(
            extension_id=request.id,  # Use the ID from extension
            platform=request.platform,
            source_url=request.source_url,
            title=request.title,
            timestamp=datetime.fromisoformat(request.timestamp.replace('Z', '+00:00')),
            messages=[{
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            } for msg in request.messages],
            tags=request.tags
        )
        
        # Trigger intelligence processing in background
        from app.services.conversation_intelligence import conversation_intelligence
        background_tasks.add_task(
            conversation_intelligence.process_conversation,
            result['id']
        )
        
        return ConversationResponse(
            id=result['id'],
            platform=result['platform'],
            title=result['title'],
            slug=result['slug'],
            permalink=result['permalink'],
            message_count=result['message_count'],
            neural_category=result.get('neural_category'),
            neural_subcategory=result.get('neural_subcategory'),
            imported_at=result['imported_at'],
            source_url=result['source_url']
        )
        
    except ValueError as e:
        logger.error(f"Validation error importing conversation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to import conversation")

@router.get("/", response_model=List[ConversationListItem])
async def list_conversations(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    category: Optional[str] = Query(None, description="Filter by neural category"),
    search: Optional[str] = Query(None, description="Search in titles"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user_optional)
):
    """
    List all imported conversations with optional filtering.
    """
    try:
        async for conn in get_db_connection():
            query = """
                SELECT 
                    c.id, c.platform, c.title, c.slug, c.permalink,
                    c.message_count, c.conversation_date, c.imported_at,
                    c.neural_category, c.neural_subcategory,
                    array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
                FROM ai_conversation_imports c
                LEFT JOIN ai_conversation_search_items csi ON c.id = csi.conversation_id
                LEFT JOIN items i ON csi.item_id = i.id
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if platform:
                param_count += 1
                query += f" AND c.platform = ${param_count}"
                params.append(platform)
            
            if category:
                param_count += 1
                query += f" AND c.neural_category = ${param_count}"
                params.append(category)
            
            if search:
                param_count += 1
                query += f" AND c.search_vector @@ plainto_tsquery(${param_count})"
                params.append(search)
            
            query += """
                GROUP BY c.id
                ORDER BY c.imported_at DESC
                LIMIT $%d OFFSET $%d
            """ % (param_count + 1, param_count + 2)
            
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            return [
                ConversationListItem(
                    id=row['id'],
                    platform=row['platform'],
                    title=row['title'],
                    slug=row['slug'],
                    permalink=row['permalink'],
                    message_count=row['message_count'],
                    timestamp=row['conversation_date'],
                    imported_at=row['imported_at'],
                    neural_category=row['neural_category'],
                    neural_subcategory=row['neural_subcategory']
                )
                for row in rows
            ]
            
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user=Depends(get_current_user_optional)
):
    """
    Get a single conversation with all messages.
    """
    try:
        async for conn in get_db_connection():
            # Get conversation details
            conv = await conn.fetchrow("""
                SELECT 
                    c.*,
                    array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
                FROM ai_conversation_imports c
                LEFT JOIN ai_conversation_search_items csi ON c.id = csi.conversation_id
                LEFT JOIN items i ON csi.item_id = i.id
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE c.id = $1
                GROUP BY c.id
            """, conversation_id)
            
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Get messages
            messages = await conn.fetch("""
                SELECT 
                    original_message_id as message_id, role, content_text, content_html, 
                    content_markdown, timestamp, sequence_number, metadata
                FROM ai_conversation_messages
                WHERE conversation_id = $1
                ORDER BY sequence_number ASC
            """, conversation_id)
            
            return ConversationDetail(
                id=conv['id'],
                platform=conv['platform'],
                title=conv['title'],
                slug=conv['slug'],
                permalink=conv['permalink'],
                source_url=conv['source_url'],
                timestamp=conv['conversation_date'],
                imported_at=conv['imported_at'],
                message_count=conv['message_count'],
                total_tokens=conv['total_tokens'] or 0,
                neural_category=conv['neural_category'],
                neural_subcategory=conv['neural_subcategory'],
                categorization_confidence=conv['categorization_confidence'],
                tags=conv['tags'] or [],
                messages=[{
                    'id': msg['message_id'],
                    'role': msg['role'],
                    'content': {
                        'text': msg['content_text'],
                        'html': msg['content_html'],
                        'markdown': msg['content_markdown']
                    },
                    'timestamp': msg['timestamp'].isoformat(),
                    'sequence': msg['sequence_number'],
                    'metadata': msg['metadata']
                } for msg in messages]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")

@router.get("/by-slug/{platform}/{slug}", response_model=ConversationDetail)
async def get_conversation_by_slug(
    platform: str,
    slug: str,
    current_user=Depends(get_current_user_optional)
):
    """
    Get a conversation by its platform and slug (for permalink support).
    """
    try:
        async for conn in get_db_connection():
            # Get conversation ID by slug
            conv_id = await conn.fetchval("""
                SELECT id FROM ai_conversation_imports
                WHERE platform = $1 AND slug = $2
            """, platform, slug)
            
            if not conv_id:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Use the existing get_conversation logic
            return await get_conversation(conv_id, current_user)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation by slug {platform}/{slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user=Depends(get_current_user_optional)
):
    """
    Delete a conversation and all its messages.
    """
    try:
        async for conn in get_db_connection():
            # Check if conversation exists
            exists = await conn.fetchval(
                "SELECT 1 FROM ai_conversation_imports WHERE id = $1",
                conversation_id
            )
            
            if not exists:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Delete conversation (cascades to messages and item link)
            await conn.execute(
                "DELETE FROM ai_conversation_imports WHERE id = $1",
                conversation_id
            )
            
            return {"message": "Conversation deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

@router.get("/stats/summary")
async def get_conversation_stats(
    current_user=Depends(get_current_user_optional)
):
    """
    Get summary statistics about imported conversations.
    """
    try:
        async for conn in get_db_connection():
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT id) as total_conversations,
                    COUNT(DISTINCT platform) as platforms_count,
                    SUM(message_count) as total_messages,
                    SUM(total_tokens) as total_tokens,
                    json_object_agg(platform, platform_count) as by_platform,
                    json_object_agg(neural_category, category_count) as by_category
                FROM (
                    SELECT 
                        platform,
                        neural_category,
                        COUNT(*) OVER (PARTITION BY platform) as platform_count,
                        COUNT(*) OVER (PARTITION BY neural_category) as category_count,
                        id, message_count, total_tokens
                    FROM ai_conversation_imports
                ) subq
            """)
            
            return {
                "total_conversations": stats['total_conversations'] or 0,
                "platforms_count": stats['platforms_count'] or 0,
                "total_messages": stats['total_messages'] or 0,
                "total_tokens": stats['total_tokens'] or 0,
                "by_platform": stats['by_platform'] or {},
                "by_category": stats['by_category'] or {}
            }
            
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")