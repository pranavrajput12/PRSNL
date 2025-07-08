from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.telegram_bot import TelegramBot
from app.config import settings
from typing import Optional, Dict

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
    
    
    
    return {"ok": True}