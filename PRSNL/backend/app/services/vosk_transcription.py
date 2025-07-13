"""
Vosk-based offline transcription service for PRSNL

Provides local, privacy-focused transcription as alternative to cloud services.
Supports multiple languages and handles rate limiting concerns.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    vosk = None

logger = logging.getLogger(__name__)


class VoskTranscriptionService:
    """Offline transcription service using Vosk speech recognition."""
    
    def __init__(self):
        self.models_dir = Path("storage/vosk_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models_cache = {}
        self._model_urls = {
            "en-us-small": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "en-us-large": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
            "multi-small": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        }
        
    async def ensure_model_available(self, model_name: str = "en-us-small") -> bool:
        """
        Ensure the specified Vosk model is downloaded and available.
        
        Args:
            model_name: Name of the model to ensure is available
            
        Returns:
            True if model is available, False otherwise
        """
        if not VOSK_AVAILABLE:
            logger.warning("Vosk is not available - offline transcription disabled")
            return False
            
        model_path = self.models_dir / f"vosk-model-{model_name}"
        
        if model_path.exists():
            logger.info(f"✅ Vosk model {model_name} already available at {model_path}")
            return True
            
        # Download model if not available
        try:
            logger.info(f"📥 Downloading Vosk model {model_name}...")
            model_url = self._model_urls.get(model_name)
            
            if not model_url:
                logger.error(f"Unknown model: {model_name}")
                return False
                
            # Download and extract model
            await self._download_and_extract_model(model_url, model_path)
            logger.info(f"✅ Vosk model {model_name} downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download Vosk model {model_name}: {e}")
            return False
    
    async def _download_and_extract_model(self, url: str, extract_path: Path):
        """Download and extract Vosk model."""
        import zipfile

        import httpx

        # Download model
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise Exception(f"Failed to download model: HTTP {response.status_code}")
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
        
        try:
            # Extract model
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(self.models_dir)
                
            # Find extracted directory and rename if needed
            for item in self.models_dir.iterdir():
                if item.is_dir() and "vosk-model" in item.name and item != extract_path:
                    item.rename(extract_path)
                    break
                    
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
    
    def _load_model(self, model_name: str = "en-us-small"):
        """Load Vosk model into memory."""
        if not VOSK_AVAILABLE:
            return None
            
        if model_name in self._models_cache:
            return self._models_cache[model_name]
            
        model_path = self.models_dir / f"vosk-model-{model_name}"
        
        if not model_path.exists():
            logger.error(f"Vosk model not found: {model_path}")
            return None
            
        try:
            model = vosk.Model(str(model_path))
            self._models_cache[model_name] = model
            logger.info(f"✅ Loaded Vosk model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load Vosk model {model_name}: {e}")
            return None
    
    async def convert_to_wav(self, input_path: str) -> Optional[str]:
        """
        Convert audio file to WAV format required by Vosk.
        
        Args:
            input_path: Path to input audio file
            
        Returns:
            Path to converted WAV file or None if conversion failed
        """
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Use ffmpeg to convert to WAV (16kHz, mono)
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Run conversion
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Audio converted to WAV: {output_path}")
                return output_path
            else:
                logger.error(f"FFmpeg conversion failed: {stderr.decode()}")
                # Cleanup failed conversion
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return None
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        model_name: str = "en-us-small",
        language: str = "en",
        confidence_threshold: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Vosk.
        
        Args:
            audio_path: Path to audio file
            model_name: Vosk model to use
            language: Language code (for future use)
            confidence_threshold: Minimum confidence for including words
            
        Returns:
            Transcription result with text and metadata
        """
        if not VOSK_AVAILABLE:
            logger.warning("Vosk not available - cannot perform offline transcription")
            return None
            
        try:
            # Ensure model is available
            if not await self.ensure_model_available(model_name):
                return None
                
            # Load model
            model = self._load_model(model_name)
            if not model:
                return None
            
            # Convert audio to WAV if needed
            wav_path = audio_path
            cleanup_wav = False
            
            if not audio_path.lower().endswith('.wav'):
                wav_path = await self.convert_to_wav(audio_path)
                if not wav_path:
                    return None
                cleanup_wav = True
            
            try:
                # Transcribe audio
                result = await self._transcribe_wav_file(wav_path, model, confidence_threshold)
                
                if result:
                    result.update({
                        'model_used': model_name,
                        'service': 'vosk',
                        'language': language,
                        'confidence_threshold': confidence_threshold
                    })
                
                return result
                
            finally:
                # Cleanup temporary WAV file
                if cleanup_wav and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            return None
    
    async def _transcribe_wav_file(
        self, 
        wav_path: str, 
        model, 
        confidence_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Transcribe WAV file using Vosk model."""
        try:
            # Open WAV file
            wf = wave.open(wav_path, "rb")
            
            # Validate WAV format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                logger.warning(f"WAV file format not optimal for Vosk: {wav_path}")
                # Continue anyway - Vosk might handle it
            
            # Create recognizer
            rec = vosk.KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)  # Enable word-level timestamps
            
            # Process audio in chunks
            full_transcript = ""
            words_with_confidence = []
            confidence_scores = []
            
            while True:
                data = wf.readframes(4000)  # Read ~0.25 seconds of audio
                if len(data) == 0:
                    break
                    
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    
                    # Extract text and confidence
                    if 'text' in result and result['text']:
                        full_transcript += " " + result['text']
                        
                    # Extract word-level information
                    if 'result' in result:
                        for word_info in result['result']:
                            confidence = word_info.get('conf', 0.0)
                            confidence_scores.append(confidence)
                            
                            if confidence >= confidence_threshold:
                                words_with_confidence.append({
                                    'word': word_info.get('word', ''),
                                    'start': word_info.get('start', 0.0),
                                    'end': word_info.get('end', 0.0),
                                    'confidence': confidence
                                })
            
            # Get final result
            final_result = json.loads(rec.FinalResult())
            if 'text' in final_result and final_result['text']:
                full_transcript += " " + final_result['text']
            
            # Calculate overall confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Clean up transcript
            full_transcript = full_transcript.strip()
            
            wf.close()
            
            return {
                'text': full_transcript,
                'confidence': avg_confidence,
                'word_count': len(full_transcript.split()) if full_transcript else 0,
                'duration': len(confidence_scores) * 0.25,  # Approximate duration
                'words': words_with_confidence,
                'high_confidence_ratio': len([c for c in confidence_scores if c >= confidence_threshold]) / len(confidence_scores) if confidence_scores else 0.0
            }
            
        except Exception as e:
            logger.error(f"WAV transcription failed: {e}")
            return None
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en",  # English
            "es",  # Spanish  
            "fr",  # French
            "de",  # German
            "ru",  # Russian
            "zh",  # Chinese
            "ja",  # Japanese
            "ko",  # Korean
            "hi",  # Hindi
            "ar"   # Arabic
        ]
    
    async def get_model_info(self, model_name: str = "en-us-small") -> Dict[str, Any]:
        """Get information about a Vosk model."""
        model_path = self.models_dir / f"vosk-model-{model_name}"
        
        return {
            'name': model_name,
            'available': model_path.exists(),
            'path': str(model_path),
            'size_mb': self._get_directory_size(model_path) if model_path.exists() else 0,
            'loaded': model_name in self._models_cache
        }
    
    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB."""
        try:
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0