import httpx
import logging
import re
import json
import time
from typing import Optional, Dict, List, Any
from uuid import uuid4

from app.core.capture_engine import CaptureEngine
from app.services.video_processor import VideoProcessor
from app.services.llm_processor import LLMProcessor
from app.db.database import get_db_pool
from app.services.embedding_service import embedding_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.video_processor = VideoProcessor()
        self.llm_processor = LLMProcessor()
        self.capture_engine = CaptureEngine()
        self.db_pool = None # Will be initialized later

    async def initialize_db_pool(self):
        if self.db_pool is None:
            from app.db.database import get_db_pool
            self.db_pool = await get_db_pool()

    async def process_message(self, message: Dict) -> bool:
        """Process incoming Telegram message"""
        await self.initialize_db_pool()
        chat_id = message['chat']['id']
        text = message.get('text') or message.get('caption', '')

        if text.startswith('/start'):
            await self._send_start_message(chat_id)
        elif text.startswith('/help'):
            await self._send_help_message(chat_id)
        elif text.startswith('/capture'):
            url = text.split(' ', 1)[1] if len(text.split(' ', 1)) > 1 else None
            if url:
                await self._capture_url(url, message)
            else:
                await self.send_message(chat_id, "Please provide a URL to capture. Usage: `/capture [url]`")
        elif text.startswith('/search'):
            query = text.split(' ', 1)[1] if len(text.split(' ', 1)) > 1 else None
            if query:
                await self._search_items(chat_id, query)
            else:
                await self.send_message(chat_id, "Please provide a query to search. Usage: `/search [query]`")
        elif text.startswith('/recent'):
            await self._show_recent_captures(chat_id)
        elif 'http' in text:
            urls = self._extract_urls(text)
            for url in urls:
                await self._capture_url(url, message)
        elif 'video' in message:
            await self._process_video(message)
        elif 'photo' in message: # Handle image with OCR
            await self._process_image(message)
        else:
            await self.send_message(chat_id, "I received your message. Send me a URL, a video, or use /help to see commands.")

        return True
    
    async def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None):
        """Send response back to user"""
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/sendMessage",
                json=payload
            )

    async def _send_start_message(self, chat_id: int):
        welcome_text = (
            "Welcome to PRSNL Bot! I can help you capture and search your personal knowledge base.\n\n"
            "Send me a URL, a video, or an image with text to capture it.\n\n"
            "Here are some commands you can use:\n"
            "/capture [url] - Capture a specific URL\n"
            "/search [query] - Search your saved items\n"
            "/recent - Show your most recent captures\n"
            "/help - Show this help message again"
        )
        await self.send_message(chat_id, welcome_text)

    async def _send_help_message(self, chat_id: int):
        help_text = (
            "Here are the commands you can use:\n"
            "/start - Get a welcome message and basic instructions\n"
            "/capture [url] - Capture a web page or article by its URL\n"
            "/search [query] - Find items in your knowledge base using keywords\n"
            "/recent - See your last 5 captured items\n"
            "/help - Display this list of commands"
        )
        await self.send_message(chat_id, help_text)

    async def _search_items(self, chat_id: int, query: str):
        await self.send_message(chat_id, f"Searching for '{query}'...")
        from app.api.semantic_search import semantic_search, SemanticSearchRequest
        try:
            search_results = await semantic_search(SemanticSearchRequest(query=query, limit=3))
            if search_results:
                response_text = f"Found {len(search_results)} results for '{query}':\n\n"
                for item in search_results:
                    response_text += f"* {item.title}\n  Similarity: {item.similarity:.2f}\n  URL: {item.url or 'N/A'}\n\n"
                await self.send_message(chat_id, response_text)
            else:
                await self.send_message(chat_id, f"No results found for '{query}'.")
        except Exception as e:
            logger.error(f"Error during Telegram search: {e}")
            await self.send_message(chat_id, "An error occurred during search. Please try again later.")

    async def _show_recent_captures(self, chat_id: int):
        await self.send_message(chat_id, "Fetching recent captures...")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            recent_items = await conn.fetch(
                "SELECT id, title, url, summary FROM items ORDER BY created_at DESC LIMIT 5"
            )
            if recent_items:
                response_text = "Your most recent captures:\n\n"
                for item in recent_items:
                    response_text += f"* {item['title']}\n  Summary: {item['summary'] or 'N/A'}\n  URL: {item['url'] or 'N/A'}\n\n"
                await self.send_message(chat_id, response_text)
            else:
                await self.send_message(chat_id, "You haven't captured any items yet.")

    async def _process_image(self, message: Dict):
        await self.send_message(message['chat']['id'], "Image capture with OCR is not yet implemented.")

    def _extract_urls(self, text: str) -> list:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)
    
    async def _capture_url(self, url: str, message: Dict):
        chat_id = message['chat']['id']
        await self.send_message(chat_id, f"Capturing {url}...")
        
        try:
            from app.api.capture import capture_item
            
            item_id = uuid4()
            await capture_item({
                'url': url,
                'title': f"Capturing: {url}",
                'metadata': {
                    'source': 'telegram',
                    'chat_id': chat_id,
                    'message_id': message.get('message_id'),
                    'item_id': str(item_id)
                }
            })
            
            pool = await get_db_pool()
            for _ in range(10): # Try a few times with delay
                async with pool.acquire() as conn:
                    item = await conn.fetchrow("SELECT title, summary, metadata FROM items WHERE id = $1", item_id)
                    if item and item['metadata'] and item['metadata'].get('ai_analysis'):
                        break
                await asyncio.sleep(2)

            if item and item['metadata'] and item['metadata'].get('ai_analysis'):
                ai_analysis = item['metadata']['ai_analysis']
                summary = ai_analysis.get('summary', 'No summary available.')
                tags = ", ".join(ai_analysis.get('tags', []))
                title = item['title']
                
                response_text = (
                    f"✅ Captured: \"{title}\"\n"
                    f"Summary: {summary}\n"
                    f"Tags: {tags or 'N/A'}\n"
                    f"View: {settings.FRONTEND_URL}/item/{item_id}"
                )
                
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {"text": "View", "url": f"{settings.FRONTEND_URL}/item/{item_id}"},
                            {"text": "Delete", "callback_data": f"delete_{item_id}"},
                            {"text": "Share", "switch_inline_query": f"Share {item_id}"}
                        ]
                    ]
                }
                await self.send_message(chat_id, response_text, reply_markup)
            else:
                await self.send_message(chat_id, "✅ Capture initiated. Processing in background. Summary will be available soon.")

        except Exception as e:
            logger.error(f"Error capturing URL via Telegram: {str(e)}", exc_info=True)
            await self.send_message(chat_id, f"❌ Failed to capture URL: {e}")

    async def _process_video(self, message: Dict):
        """Process incoming video message"""
        logger.info(f"Received video message: {message}")
        chat_id = message['chat']['id']
        video_file_id = message['video']['file_id']
        caption = message.get('caption', '')

        try:
            file_info_url = f"{self.base_url}/getFile?file_id={video_file_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(file_info_url)
                response.raise_for_status()
                file_path = response.json()['result']['file_path']

            video_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            logger.info(f"Attempting to download video from Telegram: {video_url}")

            video_data = await self.video_processor.download_video(video_url)

            from app.api.capture import capture_item
            await capture_item({
                'url': video_url,
                'title': caption or f"Telegram Video: {video_file_id}",
                'metadata': {
                    'source': 'telegram',
                    'chat_id': chat_id,
                    'message_id': message.get('message_id'),
                    'video_path': video_data.video_path,
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