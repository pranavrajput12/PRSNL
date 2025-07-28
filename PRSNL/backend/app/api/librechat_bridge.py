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

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.multimodal_embedding_service import multimodal_embedding_service
from app.services.ner_service import ner_service

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
@observe(name="librechat_chat_completions")
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
            if message.role == "user" and message.content:
                user_message = message.content
            # Only add messages with valid content
            if message.content:
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

@observe(name="enhance_query_with_knowledge_base")
async def enhance_query_with_knowledge_base(
    query: str, 
    conversation_history: List[Dict[str, str]],
    model: str
) -> str:
    """
    Enhance the user query with relevant knowledge base context using multimodal search.
    """
    try:
        # Initialize multimodal services
        await multimodal_embedding_service.initialize()
        await ner_service.initialize()
        
        # Extract entities from the query for enhanced search
        entities = await ner_service.extract_entities(query, include_technical=True)
        
        # Get enhanced search terms from NER
        search_terms = [query]
        if entities.get('keywords'):
            search_terms.extend([kw['text'] for kw in entities['keywords'][:3]])
        if entities.get('technical'):
            for tech_category, tech_items in entities['technical'].items():
                search_terms.extend([item['text'] for item in tech_items[:2]])
        
        # Perform multimodal embedding search
        relevant_items = []
        try:
            # Create text embedding for semantic search
            text_embedding = await multimodal_embedding_service.create_text_embedding(query)
            
            # Perform cross-modal search across all content types
            multimodal_results = await multimodal_embedding_service.cross_modal_search(
                query_embedding=text_embedding['vector'],
                query_type='text',
                target_types=['text', 'image', 'multimodal'],
                limit=6,
                threshold=0.4
            )
            
            # Convert multimodal results to items format
            for result in multimodal_results:
                relevant_items.append({
                    'id': result.get('item_id'),
                    'title': result.get('title', 'Untitled'),
                    'summary': result.get('summary', ''),
                    'content': '',  # Content is in embedding, summary available
                    'url': result.get('url'),
                    'type': result.get('item_type', 'content'),
                    'repository_metadata': None,
                    'similarity_score': result.get('similarity', 0),
                    'embedding_type': result.get('embedding_type', 'text')
                })
            
        except Exception as e:
            logger.warning(f"Multimodal search failed, falling back to text search: {e}")
            
            # Fallback to traditional text search (simplified to actually work)
            async for conn in get_db_connection():
                search_query = """
                    SELECT 
                        id, title, summary, content, url, type,
                        repository_metadata,
                        CASE 
                            WHEN repository_metadata IS NOT NULL THEN 'repository'
                            ELSE type 
                        END as item_type
                    FROM items 
                    WHERE title ILIKE $1
                       OR summary ILIKE $1
                       OR content ILIKE $1
                       OR (repository_metadata IS NOT NULL AND (
                           repository_metadata->>'repo_name' ILIKE $1
                           OR repository_metadata->>'description' ILIKE $1
                           OR repository_metadata->>'use_case' ILIKE $1
                       ))
                    ORDER BY 
                        CASE WHEN repository_metadata IS NOT NULL THEN 1 ELSE 2 END,
                        char_length(title) ASC
                    LIMIT 8
                """
                
                search_pattern = f"%{query}%"
                relevant_items = await conn.fetch(search_query, search_pattern)
            
        # Build context from relevant items
        context_parts = []
        
        if relevant_items:
            context_parts.append("# 🔍 Enhanced Multimodal Search Results")
            
            # Add NER analysis if available
            if entities.get('summary', {}).get('has_technical_content'):
                context_parts.append(f"\n## 🧠 Query Analysis")
                context_parts.append(f"Technical Content Detected: {entities['summary']['has_technical_content']}")
                if entities.get('summary', {}).get('total_entities') > 0:
                    context_parts.append(f"Entities Found: {entities['summary']['total_entities']}")
                if entities.get('technical'):
                    tech_summary = []
                    for tech_cat, tech_items in entities['technical'].items():
                        if tech_items:
                            tech_summary.append(f"{tech_cat}: {len(tech_items)} items")
                    if tech_summary:
                        context_parts.append(f"Technical Categories: {', '.join(tech_summary)}")
                context_parts.append("")
            
            # Separate different types of content
            repositories = [item for item in relevant_items if item.get('repository_metadata')]
            multimodal_content = [item for item in relevant_items if item.get('embedding_type') in ['image', 'multimodal']]
            other_content = [item for item in relevant_items if not item.get('repository_metadata') and item.get('embedding_type', 'text') == 'text']
            
            # Add multimodal content first (most advanced search results)
            if multimodal_content:
                context_parts.append("\n## 🎯 Multimodal Content Matches")
                for item in multimodal_content:
                    context_parts.append(f"\n### {item['title']} ({item.get('embedding_type', 'unknown')} content)")
                    if item.get('similarity_score'):
                        context_parts.append(f"Similarity Score: {item['similarity_score']:.3f}")
                    if item['summary']:
                        context_parts.append(f"Summary: {item['summary']}")
                    if item['url']:
                        context_parts.append(f"Source: {item['url']}")
                    context_parts.append("")
            
            # Add repositories (prioritized)
            if repositories:
                context_parts.append("\n## 📦 Relevant Repositories")
                for repo in repositories:
                    repo_meta = repo['repository_metadata']
                    context_parts.append(f"\n### {repo_meta.get('owner', 'unknown')}/{repo_meta.get('repo_name', 'unknown')}")
                    
                    if repo_meta.get('description'):
                        context_parts.append(f"Description: {repo_meta['description']}")
                    
                    if repo_meta.get('tech_stack'):
                        context_parts.append(f"Tech Stack: {', '.join(repo_meta['tech_stack'])}")
                    
                    if repo_meta.get('use_case'):
                        context_parts.append(f"Use Case: {repo_meta['use_case']}")
                    
                    if repo_meta.get('category'):
                        context_parts.append(f"Category: {repo_meta['category']}")
                    
                    if repo_meta.get('difficulty'):
                        context_parts.append(f"Difficulty: {repo_meta['difficulty']}")
                    
                    if repo['url']:
                        context_parts.append(f"Repository URL: {repo['url']}")
                    
                    context_parts.append("")  # Empty line separator
                
                # Add other content
                if other_content:
                    context_parts.append("\n## 📄 Related Documentation & Content")
                    for item in other_content:
                        context_parts.append(f"\n### {item['title']}")
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
            system_prompt = f"""You are PRSNL's Second Brain AI assistant with advanced multimodal search capabilities. You have access to the user's personal knowledge base including text, images, code repositories, and multimodal content.

SEARCH CAPABILITIES:
• Multimodal semantic search across text, images, and combined content
• Advanced Named Entity Recognition (NER) for technical terms and concepts
• Cross-modal similarity matching using neural embeddings
• Repository-aware search with tech stack understanding

{knowledge_context}

Based on the above enhanced search results from the user's knowledge base, please provide a comprehensive response. When referencing content:
- Mention if results came from multimodal/image content vs text
- Include similarity scores when relevant (higher = more relevant)
- Reference technical entities and categories that were detected
- Suggest related searches if the multimodal search revealed interesting connections

If you need more specific information, you can suggest targeted searches using technical terms or concepts that were identified."""

            # Generate response using AI service
            messages = [{"role": "system", "content": system_prompt}] + conversation_history
            
            # Use LibreChat-specific model for this integration
            model_to_use = settings.AZURE_OPENAI_LIBRECHAT_DEPLOYMENT
            response = await ai_service.complete(
                prompt=query,
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

@observe(name="stream_chat_response")
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
    # Ensure response is not None or empty
    if not response:
        response = "I apologize, but I couldn't generate a response. Please try again."
    
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
            "prompt_tokens": len(" ".join([msg.content for msg in request.messages if msg.content]).split()),
            "completion_tokens": len(response.split()),
            "total_tokens": len(" ".join([msg.content for msg in request.messages if msg.content]).split()) + len(response.split())
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