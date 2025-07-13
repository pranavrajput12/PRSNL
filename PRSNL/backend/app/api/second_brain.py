"""
Second Brain Chat API endpoints
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.db.database import get_db
from app.services.second_brain import SecondBrainService

logger = logging.getLogger(__name__)

router = APIRouter()
second_brain_service = SecondBrainService()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    chat_mode: str = "general"  # general, research, learning, creative
    context_items: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    citations: List[Dict[str, Any]]
    suggested_items: List[Dict[str, Any]]
    insights: Dict[str, Any]
    chat_mode: str
    timestamp: str

class ConversationSummaryResponse(BaseModel):
    conversation_id: str
    summary: str
    main_topics: List[str]
    items_referenced: List[Dict[str, Any]]
    insights_generated: List[Dict[str, Any]]

class SuggestedQuestionsResponse(BaseModel):
    questions: List[str]
    based_on: str  # "recent_items", "context", "trending"

# REST Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Send a message to the Second Brain chat
    """
    try:
        result = await second_brain_service.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            chat_mode=request.chat_mode,
            context_items=request.context_items,
            db=db
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get a summary of a conversation
    """
    try:
        summary = await second_brain_service.get_conversation_summary(
            conversation_id=conversation_id,
            db=db
        )
        
        return ConversationSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest-questions", response_model=SuggestedQuestionsResponse)
async def suggest_questions(
    context_items: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get suggested questions to ask the Second Brain
    """
    try:
        # Parse context items if provided
        context_list = None
        if context_items:
            context_list = context_items.split(',')
        
        questions = await second_brain_service.suggest_questions(
            context_items=context_list,
            db=db
        )
        
        return SuggestedQuestionsResponse(
            questions=questions,
            based_on="recent_items" if not context_list else "context"
        )
        
    except Exception as e:
        logger.error(f"Error suggesting questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for streaming chat
@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for streaming chat responses
    """
    await websocket.accept()
    conversation_id = None
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Extract message details
            message = message_data.get("message", "")
            chat_mode = message_data.get("chat_mode", "general")
            context_items = message_data.get("context_items", None)
            
            if not conversation_id:
                conversation_id = message_data.get("conversation_id")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "data": {"status": "thinking"}
            })
            
            # Find relevant items
            relevant_items = await second_brain_service._find_relevant_items(
                message, db
            )
            
            # Send relevant items preview
            if relevant_items:
                await websocket.send_json({
                    "type": "context",
                    "data": {
                        "relevant_items": relevant_items[:3],
                        "count": len(relevant_items)
                    }
                })
            
            # Get knowledge graph connections
            connections = []
            if relevant_items:
                kg_service = second_brain_service.knowledge_graph
                for item in relevant_items[:2]:
                    item_connections = await kg_service.get_item_relationships(
                        item['id'], 
                        db=db
                    )
                    connections.extend(item_connections['relationships'][:2])
            
            # Build context
            context = second_brain_service._build_context(
                message=message,
                relevant_items=relevant_items,
                connections=connections,
                conversation_history=[],  # Would fetch from DB
                context_items=context_items
            )
            
            # Stream response
            system_prompt = second_brain_service.system_prompts.get(
                chat_mode, 
                second_brain_service.system_prompts["general"]
            )
            
            # Simulate streaming (in production, use actual streaming API)
            full_response = await second_brain_service.llm_processor.process_with_llm(
                prompt=context,
                system_message=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Send response in chunks
            chunk_size = 50
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                await websocket.send_json({
                    "type": "response_chunk",
                    "data": {"text": chunk}
                })
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
            # Extract citations
            citations = second_brain_service._extract_citations(
                full_response, 
                relevant_items
            )
            
            # Get suggested items
            suggested_items = await second_brain_service._get_suggested_items(
                message, 
                relevant_items, 
                db
            )
            
            # Analyze conversation
            insights = await second_brain_service._analyze_conversation(
                message=message,
                response=full_response,
                relevant_items=relevant_items
            )
            
            # Send complete response with metadata
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "response": full_response,
                    "citations": citations,
                    "suggested_items": suggested_items,
                    "insights": insights,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
        await websocket.close()

@router.get("/chat-modes")
async def get_chat_modes():
    """
    Get available chat modes and their descriptions
    """
    return {
        "modes": [
            {
                "id": "general",
                "name": "General",
                "description": "General conversation about your knowledge base",
                "icon": "message-circle"
            },
            {
                "id": "research",
                "name": "Research",
                "description": "Deep dive into topics and find connections",
                "icon": "search"
            },
            {
                "id": "learning",
                "name": "Learning",
                "description": "Understand and retain information better",
                "icon": "book-open"
            },
            {
                "id": "creative",
                "name": "Creative",
                "description": "Generate new ideas and unexpected connections",
                "icon": "lightbulb"
            }
        ]
    }