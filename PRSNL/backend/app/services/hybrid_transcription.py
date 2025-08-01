"""
Hybrid Transcription Service for PRSNL

Combines Azure OpenAI Whisper (cloud) with whisper.cpp (offline) transcription.
Automatically selects best service based on context, availability, and user preferences.
"""

import asyncio
import logging
import os
from enum import Enum
from typing import Any, Dict, Literal, Optional

# Import whisper.cpp for high-quality offline transcription
try:
    from .whisper_cpp_transcription import whisper_cpp_service as WhisperCppTranscriptionService
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    WhisperCppTranscriptionService = None

# Import existing transcription service if available
try:
    from .transcription import TranscriptionService
    WHISPER_CLOUD_AVAILABLE = True
except ImportError:
    WHISPER_CLOUD_AVAILABLE = False
    TranscriptionService = None

logger = logging.getLogger(__name__)


class TranscriptionStrategy(str, Enum):
    """Transcription strategy options."""
    AUTO = "auto"           # Automatically choose best service
    PREFER_OFFLINE = "prefer_offline"  # Prefer whisper.cpp, fallback to cloud
    PREFER_CLOUD = "prefer_cloud"      # Prefer cloud Whisper, fallback to whisper.cpp
    OFFLINE_ONLY = "offline_only"      # Only use whisper.cpp
    CLOUD_ONLY = "cloud_only"          # Only use cloud Whisper
    PRIVACY_MODE = "privacy_mode"      # Force offline for sensitive content


