"""
Jina Reader Service - Simple and effective web content extraction
Just prepend https://r.jina.ai/ to any URL
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class JinaReaderService:
    """Simple web content extraction using Jina Reader API"""
    
    def __init__(self):
        self.base_url = "https://r.jina.ai/"
        self.timeout = 30
        self.enabled = True  # Always enabled, no API key needed
        
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape URL content using Jina Reader
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with content and metadata
        """
        try:
            # Jina Reader: just prepend https://r.jina.ai/ to the URL
            jina_url = f"{self.base_url}{url}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(jina_url)
                response.raise_for_status()
                
                content = response.text
                
                # Extract title from content if available
                title = ""
                lines = content.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if line.strip() and len(line.strip()) > 10:
                        if not line.startswith('#') and not line.startswith('http'):
                            title = line.strip()
                            break
                
                return {
                    "success": True,
                    "data": {
                        "content": content,
                        "markdown": content,
                        "title": title,
                        "sourceURL": url,
                        "description": content[:200] + "..." if len(content) > 200 else content,
                        "language": "en",  # Default
                        "scraper_used": "jina"
                    }
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "success": False,
                "error": str(e)
            }