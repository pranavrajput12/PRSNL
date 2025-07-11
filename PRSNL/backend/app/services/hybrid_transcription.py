"""
Hybrid Transcription Service for PRSNL

Combines Azure OpenAI Whisper (cloud) with Vosk (offline) transcription.
Automatically selects best service based on context, availability, and user preferences.
"""

import os
import logging
from typing import Optional, Dict, Any, Literal
from enum import Enum
import asyncio

from .vosk_transcription import VoskTranscriptionService, VOSK_AVAILABLE

# Import existing transcription service if available
try:
    from .transcription import TranscriptionService
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    TranscriptionService = None

logger = logging.getLogger(__name__)


class TranscriptionStrategy(str, Enum):
    """Transcription strategy options."""
    AUTO = "auto"           # Automatically choose best service
    PREFER_OFFLINE = "prefer_offline"  # Prefer Vosk, fallback to Whisper
    PREFER_CLOUD = "prefer_cloud"      # Prefer Whisper, fallback to Vosk
    OFFLINE_ONLY = "offline_only"      # Only use Vosk
    CLOUD_ONLY = "cloud_only"          # Only use Whisper
    PRIVACY_MODE = "privacy_mode"      # Force offline for sensitive content


class HybridTranscriptionService:
    """
    Hybrid transcription service that intelligently routes between
    Azure OpenAI Whisper and Vosk based on availability, performance, and privacy needs.
    """
    
    def __init__(self):
        self.vosk_service = VoskTranscriptionService() if VOSK_AVAILABLE else None
        self.whisper_service = TranscriptionService() if WHISPER_AVAILABLE else None
        
        # Service availability flags
        self.vosk_available = VOSK_AVAILABLE
        self.whisper_available = WHISPER_AVAILABLE
        
        # Rate limiting tracking for Whisper (3 requests per minute)
        self.whisper_request_times = []
        self.whisper_rate_limit = 3  # requests per minute
        
        logger.info(f"Hybrid Transcription Service initialized:")
        logger.info(f"  🎯 Vosk (offline): {'✅ Available' if self.vosk_available else '❌ Not available'}")
        logger.info(f"  ☁️ Whisper (cloud): {'✅ Available' if self.whisper_available else '❌ Not available'}")
    
    async def transcribe_audio(
        self,
        audio_path: str,
        strategy: TranscriptionStrategy = TranscriptionStrategy.AUTO,
        language: str = "en",
        privacy_sensitive: bool = False,
        user_preference: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using the optimal service based on strategy and context.
        
        Args:
            audio_path: Path to audio file
            strategy: Transcription strategy to use
            language: Language code for transcription
            privacy_sensitive: Whether content contains sensitive information
            user_preference: User's preferred transcription service
            
        Returns:
            Transcription result with service metadata
        """
        logger.info(f"🎙️ Starting hybrid transcription for {audio_path}")
        logger.info(f"  Strategy: {strategy}, Language: {language}, Privacy: {privacy_sensitive}")
        
        # Force privacy mode for sensitive content
        if privacy_sensitive:
            strategy = TranscriptionStrategy.PRIVACY_MODE
        
        # Determine which service to use
        primary_service, fallback_service = self._determine_services(strategy)
        
        # Try primary service
        if primary_service:
            logger.info(f"🚀 Attempting transcription with primary service: {primary_service}")
            result = await self._transcribe_with_service(
                primary_service, audio_path, language
            )
            
            if result:
                result['primary_service'] = primary_service
                result['fallback_used'] = False
                logger.info(f"✅ Transcription successful with {primary_service}")
                return result
            else:
                logger.warning(f"❌ Primary service {primary_service} failed")
        
        # Try fallback service
        if fallback_service:
            logger.info(f"🔄 Attempting transcription with fallback service: {fallback_service}")
            result = await self._transcribe_with_service(
                fallback_service, audio_path, language
            )
            
            if result:
                result['primary_service'] = primary_service
                result['fallback_used'] = True
                result['fallback_service'] = fallback_service
                logger.info(f"✅ Transcription successful with fallback {fallback_service}")
                return result
            else:
                logger.error(f"❌ Fallback service {fallback_service} also failed")
        
        logger.error("❌ All transcription services failed")
        return None
    
    def _determine_services(self, strategy: TranscriptionStrategy) -> tuple[Optional[str], Optional[str]]:
        """
        Determine primary and fallback services based on strategy.
        
        Returns:
            Tuple of (primary_service, fallback_service)
        """
        if strategy == TranscriptionStrategy.OFFLINE_ONLY:
            return ("vosk", None) if self.vosk_available else (None, None)
        
        elif strategy == TranscriptionStrategy.CLOUD_ONLY:
            return ("whisper", None) if self.whisper_available else (None, None)
        
        elif strategy == TranscriptionStrategy.PRIVACY_MODE:
            return ("vosk", None) if self.vosk_available else (None, None)
        
        elif strategy == TranscriptionStrategy.PREFER_OFFLINE:
            if self.vosk_available and self.whisper_available:
                return ("vosk", "whisper")
            elif self.vosk_available:
                return ("vosk", None)
            elif self.whisper_available:
                return ("whisper", None)
            else:
                return (None, None)
        
        elif strategy == TranscriptionStrategy.PREFER_CLOUD:
            if self._can_use_whisper() and self.whisper_available:
                if self.vosk_available:
                    return ("whisper", "vosk")
                else:
                    return ("whisper", None)
            elif self.vosk_available:
                return ("vosk", None)
            else:
                return (None, None)
        
        else:  # AUTO strategy
            # Smart routing based on current conditions
            whisper_available = self.whisper_available and self._can_use_whisper()
            
            if whisper_available and self.vosk_available:
                # Both available - prefer cloud for accuracy, offline as fallback
                return ("whisper", "vosk")
            elif whisper_available:
                return ("whisper", None)
            elif self.vosk_available:
                return ("vosk", None)
            else:
                return (None, None)
    
    def _can_use_whisper(self) -> bool:
        """Check if Whisper can be used based on rate limiting."""
        import time
        
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.whisper_request_times = [
            t for t in self.whisper_request_times 
            if current_time - t < 60
        ]
        
        # Check if we're under the rate limit
        return len(self.whisper_request_times) < self.whisper_rate_limit
    
    def _track_whisper_request(self):
        """Track a Whisper API request for rate limiting."""
        import time
        self.whisper_request_times.append(time.time())
    
    async def _transcribe_with_service(
        self, 
        service: str, 
        audio_path: str, 
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Transcribe with specific service."""
        try:
            if service == "vosk" and self.vosk_service:
                # Determine appropriate Vosk model based on language
                model_name = self._get_vosk_model_for_language(language)
                
                result = await self.vosk_service.transcribe_audio(
                    audio_path=audio_path,
                    model_name=model_name,
                    language=language
                )
                
                if result:
                    result['service_used'] = 'vosk'
                return result
                
            elif service == "whisper" and self.whisper_service:
                # Track request for rate limiting
                self._track_whisper_request()
                
                # Use existing Whisper service
                transcription_text = await self.whisper_service.transcribe_audio(audio_path)
                
                if transcription_text:
                    return {
                        'text': transcription_text,
                        'service_used': 'whisper',
                        'confidence': 0.95,  # Whisper typically has high confidence
                        'word_count': len(transcription_text.split()),
                        'language': language
                    }
                    
        except Exception as e:
            logger.error(f"Service {service} transcription failed: {e}")
        
        return None
    
    def _get_vosk_model_for_language(self, language: str) -> str:
        """Get appropriate Vosk model for language."""
        language_models = {
            "en": "en-us-small",
            "es": "en-us-small",  # Use English model as fallback
            "fr": "en-us-small",
            "de": "en-us-small",
            "ru": "en-us-small",
            "zh": "en-us-small",
            "ja": "en-us-small",
            "ko": "en-us-small",
            "hi": "en-us-small",
            "ar": "en-us-small"
        }
        return language_models.get(language, "en-us-small")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all transcription services."""
        status = {
            'vosk': {
                'available': self.vosk_available,
                'status': 'ready' if self.vosk_available else 'unavailable'
            },
            'whisper': {
                'available': self.whisper_available,
                'status': 'ready' if self.whisper_available else 'unavailable',
                'rate_limited': not self._can_use_whisper() if self.whisper_available else False,
                'requests_in_last_minute': len(self.whisper_request_times)
            },
            'hybrid': {
                'ready': self.vosk_available or self.whisper_available,
                'preferred_strategy': self._get_recommended_strategy()
            }
        }
        
        # Add Vosk model information if available
        if self.vosk_available and self.vosk_service:
            try:
                model_info = await self.vosk_service.get_model_info()
                status['vosk']['model_info'] = model_info
            except:
                pass
        
        return status
    
    def _get_recommended_strategy(self) -> str:
        """Get recommended strategy based on current service availability."""
        if not self.whisper_available and not self.vosk_available:
            return "none_available"
        elif not self.whisper_available:
            return "offline_only"
        elif not self.vosk_available:
            return "cloud_only"
        elif not self._can_use_whisper():
            return "prefer_offline"
        else:
            return "auto"
    
    async def download_vosk_models(self, models: list[str] = None) -> Dict[str, bool]:
        """Download Vosk models for offline transcription."""
        if not self.vosk_available or not self.vosk_service:
            return {}
        
        if models is None:
            models = ["en-us-small"]  # Default model
        
        results = {}
        for model in models:
            logger.info(f"📥 Downloading Vosk model: {model}")
            success = await self.vosk_service.ensure_model_available(model)
            results[model] = success
            
        return results
    
    async def cleanup_resources(self):
        """Cleanup resources and cached models."""
        if self.vosk_service:
            # Clear model cache to free memory
            self.vosk_service._models_cache.clear()
            logger.info("🧹 Vosk model cache cleared")


# Global instance for use across the application
hybrid_transcription_service = HybridTranscriptionService()