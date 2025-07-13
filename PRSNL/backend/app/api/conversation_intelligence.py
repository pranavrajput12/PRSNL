"""
Conversation Intelligence API - Endpoints for AI-powered conversation analysis

Provides endpoints to trigger intelligence processing and view results.
"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.db.database import get_db_connection
from app.services.conversation_intelligence import conversation_intelligence
from app.core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations/intelligence", tags=["conversation-intelligence"])

class IntelligenceResponse(BaseModel):
    """Response from intelligence processing"""
    conversation_id: str
    status: str
    summary: Optional[dict] = None
    learning_journey: Optional[dict] = None
    concepts: Optional[dict] = None
    insights: Optional[dict] = None

@router.post("/{conversation_id}/process")
async def process_conversation_intelligence(
    conversation_id: UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_optional)
):
    """
    Trigger AI intelligence processing for a conversation.
    
    This runs in the background and updates the conversation with:
    - Comprehensive summary
    - Learning journey analysis
    - Key concepts and topics
    - Knowledge gaps
    - Actionable insights
    """
    try:
        # Check if conversation exists
        async for conn in get_db_connection():
            exists = await conn.fetchval(
                "SELECT 1 FROM ai_conversation_imports WHERE id = $1",
                conversation_id
            )
            
            if not exists:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Check processing status
            status = await conn.fetchval(
                "SELECT processing_status FROM ai_conversation_imports WHERE id = $1",
                conversation_id
            )
            
            if status == 'processing':
                return {"message": "Processing already in progress", "status": "processing"}
            
            # Mark as processing
            await conn.execute(
                "UPDATE ai_conversation_imports SET processing_status = 'processing' WHERE id = $1",
                conversation_id
            )
        
        # Add background task
        background_tasks.add_task(
            conversation_intelligence.process_conversation,
            conversation_id
        )
        
        return {
            "message": "Intelligence processing started",
            "conversation_id": str(conversation_id),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting intelligence processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

@router.get("/{conversation_id}")
async def get_conversation_intelligence(
    conversation_id: UUID,
    current_user=Depends(get_current_user_optional)
):
    """
    Get intelligence analysis results for a conversation.
    """
    try:
        async for conn in get_db_connection():
            # Get conversation with intelligence data
            conv = await conn.fetchrow("""
                SELECT 
                    id, title, platform, processing_status,
                    summary, key_topics, learning_points,
                    user_journey, knowledge_gaps,
                    neural_category, neural_subcategory,
                    categorization_confidence
                FROM ai_conversation_imports
                WHERE id = $1
            """, conversation_id)
            
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Get message insights
            messages_with_insights = await conn.fetch("""
                SELECT 
                    sequence_number, role, 
                    summary, key_points, concepts_introduced
                FROM ai_conversation_messages
                WHERE conversation_id = $1 
                    AND (summary IS NOT NULL OR key_points IS NOT NULL)
                ORDER BY sequence_number
            """, conversation_id)
            
            return IntelligenceResponse(
                conversation_id=str(conv['id']),
                status=conv['processing_status'],
                summary={
                    "text": conv['summary'],
                    "platform": conv['platform'],
                    "title": conv['title']
                } if conv['summary'] else None,
                learning_journey={
                    "narrative": conv['user_journey'],
                    "key_learnings": conv['learning_points'] or []
                } if conv['user_journey'] else None,
                concepts={
                    "topics": conv['key_topics'] or [],
                    "category": conv['neural_category'],
                    "subcategory": conv['neural_subcategory'],
                    "confidence": conv['categorization_confidence']
                } if conv['key_topics'] else None,
                insights={
                    "knowledge_gaps": conv['knowledge_gaps'] or [],
                    "message_insights": [
                        {
                            "position": msg['sequence_number'],
                            "role": msg['role'],
                            "summary": msg['summary'],
                            "key_points": msg['key_points'] or [],
                            "concepts": msg['concepts_introduced'] or []
                        }
                        for msg in messages_with_insights
                    ]
                } if conv['processing_status'] == 'completed' else None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intelligence data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get intelligence data")

@router.post("/batch/process")
async def process_batch_intelligence(
    background_tasks: BackgroundTasks,
    platform: Optional[str] = None,
    limit: int = 10,
    current_user=Depends(get_current_user_optional)
):
    """
    Process intelligence for multiple conversations that haven't been processed yet.
    """
    try:
        async for conn in get_db_connection():
            # Find unprocessed conversations
            query = """
                SELECT id FROM ai_conversation_imports
                WHERE processing_status = 'pending'
            """
            params = []
            
            if platform:
                query += " AND platform = $1"
                params.append(platform)
            
            query += " ORDER BY imported_at DESC LIMIT $%d" % (len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            if not rows:
                return {
                    "message": "No pending conversations found",
                    "processed_count": 0
                }
            
            # Mark all as processing and add to background tasks
            conversation_ids = [row['id'] for row in rows]
            
            await conn.execute("""
                UPDATE ai_conversation_imports 
                SET processing_status = 'processing'
                WHERE id = ANY($1)
            """, conversation_ids)
            
            # Add all to background processing
            for conv_id in conversation_ids:
                background_tasks.add_task(
                    conversation_intelligence.process_conversation,
                    conv_id
                )
            
            return {
                "message": f"Started processing {len(conversation_ids)} conversations",
                "processed_count": len(conversation_ids),
                "conversation_ids": [str(id) for id in conversation_ids]
            }
            
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch processing")