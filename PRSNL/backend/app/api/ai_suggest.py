
"""
AI-powered suggestion endpoint for auto-generating capture metadata
"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl
from openai import AzureOpenAI

from app.core.exceptions import InternalServerError
from app.services.ai_router import AITask, TaskType, ai_router, AIProvider
from app.services.scraper import WebScraper
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class SuggestionRequest(BaseModel):
    url: HttpUrl


class SuggestionResponse(BaseModel):
    title: str
    summary: str
    tags: List[str]
    category: Optional[str] = None


def _create_llm_prompt(url: HttpUrl, title: str, content: str) -> str:
    """Creates the prompt for the LLM to generate suggestions."""
    # Truncate content to avoid exceeding token limits
    truncated_content = content[:4000] if content else "No content available."

    return f"""You are analyzing a webpage to generate optimized metadata for a personal knowledge management system. Your goal is to create highly searchable and categorized content.

WEBPAGE INFORMATION:
- URL: {url}
- Original Title: {title}
- Content Preview: {truncated_content}

TASK: Generate metadata that maximizes discoverability and accurate categorization.

REQUIREMENTS:
1. TITLE: Create an improved, action-oriented title (max 80 chars)
   - Make it descriptive and searchable
   - Use "How to", "Guide to", or topic-focused formats
   - Improve upon the original if it's vague or clickbait

2. SUMMARY: Write a concise summary (100-150 chars)
   - Explain what users will learn or achieve
   - Focus on practical value and outcomes
   - Be specific about the content's purpose

3. TAGS: Generate 5-8 highly relevant tags
   - Use lowercase, hyphenated for multi-word (e.g., "machine-learning")
   - Include: tools, technologies, skills, concepts, domains
   - Order by relevance (most important first)
   - Avoid generic tags like "web", "internet", "computer"

4. CATEGORY: Select the most appropriate category:
   - tutorial: Step-by-step guides and how-tos
   - article: Informational content, blog posts, news
   - documentation: Technical docs, API references, manuals
   - video: Video content or video-centric pages
   - tool: Software, services, or utility pages
   - reference: Cheat sheets, quick references, glossaries
   - news: Current events, updates, announcements

OUTPUT FORMAT (strict JSON):
{{
    "title": "Clear, searchable title here",
    "summary": "Concise summary of value and content",
    "tags": ["specific-tag1", "tool-name", "concept", "skill", "domain"],
    "category": "most-appropriate-category"
}}"""


async def _execute_llm_suggestion_task(provider: AIProvider, task: AITask) -> str:
    """Executes the suggestion task with a given AI provider."""
    if provider == AIProvider.AZURE_OPENAI:
        try:
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                timeout=30.0,
            )
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": task.content}],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI request failed: {e}")
            raise

    elif provider == AIProvider.FALLBACK:
        logger.warning("Executing AI suggestion task with fallback provider.")
        return json.dumps(task.options.get("fallback_response", {}))

    raise InternalServerError(f"Provider {provider.value} not supported for this task.")


@router.post("/suggest", response_model=SuggestionResponse)
async def get_ai_suggestions(request: SuggestionRequest):
    """
    Get AI-powered suggestions for title, summary, and tags based on URL content.
    This endpoint uses an AI router to ensure resilience and fallback capabilities.
    """
    logger.info(f"Received suggestion request for URL: {request.url}")

    # 1. Scrape content from URL
    try:
        async with WebScraper() as scraper:
            scraped_data = await scraper.scrape(str(request.url))
    except Exception as e:
        logger.error(f"Scraping failed for {request.url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to scrape the URL. It might be inaccessible or block scraping."
        )

    if not scraped_data or not scraped_data.content:
        logger.error(f"No content scraped from {request.url}. Content extraction failed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract meaningful content from the URL. The page might be empty, dynamic, or block content extraction."
        )

    # 2. Prepare AI task
    prompt = _create_llm_prompt(request.url, scraped_data.title, scraped_data.content)
    
    fallback_response = {
        "title": scraped_data.title[:100] if scraped_data.title else "Untitled",
        "summary": scraped_data.content[:200] if scraped_data.content else "No description available",
        "tags": ["uncategorized"],
        "category": "article"
    }

    ai_task = AITask(
        type=TaskType.TEXT_GENERATION,
        content=prompt,
        options={"fallback_response": fallback_response},
        priority=8 # High priority for user-facing feature
    )

    # 3. Execute with AI Router for resilience
    try:
        logger.info(f"Executing suggestion task for {request.url} via AI Router.")
        ai_response_str = await ai_router.execute_with_fallback(
            ai_task, 
            _execute_llm_suggestion_task
        )
        
        if not ai_response_str:
             raise InternalServerError("AI provider returned an empty response.")

        suggestions = json.loads(ai_response_str)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {ai_response_str}")
        suggestions = fallback_response
    except Exception as e:
        logger.error(f"Failed to get AI suggestions for {request.url}: {e}", exc_info=True)
        suggestions = fallback_response

    # 4. Clean and validate the response
    if 'tags' in suggestions and isinstance(suggestions['tags'], list):
        suggestions['tags'] = [str(tag).lower().strip().replace(" ", "-") for tag in suggestions['tags'] if str(tag).strip()][:10]
    else:
        suggestions['tags'] = ["uncategorized"]

    if 'title' in suggestions and isinstance(suggestions['title'], str):
        suggestions['title'] = suggestions['title'][:120]
    else:
        suggestions['title'] = fallback_response['title']
        
    if 'summary' not in suggestions:
        suggestions['summary'] = fallback_response['summary']
        
    if 'category' not in suggestions:
        suggestions['category'] = fallback_response['category']

    return SuggestionResponse(**suggestions)
