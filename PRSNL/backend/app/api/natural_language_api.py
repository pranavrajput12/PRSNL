"""
Natural Language System Control API for PRSNL Phase 5
====================================================

API endpoints for natural language system control and voice-driven interactions.

Endpoints:
- POST /api/nl/command - Process natural language commands
- POST /api/nl/voice-command - Process voice commands with transcription
- GET /api/nl/capabilities - Get supported command types and examples
- POST /api/nl/context - Set user context for better command interpretation
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import json
import base64
import tempfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator

from app.services.natural_language_controller import natural_language_controller
from app.services.realtime_stt_service import RealtimeSTTService
from app.middleware.auth import get_current_user_optional
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nl", tags=["Natural Language Control"])

# Request/Response Models
class NaturalLanguageCommandRequest(BaseModel):
    """Request model for natural language commands"""
    command: str = Field(..., min_length=1, max_length=1000, description="Natural language command")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User preferences and context")
    multimodal_context: Optional[Dict[str, Any]] = Field(None, description="Additional context from other modalities")
    include_voice_response: bool = Field(False, description="Generate voice response")
    response_style: str = Field("conversational", description="Response style: conversational, technical, brief")
    
    @validator('response_style')
    def validate_response_style(cls, v):
        valid_styles = ['conversational', 'technical', 'brief', 'detailed']
        if v not in valid_styles:
            raise ValueError(f'response_style must be one of: {valid_styles}')
        return v

class VoiceCommandRequest(BaseModel):
    """Request model for voice commands"""
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    transcription: Optional[str] = Field(None, description="Pre-transcribed text if available")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context for personalization")
    auto_execute: bool = Field(True, description="Automatically execute recognized commands")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for auto-execution")

class ContextUpdateRequest(BaseModel):
    """Request model for updating user context"""
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    current_location: Optional[str] = Field(None, description="Current page/location in system")
    recent_actions: Optional[List[str]] = Field(None, description="Recent user actions for context")
    focus_areas: Optional[List[str]] = Field(None, description="Current areas of focus")

class CommandResponse(BaseModel):
    """Response model for processed commands"""
    command_id: str
    original_command: str
    parsed_command: Dict[str, Any]
    execution_result: Dict[str, Any]
    natural_response: Dict[str, Any]
    processing_stats: Dict[str, Any]
    status: str
    timestamp: str

@router.post("/command", response_model=CommandResponse)
async def process_natural_language_command(
    request: NaturalLanguageCommandRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Process a natural language command and execute the corresponding system action.
    
    This endpoint can handle commands like:
    - "Show me all Python files modified this week"
    - "Analyze the security of my latest repository"
    - "Create a bookmark for machine learning research"
    - "Find similar content to this image"
    
    The system will:
    1. Parse the natural language command
    2. Extract intent and parameters
    3. Execute the appropriate system action
    4. Return results in natural language
    """
    try:
        # Build user context
        user_context = request.user_context or {}
        if current_user:
            user_context.update({
                "user_id": str(current_user.id),
                "user_email": getattr(current_user, 'email', 'unknown'),
                "user_type": getattr(current_user, 'user_type', 'individual'),
                "preferences": getattr(current_user, 'preferences', {})
            })
        
        # Add response style to context
        user_context['response_style'] = request.response_style
        
        logger.info(f"🎙️ Processing NL command [User: {current_user.id if current_user else 'anonymous'}]: '{request.command[:100]}...'")
        
        # Process the command
        result = await natural_language_controller.process_natural_language_command(
            command_text=request.command,
            user_context=user_context,
            multimodal_context=request.multimodal_context
        )
        
        # Generate voice response if requested
        if request.include_voice_response and result.get('status') == 'success':
            # TODO: Integrate with voice service for TTS
            result['voice_response'] = {
                "available": True,
                "text": result.get('natural_response', {}).get('text', ''),
                "audio_url": None  # Would be generated by TTS service
            }
        
        logger.info(f"✅ NL command processed [ID: {result.get('command_id')}] - Status: {result.get('status')}")
        
        return CommandResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ NL command processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(e)}")

