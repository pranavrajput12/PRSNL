"""LLM processing service - Wrapper around UnifiedAIService for backward compatibility"""
import json
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional

from app.config import settings
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)

@dataclass
class ProcessedContent:
    title: str
    summary: str
    content: str
    tags: List[str]
    key_points: List[str]
    sentiment: str
    reading_time: int
    entities: Dict[str, List[str]]
    questions: List[str]

class LLMProcessor:
    """
    Legacy LLM processor that now delegates to UnifiedAIService.
    Kept for backward compatibility with existing code.
    """
    def __init__(self):
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI API key is required")
        self.unified_ai = unified_ai_service

    async def process_content(
        self, 
        content: str, 
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> ProcessedContent:
        """Process content and return structured data"""
        
        # Use unified AI service for analysis
        analysis = await self.unified_ai.analyze_content(content, url)
        
        # Convert to ProcessedContent format
        return ProcessedContent(
            title=analysis.get("title", title or "Untitled"),
            summary=analysis.get("summary", ""),
            content=content,  # Keep original content
            tags=analysis.get("tags", []),
            key_points=analysis.get("key_points", []),
            sentiment=analysis.get("sentiment", "neutral"),
            reading_time=analysis.get("estimated_reading_time", 5),
            entities=analysis.get("entities", {}),
            questions=[]  # Not provided by analyze_content
        )

    async def generate_tags(self, content: str, limit: int = 10) -> List[str]:
        """Generate tags for content"""
        analysis = await self.unified_ai.analyze_content(content)
        tags = analysis.get("tags", [])
        return tags[:limit]

    async def summarize_content(self, content: str) -> str:
        """Generate a summary of the content"""
        return await self.unified_ai.generate_summary(content, summary_type="brief")

    async def extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        analysis = await self.unified_ai.analyze_content(content)
        return analysis.get("key_points", [])

    async def stream_content(
        self, 
        content: str,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream processed content analysis"""
        prompt = self._construct_process_prompt(content, url, title)
        
        system_prompt = """You are an expert content analyst specializing in extracting actionable knowledge from web content. 
        Your goal is to transform raw content into structured, searchable insights that help users learn and apply new skills efficiently."""
        
        async for chunk in self.unified_ai.stream_chat_response(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1000
        ):
            yield chunk

    async def stream_tag_suggestions(
        self, 
        content: str,
        limit: int = 8
    ) -> AsyncGenerator[str, None]:
        """Stream tag suggestions"""
        prompt = self._construct_tag_prompt(content, limit)
        
        system_prompt = "You are an expert at generating relevant, searchable tags for content."
        
        async for chunk in self.unified_ai.stream_chat_response(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.5,
            max_tokens=100
        ):
            yield chunk

    def _construct_process_prompt(self, content: str, url: Optional[str], title: Optional[str]) -> str:
        return f"""Analyze the following content and extract structured, actionable information.

URL: {url or 'N/A'}
Original Title: {title or 'N/A'}

Content to analyze:
{content[:4000]}

Extract and structure the information according to these requirements:

1. TITLE: Create a clear, action-oriented title (max 80 chars)
2. SUMMARY: Write a concise summary (max 150 chars)
3. TAGS: Extract 5-10 relevant tags
4. KEY_POINTS: List 3-5 main steps or key takeaways
5. SENTIMENT: Classify difficulty as beginner/intermediate/advanced
6. READING_TIME: Estimate completion time in minutes
7. ENTITIES: Categorize mentioned items into Tools, Skills, Prerequisites
8. QUESTIONS: Generate 3 discovery questions
9. PROCESSED: Rewrite as a clean, step-by-step guide

Format your response EXACTLY as specified."""

    def _construct_tag_prompt(self, content: str, limit: int) -> str:
        return f"""Generate {limit} relevant tags for the following content.

Content: {content[:2000]}

Requirements:
- Focus on specific technologies, concepts, and skills
- Use lowercase, hyphenated format (e.g., "react-hooks", "docker-compose")
- Include both broad categories and specific topics
- Prioritize searchability and relevance

Return only the tags, comma-separated."""

# Create singleton instance for backward compatibility
llm_processor = LLMProcessor()