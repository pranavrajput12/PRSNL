"""
Media Detection Utilities - Detect videos, images, and other media types
"""
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, List, Tuple
import mimetypes

class MediaDetector:
    """Detect and extract information about media content"""
    
    # Video platforms and their patterns
    VIDEO_PATTERNS = {
        'youtube': [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ],
        'vimeo': [
            r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)',
            r'(?:https?://)?player\.vimeo\.com/video/(\d+)'
        ],
        'twitter': [
            r'(?:https?://)?(?:www\.)?twitter\.com/\w+/status/(\d+)/video/\d+',
            r'(?:https?://)?(?:www\.)?x\.com/\w+/status/(\d+)/video/\d+',
            # NOTE: Regular status URLs require content analysis to determine if video
        ],
        'instagram': [
            # Instagram Reels are definitely videos
            r'(?:https?://)?(?:www\.)?instagram\.com/reel/([a-zA-Z0-9_-]+)',
            # Instagram TV is definitely videos  
            r'(?:https?://)?(?:www\.)?instagram\.com/tv/([a-zA-Z0-9_-]+)',
            # NOTE: Regular posts (/p/) can be images or videos, need content analysis
        ],
        'dailymotion': [
            r'(?:https?://)?(?:www\.)?dailymotion\.com/video/([a-zA-Z0-9]+)'
        ],
        'twitch': [
            r'(?:https?://)?(?:www\.)?twitch\.tv/videos/(\d+)',
            r'(?:https?://)?clips\.twitch\.tv/([a-zA-Z0-9_-]+)'
        ]
    }
    
    # Image file extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.tiff'}
    
    # Video file extensions
    VIDEO_FILE_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    @classmethod
    def detect_media_type(cls, url: str) -> Dict[str, any]:
        """
        Detect the type of media from a URL
        
        Returns:
            Dict with media information:
            - type: 'video', 'image', 'article', etc.
            - platform: For videos, the platform name
            - id: For videos, the video ID
            - embed_url: For videos, the embed URL
            - direct_url: For images/videos, the direct media URL
        """
        # Check if it's a video platform (including Twitter)
        video_info = cls.detect_video_platform(url)
        if video_info:
            # For Twitter, we'll let yt-dlp determine if it's actually a video
            # during the validation phase
            return {
                'type': 'video',
                'platform': video_info['platform'],
                'id': video_info['id'],
                'embed_url': video_info['embed_url'],
                'metadata': video_info
            }
        
        # Check if it's a direct media file
        parsed = urlparse(url.lower())
        path = parsed.path
        
        # Check for image
        if any(path.endswith(ext) for ext in cls.IMAGE_EXTENSIONS):
            return {
                'type': 'image',
                'direct_url': url,
                'format': path.split('.')[-1]
            }
        
        # Check for video file
        if any(path.endswith(ext) for ext in cls.VIDEO_FILE_EXTENSIONS):
            return {
                'type': 'video_file',
                'direct_url': url,
                'format': path.split('.')[-1]
            }
        
        # Check content type if available
        mime_type, _ = mimetypes.guess_type(url)
        if mime_type:
            if mime_type.startswith('image/'):
                return {
                    'type': 'image',
                    'direct_url': url,
                    'mime_type': mime_type
                }
            elif mime_type.startswith('video/'):
                return {
                    'type': 'video_file',
                    'direct_url': url,
                    'mime_type': mime_type
                }
        
        # Default to article/webpage
        return {
            'type': 'article',
            'url': url
        }
    
    @classmethod
    def detect_video_platform(cls, url: str) -> Optional[Dict[str, str]]:
        """
        Detect video platform and extract video ID
        """
        for platform, patterns in cls.VIDEO_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    video_id = match.group(1)
                    return {
                        'platform': platform,
                        'id': video_id,
                        'embed_url': cls.get_embed_url(platform, video_id),
                        'thumbnail_url': cls.get_thumbnail_url(platform, video_id)
                    }
        return None
    
    @classmethod
    def is_ambiguous_media_url(cls, url: str) -> bool:
        """
        Check if URL could be either video or image (requires content analysis)
        """
        ambiguous_patterns = [
            r'(?:https?://)?(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)',  # Instagram posts
            r'(?:https?://)?(?:www\.)?twitter\.com/\w+/status/(\d+)(?!/video)',  # Twitter posts without /video
            r'(?:https?://)?(?:www\.)?x\.com/\w+/status/(\d+)(?!/video)',  # X posts without /video
        ]
        
        for pattern in ambiguous_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def get_embed_url(cls, platform: str, video_id: str) -> str:
        """
        Get the embed URL for a video
        """
        embed_templates = {
            'youtube': 'https://www.youtube.com/embed/{id}',
            'vimeo': 'https://player.vimeo.com/video/{id}',
            'dailymotion': 'https://www.dailymotion.com/embed/video/{id}',
            'twitch': 'https://player.twitch.tv/?video={id}&parent=localhost',
        }
        
        template = embed_templates.get(platform)
        if template:
            return template.format(id=video_id)
        
        # For platforms without standard embeds
        return ''
    
    @classmethod
    def get_thumbnail_url(cls, platform: str, video_id: str) -> Optional[str]:
        """
        Get thumbnail URL for a video
        """
        thumbnail_templates = {
            'youtube': 'https://img.youtube.com/vi/{id}/maxresdefault.jpg',
            'vimeo': 'https://vumbnail.com/{id}.jpg',
            'dailymotion': 'https://www.dailymotion.com/thumbnail/video/{id}'
        }
        
        template = thumbnail_templates.get(platform)
        if template:
            return template.format(id=video_id)
        return None
    
    @classmethod
    def extract_images_from_html(cls, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract image URLs from HTML content
        """
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Make URL absolute
                full_url = urljoin(base_url, src)
                
                # Get additional attributes
                alt = img.get('alt', '')
                title = img.get('title', '')
                
                # Skip small images (likely icons)
                width = img.get('width', '')
                height = img.get('height', '')
                if width and height:
                    try:
                        if int(width) < 100 or int(height) < 100:
                            continue
                    except:
                        pass
                
                images.append({
                    'url': full_url,
                    'alt': alt,
                    'title': title,
                    'original_src': src
                })
        
        # Also check for og:image meta tags
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.insert(0, {
                'url': urljoin(base_url, og_image['content']),
                'alt': 'Featured image',
                'title': 'Featured image',
                'is_featured': True
            })
        
        return images
    
    @classmethod
    def should_store_image(cls, image_url: str, image_info: Dict) -> bool:
        """
        Determine if an image should be stored
        """
        # Skip data URLs
        if image_url.startswith('data:'):
            return False
        
        # Skip tracking pixels and tiny images
        suspicious_patterns = [
            r'pixel\.gif',
            r'tracking',
            r'analytics',
            r'beacon',
            r'1x1',
            r'spacer\.gif'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, image_url, re.IGNORECASE):
                return False
        
        # Skip if marked as featured (usually we want these)
        if image_info.get('is_featured'):
            return True
        
        # Otherwise store it
        return True