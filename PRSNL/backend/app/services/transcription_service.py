import os
import openai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not set - transcription service will be disabled")

    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribes an audio file using OpenAI Whisper."""
        if not self.client:
            logger.warning("Transcription service is disabled - OPENAI_API_KEY not set")
            return None
            
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Error transcribing audio file {audio_file_path}: {e}")
            return None

transcription_service = TranscriptionService()
