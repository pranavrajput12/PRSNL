"""Web scraping service with MarkItDown enhancement"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin
import tempfile
import os

import httpx
from bs4 import BeautifulSoup
from readability.readability import Document
from markitdown import MarkItDown

logger = logging.getLogger(__name__)


@dataclass
class ScrapedData:
    url: str
    title: Optional[str]
    content: Optional[str]
    html: Optional[str]
    author: Optional[str]
    published_date: Optional[str]
    scraped_at: datetime
    images: List[Dict[str, str]] = field(default_factory=list)


class WebScraper:
    """Scrapes and extracts content from web pages with MarkItDown enhancement"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        self.markitdown = MarkItDown()  # Initialize MarkItDown processor
    
    async def scrape(self, url: str) -> ScrapedData:
        """
        Scrape a URL and extract content from meta tags
        """
        try:
            # Fetch the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title - prioritize og:title, fallback to title tag
            title = None
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title.get('content').strip()
            else:
                title_tag = soup.find('title')
                if title_tag and title_tag.text:
                    title = title_tag.text.strip()
            
            # Extract content from meta description with fallbacks
            content = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = meta_desc.get('content').strip()
            else:
                og_desc = soup.find('meta', property='og:description')
                if og_desc and og_desc.get('content'):
                    content = og_desc.get('content').strip()
            
            # Enhanced fallback: use MarkItDown, then readability, then basic extraction
            if not content or len(content) < 50:
                try:
                    # First, try MarkItDown for better HTML processing
                    markitdown_content = await self._extract_with_markitdown(response.text, url)
                    if markitdown_content and len(markitdown_content) > 50:
                        content = markitdown_content
                    else:
                        # Fallback to readability
                        doc = Document(response.text)
                        readable_content = doc.summary()
                        if readable_content:
                            readable_soup = BeautifulSoup(readable_content, 'html.parser')
                            content = readable_soup.get_text(strip=True)[:500] + "..."
                        
                        # If readability fails, try first paragraph
                        if not content or len(content) < 50:
                            paragraphs = soup.find_all(['p', 'article', 'main'])
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if len(text) > 50:
                                    content = text[:500] + ("..." if len(text) > 500 else "")
                                    break
                        
                        # Final fallback: use title as content
                        if not content and title:
                            content = f"Content from {url}: {title}"
                        
                except Exception as e:
                    logger.warning(f"Enhanced content extraction failed for {url}: {e}")
                    content = f"Content from {url}: {title or 'Web page'}"
            
            # Extract basic metadata  
            author = None
            published_date = None
            images = []
            
            return ScrapedData(
                url=url,
                title=title,
                content=content,
                html=response.text,
                author=author,
                published_date=published_date,
                scraped_at=datetime.now(),
                images=images
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
            return ScrapedData(
                url=url,
                title=None,
                content=None,
                html=None,
                author=None,
                published_date=None,
                scraped_at=datetime.now()
            )
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract images from the page
        """
        images = []
        seen_urls = set()
        
        # Find all img tags
        for img in soup.find_all('img'):
            img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not img_url:
                continue
                
            # Make absolute URL if relative
            if not img_url.startswith(('http://', 'https://', 'data:')):
                img_url = urljoin(base_url, img_url)
            
            # Skip if already seen or if it's a data URL
            if img_url in seen_urls or img_url.startswith('data:'):
                continue
                
            seen_urls.add(img_url)
            
            # Extract image metadata
            images.append({
                'url': img_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
            
            # Limit to first 10 images
            if len(images) >= 10:
                break
        
        # Also check for Open Graph and Twitter Card images
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin(base_url, img_url)
            if img_url not in seen_urls:
                images.insert(0, {
                    'url': img_url,
                    'alt': 'Article preview image',
                    'title': 'Open Graph image',
                    'width': '',
                    'height': ''
                })
        
        return images
    

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Try to extract author from meta tags
        """
        # Common author meta tags
        author_selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'twitter:creator'}),
            ('span', {'class': 'author'}),
            ('a', {'rel': 'author'})
        ]
        
        for tag, attrs in author_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content')
                else:
                    return element.get_text(strip=True)
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Try to extract publish date from meta tags
        """
        # Common date meta tags
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publish_date'}),
            ('meta', {'name': 'DC.date.issued'}),
            ('time', {'datetime': True})
        ]
        
        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content')
                elif tag == 'time':
                    return element.get('datetime')
        
        return None
    
    async def _extract_with_markitdown(self, html_content: str, url: str) -> Optional[str]:
        """Extract content using MarkItDown for better HTML processing"""
        try:
            # Create temporary HTML file for MarkItDown processing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with MarkItDown
                result = self.markitdown.convert(temp_file_path)
                
                # Extract text content
                text_content = result.text_content if hasattr(result, 'text_content') else str(result)
                
                # Clean and format the content
                if text_content:
                    # Remove excessive whitespace
                    cleaned_content = ' '.join(text_content.split())
                    
                    # Truncate to reasonable length for preview
                    if len(cleaned_content) > 1000:
                        cleaned_content = cleaned_content[:1000] + "..."
                    
                    logger.info(f"MarkItDown successfully extracted {len(cleaned_content)} characters from {url}")
                    return cleaned_content
                
                return None
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.warning(f"MarkItDown HTML extraction failed for {url}: {e}")
            return None
    
    async def scrape_with_markitdown(self, url: str) -> ScrapedData:
        """
        Enhanced scraping method that uses MarkItDown for full content extraction
        """
        try:
            # Fetch the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Use MarkItDown to extract full content
            markitdown_content = await self._extract_with_markitdown(response.text, url)
            
            # Parse with BeautifulSoup for metadata
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = None
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title.get('content').strip()
            else:
                title_tag = soup.find('title')
                if title_tag and title_tag.text:
                    title = title_tag.text.strip()
            
            # Use MarkItDown content as primary content
            content = markitdown_content
            
            # Fallback to meta description if MarkItDown fails
            if not content:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    content = meta_desc.get('content').strip()
                else:
                    og_desc = soup.find('meta', property='og:description')
                    if og_desc and og_desc.get('content'):
                        content = og_desc.get('content').strip()
            
            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_publish_date(soup)
            images = self._extract_images(soup, url)
            
            return ScrapedData(
                url=url,
                title=title,
                content=content,
                html=response.text,
                author=author,
                published_date=published_date,
                scraped_at=datetime.now(),
                images=images
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url} with MarkItDown: {str(e)}", exc_info=True)
            # Fallback to regular scraping
            return await self.scrape(url)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()