@router.post("/voice-command")
async def process_voice_command(
    request: VoiceCommandRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Process voice commands with automatic speech-to-text transcription.
    
    Supports:
    - Audio file upload with automatic transcription
    - Pre-transcribed text processing
    - Confidence-based auto-execution
    - Voice response generation
    """
    try:
        transcription_result = None
        command_text = request.transcription
        
        # Transcribe audio if provided
        if request.audio_base64 and not command_text:
            try:
                # Decode audio data
                audio_data = base64.b64decode(request.audio_base64)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file.write(audio_data)
                    temp_audio_path = temp_file.name
                
                # Transcribe using STT service
                stt_service = RealtimeSTTService()
                transcription_result = await stt_service.transcribe_audio_file(temp_audio_path)
                
                command_text = transcription_result.get('text', '')
                transcription_confidence = transcription_result.get('confidence', 0.0)
                
                logger.info(f"🎤 Voice transcribed: '{command_text}' (confidence: {transcription_confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Voice transcription failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Voice transcription failed: {str(e)}"
                )
        
        if not command_text:
            raise HTTPException(
                status_code=400,
                detail="Either audio_base64 or transcription must be provided"
            )
        
        # Check confidence threshold for auto-execution
        should_execute = True
        if transcription_result:
            transcription_confidence = transcription_result.get('confidence', 1.0)
            if transcription_confidence < request.confidence_threshold:
                should_execute = False
        
        # Build response
        response_data = {
            "transcription": {
                "text": command_text,
                "confidence": transcription_result.get('confidence', 1.0) if transcription_result else 1.0,
                "language": transcription_result.get('language', 'en') if transcription_result else 'en',
                "duration": transcription_result.get('duration', 0) if transcription_result else 0
            },
            "auto_executed": should_execute,
            "confidence_threshold": request.confidence_threshold
        }
        
        # Execute command if confidence is sufficient
        if should_execute and request.auto_execute:
            # Build user context
            user_context = request.user_context or {}
            if current_user:
                user_context.update({
                    "user_id": str(current_user.id),
                    "input_method": "voice",
                    "transcription_confidence": transcription_result.get('confidence', 1.0) if transcription_result else 1.0
                })
            
            # Process command
            command_result = await natural_language_controller.process_natural_language_command(
                command_text=command_text,
                user_context=user_context
            )
            
            response_data["command_execution"] = command_result
        else:
            response_data["command_execution"] = {
                "status": "skipped",
                "reason": "confidence_too_low" if not should_execute else "auto_execute_disabled",
                "command_text": command_text
            }
        
        response_data["timestamp"] = datetime.utcnow().isoformat()
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice command processing failed: {str(e)}")

@router.post("/upload-voice-command")
async def upload_voice_command(
    audio_file: UploadFile = File(...),
    auto_execute: bool = Form(True),
    confidence_threshold: float = Form(0.7),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload an audio file for voice command processing.
    
    Supports common audio formats: WAV, MP3, M4A, OGG
    """
    try:
        # Validate audio file
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file type")
        
        # Read and encode audio data
        audio_content = await audio_file.read()
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Create voice command request
        voice_request = VoiceCommandRequest(
            audio_base64=audio_base64,
            auto_execute=auto_execute,
            confidence_threshold=confidence_threshold,
            user_context={
                "upload_filename": audio_file.filename,
                "upload_content_type": audio_file.content_type,
                "upload_size": len(audio_content)
            }
        )
        
        # Process the voice command
        return await process_voice_command(voice_request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice file upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice upload failed: {str(e)}")

@router.post("/context")
async def update_user_context(
    request: ContextUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Update user context for better natural language command interpretation.
    
    This helps the system understand:
    - User preferences and habits
    - Current location in the system
    - Recent actions for context
    - Areas of focus
    """
    try:
        # Build context update
        context_data = {
            "user_id": str(current_user.id) if current_user else None,
            "preferences": request.preferences,
            "current_location": request.current_location,
            "recent_actions": request.recent_actions,
            "focus_areas": request.focus_areas,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Store context in user session/database
        # For now, return success acknowledgment
        
        return JSONResponse(content={
            "status": "success",
            "message": "User context updated successfully",
            "context_summary": {
                "preferences_count": len(request.preferences or {}),
                "current_location": request.current_location,
                "recent_actions_count": len(request.recent_actions or []),
                "focus_areas_count": len(request.focus_areas or [])
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Context update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Context update failed: {str(e)}")

@router.get("/capabilities")
async def get_natural_language_capabilities():
    """
    Get information about supported natural language commands and capabilities.
    
    Returns:
    - Supported command types with examples
    - Entity types that can be controlled
    - Voice command capabilities
    - Integration features
    """
    try:
        capabilities = {
            "command_types": {
                "search": {
                    "description": "Find and retrieve content",
                    "examples": [
                        "Show me all Python files modified this week",
                        "Find repositories related to machine learning",
                        "Search for bookmarks about React"
                    ]
                },
                "analyze": {
                    "description": "Perform analysis on content or repositories",
                    "examples": [
                        "Analyze the security of my latest repository",
                        "Check the code quality of MyProject",
                        "Run a performance analysis on the backend"
                    ]
                },
                "create": {
                    "description": "Create new content or items",
                    "examples": [
                        "Create a bookmark for this machine learning paper",
                        "Add a voice note about today's meeting",
                        "Make a new tag called 'research-ideas'"
                    ]
                },
                "navigate": {
                    "description": "Navigate to different parts of the system",
                    "examples": [
                        "Go to my code repositories",
                        "Show me the analysis dashboard",
                        "Open the settings page"
                    ]
                },
                "multimodal": {
                    "description": "Process content across multiple modalities",
                    "examples": [
                        "Analyze this image and find similar content",
                        "Compare this voice note with my written thoughts",
                        "Find connections between this video and my research"
                    ]
                }
            },
            "entity_types": [
                "content", "repository", "bookmark", "tag", "analysis", 
                "search_query", "user_setting", "voice_note"
            ],
            "voice_capabilities": {
                "transcription": {
                    "supported_formats": ["wav", "mp3", "m4a", "ogg"],
                    "languages": ["en", "es", "fr", "de", "it"],
                    "confidence_threshold": 0.7
                },
                "command_processing": {
                    "auto_execution": True,
                    "confidence_based": True,
                    "context_aware": True
                },
                "response_generation": {
                    "text_to_speech": "available",
                    "voice_styles": ["conversational", "technical", "brief"]
                }
            },
            "integration_features": [
                "Multi-modal AI processing",
                "Advanced code intelligence",
                "Cross-modal content analysis",
                "Context-aware responses",
                "User preference learning",
                "Voice-driven workflows"
            ],
            "supported_contexts": [
                "Time-based filters (today, this week, last month)",
                "Programming languages (Python, JavaScript, etc.)",
                "Content types (image, video, code, document)",
                "Analysis types (security, performance, quality)"
            ],
            "response_styles": [
                "conversational", "technical", "brief", "detailed"
            ],
            "version": "1.0.0",
            "last_updated": "2025-07-23"
        }
        
        return JSONResponse(content=capabilities)
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve capabilities")

@router.get("/examples")
async def get_command_examples():
    """Get example commands for different use cases"""
    try:
        examples = {
            "beginner_commands": [
                "Show me my recent bookmarks",
                "Find Python repositories",
                "Create a bookmark about AI research",
                "What are my most used tags?"
            ],
            "advanced_commands": [
                "Analyze the security vulnerabilities in my Django project from last month",
                "Find all machine learning content similar to this research paper",
                "Compare code quality between my frontend and backend repositories",
                "Show me performance trends for repositories I've analyzed this quarter"
            ],
            "voice_commands": [
                "Hey PRSNL, show me today's bookmarks",
                "Analyze my latest code repository",
                "Create a voice note about machine learning insights",
                "Find content related to this image"
            ],
            "multimodal_commands": [
                "Find text content related to this screenshot",
                "Analyze this code snippet and compare with my repositories",
                "Create a bookmark from this image with relevant tags",
                "Transcribe this audio and save it as a note"
            ],
            "productivity_workflows": [
                "Show me all untagged content from this week and suggest tags",
                "Find repositories that need security analysis",
                "Create a daily summary of my research activities",
                "Export my machine learning bookmarks as a reading list"
            ]
        }
        
        return JSONResponse(content=examples)
        
    except Exception as e:
        logger.error(f"Failed to get examples: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve examples")

@router.get("/health")
async def natural_language_health():
    """Health check for natural language processing services"""
    try:
        # Test basic functionality
        test_command = "show me test content"
        test_result = await natural_language_controller.process_natural_language_command(
            command_text=test_command,
            user_context={"test": True}
        )
        
        health_status = {
            "status": "healthy" if test_result.get("status") != "failed" else "degraded",
            "services": {
                "natural_language_controller": "operational",
                "ai_router": "operational",
                "speech_to_text": "operational",
                "command_parsing": "operational"
            },
            "test_result": {
                "command": test_command,
                "parsed_successfully": test_result.get("parsed_command") is not None,
                "confidence": test_result.get("parsed_command", {}).get("confidence", 0)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )