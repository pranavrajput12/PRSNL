"""
Azure OpenAI Whisper Cloud Transcription Service

This is the cloud-only transcription service using Azure OpenAI Whisper.
For production use, please use HybridTranscriptionService which provides
intelligent routing between cloud and offline transcription.
"""

import logging
import os
from typing import Optional

import httpx
from langfuse import observe

from app.config import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            self.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT
            self.azure_key = settings.AZURE_OPENAI_API_KEY
            self.api_version = settings.AZURE_OPENAI_API_VERSION
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Azure OpenAI not configured - transcription service will be disabled")

    @observe(name="transcribe_audio_azure")
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribes an audio file using Azure OpenAI Whisper."""
        if not self.enabled:
            logger.warning("Transcription service is disabled - Azure OpenAI not configured")
            return None
            
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        try:
            # Azure OpenAI Whisper endpoint
            url = f"{self.azure_endpoint}/openai/deployments/{settings.AZURE_OPENAI_WHISPER_DEPLOYMENT}/audio/transcriptions?api-version={self.api_version}"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(audio_file_path, "rb") as audio_file:
                    # Determine MIME type based on file extension
                    file_ext = os.path.splitext(audio_file_path)[1].lower()
                    mime_type = {
                        '.mp3': 'audio/mpeg',
                        '.mp4': 'video/mp4',
                        '.mpeg': 'video/mpeg',
                        '.mpga': 'audio/mpeg',
                        '.m4a': 'audio/mp4',
                        '.wav': 'audio/wav',
                        '.webm': 'video/webm'
                    }.get(file_ext, 'application/octet-stream')
                    
                    files = {"file": (os.path.basename(audio_file_path), audio_file, mime_type)}
                    headers = {"api-key": self.azure_key}
                    data = {"model": settings.AZURE_OPENAI_WHISPER_DEPLOYMENT}
                    
                    response = await client.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    
                result = response.json()
                return result.get("text", "")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error("Whisper deployment not found in Azure OpenAI. Please deploy a Whisper model.")
            else:
                logger.error(f"Azure OpenAI API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio file {audio_file_path}: {e}")
            return None

transcription_service = TranscriptionService()
