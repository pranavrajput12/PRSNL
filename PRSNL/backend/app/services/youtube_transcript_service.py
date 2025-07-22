"""
YouTube Transcript Service with multiple fallback methods
Handles transcript extraction with robust error handling
"""
import asyncio
import json
import logging
import re
import tempfile
import os
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class YouTubeTranscriptService:
    """Service for extracting YouTube video transcripts with multiple fallback methods"""
    
    def __init__(self):
        self.supported_languages = ['en', 'en-US', 'en-GB', 'en-AU', 'en-CA']
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum seconds between requests
        
    async def extract_transcript(self, video_url: str) -> Tuple[str, List[Dict]]:
        """
        Extract transcript from YouTube video using multiple methods
        
        Returns:
            Tuple of (transcript_text, key_moments)
        """
        video_id = self._extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return "", []
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Try multiple extraction methods in order
        methods = [
            ("youtube_transcript_api", self._extract_with_youtube_transcript_api),
            ("yt-dlp direct", self._extract_with_ytdlp_direct),
            ("yt-dlp download", self._extract_with_ytdlp_download),
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Attempting transcript extraction with {method_name}")
                transcript_text, key_moments = await method_func(video_id, video_url)
                if transcript_text:
                    logger.info(f"Success with {method_name}: {len(transcript_text)} characters")
                    return transcript_text, key_moments
            except Exception as e:
                error_str = str(e)
                # Check for rate limiting
                if '429' in error_str or 'Too Many Requests' in error_str:
                    logger.warning(f"{method_name} rate limited, waiting before next attempt...")
                    await asyncio.sleep(5)  # Extra wait for rate limiting
                else:
                    logger.warning(f"{method_name} failed: {error_str}")
                continue
        
        logger.warning(f"All transcript extraction methods failed for {video_url}")
        return "", []
    
    async def _apply_rate_limit(self):
        """Apply rate limiting to avoid 429 errors"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _extract_with_youtube_transcript_api(self, video_id: str, video_url: str) -> Tuple[str, List[Dict]]:
        """Method 1: Use youtube_transcript_api library"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
            
            # Try to get transcript
            transcript_entries = []
            
            # Try preferred languages first
            for lang in self.supported_languages:
                try:
                    transcript_entries = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    logger.info(f"Found transcript in {lang}")
                    break
                except (TranscriptsDisabled, NoTranscriptFound):
                    continue
            
            # If no preferred language, try to get any available
            if not transcript_entries:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    try:
                        transcript_entries = transcript.fetch()
                        logger.info(f"Found transcript in {transcript.language} (auto-generated: {transcript.is_generated})")
                        break
                    except:
                        continue
            
            if transcript_entries:
                # Process transcript
                transcript_text = " ".join([entry['text'] for entry in transcript_entries])
                key_moments = self._extract_key_moments(transcript_entries)
                return transcript_text, key_moments
                
        except Exception as e:
            logger.debug(f"youtube_transcript_api error: {str(e)}")
            raise
        
        return "", []
    
    async def _extract_with_ytdlp_direct(self, video_id: str, video_url: str) -> Tuple[str, List[Dict]]:
        """Method 2: Use yt-dlp to get subtitle URLs and fetch directly"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Check for subtitles
                subtitle_url = None
                
                # Check manual subtitles first
                if 'subtitles' in info:
                    for lang in self.supported_languages:
                        if lang in info['subtitles']:
                            for sub in info['subtitles'][lang]:
                                if sub.get('ext') in ['vtt', 'srv3', 'srv2', 'srv1']:
                                    subtitle_url = sub.get('url')
                                    break
                            if subtitle_url:
                                break
                
                # Check automatic captions
                if not subtitle_url and 'automatic_captions' in info:
                    for lang in self.supported_languages:
                        if lang in info['automatic_captions']:
                            for sub in info['automatic_captions'][lang]:
                                if sub.get('ext') in ['vtt', 'srv3', 'srv2', 'srv1']:
                                    subtitle_url = sub.get('url')
                                    break
                            if subtitle_url:
                                break
                
                if subtitle_url:
                    # Fetch and parse subtitles
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(subtitle_url)
                        if response.status_code == 200:
                            transcript_text = self._parse_subtitle_content(response.text)
                            return transcript_text, []
                            
        except Exception as e:
            logger.debug(f"yt-dlp direct method error: {str(e)}")
            raise
        
        return "", []
    
    async def _extract_with_ytdlp_download(self, video_id: str, video_url: str) -> Tuple[str, List[Dict]]:
        """Method 3: Use yt-dlp to download subtitles to file"""
        try:
            import yt_dlp
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
                
                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': self.supported_languages,
                    'outtmpl': output_path,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.download([video_url])
                    
                    # Look for downloaded subtitle files
                    for lang in self.supported_languages:
                        for ext in ['vtt', 'srt', 'ass']:
                            subtitle_files = [f for f in os.listdir(temp_dir) 
                                           if f.endswith(f'.{lang}.{ext}')]
                            
                            if subtitle_files:
                                subtitle_path = os.path.join(temp_dir, subtitle_files[0])
                                with open(subtitle_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    transcript_text = self._parse_subtitle_content(content)
                                    return transcript_text, []
                                    
        except Exception as e:
            logger.debug(f"yt-dlp download method error: {str(e)}")
            raise
        
        return "", []
    
    def _parse_subtitle_content(self, content: str) -> str:
        """Parse various subtitle formats to extract plain text"""
        lines = content.split('\n')
        text_lines = []
        
        # Simple parsing for common formats
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip timecodes (e.g., "00:00:00,000 --> 00:00:05,000")
            if '-->' in line:
                continue
            # Skip numbers (subtitle indices)
            if line.isdigit():
                continue
            # Skip VTT headers
            if line.startswith('WEBVTT') or line.startswith('NOTE'):
                continue
            # Remove HTML-like tags
            line = re.sub(r'<[^>]+>', '', line)
            # Add the cleaned line
            if line:
                text_lines.append(line)
        
        return ' '.join(text_lines)
    
    def _extract_key_moments(self, transcript_entries: List[Dict]) -> List[Dict]:
        """Extract key moments from transcript entries"""
        key_moments = []
        
        # Sample key moments at regular intervals
        total_entries = len(transcript_entries)
        if total_entries > 0:
            interval = max(1, total_entries // 10)  # Get ~10 key moments
            
            for i in range(0, total_entries, interval):
                entry = transcript_entries[i]
                key_moments.append({
                    'timestamp': self._format_timestamp(entry.get('start', 0)),
                    'text': entry.get('text', '')[:100],
                    'start_seconds': entry.get('start', 0)
                })
        
        return key_moments[:10]  # Limit to 10 key moments
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


# Singleton instance
youtube_transcript_service = YouTubeTranscriptService()