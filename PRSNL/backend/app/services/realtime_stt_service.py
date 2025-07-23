"""
RealtimeSTT Service for PRSNL - Real-time streaming speech-to-text
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

try:
    from RealtimeSTT import AudioToTextRecorder
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("RealtimeSTT not installed. Please install with: pip install RealtimeSTT")
    raise

logger = logging.getLogger(__name__)


class RealtimeSTTService:
    """Service for real-time streaming speech-to-text"""
    
    def __init__(self):
        self.recorder: Optional[AudioToTextRecorder] = None
        self.is_recording = False
        self.text_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialize_recorder()
        
    def _initialize_recorder(self):
        """Initialize the RealtimeSTT recorder"""
        try:
            # Configure recorder with optimal settings
            self.recorder = AudioToTextRecorder(
                model="base",  # Can be tiny, base, small, medium, large
                language="en",
                silero_sensitivity=0.4,  # Silence detection sensitivity
                webrtc_sensitivity=3,  # Voice activity detection
                post_speech_silence_duration=0.4,  # Pause after speech before processing
                min_length_of_recording=0.5,  # Minimum recording length
                min_gap_between_recordings=0.3,  # Gap between recordings
                enable_realtime_transcription=True,  # Enable streaming
                realtime_processing_pause=0.2,  # Pause for real-time processing
                realtime_model_type="tiny",  # Faster model for real-time
                on_recording_start=self._on_recording_start,
                on_recording_stop=self._on_recording_stop,
                on_realtime_transcription_update=self._on_realtime_update,
                on_realtime_transcription_stabilized=self._on_realtime_stabilized
            )
            logger.info("RealtimeSTT recorder initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RealtimeSTT recorder: {e}")
            raise
    
    def _on_recording_start(self):
        """Callback when recording starts"""
        logger.debug("Recording started")
        self.is_recording = True
        
    def _on_recording_stop(self):
        """Callback when recording stops"""
        logger.debug("Recording stopped")
        self.is_recording = False
        
    def _on_realtime_update(self, text: str):
        """Callback for real-time transcription updates"""
        logger.debug(f"Realtime update: {text}")
        self.text_queue.put({
            "type": "partial",
            "text": text,
            "is_final": False
        })
        
    def _on_realtime_stabilized(self, text: str):
        """Callback when transcription is stabilized"""
        logger.debug(f"Stabilized text: {text}")
        self.text_queue.put({
            "type": "final",
            "text": text,
            "is_final": True
        })
    
    async def start_streaming(self, 
                            on_text: Optional[Callable[[Dict[str, Any]], None]] = None,
                            on_error: Optional[Callable[[str], None]] = None):
        """
        Start streaming transcription
        
        Args:
            on_text: Callback for transcribed text (partial and final)
            on_error: Callback for errors
        """
        try:
            # Start recording in a separate thread
            future = self.executor.submit(self._start_recording_thread)
            
            # Process text queue
            while True:
                try:
                    # Check for new text with timeout
                    text_data = self.text_queue.get(timeout=0.1)
                    
                    if on_text:
                        # Run callback in asyncio context
                        await asyncio.get_event_loop().run_in_executor(
                            None, on_text, text_data
                        )
                        
                except queue.Empty:
                    # No new text, continue
                    pass
                    
                # Allow other tasks to run
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            if on_error:
                await asyncio.get_event_loop().run_in_executor(
                    None, on_error, str(e)
                )
    
    def _start_recording_thread(self):
        """Start recording in a separate thread"""
        try:
            if self.recorder:
                self.recorder.start()
                logger.info("RealtimeSTT recording started")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
    
    def stop_streaming(self):
        """Stop streaming transcription"""
        try:
            if self.recorder and self.is_recording:
                self.recorder.stop()
                logger.info("RealtimeSTT recording stopped")
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
    
    def process_audio_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """
        Process an audio chunk and return transcription if available
        
        Args:
            audio_chunk: Raw audio bytes
            
        Returns:
            Transcribed text if available, None otherwise
        """
        # This method is for compatibility with chunk-based processing
        # RealtimeSTT handles its own audio capture, so this might not be used
        logger.warning("process_audio_chunk called but RealtimeSTT uses its own audio capture")
        return None
    
    def set_language(self, language: str):
        """Set the transcription language"""
        if self.recorder:
            self.recorder.language = language
            logger.info(f"Language set to: {language}")
    
    def set_model(self, model: str):
        """Set the Whisper model size"""
        if model in ["tiny", "base", "small", "medium", "large"]:
            # Would need to reinitialize recorder with new model
            logger.info(f"Model change to {model} requires recorder reinitialization")
        else:
            logger.warning(f"Invalid model: {model}")
    
    def __del__(self):
        """Cleanup resources"""
        try:
            if self.recorder:
                self.recorder.stop()
            self.executor.shutdown(wait=False)
        except:
            pass


# Singleton instance
_realtime_stt_service: Optional[RealtimeSTTService] = None


def get_realtime_stt_service() -> RealtimeSTTService:
    """Get or create RealtimeSTT service instance"""
    global _realtime_stt_service
    if _realtime_stt_service is None:
        _realtime_stt_service = RealtimeSTTService()
    return _realtime_stt_service