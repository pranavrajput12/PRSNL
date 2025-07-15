"""
Web-related Crew.ai tools that wrap existing PRSNL services
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Type, Union
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.crawl_ai_service import CrawlAIService
from app.services.unified_ai_service import unified_ai_service
from app.tools import register_tool

logger = logging.getLogger(__name__)


class WebScraperInput(BaseModel):
    """Input schema for web scraper tool"""
    url: str = Field(..., description="The URL to scrape")
    max_depth: Optional[int] = Field(1, description="Maximum crawl depth")
    include_links: Optional[bool] = Field(True, description="Whether to include links")


@register_tool("web_scraper")
class WebScraperTool(BaseTool):
    name: str = "Web Scraper"
    description: str = (
        "Scrapes and extracts content from web pages. "
        "Returns cleaned content, metadata, and optionally links."
    )
    args_schema: Type[BaseModel] = WebScraperInput
    
    def _run(
        self,
        url: str,
        max_depth: int = 1,
        include_links: bool = True
    ) -> str:
        """Synchronous wrapper for the async scraping service"""
        try:
            # Run async code in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_scrape(url, max_depth, include_links))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return f"Failed to scrape {url}: {str(e)}"
    
    async def _async_scrape(self, url: str, max_depth: int, include_links: bool) -> str:
        """Async scraping using existing CrawlAIService"""
        try:
            crawl_service = CrawlAIService()
            result = await crawl_service.crawl(
                url=url,
                max_depth=max_depth,
                include_links=include_links
            )
            
            # Format result for agent consumption
            output = f"Content from {url}:\n\n"
            output += f"Title: {result.metadata.get('title', 'N/A')}\n"
            output += f"Description: {result.metadata.get('description', 'N/A')}\n\n"
            output += f"Content:\n{result.content[:2000]}..."
            
            if include_links and result.links:
                output += f"\n\nFound {len(result.links)} links"
                
            return output
        except Exception as e:
            logger.error(f"Async scraping failed: {e}")
            raise


class ContentAnalyzerInput(BaseModel):
    """Input schema for content analyzer tool"""
    content: str = Field(..., description="The content to analyze")
    analysis_type: Optional[str] = Field("comprehensive", description="Type of analysis")


@register_tool("content_analyzer")
class ContentAnalyzerTool(BaseTool):
    name: str = "Content Analyzer"
    description: str = (
        "Analyzes content to extract key information, entities, "
        "themes, and generate summaries. Uses AI for deep analysis."
    )
    args_schema: Type[BaseModel] = ContentAnalyzerInput
    
    def _run(
        self,
        content: str,
        analysis_type: str = "comprehensive"
    ) -> str:
        """Analyze content using unified AI service"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_analyze(content, analysis_type)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return f"Failed to analyze content: {str(e)}"
    
    async def _async_analyze(self, content: str, analysis_type: str) -> str:
        """Async content analysis"""
        try:
            # Use existing unified AI service
            analysis = await unified_ai_service.analyze_content(
                content=content[:4000],  # Limit for AI
                enable_key_points=True,
                enable_entities=True,
                enable_themes=True
            )
            
            # Format result
            output = "Content Analysis Results:\n\n"
            
            if analysis.get("summary"):
                output += f"Summary: {analysis['summary']}\n\n"
            
            if analysis.get("key_points"):
                output += "Key Points:\n"
                for point in analysis["key_points"]:
                    output += f"- {point}\n"
                output += "\n"
            
            if analysis.get("entities"):
                output += "Entities Found:\n"
                for entity_type, entities in analysis["entities"].items():
                    if entities:
                        output += f"- {entity_type}: {', '.join(entities[:5])}\n"
                output += "\n"
            
            if analysis.get("themes"):
                output += f"Themes: {', '.join(analysis['themes'])}\n"
            
            if analysis.get("category"):
                output += f"Category: {analysis['category']}\n"
            
            if analysis.get("tags"):
                output += f"Tags: {', '.join(analysis['tags'])}\n"
            
            return output
        except Exception as e:
            logger.error(f"Async analysis failed: {e}")
            raise


class LinkExtractorInput(BaseModel):
    """Input schema for link extractor tool"""
    url: str = Field(..., description="The URL to extract links from")
    filter_external: Optional[bool] = Field(False, description="Filter out external links")


@register_tool("link_extractor")
class LinkExtractorTool(BaseTool):
    name: str = "Link Extractor"
    description: str = (
        "Extracts all links from a web page. "
        "Can filter internal vs external links."
    )
    args_schema: Type[BaseModel] = LinkExtractorInput
    
    def _run(
        self,
        url: str,
        filter_external: bool = False
    ) -> str:
        """Extract links from a web page"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_extract_links(url, filter_external)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Link extraction failed: {e}")
            return f"Failed to extract links: {str(e)}"
    
    async def _async_extract_links(self, url: str, filter_external: bool) -> str:
        """Async link extraction"""
        try:
            crawl_service = CrawlAIService()
            result = await crawl_service.crawl(
                url=url,
                max_depth=1,
                include_links=True
            )
            
            if not result.links:
                return "No links found on the page."
            
            # Parse base domain for filtering
            from urllib.parse import urlparse
            base_domain = urlparse(url).netloc
            
            links = result.links
            if filter_external:
                links = [
                    link for link in links 
                    if urlparse(link).netloc == base_domain
                ]
            
            output = f"Found {len(links)} links:\n\n"
            for link in links[:20]:  # Limit output
                output += f"- {link}\n"
            
            if len(links) > 20:
                output += f"\n... and {len(links) - 20} more links"
            
            return output
        except Exception as e:
            logger.error(f"Async link extraction failed: {e}")
            raise


class DeepWebScraperInput(BaseModel):
    """Input schema for deep web scraper tool (placeholder)"""
    url: str = Field(..., description="URL to deep scrape")
    depth: Optional[int] = Field(3, description="Crawl depth")


@register_tool("deep_web_scraper")
class DeepWebScraperTool(BaseTool):
    name: str = "Deep Web Scraper"
    description: str = "Advanced scraping for deep web content (placeholder)"
    args_schema: Type[BaseModel] = DeepWebScraperInput
    
    def _run(self, url: str, depth: int = 3) -> str:
        return f"Deep web scraping of {url} with depth {depth} (placeholder)"


class ArchiveSearchInput(BaseModel):
    """Input schema for archive search tool (placeholder)"""
    query: str = Field(..., description="Search query")
    start_year: Optional[int] = Field(None, description="Start year for search")


@register_tool("archive_search")
class ArchiveSearchTool(BaseTool):
    name: str = "Archive Search"
    description: str = "Search archived web content (placeholder)"
    args_schema: Type[BaseModel] = ArchiveSearchInput
    
    def _run(self, query: str, start_year: Optional[int] = None) -> str:
        return f"Archive search for '{query}' from {start_year or 'all time'} (placeholder)"