"""Video processing service for Instagram and other platforms"""
import yt_dlp
import os
import asyncio
import httpx
from pathlib import Path
from typing import List, Optional, Dict, Callable, Any, Coroutine
from datetime import datetime, timedelta
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import time

import asyncio
import httpx
import os
import json
from pathlib import Path
import logging
import math
import re

import yt_dlp
from PIL import Image

from app.config import settings
from app.services.platforms import PlatformProcessor
from app.services.platforms.instagram import InstagramProcessor
from app.services.platforms.youtube import YouTubeProcessor
from app.services.platforms.twitter import TwitterProcessor
from app.services.platforms.tiktok import TikTokProcessor
from app.monitoring.metrics import VIDEO_PROCESSING_DURATION_SECONDS
from app.services.transcription_service import transcription_service
from app.services.websocket_manager import websocket_manager

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
        self.temp_dir = self.media_dir / "temp" / "processing"
        
        self.videos_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.platform_processors: List[PlatformProcessor] = [
            InstagramProcessor(),
            YouTubeProcessor(),
            TwitterProcessor(),
            TikTokProcessor(),
        ]
        self._progress_callback: Optional[Callable[[Dict], Coroutine[Any, Any, None]]] = None

    def set_progress_callback(self, callback: Callable[[Dict], Coroutine[Any, Any, None]]):
        self._progress_callback = callback

    async def _progress_hook(self, d: Dict):
        if self._progress_callback:
            await self._progress_callback(d)

    def _get_platform_processor(self, url: str) -> Optional[PlatformProcessor]:
        for processor in self.platform_processors:
            if processor.can_process(url):
                return processor
        return None

    async def validate_video_url(self, url: str) -> Dict:
        """
        Validates a video URL and returns basic info without downloading.
        Raises ValueError if validation fails or video exceeds size limits.
        """
        processor = self._get_platform_processor(url)
        if not processor:
            raise ValueError(f"Unsupported video platform for URL: {url}")

        try:
            info = await processor.get_info(url)
            
            if not info:
                raise ValueError("Could not extract video information.")

            # Check file size limit
            file_size_bytes = info.get('filesize') or info.get('filesize_approx')
            if file_size_bytes and file_size_bytes > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
                raise ValueError(f"Video size ({file_size_bytes / (1024*1024):.2f} MB) exceeds maximum allowed size of {settings.MAX_VIDEO_SIZE_MB} MB.")

            # Basic format validation (ensure it's a video)
            if info.get('is_live'):
                raise ValueError("Live streams are not supported.")
            if info.get('extractor') == 'generic' and not info.get('formats'):
                raise ValueError("Could not determine video format. Generic extractor without formats.")

            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': processor.get_platform_name(),
                'filesize': file_size_bytes,
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Video URL validation failed for {url}: {e}")
            raise ValueError(f"Video validation failed: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True,
           retry=retry_if_exception_type((httpx.RequestError, ValueError, FileNotFoundError)))
    async def download_video(self, url: str) -> VideoData:
        """
        Download video from URL, compress, and generate thumbnails.
        """
        processor = self._get_platform_processor(url)
        if not processor:
            raise ValueError(f"Unsupported video platform for URL: {url}")

        temp_video_path = None
        try:
            # Validate first
            video_info_pre_download = await self.validate_video_url(url)
            
            # Ensure temp directory is clean for this download
            for f in self.temp_dir.iterdir():
                if f.is_file() and f.name.startswith(video_info_pre_download.get('id', '')):
                    os.remove(f)
                    logger.info(f"Removed old temp file: {f}")

            # Define output template for yt-dlp
            video_id = video_info_pre_download.get('id', 'unknown')
            original_ext = video_info_pre_download.get('ext', 'mp4')
            output_template = str(self.temp_dir / f"{video_id}.%(ext)s")

            # Download video using the specific processor
            video_info = await processor.download(url, output_template, self._progress_hook)
            
            if not video_info:
                raise ValueError("Failed to download video information.")

            temp_video_path = self.temp_dir / f"{video_id}.{original_ext}"

            if not temp_video_path.exists():
                found_files = list(self.temp_dir.glob(f"{video_id}.*"))
                if not found_files:
                    all_temp_files = sorted(self.temp_dir.iterdir(), key=os.path.getmtime, reverse=True)
                    found_files = [f for f in all_temp_files if f.is_file() and f.suffix in ['.mp4', '.webm', '.mkv', '.mov']]
                
                if not found_files:
                    raise FileNotFoundError(f"Downloaded video file not found in temp directory for {url}. Expected: {temp_video_path}")
                temp_video_path = found_files[0]
                logger.warning(f"Downloaded video path mismatch. Found: {temp_video_path}")

            # Define final video path
            current_year = datetime.now().year
            current_month = datetime.now().month
            final_video_dir = self.videos_dir / str(current_year) / f"{current_month:02d}"
            final_video_dir.mkdir(parents=True, exist_ok=True)
            final_video_path = final_video_dir / f"{video_id}.mp4" # Always convert to mp4

            # Compression and format conversion (if not already mp4 or too large)
            if original_ext != 'mp4' or temp_video_path.stat().st_size > settings.MAX_VIDEO_SIZE_MB * 0.8 * 1024 * 1024: # Compress if > 80% of max size
                logger.info(f"Compressing/converting video {temp_video_path} to {final_video_path}")
                await self._compress_and_convert_video(temp_video_path, final_video_path)
            else:
                logger.info(f"Moving video {temp_video_path} to {final_video_path}")
                await asyncio.to_thread(os.rename, temp_video_path, final_video_path) # Use os.rename for atomic move

            # Generate thumbnails
            thumbnail_path = await self._generate_thumbnails(final_video_path, video_id)
            
            return VideoData(
                url=url,
                title=video_info.get('title', 'Untitled'),
                description=video_info.get('description'),
                author=video_info.get('uploader', video_info.get('channel')),
                duration=video_info.get('duration'),
                video_path=str(final_video_path),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                platform=processor.get_platform_name(),
                metadata={
                    'width': video_info.get('width'),
                    'height': video_info.get('height'),
                    'view_count': video_info.get('view_count'),
                    'like_count': video_info.get('like_count'),
                    'upload_date': video_info.get('upload_date'),
                    'codec': video_info.get('vcodec'),
                    'audio_codec': video_info.get('acodec'),
                    'average_bitrate': video_info.get('average_bitrate'),
                    'filesize': video_info.get('filesize') or video_info.get('filesize_approx')
                },
                downloaded_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error downloading or processing video from {url}: {e}", exc_info=True)
            # Clean up temp file if it exists
            if temp_video_path and temp_video_path.exists():
                await asyncio.to_thread(os.remove, temp_video_path)
                logger.info(f"Cleaned up temp video file: {temp_video_path}")
            raise

    async def _compress_and_convert_video(self, input_path: Path, output_path: Path):
        """
        Compresses and converts video to MP4 using ffmpeg.
        Assumes ffmpeg is available in the environment.
        """
        start_time = time.time()
        # Example: H.264 video, AAC audio, CRF for quality control
        # You might need to adjust CRF (Constant Rate Factor) for desired quality/size
        # Lower CRF means higher quality, larger file. 23 is a good default.
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libx64",
            "-crf", "28", # Adjust as needed (e.g., 23 for higher quality, 30 for more compression)
            "-preset", "fast", # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
            "-c:a", "aac",
            "-b:a", "128k",
            "-vf", "scale='min(1920,iw)':-2", # Scale down if width > 1920, maintain aspect ratio
            "-movflags", "faststart",
            "-y", # Overwrite output file if it exists
            str(output_path)
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_message = f"FFmpeg compression/conversion failed: {stderr.decode()}"
            logger.error(error_message)
            VIDEO_PROCESSING_DURATION_SECONDS.labels(outcome='failed').observe(time.time() - start_time)
            raise RuntimeError(error_message)
        logger.info(f"Video compressed/converted: {output_path}")
        VIDEO_PROCESSING_DURATION_SECONDS.labels(outcome='success').observe(time.time() - start_time)

    async def _generate_thumbnails(self, video_path: Path, video_id: str) -> Optional[Path]:
        """
        Generates multiple thumbnails from the video.
        """
        thumbnail_base_path = self.thumbnails_dir / video_id
        thumbnail_base_path.mkdir(parents=True, exist_ok=True)

        sizes = {
            "small": (320, 180),
            "medium": (640, 360),
            "large": (1280, 720)
        }
        generated_thumbnail_path = None

        for size_name, (width, height) in sizes.items():
            output_thumbnail_path = thumbnail_base_path / f"{size_name}.jpg"
            # Extract frame at 5 seconds or 10% of duration
            # Use ffprobe to get duration if not available in video_info
            
            # For simplicity, let's just use 5 seconds for now.
            # A more robust solution would get video duration first.
            ffmpeg_cmd = [
                "ffmpeg",
                "-ss", "00:00:05", # Seek to 5 seconds
                "-i", str(video_path),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-vframes", "1",
                "-q:v", "2", # Quality
                "-y", # Overwrite
                str(output_thumbnail_path)
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"FFmpeg thumbnail generation failed for {size_name} ({video_path}): {stderr.decode()}")
            else:
                logger.info(f"Generated {size_name} thumbnail: {output_thumbnail_path}")
                if size_name == "medium": # Return path to medium thumbnail as primary
                    generated_thumbnail_path = output_thumbnail_path
        
        return generated_thumbnail_path

    async def transcribe_video(self, video_path: str) -> Optional[str]:
        """Transcribes the given video file."""
        logger.info(f"Starting transcription for video: {video_path}")
        transcription = await transcription_service.transcribe_audio(video_path)
        if transcription:
            logger.info(f"Transcription complete for {video_path}")
            return transcription
        else:
            logger.error(f"Transcription failed for {video_path}")
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
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}).extract_info(url, download=False))
            if not info:
                return None
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': self._detect_platform(url),
                'filesize': info.get('filesize') or info.get('filesize_approx'),
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None

    async def transcribe_video(self, video_path: str) -> Optional[str]:
        """Transcribes the given video file."""
        logger.info(f"Starting transcription for video: {video_path}")
        transcription = await transcription_service.transcribe_audio(video_path)
        if transcription:
            logger.info(f"Transcription complete for {video_path}")
            return transcription
        else:
            logger.error(f"Transcription failed for {video_path}")
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
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}).extract_info(url, download=False))
            if not info:
                return None
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': self._detect_platform(url),
                'filesize': info.get('filesize') or info.get('filesize_approx'),
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
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
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}).extract_info(url, download=False))
            if not info:
                return None
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': self._detect_platform(url),
                'filesize': info.get('filesize') or info.get('filesize_approx'),
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
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
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}).extract_info(url, download=False))
            if not info:
                return None
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': self._detect_platform(url),
                'filesize': info.get('filesize') or info.get('filesize_approx'),
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
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
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video info without downloading
        """
        try:
            info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}).extract_info(url, download=False))
            if not info:
                return None
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'author': info.get('uploader', info.get('channel')),
                'thumbnail': info.get('thumbnail'),
                'platform': self._detect_platform(url),
                'filesize': info.get('filesize') or info.get('filesize_approx'),
                'width': info.get('width'),
                'height': info.get('height'),
                'ext': info.get('ext')
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None