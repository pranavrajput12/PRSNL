"""Web scraping service"""
import httpx
from bs4 import BeautifulSoup
from readability.readability import Document
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from urllib.parse import urljoin
import logging

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
    """Scrapes and extracts content from web pages"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; PRSNL/1.0; +http://localhost)"
            }
        )
    
    async def scrape(self, url: str) -> ScrapedData:
        """
        Scrape a URL and extract content
        """
        try:
            # Fetch the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Use readability for content extraction
            doc = Document(html)
            article = doc.summary()
            title = doc.title()
            
            # Parse with BeautifulSoup for additional extraction
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract images before stripping HTML
            images = self._extract_images(soup, url)
            
            # Extract text content
            article_soup = BeautifulSoup(article, 'html.parser')
            content = article_soup.get_text(separator='\n', strip=True)
            
            # Try to extract author
            author = self._extract_author(soup)
            
            # Try to extract publish date
            published_date = self._extract_publish_date(soup)
            
            return ScrapedData(
                url=url,
                title=title,
                content=content,
                html=html,
                author=author,
                published_date=published_date,
                scraped_at=datetime.now(),
                images=images
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
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
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()