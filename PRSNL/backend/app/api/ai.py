"""
AI API endpoints for PRSNL

Provides REST API access to AI services including:
- Content analysis with validation
- Tag generation
- Summary generation
- Transcription
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import logging

from app.services.unified_ai_service import unified_ai_service
from app.services.whisper_only_transcription import transcription_service, TranscriptionModel
from app.services.ai_validation_service import ai_validation_service, GUARDRAILS_AVAILABLE
from app.core.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


# Request/Response Models
class ContentAnalysisRequest(BaseModel):
    """Request model for content analysis."""
    content: str = Field(..., min_length=1, max_length=50000)
    enable_key_points: bool = True
    enable_entities: bool = True
    language: str = "en"


class TagGenerationRequest(BaseModel):
    """Request model for tag generation."""
    content: str = Field(..., min_length=1, max_length=50000)
    limit: int = Field(10, ge=1, le=20)
    language: str = "en"


class SummaryGenerationRequest(BaseModel):
    """Request model for summary generation."""
    content: str = Field(..., min_length=1, max_length=50000)
    summary_type: Literal["brief", "detailed", "key_points"] = "brief"
    language: str = "en"


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    audio_url: str = Field(..., description="URL or path to audio file")
    model: Optional[TranscriptionModel] = None
    language: str = "en"
    priority: Literal["speed", "balanced", "accuracy"] = "balanced"


# Endpoints
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "ok", "message": "test"}

@router.post("/analyze")
async def analyze_content(
    request: ContentAnalysisRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Analyze content using AI with automatic validation.
    
    Returns comprehensive analysis including:
    - Title, summary, and detailed summary
    - Category and tags
    - Key points and entities
    - Sentiment and difficulty level
    - Reading time estimate
    """
    try:
        user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Analyzing content for user {user_id}")
        
        result = await unified_ai_service.analyze_content(
            content=request.content,
            enable_key_points=request.enable_key_points,
            enable_entities=request.enable_entities
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Content analysis failed"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/tags")
async def generate_tags(
    request: TagGenerationRequest,
    current_user = Depends(get_current_user_optional)
) -> List[str]:
    """
    Generate tags for content with automatic validation.
    
    Returns list of lowercase, deduplicated tags.
    """
    try:
        user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Generating tags for user {user_id}")
        
        tags = await unified_ai_service.generate_tags(
            content=request.content,
            limit=request.limit
        )
        
        return tags
        
    except Exception as e:
        logger.error(f"Tag generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tag generation failed: {str(e)}"
        )


@router.post("/summary")
async def generate_summary(
    request: SummaryGenerationRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Generate summary of content.
    
    Summary types:
    - brief: 50-300 characters
    - detailed: 100-1000 characters
    - key_points: 3-5 bullet points
    """
    try:
        user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Generating {request.summary_type} summary for user {user_id}")
        
        result = await unified_ai_service.generate_summary(
            content=request.content,
            summary_type=request.summary_type
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Summary generation failed"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.post("/transcribe")
async def transcribe_audio(
    request: TranscriptionRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Transcribe audio using whisper.cpp.
    
    Priority options:
    - speed: Uses tiny model for fastest results
    - balanced: Uses base model (default)
    - accuracy: Uses small model for best accuracy
    """
    try:
        user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Transcribing audio for user {user_id} with priority: {request.priority}")
        
        if not transcription_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Transcription service not available"
            )
        
        # Handle URL vs local path
        audio_path = request.audio_url
        # In production, you'd download the URL or validate the path
        
        result = await transcription_service.transcribe_with_options(
            audio_path=audio_path,
            priority=request.priority
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Transcription failed"
            )
        
        return {
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "word_count": result.get("word_count", 0),
            "duration": result.get("duration", 0),
            "model_used": result.get("model_used", "unknown"),
            "service": "whisper.cpp"
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get("/models")
async def get_available_models(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get information about available transcription models."""
    try:
        models = await transcription_service.get_available_models()
        languages = await transcription_service.get_supported_languages()
        
        return {
            "models": models,
            "supported_languages": len(languages),
            "language_sample": languages[:10]
        }
        
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.get("/validation/status")
async def get_validation_status(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get AI validation service status."""
    try:
        return {
            "guardrails_available": GUARDRAILS_AVAILABLE,
            "validation_enabled": True,
            "supported_schemas": [
                "content_analysis",
                "summary",
                "tags"
            ],
            "fallback_available": True
        }
        
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation status: {str(e)}"
        )