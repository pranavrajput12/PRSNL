"""Video processing service for Instagram and other platforms"""
import yt_dlp
import os
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from PIL import Image
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VideoData:
    """Container for video metadata and file paths"""
    url: str
    title: str
    description: Optional[str]
    author: Optional[str]
    duration: Optional[int]  # in seconds
    video_path: str
    thumbnail_path: Optional[str]
    platform: str
    metadata: Dict
    downloaded_at: datetime


class VideoProcessor:
    """Process and download videos from Instagram and other platforms"""
    
    def __init__(self, media_dir: str = "/app/media"):
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.videos_dir = self.media_dir / "videos"
        self.thumbnails_dir = self.media_dir / "thumbnails"
        self.videos_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        
        # yt-dlp options for Instagram
        self.ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(self.videos_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,  # Can add Instagram cookies if needed
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
    
    async def download_video(self, url: str) -> VideoData:
        """
        Download video from URL (Instagram Reels, Posts, etc.)
        """
        try:
            # Run yt-dlp in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            video_info = await loop.run_in_executor(
                None, self._download_with_ytdlp, url
            )
            
            if not video_info:
                raise ValueError("Failed to download video")
            
            # Extract metadata
            video_id = video_info.get('id', 'unknown')
            video_ext = video_info.get('ext', 'mp4')
            video_path = self.videos_dir / f"{video_id}.{video_ext}"
            
            # Download thumbnail
            thumbnail_path = None
            if video_info.get('thumbnail'):
                thumbnail_path = await self._download_thumbnail(
                    video_info['thumbnail'], video_id
                )
            
            # Detect platform
            platform = self._detect_platform(url)
            
            return VideoData(
                url=url,
                title=video_info.get('title', 'Untitled'),
                description=video_info.get('description'),
                author=video_info.get('uploader', video_info.get('channel')),
                duration=video_info.get('duration'),
                video_path=str(video_path),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                platform=platform,
                metadata={
                    'width': video_info.get('width'),
                    'height': video_info.get('height'),
                    'view_count': video_info.get('view_count'),
                    'like_count': video_info.get('like_count'),
                    'upload_date': video_info.get('upload_date'),
                },
                downloaded_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error downloading video from {url}: {str(e)}")
            raise
    
    def _download_with_ytdlp(self, url: str) -> Dict:
        """
        Download video using yt-dlp (blocking operation)
        """
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                # Download the video
                ydl.download([url])
                
                return info
            except Exception as e:
                logger.error(f"yt-dlp error: {str(e)}")
                raise
    
    async def _download_thumbnail(self, thumbnail_url: str, video_id: str) -> Optional[Path]:
        """
        Download and save thumbnail
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(thumbnail_url)
                response.raise_for_status()
                
                # Save thumbnail
                thumbnail_path = self.thumbnails_dir / f"{video_id}.jpg"
                thumbnail_path.write_bytes(response.content)
                
                # Optionally resize thumbnail
                img = Image.open(thumbnail_path)
                img.thumbnail((640, 640), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
                
                return thumbnail_path
                
        except Exception as e:
            logger.error(f"Error downloading thumbnail: {str(e)}")
            return None
    
    def _detect_platform(self, url: str) -> str:
        """
        Detect the platform from URL
        """
        if 'instagram.com' in url:
            if '/reel/' in url:
                return 'instagram_reel'
            elif '/p/' in url:
                return 'instagram_post'
            else:
                return 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        else:
            return 'unknown'
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        opts = self.ydl_opts.copy()
        opts['skip_download'] = True
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'author': info.get('uploader'),
                    'thumbnail': info.get('thumbnail'),
                    'platform': self._detect_platform(url)
                }
            except Exception as e:
                logger.error(f"Error getting video info: {str(e)}")
                return None