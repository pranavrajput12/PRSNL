# TELEGRAM BOT INTEGRATION - PRSNL

## Overview
Add Telegram bot integration to PRSNL for capturing links/videos sent via Telegram - **100% FREE**!

## Why Telegram?
- ✅ Completely FREE (no API costs)
- ✅ Official Bot API with Python library
- ✅ Supports all media types (links, videos, images, documents)
- ✅ Works on all devices
- ✅ Real-time updates via webhooks or polling
- ✅ No rate limits for personal use

## Architecture

```
User sends link/video to Telegram Bot
                ↓
        Telegram Bot API
                ↓
    PRSNL Backend (webhook endpoint)
                ↓
    Process & Store in Database
                ↓
    Available in PRSNL Timeline
```

## Implementation Plan

### Step 1: Create Telegram Bot
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Choose name: "PRSNL Capture Bot"
4. Get bot token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Backend Integration

#### New Files to Create:
```
/PRSNL/backend/app/services/telegram_bot.py
/PRSNL/backend/app/api/telegram.py
```

#### telegram_bot.py:
```python
import httpx
from typing import Optional, Dict
import logging
from app.core.capture_engine import CaptureEngine

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
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
```

#### telegram.py (API endpoint):
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.telegram_bot import TelegramBot
from app.config import settings

router = APIRouter()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Dict] = None

@router.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming Telegram updates"""
    if not update.message:
        return {"ok": True}
        
    bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    
    # Process the message
    success = await bot.process_message(update.message)
    
    # Send confirmation back to user
    if success:
        chat_id = update.message['chat']['id']
        await bot.send_message(chat_id, "✅ Captured successfully!")
    
    return {"ok": True}
```

### Step 3: Configuration

#### Add to .env:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET=generate_random_secret
```

#### Update config.py:
```python
TELEGRAM_BOT_TOKEN: str = ""
TELEGRAM_WEBHOOK_SECRET: str = ""
```

### Step 4: Setup Webhook (or Polling)

#### Option A: Webhook (Recommended for production)
```python
# Set webhook to your server
async def setup_telegram_webhook():
    bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    webhook_url = f"https://your-domain.com/api/telegram/webhook"
    await bot.set_webhook(webhook_url)
```

#### Option B: Polling (For local development)
```python
# Poll for updates (runs in background)
async def telegram_polling():
    bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    offset = 0
    
    while True:
        updates = await bot.get_updates(offset)
        for update in updates:
            await bot.process_message(update['message'])
            offset = update['update_id'] + 1
        
        await asyncio.sleep(1)
```

### Step 5: User Experience

1. User adds @YourPRSNLBot on Telegram
2. User sends `/start` to initialize
3. User sends any link or video
4. Bot responds: "✅ Captured successfully!"
5. Item appears in PRSNL timeline

### Supported Message Types:
- Text with URLs
- Videos (downloaded directly)
- Images with captions
- Documents (PDFs, etc.)
- Forwarded messages

## Testing Locally

1. Use ngrok for webhook testing:
```bash
ngrok http 8000
# Use the HTTPS URL for webhook
```

2. Or use polling mode for local dev

## Security Considerations

1. Validate webhook secret
2. Only accept messages from authorized users
3. Rate limit per user
4. Sanitize all input

## Database Migration

No need to migrate to Supabase! Current PostgreSQL setup works perfectly with Telegram bot.

## Cost: $0
- Telegram Bot API: FREE
- No hosting costs (runs on existing backend)
- No API limits for personal use
- No subscription fees