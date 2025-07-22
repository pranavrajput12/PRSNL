"""
Voice Chat API - WebSocket endpoints for real-time voice communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging
import asyncio
import base64
import io

from app.core.auth import get_current_user_ws_optional
from app.services.voice_service import get_voice_service
from app.db.database import get_db_connection
from app.core.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Store active voice connections
active_connections: Dict[str, WebSocket] = {}


class VoiceConnectionManager:
    """Manage voice WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, bytes] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.audio_buffers[user_id] = b""
        logger.info(f"Voice connection established for user: {user_id}")
        
    def disconnect(self, user_id: str):
        """Remove connection and clean up"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.audio_buffers:
            del self.audio_buffers[user_id]
        logger.info(f"Voice connection closed for user: {user_id}")
        
    async def send_json(self, user_id: str, data: dict):
        """Send JSON data to specific user"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(data)
            
    async def send_bytes(self, user_id: str, data: bytes):
        """Send binary data to specific user"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_bytes(data)
            
    def add_audio_chunk(self, user_id: str, chunk: bytes):
        """Add audio chunk to buffer"""
        if user_id in self.audio_buffers:
            self.audio_buffers[user_id] += chunk
            
    def get_and_clear_audio_buffer(self, user_id: str) -> bytes:
        """Get complete audio buffer and clear it"""
        audio = self.audio_buffers.get(user_id, b"")
        self.audio_buffers[user_id] = b""
        return audio


# Create connection manager instance
voice_manager = VoiceConnectionManager()


@router.websocket("/ws")
async def voice_chat_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Depends(get_current_user_ws_optional)
):
    """
    WebSocket endpoint for real-time voice chat
    
    Protocol:
    - Client sends audio chunks as binary data
    - Client sends {"type": "end_recording"} to process audio
    - Server responds with transcription and audio response
    """
    
    # Use anonymous ID if not authenticated
    if not user_id:
        user_id = f"anonymous_{id(websocket)}"
    
    await voice_manager.connect(websocket, user_id)
    voice_service = get_voice_service()
    
    try:
        while True:
            # Handle both binary and text messages
            message = await websocket.receive()
            
            if "bytes" in message:
                # Audio chunk received
                audio_chunk = message["bytes"]
                voice_manager.add_audio_chunk(user_id, audio_chunk)
                
                # Send acknowledgment
                await voice_manager.send_json(user_id, {
                    "type": "chunk_received",
                    "size": len(audio_chunk)
                })
                
            elif "text" in message:
                # Control message received
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == "end_recording":
                        # Process complete audio
                        audio_buffer = voice_manager.get_and_clear_audio_buffer(user_id)
                        
                        if audio_buffer:
                            # Send processing status
                            await voice_manager.send_json(user_id, {
                                "type": "processing",
                                "status": "transcribing"
                            })
                            
                            # Process voice message
                            try:
                                result = await voice_service.process_voice_message(
                                    audio_buffer,
                                    user_id
                                )
                                
                                # Send transcription with all data
                                await voice_manager.send_json(user_id, {
                                    "type": "transcription",
                                    "data": {
                                        "user_text": result["user_text"],
                                        "ai_text": result["ai_text"],
                                        "personalized_text": result["personalized_text"],
                                        "mood": result["mood"]
                                    }
                                })
                                
                                # Send audio response
                                await voice_manager.send_json(user_id, {
                                    "type": "audio_response",
                                    "format": result["audio_format"],
                                    "data": base64.b64encode(result["audio_data"]).decode()
                                })
                                
                                # Log interaction for analytics
                                await log_voice_interaction(user_id, result)
                                
                            except Exception as e:
                                logger.error(f"Error processing voice: {e}")
                                await voice_manager.send_json(user_id, {
                                    "type": "error",
                                    "message": "Failed to process voice message"
                                })
                    
                    elif msg_type == "ping":
                        # Keepalive
                        await voice_manager.send_json(user_id, {"type": "pong"})
                        
                    elif msg_type == "set_voice":
                        # Change voice settings
                        gender = data.get("gender", "female")
                        voice_service.set_voice_gender(gender)
                        await voice_manager.send_json(user_id, {
                            "type": "voice_changed",
                            "gender": gender
                        })
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    await voice_manager.send_json(user_id, {
                        "type": "error",
                        "message": "Invalid message format"
                    })
                    
    except WebSocketDisconnect:
        voice_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        voice_manager.disconnect(user_id)


async def log_voice_interaction(user_id: str, result: Dict[str, Any]):
    """Log voice interaction for analytics"""
    try:
        async for conn in get_db_connection():
            await conn.execute("""
                INSERT INTO voice_interactions 
                (user_id, user_text, ai_response, mood, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, 
            user_id if user_id.startswith("user_") else None,  # Only log real users
            result["user_text"],
            result["ai_text"],
            result["mood"]
            )
    except Exception as e:
        # Don't fail if logging fails
        logger.warning(f"Failed to log voice interaction: {e}")


@router.get("/health")
async def voice_health_check():
    """Check if voice service is healthy - no auth required"""
    try:
        voice_service = get_voice_service()
        
        # Check if Whisper model is loaded
        if not hasattr(voice_service, 'whisper_model'):
            raise HTTPException(status_code=503, detail="Whisper model not loaded")
            
        return {
            "status": "healthy",
            "whisper_model": "loaded",
            "personality": "Cortex",
            "voices_available": list(voice_service.VOICE_OPTIONS.keys())
        }
    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


class VoiceTestRequest(BaseModel):
    """Voice test request model"""
    text: str = "Hello! This is a test of the voice settings."
    settings: Optional[Dict[str, Any]] = None


@router.post("/test") 
async def test_voice_processing(
    request: VoiceTestRequest,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Test voice settings with custom text and configuration"""
    try:
        voice_service = get_voice_service()
        
        # Apply temporary settings if provided
        if request.settings:
            # Save current settings
            original_gender = voice_service.voice_gender
            original_use_crew = voice_service.use_crew
            original_tts_backend = voice_service.tts_manager.primary_backend
            
            try:
                # Apply test settings
                if "defaultGender" in request.settings:
                    voice_service.set_voice_gender(request.settings["defaultGender"])
                    
                if "useCrewAI" in request.settings:
                    voice_service.use_crew = request.settings["useCrewAI"]
                    
                if "ttsEngine" in request.settings:
                    from app.services.tts_manager import TTSManager
                    voice_service.tts_manager = TTSManager(primary_backend=request.settings["ttsEngine"])
                
                # Get Cortex response
                context = {"mood": "primary", "first_interaction": True}
                personalized = voice_service.personality.add_personality(request.text, context)
                
                # Generate speech with test settings
                audio_data = await voice_service.text_to_speech(personalized, context)
                
                # Restore original settings
                voice_service.set_voice_gender(original_gender)
                voice_service.use_crew = original_use_crew
                voice_service.tts_manager = TTSManager(primary_backend=original_tts_backend)
                
            except Exception as e:
                # Restore settings on error
                voice_service.set_voice_gender(original_gender)
                voice_service.use_crew = original_use_crew
                voice_service.tts_manager = TTSManager(primary_backend=original_tts_backend)
                raise e
        else:
            # Use current settings
            context = {"mood": "primary", "first_interaction": True}
            personalized = voice_service.personality.add_personality(request.text, context)
            audio_data = await voice_service.text_to_speech(personalized, context)
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=voice_test.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"Voice test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))