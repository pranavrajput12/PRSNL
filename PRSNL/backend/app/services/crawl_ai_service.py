"""
Crawl.ai Service - Advanced web crawling and content analysis
Integrates Crawl4AI for intelligent web scraping with AI-powered analysis
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class RepositoryMetadata(BaseModel):
    """GitHub/GitLab repository metadata"""
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    topics: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    default_branch: str = "main"
    is_fork: bool = False
    size: int = 0
    readme_content: Optional[str] = None
    tech_stack: List[str] = []
    package_managers: List[str] = []
    frameworks: List[str] = []
    ai_summary: Optional[str] = None
    ai_category: Optional[str] = None
    ai_tags: List[str] = []


@dataclass
class CrawlResult:
    """Result from Crawl4AI crawling"""
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: List[Dict[str, str]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    repository_data: Optional[RepositoryMetadata] = None
    crawled_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class CrawlAIService:
    """
    Advanced web crawling service using Crawl4AI
    Replaces the old AutoAgent-based scraping with a more efficient solution
    """

    def __init__(self):
        self.crawler = None
        self._github_api_base = "https://api.github.com"
        
    async def __aenter__(self):
        """Initialize async crawler"""
        self.crawler = AsyncWebCrawler(
            verbose=False,
            headless=True,
            browser_type="chromium"
        )
        await self.crawler.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    async def crawl_url(self, url: str, extract_content: bool = True) -> CrawlResult:
        """
        Crawl a URL using Crawl4AI with intelligent extraction
        """
        try:
            # Check if it's a GitHub/GitLab repository
            if self._is_repository_url(url):
                return await self._crawl_repository(url)
            
            # Regular web page crawling
            result = await self.crawler.arun(
                url=url,
                word_count_threshold=50,
                excluded_tags=['nav', 'footer', 'aside'],
                bypass_cache=True
            )
            
            if not result.success:
                return CrawlResult(
                    url=url,
                    error=f"Failed to crawl: {result.error_message}"
                )
            
            # Extract clean content
            content = result.text_content.strip() if result.text_content else ""
            markdown = result.markdown.strip() if result.markdown else ""
            
            # Use AI to analyze content if enabled
            ai_metadata = {}
            if extract_content and content:
                try:
                    analysis = await unified_ai_service.analyze_content(
                        content[:4000],  # Limit content for AI analysis
                        url=url
                    )
                    ai_metadata = {
                        "ai_title": analysis.get("title"),
                        "ai_summary": analysis.get("summary"),
                        "ai_tags": analysis.get("tags", []),
                        "ai_category": analysis.get("category"),
                        "ai_entities": analysis.get("entities", {})
                    }
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
            
            # Extract images and links
            images = self._extract_images(result)
            links = self._extract_links(result)
            
            return CrawlResult(
                url=url,
                title=result.title or ai_metadata.get("ai_title"),
                content=content,
                markdown=markdown,
                html=result.html,
                metadata={
                    **result.metadata,
                    **ai_metadata,
                    "word_count": len(content.split()) if content else 0,
                    "language": result.metadata.get("language", "en")
                },
                images=images,
                links=links
            )
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return CrawlResult(
                url=url,
                error=str(e)
            )

    async def _crawl_repository(self, url: str) -> CrawlResult:
        """
        Specialized crawling for GitHub/GitLab repositories
        """
        try:
            # Parse repository info from URL
            repo_info = self._parse_repository_url(url)
            if not repo_info:
                return await self.crawl_url(url, extract_content=True)
            
            # Crawl the repository page
            result = await self.crawler.arun(
                url=url,
                bypass_cache=True
            )
            
            if not result.success:
                return CrawlResult(
                    url=url,
                    error=f"Failed to crawl repository: {result.error_message}"
                )
            
            # Extract repository metadata using CSS selectors
            repo_data = await self._extract_repository_metadata(result, repo_info)
            
            # Get README content if available
            readme_content = await self._get_readme_content(repo_info)
            if readme_content:
                repo_data.readme_content = readme_content
            
            # Analyze with AI for tech stack and categorization
            if readme_content or repo_data.description:
                content_to_analyze = f"""
                Repository: {repo_data.full_name}
                Description: {repo_data.description or 'No description'}
                README: {readme_content[:2000] if readme_content else 'No README'}
                Topics: {', '.join(repo_data.topics)}
                Language: {repo_data.language}
                """
                
                try:
                    ai_analysis = await unified_ai_service.analyze_content(
                        content_to_analyze,
                        url=url
                    )
                    
                    # Extract tech stack and frameworks from AI analysis
                    entities = ai_analysis.get("entities", {})
                    repo_data.tech_stack = entities.get("technologies", [])
                    repo_data.frameworks = [
                        tech for tech in entities.get("technologies", [])
                        if any(keyword in tech.lower() for keyword in ["framework", "library", "sdk"])
                    ]
                    repo_data.ai_summary = ai_analysis.get("summary")
                    repo_data.ai_category = ai_analysis.get("category")
                    repo_data.ai_tags = ai_analysis.get("tags", [])
                    
                except Exception as e:
                    logger.error(f"AI analysis failed for repository: {e}")
            
            return CrawlResult(
                url=url,
                title=f"{repo_data.full_name} - {repo_data.description or 'Repository'}"[:200],
                content=repo_data.readme_content or repo_data.description,
                markdown=result.markdown,
                html=result.html,
                repository_data=repo_data,
                metadata={
                    "type": "repository",
                    "platform": repo_info["platform"],
                    "stars": repo_data.stars,
                    "language": repo_data.language
                }
            )
            
        except Exception as e:
            logger.error(f"Error crawling repository {url}: {e}")
            return CrawlResult(
                url=url,
                error=str(e)
            )

    def _is_repository_url(self, url: str) -> bool:
        """Check if URL is a GitHub/GitLab repository"""
        parsed = urlparse(url)
        return any(
            domain in parsed.netloc 
            for domain in ["github.com", "gitlab.com", "bitbucket.org"]
        )

    def _parse_repository_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse repository URL to extract owner and repo name"""
        parsed = urlparse(url)
        
        if "github.com" in parsed.netloc:
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                return {
                    "platform": "github",
                    "owner": parts[0],
                    "repo": parts[1],
                    "api_url": f"{self._github_api_base}/repos/{parts[0]}/{parts[1]}"
                }
        
        # Add GitLab and Bitbucket parsing as needed
        
        return None

    async def _extract_repository_metadata(
        self, 
        crawl_result: Any, 
        repo_info: Dict[str, str]
    ) -> RepositoryMetadata:
        """Extract repository metadata from crawled HTML"""
        # This uses CSS selectors to extract GitHub metadata
        # In production, you might want to use the GitHub API directly
        
        extraction_strategy = JsonCssExtractionStrategy(
            schema={
                "stars": "a[href$='/stargazers'] strong",
                "forks": "a[href$='/forks'] strong", 
                "issues": "a[href$='/issues'] strong span",
                "language": "span.ml-0.mr-3:contains('language')",
                "topics": "a.topic-tag",
                "description": "p.f4.my-3",
                "license": "a[href$='/license']"
            }
        )
        
        # Extract using strategy
        extracted = {}
        try:
            # This is a simplified extraction - in production use proper selectors
            html_content = crawl_result.html
            
            # Basic extraction (would need proper implementation)
            extracted = {
                "name": repo_info["repo"],
                "full_name": f"{repo_info['owner']}/{repo_info['repo']}",
                "description": crawl_result.metadata.get("description"),
                "language": "Python",  # Would extract from page
                "stars": 0,
                "forks": 0,
                "open_issues": 0,
                "topics": [],
                "default_branch": "main"
            }
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
        
        return RepositoryMetadata(**extracted)

    async def _get_readme_content(self, repo_info: Dict[str, str]) -> Optional[str]:
        """Get README content from repository"""
        # In production, this would fetch from GitHub API or crawl README directly
        # For now, return None and let the main crawl handle it
        return None

    def _extract_images(self, result: Any) -> List[Dict[str, str]]:
        """Extract images from crawl result"""
        images = []
        if hasattr(result, 'images'):
            for img in result.images[:10]:  # Limit to 10 images
                images.append({
                    "url": img.get("src", ""),
                    "alt": img.get("alt", ""),
                    "width": img.get("width", ""),
                    "height": img.get("height", "")
                })
        return images

    def _extract_links(self, result: Any) -> List[Dict[str, str]]:
        """Extract links from crawl result"""
        links = []
        if hasattr(result, 'links'):
            for link in result.links[:20]:  # Limit to 20 links
                links.append({
                    "url": link.get("href", ""),
                    "text": link.get("text", ""),
                    "title": link.get("title", "")
                })
        return links

    async def analyze_with_ai(
        self, 
        url: str, 
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content using the unified AI service
        This replaces the old AutoAgent analysis
        """
        try:
            # Use the existing AI service for analysis
            analysis = await unified_ai_service.analyze_content(
                content=content,
                url=url,
                enable_key_points=True,
                enable_entities=True
            )
            
            # Add any additional context-specific analysis
            if context and context.get("type") == "repository":
                # Enhance with repository-specific insights
                tech_stack_prompt = f"""
                Based on this repository information, identify:
                1. Primary programming languages and frameworks
                2. Build tools and package managers
                3. Key dependencies and integrations
                4. Development practices (CI/CD, testing frameworks, etc.)
                
                Repository: {context.get('full_name')}
                Content: {content[:2000]}
                """
                
                tech_analysis = await unified_ai_service.complete(
                    prompt=tech_stack_prompt,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                try:
                    tech_data = json.loads(tech_analysis)
                    analysis["tech_stack_analysis"] = tech_data
                except:
                    pass
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": str(e),
                "title": "Analysis Failed",
                "summary": "Unable to analyze content",
                "tags": ["error"],
                "category": "unknown"
            }


# Singleton instance
crawl_ai_service = CrawlAIService()