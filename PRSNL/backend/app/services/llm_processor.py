"""LLM processing service with Ollama and Azure OpenAI"""
import httpx
import json
from typing import List, Optional
from dataclasses import dataclass
from app.config import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessedContent:
    title: str
    summary: str
    content: str
    tags: List[str]


class LLMProcessor:
    """Process content using LLMs (Ollama first, Azure OpenAI fallback)"""
    
    def __init__(self):
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=60.0
        )
        self.azure_client = None
        if settings.AZURE_OPENAI_API_KEY:
            self.azure_client = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "api-key": settings.AZURE_OPENAI_API_KEY,
                    "Content-Type": "application/json"
                }
            )
    
    async def process(
        self, 
        content: str, 
        url: str,
        title: Optional[str] = None
    ) -> ProcessedContent:
        """
        Process content to extract structured information
        """
        # Truncate content if too long
        if len(content) > settings.MAX_CONTENT_LENGTH:
            content = content[:settings.MAX_CONTENT_LENGTH] + "..."
        
        # Try Ollama first
        try:
            return await self._process_with_ollama(content, url, title)
        except Exception as e:
            logger.warning(f"Ollama processing failed: {str(e)}")
            
            # Fallback to Azure OpenAI if available
            if self.azure_client:
                try:
                    return await self._process_with_azure(content, url, title)
                except Exception as e:
                    logger.error(f"Azure OpenAI processing failed: {str(e)}")
        
        # Final fallback: basic processing
        return self._basic_process(content, url, title)
    
    async def _process_with_ollama(
        self, 
        content: str, 
        url: str,
        title: Optional[str]
    ) -> ProcessedContent:
        """
        Process with local Ollama
        """
        prompt = f"""Analyze this web content and provide:
1. A concise, descriptive title (max 100 chars)
2. A brief summary (max 200 chars)
3. 5-10 relevant topic tags
4. Clean, processed text (remove ads, navigation, etc)

URL: {url}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [your title here]
SUMMARY: [your summary here]
TAGS: tag1, tag2, tag3, tag4, tag5
PROCESSED:
[cleaned content here]"""

        response = await self.ollama_client.post(
            "/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        return self._parse_llm_response(result['response'])
    
    async def _process_with_azure(
        self, 
        content: str, 
        url: str,
        title: Optional[str]
    ) -> ProcessedContent:
        """
        Process with Azure OpenAI
        """
        messages = [
            {
                "role": "system",
                "content": "You are a content analysis assistant. Extract key information and clean up web content."
            },
            {
                "role": "user",
                "content": f"""Analyze this web content and provide:
1. A concise, descriptive title (max 100 chars)
2. A brief summary (max 200 chars)
3. 5-10 relevant topic tags
4. Clean, processed text (remove ads, navigation, etc)

URL: {url}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [your title here]
SUMMARY: [your summary here]
TAGS: tag1, tag2, tag3, tag4, tag5
PROCESSED:
[cleaned content here]"""
            }
        ]
        
        response = await self.azure_client.post(
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}",
            json={
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        return self._parse_llm_response(result['choices'][0]['message']['content'])
    
    def _parse_llm_response(self, response: str) -> ProcessedContent:
        """
        Parse LLM response into structured format
        """
        lines = response.strip().split('\n')
        
        title = ""
        summary = ""
        tags = []
        processed_content = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("TITLE:"):
                title = line[6:].strip()
            elif line.startswith("SUMMARY:"):
                summary = line[8:].strip()
            elif line.startswith("TAGS:"):
                tags_str = line[5:].strip()
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            elif line.startswith("PROCESSED:"):
                current_section = "processed"
            elif current_section == "processed" and line:
                processed_content.append(line)
        
        return ProcessedContent(
            title=title[:100],
            summary=summary[:200],
            content='\n'.join(processed_content),
            tags=tags[:10]
        )
    
    def _basic_process(
        self, 
        content: str, 
        url: str,
        title: Optional[str]
    ) -> ProcessedContent:
        """
        Basic processing without LLM
        """
        # Use provided title or extract from URL
        if not title:
            title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        
        # Create basic summary from first paragraph
        paragraphs = content.split('\n\n')
        summary = paragraphs[0][:200] if paragraphs else ""
        
        # Generate basic tags from common words
        words = content.lower().split()
        word_freq = {}
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were'}
        
        for word in words:
            if len(word) > 4 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 5 words as tags
        tags = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        tags = [tag[0] for tag in tags]
        
        return ProcessedContent(
            title=title[:100],
            summary=summary,
            content=content,
            tags=tags
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.ollama_client.aclose()
        if self.azure_client:
            await self.azure_client.aclose()