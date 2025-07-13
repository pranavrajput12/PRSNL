from abc import ABC, abstractmethod
from typing import Dict, Optional


class PlatformProcessor(ABC):
    """Abstract base class for platform-specific video processors."""

    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 5,
            'concurrent_fragment_downloads': 5,
            'buffer_size': '10M',
            'continuedl': True,
            'nopart': True,
            'trim_filenames': 200,
            'throttled_rate': '10M', # Limit download speed to 10MB/s
            'ffmpeg_location': '/opt/homebrew/bin',  # Set ffmpeg location for ARM64
        }

    @abstractmethod
    def get_platform_name(self) -> str:
        """Returns the name of the platform."""
        pass

    @abstractmethod
    def can_process(self, url: str) -> bool:
        """Checks if this processor can handle the given URL."""
        pass

    @abstractmethod
    async def get_info(self, url: str) -> Optional[Dict]:
        """Extracts video information without downloading."""
        pass

    @abstractmethod
    async def download(self, url: str, output_path: str, progress_hook: Optional[callable] = None) -> Optional[Dict]:
        """Downloads the video and returns its info."""
        pass
