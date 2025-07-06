import os
import openai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribes an audio file using OpenAI Whisper."""
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
