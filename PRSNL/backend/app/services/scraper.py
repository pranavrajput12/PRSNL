"""Web scraping service"""
import httpx
from bs4 import BeautifulSoup
from readability.readability import Document
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
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
                scraped_at=datetime.now()
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