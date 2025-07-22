"""
Settings API endpoints
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.db.database import get_db_connection
from app.config import settings
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class VoiceSettings(BaseModel):
    """Voice settings model"""
    ttsEngine: str = "edge-tts"
    sttModel: str = "small"
    useCrewAI: bool = True
    enableStreaming: bool = False
    defaultGender: str = "female"
    emotionStrength: float = 1.2


@router.get("/settings/voice")
async def get_voice_settings(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get voice settings for the current user"""
    try:
        user_id = current_user.get("user_id")
        
        async with get_db_connection() as conn:
            # Try to get user-specific settings
            user_settings = await conn.fetchrow(
                """
                SELECT settings 
                FROM user_profiles 
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Start with system defaults
            voice_settings = {
                "ttsEngine": settings.VOICE_TTS_ENGINE,
                "sttModel": settings.VOICE_STT_MODEL,
                "useCrewAI": settings.VOICE_USE_CREWAI,
                "enableStreaming": settings.VOICE_ENABLE_STREAMING,
                "defaultGender": settings.VOICE_DEFAULT_GENDER,
                "emotionStrength": settings.VOICE_EMOTION_STRENGTH
            }
            
            # Override with user settings if available
            if user_settings and user_settings["settings"]:
                user_voice_settings = user_settings["settings"].get("voice", {})
                voice_settings.update(user_voice_settings)
                
        return voice_settings
        
    except Exception as e:
        logger.error(f"Error getting voice settings: {e}")
        # Return defaults on error
        return {
            "ttsEngine": settings.VOICE_TTS_ENGINE,
            "sttModel": settings.VOICE_STT_MODEL,
            "useCrewAI": settings.VOICE_USE_CREWAI,
            "enableStreaming": settings.VOICE_ENABLE_STREAMING,
            "defaultGender": settings.VOICE_DEFAULT_GENDER,
            "emotionStrength": settings.VOICE_EMOTION_STRENGTH
        }


@router.put("/settings/voice")
async def update_voice_settings(
    voice_settings: VoiceSettings,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update voice settings for the current user"""
    try:
        user_id = current_user.get("user_id")
        
        async with get_db_connection() as conn:
            # Get existing user settings
            user_profile = await conn.fetchrow(
                """
                SELECT settings 
                FROM user_profiles 
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Merge voice settings into user settings
            if user_profile and user_profile["settings"]:
                current_settings = user_profile["settings"]
            else:
                current_settings = {}
                
            current_settings["voice"] = voice_settings.model_dump()
            
            # Update user profile
            await conn.execute(
                """
                UPDATE user_profiles 
                SET settings = $2, updated_at = NOW()
                WHERE user_id = $1
                """,
                user_id,
                current_settings
            )
            
            # Update the global voice service with new settings
            from app.services.voice_service import get_voice_service
            voice_service = get_voice_service()
            
            # Apply settings to voice service
            if voice_settings.defaultGender != voice_service.voice_gender:
                voice_service.set_voice_gender(voice_settings.defaultGender)
            
            # Update other settings in voice service
            voice_service.use_crew = voice_settings.useCrewAI
            
            # Update TTS manager with new engine
            if voice_settings.ttsEngine != voice_service.tts_manager.primary_backend:
                from app.services.tts_manager import TTSManager
                voice_service.tts_manager = TTSManager(primary_backend=voice_settings.ttsEngine)
                
            logger.info(f"Voice settings updated for user {user_id}")
            
            return {"status": "success", "settings": voice_settings.model_dump()}
            
    except Exception as e:
        logger.error(f"Error updating voice settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))