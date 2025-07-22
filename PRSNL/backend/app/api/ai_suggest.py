
"""
AI-powered suggestion endpoint for auto-generating capture metadata
"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from openai import AzureOpenAI
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.core.exceptions import InternalServerError
from app.services.ai_router import ai_router, AIProvider, AITask, TaskType
from app.services.jina_reader import JinaReaderService

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

    # 1. Use Jina Reader to scrape content (free, no API key needed)
    scraped_data = None
    scrape_error = None
    
    try:
        logger.info(f"Scraping {request.url} with Jina Reader for AI suggestions")
        jina_service = JinaReaderService()
        result = await jina_service.scrape_url(str(request.url))
        if result.get("success"):
            scraped_data = result["data"]
            logger.info(f"Successfully scraped {request.url} with Jina Reader")
        else:
            scrape_error = result.get("error", "Unknown error")
            logger.error(f"Jina Reader failed for {request.url}: {scrape_error}")
    except Exception as e:
        logger.error(f"Jina Reader exception for {request.url}: {e}")
        scrape_error = str(e)
    
    # If scraping failed, return error
    if not scraped_data:
        logger.error(f"Failed to scrape {request.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to crawl the URL. It might be inaccessible or block crawling. Error: {scrape_error}"
        )
    
    # Extract content from scraped data
    content = scraped_data.get("content", "")
    title = scraped_data.get("title", "")
    
    if not content:
        logger.error(f"No content extracted from {request.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract meaningful content from the URL. The page might be empty or require JavaScript."
        )

    # 2. Check if AI already analyzed the content 
    metadata = scraped_data.get("metadata", {})
    if metadata.get("ai_title") and metadata.get("ai_tags"):
        # Use pre-analyzed data
        return SuggestionResponse(
            title=metadata["ai_title"][:120],
            summary=metadata.get("ai_summary", content[:200])[:200],
            tags=metadata.get("ai_tags", ["uncategorized"])[:10],
            category=metadata.get("ai_category", "article")
        )
    
    # 3. Prepare AI task for additional analysis if needed
    prompt = _create_llm_prompt(request.url, title, content)
    
    fallback_response = {
        "title": title[:100] if title else "Untitled",
        "summary": content[:200] if content else "No description available",
        "tags": metadata.get("ai_tags", ["uncategorized"]),
        "category": metadata.get("ai_category", "article")
    }

    ai_task = AITask(
        type=TaskType.TEXT_GENERATION,
        content=prompt,
        options={"fallback_response": fallback_response},
        priority=8 # High priority for user-facing feature
    )

    # 4. Execute with AI Router for resilience
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

    # 5. Clean and validate the response
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
