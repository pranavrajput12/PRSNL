import asyncio
import logging
from typing import Dict, Optional

import yt_dlp

from . import PlatformProcessor

logger = logging.getLogger(__name__)

class TikTokProcessor(PlatformProcessor):
    def __init__(self):
        super().__init__()
        self.ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        })

    def get_platform_name(self) -> str:
        return "tiktok"

    def can_process(self, url: str) -> bool:
        return "tiktok.com" in url

    async def get_info(self, url: str) -> Optional[Dict]:
        opts = self.ydl_opts.copy()
        opts['skip_download'] = True
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=False))
            return info
        except Exception as e:
            logger.error(f"Error getting TikTok video info for {url}: {e}")
            return None

    async def download(self, url: str, output_path: str, progress_hook: Optional[callable] = None) -> Optional[Dict]:
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = output_path
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True))
            return info
        except Exception as e:
            logger.error(f"Error downloading TikTok video from {url}: {e}")
            raise
