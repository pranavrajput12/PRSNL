"""
Image Processing Service - Extract and store images from content
"""
import asyncio
import httpx
import hashlib
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import logging
from pathlib import Path
from PIL import Image
from io import BytesIO
from app.utils.media_detector import MediaDetector
from app.config import settings

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Process and store images from articles and web pages"""
    
    def __init__(self):
        self.media_dir = Path(settings.MEDIA_DIR) if hasattr(settings, 'MEDIA_DIR') else Path("/app/media")
        self.images_dir = self.media_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Image processing settings
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (400, 400),
            'large': (800, 800)
        }
    
    async def process_article_images(
        self, 
        item_id: str,
        html_content: str, 
        base_url: str
    ) -> List[Dict[str, any]]:
        """
        Extract and store images from an article
        
        Returns:
            List of image metadata dictionaries
        """
        try:
            # Extract image URLs from HTML
            images = MediaDetector.extract_images_from_html(html_content, base_url)
            
            if not images:
                logger.info(f"No images found in article {item_id}")
                return []
            
            # Process each image
            processed_images = []
            async with httpx.AsyncClient() as client:
                for img_info in images[:10]:  # Limit to 10 images per article
                    try:
                        image_data = await self._download_and_process_image(
                            client,
                            item_id,
                            img_info['url'],
                            img_info
                        )
                        
                        if image_data:
                            processed_images.append(image_data)
                    
                    except Exception as e:
                        logger.error(f"Error processing image {img_info['url']}: {str(e)}")
                        continue
            
            logger.info(f"Processed {len(processed_images)} images for item {item_id}")
            return processed_images
            
        except Exception as e:
            logger.error(f"Error processing article images: {str(e)}")
            return []