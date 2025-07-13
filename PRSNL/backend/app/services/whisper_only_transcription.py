"""
Simplified Transcription Service using only whisper.cpp

This replaces the hybrid transcription service with a simpler,
whisper.cpp-only implementation for maximum accuracy and simplicity.
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from .whisper_cpp_transcription import (
    WHISPER_CPP_AVAILABLE,
    WhisperCppTranscriptionService,
)

logger = logging.getLogger(__name__)


class TranscriptionModel(str, Enum):
    """Available whisper.cpp models."""
    TINY = "tiny"       # 39MB - Fastest
    BASE = "base"       # 74MB - Default
    SMALL = "small"     # 244MB - High quality
    MEDIUM = "medium"   # 769MB - Professional
    LARGE = "large"     # 1.5GB - Maximum accuracy


class SimplifiedTranscriptionService:
    """
    Simplified transcription service using only whisper.cpp.
    Provides high-accuracy offline transcription with no external dependencies.
    """
    
    def __init__(self):
        self.whisper_service = WhisperCppTranscriptionService() if WHISPER_CPP_AVAILABLE else None
        self.default_model = TranscriptionModel.BASE
        
        if not WHISPER_CPP_AVAILABLE:
            logger.error("⚠️ whisper.cpp is not available - please install pywhispercpp")
        else:
            logger.info("✅ Transcription service initialized with whisper.cpp")
    
    async def transcribe_audio(
        self,
        audio_path: str,
        model: Optional[TranscriptionModel] = None,
        language: str = "en",
        word_timestamps: bool = True,
        auto_model_selection: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using whisper.cpp.
        
        Args:
            audio_path: Path to audio file
            model: Model to use (if None, auto-selects based on file)
            language: Language code for transcription
            word_timestamps: Include word-level timestamps
            auto_model_selection: Automatically select model based on file size
            
        Returns:
            Transcription result with text and metadata
        """
        if not self.whisper_service:
            logger.error("Transcription service not available - whisper.cpp not installed")
            return None
        
        # Auto-select model based on file size if enabled
        if auto_model_selection and model is None:
            model = self._select_model_for_file(audio_path)
        elif model is None:
            model = self.default_model
        
        logger.info(f"🎙️ Transcribing {audio_path} with model: {model.value}")
        
        # Ensure model is available
        model_available = await self.whisper_service.ensure_model_available(model.value)
        if not model_available:
            logger.error(f"Failed to ensure model {model.value} is available")
            return None
        
        # Transcribe
        result = await self.whisper_service.transcribe_audio(
            audio_path=audio_path,
            model_name=model.value,
            language=language,
            word_timestamps=word_timestamps
        )
        
        if result:
            logger.info(f"✅ Transcription complete - {result.get('word_count', 0)} words")
            result['model_used'] = model.value
        else:
            logger.error("❌ Transcription failed")
        
        return result
    
    def _select_model_for_file(self, audio_path: str) -> TranscriptionModel:
        """
        Select appropriate model based on file size and characteristics.
        
        Returns model enum value.
        """
        try:
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            
            if file_size_mb < 5:
                # Small files - use base for speed
                return TranscriptionModel.BASE
            elif file_size_mb < 20:
                # Medium files - use small for quality
                return TranscriptionModel.SMALL
            elif file_size_mb < 50:
                # Larger files - balance quality and speed
                return TranscriptionModel.SMALL
            else:
                # Very large files - use base for performance
                return TranscriptionModel.BASE
                
        except Exception as e:
            logger.warning(f"Could not determine file size: {e}")
            return self.default_model
    
    async def transcribe_with_options(
        self,
        audio_path: str,
        priority: str = "balanced"
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe with predefined priority settings.
        
        Args:
            audio_path: Path to audio file
            priority: "speed", "balanced", or "accuracy"
            
        Returns:
            Transcription result
        """
        model_map = {
            "speed": TranscriptionModel.TINY,
            "balanced": TranscriptionModel.BASE,
            "accuracy": TranscriptionModel.SMALL
        }
        
        model = model_map.get(priority, TranscriptionModel.BASE)
        
        return await self.transcribe_audio(
            audio_path=audio_path,
            model=model,
            auto_model_selection=False
        )
    
    async def batch_transcribe(
        self,
        audio_paths: List[str],
        model: Optional[TranscriptionModel] = None,
        language: str = "en"
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Transcribe multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            model: Model to use for all files
            language: Language code
            
        Returns:
            List of transcription results
        """
        results = []
        
        for i, audio_path in enumerate(audio_paths, 1):
            logger.info(f"Processing file {i}/{len(audio_paths)}: {audio_path}")
            
            result = await self.transcribe_audio(
                audio_path=audio_path,
                model=model,
                language=language
            )
            
            results.append(result)
        
        return results
    
    async def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available models."""
        if not self.whisper_service:
            return {}
        
        models_info = {}
        
        for model in TranscriptionModel:
            info = await self.whisper_service.get_model_info(model.value)
            models_info[model.value] = {
                "name": model.value,
                "available": info.get('available', False),
                "size_mb": info.get('size_mb', 0),
                "accuracy": info.get('accuracy', 'Unknown'),
                "speed": info.get('speed', 'Unknown'),
                "recommended_for": self._get_model_recommendation(model)
            }
        
        return models_info
    
    def _get_model_recommendation(self, model: TranscriptionModel) -> str:
        """Get usage recommendation for a model."""
        recommendations = {
            TranscriptionModel.TINY: "Real-time transcription, quick drafts",
            TranscriptionModel.BASE: "General use, good balance (recommended)",
            TranscriptionModel.SMALL: "High quality content, presentations",
            TranscriptionModel.MEDIUM: "Professional content, high accuracy",
            TranscriptionModel.LARGE: "Maximum accuracy, critical content"
        }
        return recommendations.get(model, "General use")
    
    async def download_models(self, models: Optional[List[TranscriptionModel]] = None) -> Dict[str, bool]:
        """
        Download specific models.
        
        Args:
            models: List of models to download (None = download default)
            
        Returns:
            Dict of model_name: success
        """
        if not self.whisper_service:
            return {}
        
        if models is None:
            models = [TranscriptionModel.BASE]
        
        results = {}
        
        for model in models:
            logger.info(f"📥 Downloading {model.value} model...")
            success = await self.whisper_service.ensure_model_available(model.value)
            results[model.value] = success
            
            if success:
                logger.info(f"✅ {model.value} model ready")
            else:
                logger.error(f"❌ Failed to download {model.value} model")
        
        return results
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        if not self.whisper_service:
            return []
        
        return await self.whisper_service.get_supported_languages()
    
    def is_available(self) -> bool:
        """Check if transcription service is available."""
        return WHISPER_CPP_AVAILABLE


# Global instance for easy import
transcription_service = SimplifiedTranscriptionService()