class HybridTranscriptionService:
    """
    Hybrid transcription service that intelligently routes between
    Azure OpenAI Whisper and whisper.cpp based on availability, performance, and privacy needs.
    """
    
    def __init__(self):
        self.whisper_cpp_service = WhisperCppTranscriptionService if WHISPER_CPP_AVAILABLE else None
        self.whisper_cloud_service = TranscriptionService() if WHISPER_CLOUD_AVAILABLE else None
        
        # Service availability flags
        self.whisper_cpp_available = WHISPER_CPP_AVAILABLE
        self.whisper_cloud_available = WHISPER_CLOUD_AVAILABLE
        
        # Rate limiting tracking for cloud Whisper (3 requests per minute)
        self.whisper_cloud_request_times = []
        self.whisper_cloud_rate_limit = 3  # requests per minute
        
        logger.info(f"Hybrid Transcription Service initialized:")
        logger.info(f"  🚀 whisper.cpp (offline): {'✅ Available' if self.whisper_cpp_available else '❌ Not available'}")
        logger.info(f"  ☁️ Whisper (cloud): {'✅ Available' if self.whisper_cloud_available else '❌ Not available'}")
    
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
            # Use whisper.cpp for high-quality offline transcription
            if self.whisper_cpp_available:
                return ("whisper_cpp", None)
            else:
                return (None, None)
        
        elif strategy == TranscriptionStrategy.CLOUD_ONLY:
            return ("whisper_cloud", None) if self.whisper_cloud_available else (None, None)
        
        elif strategy == TranscriptionStrategy.PRIVACY_MODE:
            # Force offline for privacy - use whisper.cpp
            if self.whisper_cpp_available:
                return ("whisper_cpp", None)
            else:
                return (None, None)
        
        elif strategy == TranscriptionStrategy.PREFER_OFFLINE:
            # Prefer offline services, use cloud as fallback
            if self.whisper_cpp_available:
                if self.whisper_cloud_available:
                    return ("whisper_cpp", "whisper_cloud")
                else:
                    return ("whisper_cpp", None)
            elif self.whisper_cloud_available:
                return ("whisper_cloud", None)
            else:
                return (None, None)
        
        elif strategy == TranscriptionStrategy.PREFER_CLOUD:
            if self._can_use_whisper_cloud() and self.whisper_cloud_available:
                # Cloud available - use whisper.cpp as fallback
                if self.whisper_cpp_available:
                    return ("whisper_cloud", "whisper_cpp")
                else:
                    return ("whisper_cloud", None)
            # Cloud not available, fall back to offline
            elif self.whisper_cpp_available:
                return ("whisper_cpp", None)
            else:
                return (None, None)
        
        else:  # AUTO strategy
            # Smart routing based on current conditions
            cloud_available = self.whisper_cloud_available and self._can_use_whisper_cloud()
            
            if cloud_available and self.whisper_cpp_available:
                # Both available - prefer cloud for latest features, whisper.cpp as fallback
                return ("whisper_cloud", "whisper_cpp")
            elif cloud_available:
                return ("whisper_cloud", None)
            elif self.whisper_cpp_available:
                return ("whisper_cpp", None)
            else:
                return (None, None)
    
    def _can_use_whisper_cloud(self) -> bool:
        """Check if cloud Whisper can be used based on rate limiting."""
        import time
        
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.whisper_cloud_request_times = [
            t for t in self.whisper_cloud_request_times 
            if current_time - t < 60
        ]
        
        # Check if we're under the rate limit
        return len(self.whisper_cloud_request_times) < self.whisper_cloud_rate_limit
    
    def _track_whisper_cloud_request(self):
        """Track a cloud Whisper API request for rate limiting."""
        import time
        self.whisper_cloud_request_times.append(time.time())
    
    async def _transcribe_with_service(
        self, 
        service: str, 
        audio_path: str, 
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Transcribe with specific service."""
        try:
            if service == "whisper_cpp" and self.whisper_cpp_service:
                # Use whisper.cpp for high-accuracy offline transcription
                model_name = self._get_whisper_cpp_model_for_context(audio_path)
                
                result = await self.whisper_cpp_service.transcribe_audio(
                    audio_path=audio_path,
                    model_name=model_name,
                    language=language,
                    word_timestamps=True
                )
                
                if result:
                    result['service_used'] = 'whisper.cpp'
                return result
                
            elif service == "whisper_cloud" and self.whisper_cloud_service:
                # Track request for rate limiting
                self._track_whisper_cloud_request()
                
                # Use cloud Whisper service
                transcription_text = await self.whisper_cloud_service.transcribe_audio(audio_path)
                
                if transcription_text:
                    return {
                        'text': transcription_text,
                        'service_used': 'whisper_cloud',
                        'confidence': 0.95,  # Cloud Whisper typically has high confidence
                        'word_count': len(transcription_text.split()),
                        'language': language
                    }
                    
        except Exception as e:
            logger.error(f"Service {service} transcription failed: {e}")
        
        return None
    
    def _get_whisper_cpp_model_for_context(self, audio_path: str) -> str:
        """
        Select appropriate whisper.cpp model based on file size and context.
        
        Returns model name: tiny, base, small, medium, or large
        """
        try:
            # Get file size in MB
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            
            # Select model based on file size and available resources
            if file_size_mb < 5:
                # Small files - use base for good balance
                return "base"
            elif file_size_mb < 20:
                # Medium files - use small for better accuracy
                return "small"
            elif file_size_mb < 50:
                # Larger files - use medium if needed
                return "medium"
            else:
                # Very large files - stick with small for performance
                return "small"
                
        except Exception:
            # Default to base model on any error
            return "base"
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all transcription services."""
        status = {
            'whisper_cpp': {
                'available': self.whisper_cpp_available,
                'status': 'ready' if self.whisper_cpp_available else 'unavailable',
                'accuracy': 'high',
                'speed': 'fast',
                'privacy': 'fully offline'
            },
            'whisper_cloud': {
                'available': self.whisper_cloud_available,
                'status': 'ready' if self.whisper_cloud_available else 'unavailable',
                'rate_limited': not self._can_use_whisper_cloud() if self.whisper_cloud_available else False,
                'requests_in_last_minute': len(self.whisper_cloud_request_times),
                'accuracy': 'highest',
                'speed': 'varies',
                'privacy': 'cloud-based'
            },
            'hybrid': {
                'ready': self.whisper_cloud_available or self.whisper_cpp_available,
                'preferred_strategy': self._get_recommended_strategy()
            }
        }
        
        # Add whisper.cpp model information if available
        if self.whisper_cpp_available and self.whisper_cpp_service:
            try:
                model_info = await self.whisper_cpp_service.get_model_info()
                status['whisper_cpp']['model_info'] = model_info
            except:
                pass
        
        return status
    
    def _get_recommended_strategy(self) -> str:
        """Get recommended strategy based on current service availability."""
        offline_available = self.whisper_cpp_available
        
        if not self.whisper_cloud_available and not offline_available:
            return "none_available"
        elif not self.whisper_cloud_available:
            return "offline_only"
        elif not offline_available:
            return "cloud_only"
        elif not self._can_use_whisper_cloud():
            return "prefer_offline"
        else:
            return "auto"
    
    async def download_whisper_models(self, models: list[str] = None) -> Dict[str, bool]:
        """Download whisper.cpp models for offline transcription."""
        if not self.whisper_cpp_available or not self.whisper_cpp_service:
            return {}
        
        if models is None:
            models = ["base"]  # Default model with good balance
        
        results = {}
        for model in models:
            logger.info(f"📥 Downloading whisper.cpp model: {model}")
            success = await self.whisper_cpp_service.ensure_model_available(model)
            results[model] = success
            
        return results
    
    async def cleanup_resources(self):
        """Cleanup resources and cached models."""
        if self.whisper_cpp_service:
            # Clear model cache to free memory
            self.whisper_cpp_service.cleanup()
            logger.info("🧹 Whisper.cpp model cache cleared")


# Global instance for use across the application
hybrid_transcription_service = HybridTranscriptionService()