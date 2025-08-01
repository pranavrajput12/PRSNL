"""
Whisper.cpp Transcription Service

High-quality offline transcription using whisper.cpp bindings.
Provides better accuracy than Vosk for offline scenarios.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import pywhispercpp.model as whisper_model
from pywhispercpp.model import Model as WhisperModel

logger = logging.getLogger(__name__)


class WhisperCppTranscriptionService:
    """
    Whisper.cpp transcription service for high-quality offline transcription.
    
    Features:
    - High accuracy offline transcription
    - Multiple model sizes for quality/speed tradeoff
    - Word-level timestamps support
    - Language detection
    - Multi-language support
    """
    
    def __init__(self):
        self._models_cache: Dict[str, WhisperModel] = {}
        self._models_dir = Path.home() / ".cache" / "whisper-cpp"
        self._models_dir.mkdir(parents=True, exist_ok=True)
        
        # Available model sizes with quality/speed tradeoffs
        self.available_models = {
            "tiny": {"size": "39M", "quality": "low", "speed": "fastest"},
            "base": {"size": "74M", "quality": "moderate", "speed": "fast"},
            "small": {"size": "244M", "quality": "good", "speed": "medium"},
            "medium": {"size": "769M", "quality": "very good", "speed": "slow"},
            "large": {"size": "1550M", "quality": "excellent", "speed": "slowest"}
        }
        
        logger.info("🚀 Whisper.cpp Transcription Service initialized")
        logger.info(f"   Models directory: {self._models_dir}")
    
    async def ensure_model_available(self, model_name: str = "base") -> bool:
        """
        Ensure the specified model is available for use.
        Downloads the model if not already present.
        
        Args:
            model_name: Model size to use (tiny, base, small, medium, large)
            
        Returns:
            True if model is available, False otherwise
        """
        if model_name not in self.available_models:
            logger.error(f"Invalid model name: {model_name}")
            return False
        
        try:
            # Check if model already loaded
            if model_name in self._models_cache:
                return True
            
            # Try to load the model
            model_path = self._models_dir / f"ggml-{model_name}.bin"
            
            # Download model if not exists
            if not model_path.exists():
                logger.info(f"📥 Downloading whisper.cpp model: {model_name}")
                # pywhispercpp will automatically download models
                
            # Load the model
            model = WhisperModel(model_name)
            self._models_cache[model_name] = model
            
            logger.info(f"✅ Whisper.cpp model loaded: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure model {model_name}: {e}")
            return False
    
    def _get_model(self, model_name: str = "base") -> Optional[WhisperModel]:
        """Get cached model or load it."""
        if model_name in self._models_cache:
            return self._models_cache[model_name]
        
        try:
            model = WhisperModel(model_name)
            self._models_cache[model_name] = model
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None
    
    async def transcribe_audio(
        self,
        audio_path: str,
        model_name: str = "base",
        language: str = "en",
        word_timestamps: bool = True,
        initial_prompt: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Transcribe audio file using whisper.cpp.
        
        Args:
            audio_path: Path to audio file
            model_name: Model size to use
            language: Language code (e.g., "en", "es", "fr")
            word_timestamps: Whether to include word-level timestamps
            initial_prompt: Optional prompt to guide transcription
            
        Returns:
            Transcription result with text, segments, and metadata
        """
        try:
            # Ensure model is available
            if not await self.ensure_model_available(model_name):
                logger.error(f"Model {model_name} not available")
                return None
            
            # Get the model
            model = self._get_model(model_name)
            if not model:
                return None
            
            logger.info(f"🎙️ Transcribing with whisper.cpp ({model_name} model): {audio_path}")
            
            # Configure transcription parameters
            params = {
                "language": language if language != "auto" else None,
                "word_timestamps": word_timestamps,
                "initial_prompt": initial_prompt,
                "print_progress": False,
                "print_realtime": False
            }
            
            # Run transcription in thread pool (whisper.cpp is CPU-bound)
            loop = asyncio.get_event_loop()
            segments = await loop.run_in_executor(
                None,
                lambda: model.transcribe(audio_path, **params)
            )
            
            # Process segments
            full_text = ""
            processed_segments = []
            word_count = 0
            
            for segment in segments:
                segment_text = segment.text.strip()
                full_text += segment_text + " "
                
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment_text
                }
                
                # Add word timestamps if available
                if word_timestamps and hasattr(segment, 'words'):
                    segment_data["words"] = [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ]
                    word_count += len(segment.words)
                else:
                    word_count += len(segment_text.split())
                
                processed_segments.append(segment_data)
            
            result = {
                "text": full_text.strip(),
                "segments": processed_segments,
                "language": language,
                "duration": processed_segments[-1]["end"] if processed_segments else 0,
                "word_count": word_count,
                "model": model_name,
                "confidence": 0.85,  # whisper.cpp doesn't provide overall confidence
                "service": "whisper.cpp"
            }
            
            logger.info(f"✅ Transcription complete: {word_count} words, {len(processed_segments)} segments")
            return result
            
        except Exception as e:
            logger.error(f"Whisper.cpp transcription failed: {e}")
            return None
    
    async def detect_language(self, audio_path: str, model_name: str = "base") -> Optional[str]:
        """
        Detect the language of audio file.
        
        Args:
            audio_path: Path to audio file
            model_name: Model to use for detection
            
        Returns:
            Detected language code or None
        """
        try:
            model = self._get_model(model_name)
            if not model:
                return None
            
            # Run language detection
            loop = asyncio.get_event_loop()
            language = await loop.run_in_executor(
                None,
                lambda: model.detect_language(audio_path)
            )
            
            logger.info(f"🌐 Detected language: {language}")
            return language
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None
    
    async def get_model_info(self) -> Dict[str, any]:
        """Get information about available models."""
        info = {
            "available_models": self.available_models,
            "loaded_models": list(self._models_cache.keys()),
            "models_directory": str(self._models_dir),
            "recommended_model": "base"  # Good balance of quality and speed
        }
        
        # Check which models are downloaded
        for model_name in self.available_models:
            model_path = self._models_dir / f"ggml-{model_name}.bin"
            info[f"{model_name}_downloaded"] = model_path.exists()
        
        return info
    
    def cleanup(self):
        """Clean up loaded models to free memory."""
        self._models_cache.clear()
        logger.info("🧹 Whisper.cpp models cleaned up")


# Create a global instance
whisper_cpp_service = WhisperCppTranscriptionService()