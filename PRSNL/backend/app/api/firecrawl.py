"""
Firecrawl API endpoints for advanced web scraping
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
import logging
from datetime import datetime

from app.services.firecrawl_service import firecrawl_service
from app.core.auth import get_current_user_optional
from app.db.database import get_db_pool
import asyncpg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/firecrawl", tags=["Firecrawl"])


# Request/Response Models
class ScrapingRequest(BaseModel):
    """Request model for single URL scraping"""
    url: HttpUrl = Field(..., description="URL to scrape")
    extract_content: bool = Field(True, description="Extract clean content")
    include_markdown: bool = Field(True, description="Include markdown format")
    include_html: bool = Field(False, description="Include raw HTML")
    include_links: bool = Field(True, description="Extract links")
    include_images: bool = Field(True, description="Extract images")
    wait_for: Optional[int] = Field(None, description="Milliseconds to wait for JS rendering")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")


class CrawlingRequest(BaseModel):
    """Request model for website crawling"""
    url: HttpUrl = Field(..., description="Starting URL")
    max_pages: int = Field(10, ge=1, le=100, description="Maximum pages to crawl")
    include_paths: Optional[List[str]] = Field(None, description="URL patterns to include")
    exclude_paths: Optional[List[str]] = Field(None, description="URL patterns to exclude")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum crawl depth")
    allow_backward_links: bool = Field(True, description="Allow links to parent pages")
    allow_external_links: bool = Field(False, description="Allow external domain links")


class StructuredExtractionRequest(BaseModel):
    """Request model for structured data extraction"""
    url: HttpUrl = Field(..., description="URL to extract from")
    schema: Dict[str, Any] = Field(..., description="JSON schema for extraction")
    extraction_prompt: Optional[str] = Field(None, description="Custom extraction prompt")


class BatchScrapingRequest(BaseModel):
    """Request model for batch scraping"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=20, description="URLs to scrape")
    extract_content: bool = Field(True, description="Extract clean content")
    include_markdown: bool = Field(True, description="Include markdown format")
    include_html: bool = Field(False, description="Include raw HTML")


# Endpoints
@router.post("/scrape")
async def scrape_url(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Scrape a single URL with advanced options.
    
    Supports JavaScript rendering, content extraction, and various output formats.
    """
    if not firecrawl_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Firecrawl service not available. Please configure FIRECRAWL_API_KEY."
        )
    
    try:
        logger.info(f"Scraping URL: {request.url}")
        
        result = await firecrawl_service.scrape_url(
            url=str(request.url),
            extract_content=request.extract_content,
            include_markdown=request.include_markdown,
            include_html=request.include_html,
            include_links=request.include_links,
            include_images=request.include_images,
            wait_for=request.wait_for,
            headers=request.headers
        )
        
        # Log scraping activity
        if current_user and result.get("success"):
            background_tasks.add_task(
                log_scraping_activity,
                db_pool,
                current_user.get("id"),
                str(request.url),
                "scrape",
                result.get("content", "")[:500]  # First 500 chars
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error scraping URL {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/crawl")
async def crawl_website(
    request: CrawlingRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Crawl an entire website with configurable limits.
    
    Returns job ID for async crawling status tracking.
    """
    if not firecrawl_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Firecrawl service not available"
        )
    
    try:
        logger.info(f"Crawling website: {request.url}")
        
        result = await firecrawl_service.crawl_website(
            url=str(request.url),
            max_pages=request.max_pages,
            include_paths=request.include_paths,
            exclude_paths=request.exclude_paths,
            max_depth=request.max_depth,
            allow_backward_links=request.allow_backward_links,
            allow_external_links=request.allow_external_links
        )
        
        # Log crawling activity
        if current_user and result.get("success"):
            background_tasks.add_task(
                log_scraping_activity,
                db_pool,
                current_user.get("id"),
                str(request.url),
                "crawl",
                f"Crawled {result.get('total_pages', 0)} pages"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error crawling website {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Crawling failed: {str(e)}"
        )


@router.post("/extract")
async def extract_structured_data(
    request: StructuredExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Extract structured data from a webpage using AI.
    
    Provide a JSON schema to define the data structure you want to extract.
    """
    if not firecrawl_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Firecrawl service not available"
        )
    
    try:
        logger.info(f"Extracting structured data from: {request.url}")
        
        result = await firecrawl_service.extract_structured_data(
            url=str(request.url),
            schema=request.schema,
            extraction_prompt=request.extraction_prompt
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting from {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/batch-scrape")
async def batch_scrape(
    request: BatchScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Scrape multiple URLs concurrently.
    
    Limited to 20 URLs per request to prevent abuse.
    """
    if not firecrawl_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Firecrawl service not available"
        )
    
    try:
        logger.info(f"Batch scraping {len(request.urls)} URLs")
        
        urls = [str(url) for url in request.urls]
        results = await firecrawl_service.batch_scrape(
            urls=urls,
            extract_content=request.extract_content,
            include_markdown=request.include_markdown,
            include_html=request.include_html
        )
        
        # Count successful scrapes
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": True,
            "total_urls": len(urls),
            "successful": successful,
            "failed": len(urls) - successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch scraping failed: {str(e)}"
        )


@router.get("/job/{job_id}")
async def get_crawl_status(
    job_id: str,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get the status of a crawl job."""
    if not firecrawl_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Firecrawl service not available"
        )
    
    try:
        result = await firecrawl_service.get_job_status(job_id)
        return result
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


@router.get("/status")
async def get_service_status(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get Firecrawl service status and configuration."""
    return {
        "enabled": firecrawl_service.enabled,
        "api_configured": bool(firecrawl_service.api_key),
        "base_url": firecrawl_service.base_url,
        "features": {
            "scraping": True,
            "crawling": True,
            "structured_extraction": True,
            "batch_processing": True,
            "javascript_rendering": True
        }
    }


# Helper functions
async def log_scraping_activity(
    db_pool: asyncpg.Pool,
    user_id: int,
    url: str,
    operation: str,
    summary: str
):
    """Log scraping activity to database"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO scraping_history (user_id, url, operation, summary, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, url, operation, summary, datetime.now()
            )
    except Exception as e:
        logger.error(f"Error logging scraping activity: {e}")


# Create scraping history table if it doesn't exist
async def create_scraping_history_table(db_pool: asyncpg.Pool):
    """Create scraping history table"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    url VARCHAR(2048) NOT NULL,
                    operation VARCHAR(50) NOT NULL,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_scraping_history_user ON scraping_history(user_id);
                CREATE INDEX IF NOT EXISTS idx_scraping_history_created ON scraping_history(created_at);
            """)
    except Exception as e:
        logger.error(f"Error creating scraping history table: {e}")