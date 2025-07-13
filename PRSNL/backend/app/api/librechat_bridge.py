"""
LibreChat API Bridge for PRSNL Integration

This module provides OpenAI-compatible endpoints that LibreChat can use
to interface with PRSNL's knowledge base and AI services.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["librechat-bridge"])

# LibreChat-compatible request/response models
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    user: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Available models that LibreChat can use
AVAILABLE_MODELS = [
    {
        "id": "prsnl-gpt-4",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "prsnl"
    },
    {
        "id": "prsnl-gpt-35-turbo", 
        "object": "model",
        "created": int(time.time()),
        "owned_by": "prsnl"
    }
]

@router.get("/models", response_model=ModelsResponse)
async def list_models(
    x_prsnl_integration: Optional[str] = Header(None, alias="X-PRSNL-Integration")
):
    """
    List available models for LibreChat integration.
    Compatible with OpenAI API format.
    """
    logger.info(f"Models requested by integration: {x_prsnl_integration}")
    
    return ModelsResponse(
        object="list",
        data=[ModelInfo(**model) for model in AVAILABLE_MODELS]
    )

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_prsnl_integration: Optional[str] = Header(None, alias="X-PRSNL-Integration"),
    authorization: Optional[str] = Header(None)
):
    """
    Chat completions endpoint compatible with OpenAI API format.
    Integrates PRSNL knowledge base with LibreChat.
    """
    logger.info(f"Chat completion requested by: {x_prsnl_integration}")
    logger.debug(f"Model: {request.model}, Messages: {len(request.messages)}")
    
    try:
        # Initialize AI service
        ai_service = UnifiedAIService()
        
        # Get the latest user message
        user_message = None
        conversation_history = []
        
        for message in request.messages:
            if message.role == "user":
                user_message = message.content
            conversation_history.append({
                "role": message.role,
                "content": message.content
            })
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Enhanced query with knowledge base context
        enhanced_response = await enhance_query_with_knowledge_base(
            user_message, 
            conversation_history,
            request.model
        )
        
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_chat_response(enhanced_response, request),
                media_type="text/plain"
            )
        else:
            # Return complete response
            return create_chat_completion_response(
                enhanced_response,
                request.model,
                request
            )
            
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

async def enhance_query_with_knowledge_base(
    query: str, 
    conversation_history: List[Dict[str, str]],
    model: str
) -> str:
    """
    Enhance the user query with relevant knowledge base context.
    """
    try:
        # Search knowledge base for relevant content
        async for conn in get_db_connection():
            # Perform semantic search for relevant items
            search_query = """
                SELECT id, title, summary, content, url, type
                FROM items 
                WHERE search_vector @@ plainto_tsquery($1)
                   OR summary ILIKE $2
                   OR content ILIKE $2
                ORDER BY ts_rank(search_vector, plainto_tsquery($1)) DESC
                LIMIT 5
            """
            
            search_pattern = f"%{query}%"
            relevant_items = await conn.fetch(search_query, query, search_pattern)
            
            # Build context from relevant items
            context_parts = []
            
            if relevant_items:
                context_parts.append("# Relevant Knowledge Base Context")
                
                for item in relevant_items:
                    context_parts.append(f"\n## {item['title']}")
                    if item['summary']:
                        context_parts.append(f"Summary: {item['summary']}")
                    if item['content']:
                        # Limit content to avoid token limits
                        content = item['content'][:500]
                        if len(item['content']) > 500:
                            content += "..."
                        context_parts.append(f"Content: {content}")
                    if item['url']:
                        context_parts.append(f"Source: {item['url']}")
                    context_parts.append("")  # Empty line separator
            
            knowledge_context = "\n".join(context_parts)
            
            # Combine with conversation history for AI service
            ai_service = UnifiedAIService()
            
            # Create enhanced prompt
            system_prompt = f"""You are PRSNL's Second Brain AI assistant. You have access to the user's personal knowledge base and should provide helpful, contextual responses based on their stored information.

{knowledge_context}

Based on the above context from the user's knowledge base, please answer their question. If the context is relevant, reference it in your response. If you need to search for more specific information, you can suggest that to the user."""

            # Generate response using AI service
            messages = [{"role": "system", "content": system_prompt}] + conversation_history
            
            # Use LibreChat-specific model for this integration
            model_to_use = settings.AZURE_OPENAI_LIBRECHAT_DEPLOYMENT
            response = await ai_service.complete(
                prompt=user_message,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.7,
                model=model_to_use
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Knowledge base enhancement error: {e}")
        # Fallback to simple AI response without enhancement
        ai_service = UnifiedAIService()
        # Get the last user message
        last_user_msg = next((msg['content'] for msg in reversed(conversation_history) if msg['role'] == 'user'), query)
        return await ai_service.complete(
            prompt=last_user_msg,
            system_prompt="You are a helpful AI assistant.",
            max_tokens=1000,
            temperature=0.7,
            model=settings.AZURE_OPENAI_LIBRECHAT_DEPLOYMENT
        )

async def stream_chat_response(response: str, request: ChatCompletionRequest):
    """
    Stream chat response in OpenAI-compatible format.
    """
    request_id = f"chatcmpl-{int(time.time())}"
    
    # Split response into chunks for streaming
    words = response.split()
    chunk_size = 3  # Send 3 words at a time
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_content = " " + " ".join(chunk_words)
        
        if i + chunk_size >= len(words):
            # Last chunk
            chunk_data = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": chunk_content},
                    "finish_reason": "stop"
                }]
            }
        else:
            # Regular chunk
            chunk_data = {
                "id": request_id,
                "object": "chat.completion.chunk", 
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": chunk_content},
                    "finish_reason": None
                }]
            }
        
        yield f"data: {json.dumps(chunk_data)}\n\n"
        await asyncio.sleep(0.05)  # Small delay for realistic streaming
    
    # Send final chunk
    final_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

def create_chat_completion_response(
    response: str, 
    model: str, 
    request: ChatCompletionRequest
) -> ChatCompletionResponse:
    """
    Create a complete chat completion response in OpenAI format.
    """
    return ChatCompletionResponse(
        id=f"chatcmpl-{int(time.time())}",
        object="chat.completion",
        created=int(time.time()),
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop"
            )
        ],
        usage={
            "prompt_tokens": len(" ".join([msg.content for msg in request.messages]).split()),
            "completion_tokens": len(response.split()),
            "total_tokens": len(" ".join([msg.content for msg in request.messages]).split()) + len(response.split())
        }
    )

@router.get("/health")
async def librechat_bridge_health():
    """Health check endpoint for LibreChat bridge."""
    return {
        "status": "healthy",
        "service": "prsnl-librechat-bridge",
        "timestamp": datetime.utcnow().isoformat(),
        "models": len(AVAILABLE_MODELS)
    }