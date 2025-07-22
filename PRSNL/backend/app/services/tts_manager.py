"""
TTS Manager - Abstraction layer for multiple Text-to-Speech backends

Supports:
- Chatterbox TTS (primary) - Modern, emotion-aware TTS
- Edge-TTS (fallback) - Microsoft Edge's TTS
- Future: XTTS, Parler-TTS, etc.
"""

import logging
import tempfile
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class TTSBackend(ABC):
    """Abstract base class for TTS backends"""
    
    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        voice: str,
        **kwargs
    ) -> bytes:
        """Synthesize speech from text"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices"""
        pass
    
    @abstractmethod
    def supports_emotion(self) -> bool:
        """Check if backend supports emotion control"""
        pass


class ChatterboxTTSBackend(TTSBackend):
    """Chatterbox TTS - Modern neural TTS with emotion control"""
    
    def __init__(self):
        self.initialized = False
        self._initialize()
    
    def _initialize(self):
        """Lazy initialization of Chatterbox"""
        try:
            from chatterbox import Chatterbox
            self.tts = Chatterbox()
            self.initialized = True
            logger.info("Chatterbox TTS initialized successfully")
        except ImportError:
            logger.warning("Chatterbox TTS not available, install with: pip install chatterbox-tts")
        except Exception as e:
            logger.error(f"Failed to initialize Chatterbox TTS: {e}")
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "default",
        emotion: str = "neutral",
        emotion_strength: float = 1.0,
        **kwargs
    ) -> bytes:
        """Synthesize speech with emotion control"""
        if not self.initialized:
            raise RuntimeError("Chatterbox TTS not initialized")
        
        try:
            # Chatterbox supports emotion exaggeration
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.tts.generate(
                        text=text,
                        output_path=tmp.name,
                        emotion=emotion,
                        emotion_strength=emotion_strength
                    )
                )
                
                with open(tmp.name, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(tmp.name)
                return audio_data
                
        except Exception as e:
            logger.error(f"Chatterbox TTS synthesis failed: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available voices"""
        return [
            {"id": "default", "name": "Default Voice", "gender": "neutral"},
            {"id": "expressive", "name": "Expressive Voice", "gender": "neutral"}
        ]
    
    def supports_emotion(self) -> bool:
        return True


class EdgeTTSBackend(TTSBackend):
    """Edge-TTS backend (fallback)"""
    
    def __init__(self):
        self.voices = {
            "female": {
                "primary": "en-US-AriaNeural",
                "thoughtful": "en-US-JennyNeural",
                "excited": "en-US-SaraNeural"
            },
            "male": {
                "primary": "en-US-GuyNeural",
                "thoughtful": "en-US-DavisNeural",
                "excited": "en-US-TonyNeural"
            }
        }
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural",
        rate: str = "-5%",
        pitch: str = "+2Hz",
        **kwargs
    ) -> bytes:
        """Synthesize speech using Edge-TTS"""
        try:
            from edge_tts import Communicate
            
            communicate = Communicate(text, voice, rate=rate, pitch=pitch)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                await communicate.save(tmp.name)
                
                with open(tmp.name, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(tmp.name)
                return audio_data
                
        except Exception as e:
            logger.error(f"Edge-TTS synthesis failed: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available voices"""
        voices = []
        for gender, voice_dict in self.voices.items():
            for mood, voice_id in voice_dict.items():
                voices.append({
                    "id": voice_id,
                    "name": f"{gender.title()} - {mood.title()}",
                    "gender": gender
                })
        return voices
    
    def supports_emotion(self) -> bool:
        return False  # Edge-TTS doesn't have direct emotion control


class TTSManager:
    """Manages multiple TTS backends with fallback support"""
    
    def __init__(self, primary_backend: str = "chatterbox"):
        self.backends = {}
        self.primary_backend = primary_backend
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize available TTS backends"""
        # Try to initialize Chatterbox
        try:
            self.backends["chatterbox"] = ChatterboxTTSBackend()
        except Exception as e:
            logger.warning(f"Chatterbox backend unavailable: {e}")
        
        # Always have Edge-TTS as fallback
        self.backends["edge-tts"] = EdgeTTSBackend()
        
        # Ensure we have at least one backend
        if not self.backends:
            raise RuntimeError("No TTS backends available")
        
        # Adjust primary backend if not available
        if self.primary_backend not in self.backends:
            self.primary_backend = list(self.backends.keys())[0]
            logger.info(f"Primary TTS backend set to: {self.primary_backend}")
    
    async def synthesize(
        self,
        text: str,
        backend: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize speech using specified or primary backend
        
        Args:
            text: Text to synthesize
            backend: Backend to use (optional, uses primary if not specified)
            **kwargs: Backend-specific parameters
            
        Returns:
            Audio data as bytes
        """
        backend_name = backend or self.primary_backend
        
        # Try primary backend first
        if backend_name in self.backends:
            try:
                return await self.backends[backend_name].synthesize(text, **kwargs)
            except Exception as e:
                logger.error(f"Primary backend {backend_name} failed: {e}")
        
        # Fallback to other backends
        for name, backend_obj in self.backends.items():
            if name != backend_name:
                try:
                    logger.info(f"Falling back to {name} TTS")
                    return await backend_obj.synthesize(text, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback backend {name} failed: {e}")
        
        raise RuntimeError("All TTS backends failed")
    
    def get_backend(self, name: str) -> Optional[TTSBackend]:
        """Get specific backend"""
        return self.backends.get(name)
    
    def supports_emotion(self, backend: Optional[str] = None) -> bool:
        """Check if backend supports emotion control"""
        backend_name = backend or self.primary_backend
        if backend_name in self.backends:
            return self.backends[backend_name].supports_emotion()
        return False
    
    def get_available_backends(self) -> List[str]:
        """Get list of available backends"""
        return list(self.backends.keys())


# Singleton instance
_tts_manager = None

def get_tts_manager() -> TTSManager:
    """Get singleton TTS manager instance"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager