import httpx
from typing import Optional, Dict
import logging
from app.core.capture_engine import CaptureEngine
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.video_processor = VideoProcessor()
        
    async def process_message(self, message: Dict) -> bool:
        """Process incoming Telegram message"""
        try:
            # Extract text/caption
            text = message.get('text') or message.get('caption', '')
            
            # Check for URLs in text
            if 'http' in text:
                urls = self._extract_urls(text)
                for url in urls:
                    await self._capture_url(url, message)
                    
            # Handle video messages
            if 'video' in message:
                await self._process_video(message)
                
            return True
            
        except Exception as e:
            logger.error(f"Error processing Telegram message: {str(e)}")
            return False
    
    def _extract_urls(self, text: str) -> list:
        """Extract URLs from text"""
        import re
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)
    
    async def _capture_url(self, url: str, message: Dict):
        """Capture URL using existing capture engine"""
        # Use existing capture logic
        from app.api.capture import capture_item
        
        # Extract title from message if available
        title = f"Via Telegram: {url[:50]}..."
        
        # Call capture endpoint logic
        await capture_item({
            'url': url,
            'title': title,
            'metadata': {
                'source': 'telegram',
                'chat_id': message.get('chat', {}).get('id'),
                'message_id': message.get('message_id')
            }
        })
        
    async def send_message(self, chat_id: int, text: str):
        """Send response back to user"""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text}
            )

    async def _process_video(self, message: Dict):
        """Process incoming video message"""
        logger.info(f"Received video message: {message}")
        chat_id = message['chat']['id']
        video_file_id = message['video']['file_id']
        caption = message.get('caption', '')

        try:
            # Get file path from Telegram API
            file_info_url = f"{self.base_url}/getFile?file_id={video_file_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(file_info_url)
                response.raise_for_status()
                file_path = response.json()['result']['file_path']

            # Construct direct download URL
            video_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            logger.info(f"Attempting to download video from Telegram: {video_url}")

            # Process video using VideoProcessor
            video_data = await self.video_processor.download_video(video_url)

            # Capture the processed video as an item in PRSNL
            from app.api.capture import capture_item
            await capture_item({
                'url': video_url, # Use the Telegram file URL as the source URL
                'title': caption or f"Telegram Video: {video_file_id}",
                'metadata': {
                    'source': 'telegram',
                    'chat_id': chat_id,
                    'message_id': message.get('message_id'),
                    'video_path': video_data.video_path, # Store the path to the processed video
                    'thumbnail_path': video_data.thumbnail_path,
                    'duration': video_data.duration,
                    'platform': video_data.platform,
                    'original_metadata': video_data.metadata
                }
            })
            await self.send_message(chat_id, "✅ Video captured successfully!")

        except Exception as e:
            logger.error(f"Error processing Telegram video: {str(e)}", exc_info=True)
            await self.send_message(chat_id, f"❌ Failed to process video: {e}")