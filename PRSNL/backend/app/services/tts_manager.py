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


class PiperTTSBackend(TTSBackend):
    """Piper TTS - Lightweight neural TTS (memory-optimized)"""
    
    def __init__(self):
        self.initialized = False
        self.voices = {
            "female": {
                "primary": "en_US-amy-low",     # Lightweight female voice
                "thoughtful": "en_US-amy-medium", # Better quality female
                "excited": "en_US-kathleen-low"   # Alternative female voice
            },
            "male": {
                "primary": "en_US-ryan-low",    # Lightweight male voice  
                "thoughtful": "en_US-ryan-medium", # Better quality male
                "excited": "en_US-danny-low"    # Alternative male voice
            }
        }
        self._initialize()
    
    def _initialize(self):
        """Lazy initialization of Piper TTS"""
        try:
            # Try different import patterns for piper-tts
            try:
                import piper_tts as piper
            except ImportError:
                import piper
            
            self.piper = piper
            self.initialized = True
            logger.info("Piper TTS initialized successfully (memory-optimized)")
        except ImportError:
            logger.warning("Piper TTS not available, install with: pip install piper-tts")
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "en_US-amy-low",
        rate: float = 1.0,
        **kwargs
    ) -> bytes:
        """Synthesize speech using Piper TTS (lightweight)"""
        if not self.initialized:
            logger.warning("Piper TTS not initialized, falling back to Edge-TTS")
            raise RuntimeError("Piper TTS not initialized")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                # Run piper in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._synthesize_sync(text, voice, tmp.name, rate)
                )
                
                with open(tmp.name, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(tmp.name)
                return audio_data
                
        except Exception as e:
            logger.error(f"Piper TTS synthesis failed: {e}")
            raise
    
    def _synthesize_sync(self, text: str, voice: str, output_path: str, rate: float):
        """Synchronous Piper synthesis"""
        try:
            # Use piper CLI-style interface for maximum compatibility
            import subprocess
            
            # Piper command: echo "text" | piper --model voice --output_file output.wav
            cmd = [
                'python', '-m', 'piper',
                '--model', voice,
                '--output_file', output_path
            ]
            
            # Add rate control if supported
            if rate != 1.0:
                cmd.extend(['--length_scale', str(1.0 / rate)])  # Inverse for piper
            
            # Run piper with text input
            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                check=True,
                timeout=30  # 30 second timeout
            )
            
            logger.info(f"Piper TTS completed successfully for voice: {voice}")
            
        except subprocess.TimeoutExpired:
            logger.error("Piper TTS synthesis timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper TTS command failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Piper TTS synthesis error: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available Piper voices"""
        voices = []
        for gender, voice_dict in self.voices.items():
            for mood, voice_id in voice_dict.items():
                voices.append({
                    "id": voice_id,
                    "name": f"Piper {gender.title()} - {mood.title()} (Light)",
                    "gender": gender
                })
        return voices
    
    def supports_emotion(self) -> bool:
        return False  # Piper doesn't have direct emotion control but has voice variations


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
        # Try to initialize Piper TTS first (memory-optimized)
        try:
            self.backends["piper"] = PiperTTSBackend()
        except Exception as e:
            logger.warning(f"Piper TTS backend unavailable: {e}")
        
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
        
        # Adjust primary backend if not available - prefer memory-efficient options
        if self.primary_backend not in self.backends:
            # Priority order: piper -> chatterbox -> edge-tts
            if "piper" in self.backends:
                self.primary_backend = "piper"
            elif "chatterbox" in self.backends:
                self.primary_backend = "chatterbox"
            else:
                self.primary_backend = "edge-tts"
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