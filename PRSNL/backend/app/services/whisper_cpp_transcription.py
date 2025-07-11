"""
Whisper.cpp-based offline transcription service for PRSNL

Provides high-accuracy local transcription using whisper.cpp.
Significantly better accuracy than Vosk with CPU optimization.
"""

import os
import json
import wave
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, AsyncGenerator
import subprocess
import tempfile
import time
import hashlib

try:
    from pywhispercpp.model import Model as WhisperModel
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    WhisperModel = None

logger = logging.getLogger(__name__)


class WhisperCppTranscriptionService:
    """High-accuracy offline transcription using whisper.cpp."""
    
    # Model sizes and their download URLs
    MODEL_INFO = {
        "tiny": {
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
            "size_mb": 39,
            "accuracy": "Good for quick transcription",
            "speed": "Very fast"
        },
        "base": {
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
            "size_mb": 74,
            "accuracy": "Better accuracy, still fast",
            "speed": "Fast"
        },
        "small": {
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
            "size_mb": 244,
            "accuracy": "Good balance of speed and accuracy",
            "speed": "Moderate"
        },
        "medium": {
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
            "size_mb": 769,
            "accuracy": "High accuracy",
            "speed": "Slower"
        },
        "large": {
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large.bin",
            "size_mb": 1550,
            "accuracy": "Highest accuracy",
            "speed": "Slowest"
        }
    }
    
    def __init__(self):
        self.models_dir = Path("storage/whisper_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models_cache = {}
        self._default_model = "base"  # Good balance for most use cases
        
    async def ensure_model_available(self, model_name: str = "base") -> bool:
        """
        Ensure the specified Whisper model is downloaded and available.
        
        Args:
            model_name: Name of the model to ensure is available
            
        Returns:
            True if model is available, False otherwise
        """
        if not WHISPER_CPP_AVAILABLE:
            logger.warning("pywhispercpp is not available - whisper.cpp transcription disabled")
            return False
            
        model_path = self.models_dir / f"ggml-{model_name}.bin"
        
        if model_path.exists():
            logger.info(f"✅ Whisper model {model_name} already available at {model_path}")
            return True
            
        # Download model if not available
        try:
            logger.info(f"📥 Downloading Whisper model {model_name}...")
            model_info = self.MODEL_INFO.get(model_name)
            
            if not model_info:
                logger.error(f"Unknown model: {model_name}")
                return False
                
            # Download model
            await self._download_model(model_info['url'], model_path)
            logger.info(f"✅ Whisper model {model_name} downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download Whisper model {model_name}: {e}")
            return False
    
    async def _download_model(self, url: str, save_path: Path):
        """Download Whisper model."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download model: HTTP {response.status}")
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress logging
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if int(progress) % 10 == 0:
                                logger.info(f"Download progress: {progress:.0f}%")
    
    def _load_model(self, model_name: str = "base") -> Optional[WhisperModel]:
        """Load Whisper model into memory."""
        if not WHISPER_CPP_AVAILABLE:
            return None
            
        if model_name in self._models_cache:
            return self._models_cache[model_name]
            
        model_path = self.models_dir / f"ggml-{model_name}.bin"
        
        if not model_path.exists():
            logger.error(f"Whisper model not found: {model_path}")
            return None
            
        try:
            # Initialize whisper.cpp model
            model = WhisperModel(
                model_path=str(model_path),
                n_threads=os.cpu_count() or 4,  # Use all CPU cores
                print_progress=False,
                print_realtime=False
            )
            
            self._models_cache[model_name] = model
            logger.info(f"✅ Loaded Whisper model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model {model_name}: {e}")
            return None
    
    async def convert_to_wav(self, input_path: str) -> Optional[str]:
        """
        Convert audio file to WAV format required by whisper.cpp.
        
        Args:
            input_path: Path to input audio file
            
        Returns:
            Path to converted WAV file or None if conversion failed
        """
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Use ffmpeg to convert to WAV (16kHz, mono, 16-bit)
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
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return None
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        model_name: str = "base",
        language: str = "en",
        translate: bool = False,
        temperature: float = 0.0,
        word_timestamps: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using whisper.cpp.
        
        Args:
            audio_path: Path to audio file
            model_name: Whisper model to use (tiny, base, small, medium, large)
            language: Language code for transcription
            translate: Whether to translate to English
            temperature: Sampling temperature (0.0 = greedy decoding)
            word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Transcription result with text and metadata
        """
        if not WHISPER_CPP_AVAILABLE:
            logger.warning("whisper.cpp not available - cannot perform offline transcription")
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
                start_time = time.time()
                
                # Configure transcription parameters
                model.params.language = language.encode('utf-8')
                model.params.translate = translate
                model.params.temperature = temperature
                model.params.print_progress = False
                model.params.print_realtime = False
                model.params.token_timestamps = word_timestamps
                
                # Perform transcription
                segments = model.transcribe(wav_path)
                
                # Process results
                full_text = ""
                all_words = []
                total_confidence = 0.0
                segment_count = 0
                
                for segment in segments:
                    full_text += segment.text + " "
                    
                    # Extract word-level information if available
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            all_words.append({
                                'word': word.word,
                                'start': word.start,
                                'end': word.end,
                                'probability': word.probability
                            })
                    
                    # Track confidence (using segment probability if available)
                    if hasattr(segment, 'probability'):
                        total_confidence += segment.probability
                        segment_count += 1
                
                # Calculate metrics
                processing_time = time.time() - start_time
                avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.95
                
                # Get audio duration
                audio_duration = self._get_audio_duration(wav_path)
                
                result = {
                    'text': full_text.strip(),
                    'confidence': avg_confidence,
                    'word_count': len(full_text.split()),
                    'duration': audio_duration,
                    'processing_time': processing_time,
                    'real_time_factor': processing_time / audio_duration if audio_duration > 0 else 0,
                    'model_used': model_name,
                    'service': 'whisper.cpp',
                    'language': language,
                    'translated': translate,
                    'segments': len(segments),
                    'words': all_words if word_timestamps else []
                }
                
                return result
                
            finally:
                # Cleanup temporary WAV file
                if cleanup_wav and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
        except Exception as e:
            logger.error(f"Whisper.cpp transcription failed: {e}")
            return None
    
    def _get_audio_duration(self, wav_path: str) -> float:
        """Get duration of WAV file in seconds."""
        try:
            with wave.open(wav_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return duration
        except:
            return 0.0
    
    async def transcribe_streaming(
        self,
        audio_stream,
        model_name: str = "base",
        language: str = "en",
        chunk_duration: float = 5.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming transcription for real-time audio.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            model_name: Model to use
            language: Language code
            chunk_duration: Duration of audio chunks to process
            
        Yields:
            Transcription results for each chunk
        """
        if not WHISPER_CPP_AVAILABLE:
            logger.warning("whisper.cpp not available for streaming")
            return
            
        # Load model
        model = self._load_model(model_name)
        if not model:
            return
            
        # Process audio chunks
        buffer = bytearray()
        chunk_size = int(16000 * chunk_duration)  # 16kHz sample rate
        
        async for audio_chunk in audio_stream:
            buffer.extend(audio_chunk)
            
            # Process when we have enough audio
            if len(buffer) >= chunk_size * 2:  # 2 bytes per sample
                # Extract chunk
                chunk_data = bytes(buffer[:chunk_size * 2])
                buffer = buffer[chunk_size * 2:]
                
                # Write to temporary file and transcribe
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    # Write WAV header and data
                    self._write_wav_chunk(tmp_file.name, chunk_data)
                    
                    # Transcribe chunk
                    result = await self.transcribe_audio(
                        tmp_file.name,
                        model_name=model_name,
                        language=language,
                        word_timestamps=False  # Faster for streaming
                    )
                    
                    # Cleanup
                    os.unlink(tmp_file.name)
                    
                    if result:
                        yield {
                            'text': result['text'],
                            'is_final': False,
                            'timestamp': time.time()
                        }
    
    def _write_wav_chunk(self, path: str, audio_data: bytes):
        """Write audio data as WAV file."""
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)  # 16kHz
            wf.writeframes(audio_data)
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        # Whisper supports 99 languages
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
            "ar", "hi", "tr", "pl", "nl", "sv", "fi", "da", "no", "he",
            "id", "ms", "th", "vi", "ro", "cs", "hu", "el", "bg", "uk",
            "hr", "sr", "sk", "sl", "et", "lv", "lt", "ca", "sq", "mk",
            "is", "cy", "eu", "gl", "af", "sw", "am", "ka", "hy", "az",
            "kk", "fa", "ur", "ps", "sd", "ne", "si", "my", "km", "lo",
            "ml", "kn", "ta", "te", "bn", "gu", "mr", "pa", "or", "as",
            "mn", "bo", "tl", "mg", "mt", "ha", "yo", "so", "sn", "mi",
            "ht", "lb", "bs", "nn", "oc", "la", "br", "tk", "tt", "ba",
            "jw", "su", "ln", "zu", "om", "fo", "ti", "tg", "eo", "yi"
        ]
    
    async def get_model_info(self, model_name: str = "base") -> Dict[str, Any]:
        """Get information about a Whisper model."""
        model_path = self.models_dir / f"ggml-{model_name}.bin"
        model_info = self.MODEL_INFO.get(model_name, {})
        
        return {
            'name': model_name,
            'available': model_path.exists(),
            'path': str(model_path),
            'size_mb': model_info.get('size_mb', 0),
            'accuracy': model_info.get('accuracy', 'Unknown'),
            'speed': model_info.get('speed', 'Unknown'),
            'loaded': model_name in self._models_cache,
            'download_url': model_info.get('url', '')
        }
    
    async def benchmark_model(self, model_name: str = "base", test_audio_path: Optional[str] = None) -> Dict[str, Any]:
        """Benchmark a model's performance."""
        if not test_audio_path:
            # Use a sample audio file
            test_audio_path = "samples/test_audio.wav"
            
        if not os.path.exists(test_audio_path):
            return {
                'error': 'Test audio file not found',
                'model': model_name
            }
        
        # Run transcription and measure performance
        start_time = time.time()
        result = await self.transcribe_audio(test_audio_path, model_name=model_name)
        total_time = time.time() - start_time
        
        if result:
            return {
                'model': model_name,
                'transcription_time': total_time,
                'audio_duration': result.get('duration', 0),
                'real_time_factor': result.get('real_time_factor', 0),
                'word_count': result.get('word_count', 0),
                'confidence': result.get('confidence', 0),
                'words_per_second': result.get('word_count', 0) / total_time if total_time > 0 else 0
            }
        else:
            return {
                'error': 'Transcription failed',
                'model': model_name
            }


# Singleton instance
whisper_cpp_service = WhisperCppTranscriptionService()