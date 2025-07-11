"""
Firecrawl Web Scraping Service for PRSNL
Advanced web scraping with JS rendering and content extraction
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from urllib.parse import urljoin, urlparse

from app.config import settings

logger = logging.getLogger(__name__)


class FirecrawlService:
    """Advanced web scraping service using Firecrawl API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'FIRECRAWL_API_KEY', None)
        self.enabled = bool(self.api_key)
        self.base_url = getattr(settings, 'FIRECRAWL_BASE_URL', 'https://api.firecrawl.dev')
        self.timeout = 30
        
        if not self.enabled:
            logger.warning("Firecrawl service disabled. API key not configured.")
        else:
            logger.info("Firecrawl service enabled with API key")
    
    async def scrape_url(self, 
                        url: str, 
                        extract_content: bool = True,
                        include_markdown: bool = True,
                        include_html: bool = False,
                        include_links: bool = True,
                        include_images: bool = True,
                        wait_for: Optional[int] = None,
                        headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Scrape a single URL with advanced options
        
        Args:
            url: URL to scrape
            extract_content: Extract clean content
            include_markdown: Include markdown format
            include_html: Include raw HTML
            include_links: Extract links
            include_images: Extract images
            wait_for: Milliseconds to wait for JS rendering
            headers: Custom headers
        
        Returns:
            Scraped content and metadata
        """
        if not self.enabled:
            return {"error": "Firecrawl service not enabled"}
        
        try:
            request_data = {
                "url": url,
                "extractorOptions": {
                    "mode": "llm-extraction-from-markdown" if extract_content else "markdown",
                    "extractionPrompt": "Extract the main content, title, and key information from this webpage."
                },
                "pageOptions": {
                    "includeHtml": include_html,
                    "includeMarkdown": include_markdown,
                    "includeLinks": include_links,
                    "includeImages": include_images,
                    "waitFor": wait_for or 3000,
                    "headers": headers or {}
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/scrape",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return {
                        "success": True,
                        "content": result.get("data", {}).get("content", ""),
                        "markdown": result.get("data", {}).get("markdown", ""),
                        "html": result.get("data", {}).get("html", ""),
                        "title": result.get("data", {}).get("title", ""),
                        "description": result.get("data", {}).get("description", ""),
                        "url": url,
                        "links": result.get("data", {}).get("links", []),
                        "images": result.get("data", {}).get("images", []),
                        "metadata": result.get("data", {}).get("metadata", {}),
                        "scraped_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "url": url
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout scraping {url}")
            return {"success": False, "error": "Request timeout", "url": url}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            return {"success": False, "error": f"HTTP {e.response.status_code}", "url": url}
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"success": False, "error": str(e), "url": url}
    
    async def crawl_website(self, 
                           url: str, 
                           max_pages: int = 10,
                           include_paths: Optional[List[str]] = None,
                           exclude_paths: Optional[List[str]] = None,
                           max_depth: int = 2,
                           allow_backward_links: bool = True,
                           allow_external_links: bool = False) -> Dict[str, Any]:
        """
        Crawl an entire website with configurable limits
        
        Args:
            url: Starting URL
            max_pages: Maximum pages to crawl
            include_paths: URL patterns to include
            exclude_paths: URL patterns to exclude
            max_depth: Maximum crawl depth
            allow_backward_links: Allow links to parent pages
            allow_external_links: Allow external domain links
        
        Returns:
            Crawl results with all pages
        """
        if not self.enabled:
            return {"error": "Firecrawl service not enabled"}
        
        try:
            request_data = {
                "url": url,
                "crawlerOptions": {
                    "maxPages": max_pages,
                    "includePaths": include_paths or [],
                    "excludePaths": exclude_paths or [],
                    "maxDepth": max_depth,
                    "allowBackwardLinks": allow_backward_links,
                    "allowExternalLinks": allow_external_links
                },
                "pageOptions": {
                    "includeHtml": False,
                    "includeMarkdown": True,
                    "includeLinks": True,
                    "includeImages": True,
                    "waitFor": 3000
                }
            }
            
            async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout for crawling
                response = await client.post(
                    f"{self.base_url}/v1/crawl",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return {
                        "success": True,
                        "job_id": result.get("jobId"),
                        "pages": result.get("data", []),
                        "total_pages": len(result.get("data", [])),
                        "crawled_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown crawl error")
                    }
                    
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_structured_data(self, 
                                    url: str, 
                                    schema: Dict[str, Any],
                                    extraction_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using AI
        
        Args:
            url: URL to extract from
            schema: JSON schema for extraction
            extraction_prompt: Custom extraction prompt
        
        Returns:
            Extracted structured data
        """
        if not self.enabled:
            return {"error": "Firecrawl service not enabled"}
        
        try:
            request_data = {
                "url": url,
                "extractorOptions": {
                    "mode": "llm-extraction",
                    "extractionPrompt": extraction_prompt or "Extract structured data according to the provided schema",
                    "extractionSchema": schema
                },
                "pageOptions": {
                    "includeHtml": False,
                    "includeMarkdown": True,
                    "waitFor": 3000
                }
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/v1/scrape",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return {
                        "success": True,
                        "data": result.get("data", {}).get("llm_extraction", {}),
                        "url": url,
                        "extracted_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown extraction error"),
                        "url": url
                    }
                    
        except Exception as e:
            logger.error(f"Error extracting from {url}: {e}")
            return {"success": False, "error": str(e), "url": url}
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a crawl job"""
        if not self.enabled:
            return {"error": "Firecrawl service not enabled"}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/v1/crawl/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return {"error": str(e)}
    
    async def batch_scrape(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        if not self.enabled:
            return [{"error": "Firecrawl service not enabled"} for _ in urls]
        
        # Limit concurrent requests to avoid rate limiting
        semaphore = asyncio.Semaphore(5)
        
        async def scrape_with_limit(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.scrape_url(url, **kwargs)
        
        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "url": urls[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and scrapeable"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except:
            return False
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return ""


# Singleton instance
firecrawl_service = FirecrawlService()