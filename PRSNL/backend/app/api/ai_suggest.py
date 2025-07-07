"""
AI-powered suggestion endpoint for auto-generating capture metadata
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import logging

from app.services.llm_processor import LLMProcessor
from app.services.scraper import WebScraper
from app.core.exceptions import InvalidInput, InternalServerError

logger = logging.getLogger(__name__)
router = APIRouter()


class SuggestionRequest(BaseModel):
    url: HttpUrl


class SuggestionResponse(BaseModel):
    title: str
    summary: str
    tags: List[str]
    category: Optional[str] = None


@router.post("/suggest", response_model=SuggestionResponse)
async def get_ai_suggestions(request: SuggestionRequest):
    """
    Get AI-powered suggestions for title, summary, and tags based on URL content
    """
    try:
        # Quick scrape to get basic metadata
        scraper = WebScraper()
        
        # Do a lightweight scrape first to get title and meta tags
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(str(request.url))
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic metadata
        page_title = soup.find('title').text.strip() if soup.find('title') else ""
        meta_description = ""
        meta_keywords = []
        
        # Get meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'}) or \
                       soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc_tag:
            meta_description = meta_desc_tag.get('content', '')
            
        # Get meta keywords
        meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords_tag:
            keywords = meta_keywords_tag.get('content', '')
            meta_keywords = [k.strip() for k in keywords.split(',') if k.strip()][:5]
        
        # Get first paragraph or og:description for content preview
        first_paragraph = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs[:3]:  # Check first 3 paragraphs
            text = p.get_text().strip()
            if len(text) > 50:  # Meaningful paragraph
                first_paragraph = text[:500]
                break
                
        # Use LLM to generate better suggestions
        llm_processor = LLMProcessor()
        
        prompt = f"""Based on this webpage information, suggest a title, summary, and relevant tags.

Page Title: {page_title}
Meta Description: {meta_description}
Content Preview: {first_paragraph}
URL: {request.url}

Generate:
1. A concise, descriptive title (max 100 chars) that captures the main topic
2. A brief summary (2-3 sentences) explaining what this content is about
3. 5-8 relevant tags (lowercase, single words or short phrases)
4. A category (one of: tutorial, article, documentation, video, tool, reference, news)

Format your response as JSON:
{{
    "title": "...",
    "summary": "...",
    "tags": ["tag1", "tag2", ...],
    "category": "..."
}}"""

        ai_response = await llm_processor.process_with_llm(prompt, "suggest")
        
        # Parse AI response
        import json
        try:
            suggestions = json.loads(ai_response)
        except:
            # Fallback if AI response isn't valid JSON
            suggestions = {
                "title": page_title[:100] if page_title else "Untitled",
                "summary": meta_description[:200] if meta_description else "No description available",
                "tags": meta_keywords[:8] if meta_keywords else ["uncategorized"],
                "category": "article"
            }
        
        # Ensure tags are lowercase and cleaned
        if 'tags' in suggestions:
            suggestions['tags'] = [tag.lower().strip() for tag in suggestions['tags'] if tag.strip()][:10]
        
        # Ensure title isn't too long
        if 'title' in suggestions:
            suggestions['title'] = suggestions['title'][:100]
            
        return SuggestionResponse(**suggestions)
        
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch URL: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        raise InternalServerError(f"Failed to generate suggestions: {str(e)}")