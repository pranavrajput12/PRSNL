"""LLM processing service with Ollama and Azure OpenAI"""
import httpx
import json
from typing import List, Optional, Dict
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
    key_points: List[str]
    sentiment: str
    reading_time: int
    entities: Dict[str, List[str]]
    questions: List[str]


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
    
    async def stream_process(
        self, 
        content: str,
        url: Optional[str] = None,
        title: Optional[str] = None
    ):
        """
        Stream process content to extract structured information
        """
        # Truncate content if too long
        if len(content) > settings.MAX_CONTENT_LENGTH:
            content = content[:settings.MAX_CONTENT_LENGTH] + "..."
        
        # Try Ollama first
        try:
            async for chunk in self._stream_process_with_ollama(content, url, title):
                yield chunk
        except Exception as e:
            logger.warning(f"Ollama streaming failed: {str(e)}")
            
            # Fallback to Azure OpenAI if available
            if self.azure_client:
                try:
                    async for chunk in self._stream_process_with_azure(content, url, title):
                        yield chunk
                except Exception as e:
                    logger.error(f"Azure OpenAI streaming failed: {str(e)}")
            else:
                yield json.dumps({"error": "No streaming provider available"})

    async def _stream_process_with_ollama(
        self, 
        content: str, 
        url: Optional[str] = None,
        title: Optional[str] = None
    ):
        """
        Stream process with local Ollama
        """
        prompt = f"""Analyze this content as a how-to guide and extract actionable information:
1. A clear, action-oriented title (max 100 chars)
2. Main objective/goal of this guide (what will the user achieve?)
3. 5-10 relevant skill/tool tags
4. Step-by-step instructions (numbered list)
5. Overall difficulty level (beginner/intermediate/advanced)
6. Estimated time to complete
7. Prerequisites or tools needed
8. Common problems/solutions mentioned
9. Clean, actionable content (remove ads, focus on instructions)

URL: {url or 'None'}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [action-oriented title, e.g. "How to..."]
SUMMARY: [what the user will learn/achieve]
TAGS: skill1, tool1, technique1, category1
KEY_POINTS:
1. [First main step]
2. [Second main step]
3. [Third main step]
SENTIMENT: [difficulty: beginner/intermediate/advanced]
READING_TIME: [time to complete in minutes]
ENTITIES:
  Tools: Tool1, Tool2
  Skills: Skill1, Skill2
  Prerequisites: Prereq1, Prereq2
QUESTIONS:
- What problem does this solve?
- What are the key steps?
- What tools are needed?
PROCESSED:
[step-by-step guide extracted from content]"""

        async with self.ollama_client.stream(
            "POST",
            "/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    # Ollama sends newline-delimited JSON
                    decoded_chunk = chunk.decode('utf-8')
                    for line in decoded_chunk.splitlines():
                        if line.strip():
                            json_data = json.loads(line)
                            if "response" in json_data:
                                yield json_data["response"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Ollama stream: {chunk.decode('utf-8')}")
                    continue

    async def _stream_process_with_azure(
        self, 
        content: str, 
        url: Optional[str] = None,
        title: Optional[str] = None
    ):
        """
        Stream process with Azure OpenAI
        """
        messages = [
            {
                "role": "system",
                "content": "You are a how-to guide extraction assistant. Focus on extracting actionable steps, instructions, and practical information from content."
            },
            {
                "role": "user",
                "content": f"""Analyze this content as a how-to guide and extract actionable information:
1. A clear, action-oriented title (max 100 chars)
2. Main objective/goal of this guide (what will the user achieve?)
3. 5-10 relevant skill/tool tags
4. Step-by-step instructions (numbered list)
5. Overall difficulty level (beginner/intermediate/advanced)
6. Estimated time to complete
7. Prerequisites or tools needed
8. Common problems/solutions mentioned
9. Clean, actionable content (remove ads, focus on instructions)

URL: {url or 'None'}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [action-oriented title, e.g. "How to..."]
SUMMARY: [what the user will learn/achieve]
TAGS: skill1, tool1, technique1, category1
KEY_POINTS:
1. [First main step]
2. [Second main step]
3. [Third main step]
SENTIMENT: [difficulty: beginner/intermediate/advanced]
READING_TIME: [time to complete in minutes]
ENTITIES:
  Tools: Tool1, Tool2
  Skills: Skill1, Skill2
  Prerequisites: Prereq1, Prereq2
QUESTIONS:
- What problem does this solve?
- What are the key steps?
- What tools are needed?
PROCESSED:
[step-by-step guide extracted from content]"""
            }
        ]
        
        async with self.azure_client.stream(
            "POST",
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}",
            json={
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "stream": True
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    decoded_chunk = chunk.decode('utf-8')
                    # Azure OpenAI sends data: JSON format
                    for line in decoded_chunk.splitlines():
                        if line.startswith("data:"):
                            json_str = line[len("data:"):].strip()
                            if json_str == "[DONE]":
                                break
                            json_data = json.loads(json_str)
                            if "choices" in json_data and len(json_data["choices"]) > 0:
                                delta = json_data["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Azure stream: {chunk.decode('utf-8')}")
                    continue

    async def stream_tag_suggestions(
        self, 
        content: str,
        limit: int = 5
    ):
        """
        Stream AI-generated tag suggestions for the given content.
        """
        prompt = f"""Analyze the following content and suggest {limit} relevant, concise, single-word tags. Separate tags with commas. Do not include any other text.

Content:
{content[:2000]}

TAGS:"""

        # Try Ollama first
        try:
            async for chunk in self._stream_raw_ollama_response(prompt):
                yield chunk
        except Exception as e:
            logger.warning(f"Ollama streaming tag suggestions failed: {str(e)}")
            
            # Fallback to Azure OpenAI if available
            if self.azure_client:
                try:
                    async for chunk in self._stream_raw_azure_response(prompt):
                        yield chunk
                except Exception as e:
                    logger.error(f"Azure OpenAI streaming tag suggestions failed: {str(e)}")
            else:
                yield json.dumps({"error": "No streaming provider available for tag suggestions"})

    async def _stream_raw_ollama_response(self, prompt: str):
        async with self.ollama_client.stream(
            "POST",
            "/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    decoded_chunk = chunk.decode('utf-8')
                    for line in decoded_chunk.splitlines():
                        if line.strip():
                            json_data = json.loads(line)
                            if "response" in json_data:
                                yield json_data["response"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Ollama stream: {chunk.decode('utf-8')}")
                    continue

    async def _stream_raw_azure_response(self, prompt: str):
        messages = [
            {
                "role": "system",
                "content": "You are a tag suggestion assistant. Provide only comma-separated tags."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        async with self.azure_client.stream(
            "POST",
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}",
            json={
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 100,
                "stream": True
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    decoded_chunk = chunk.decode('utf-8')
                    for line in decoded_chunk.splitlines():
                        if line.startswith("data:"):
                            json_str = line[len("data:"):].strip()
                            if json_str == "[DONE]":
                                break
                            json_data = json.loads(json_str)
                            if "choices" in json_data and len(json_data["choices"]) > 0:
                                delta = json_data["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Azure stream: {chunk.decode('utf-8')}")
                    continue

    async def stream_tag_suggestions(
        self, 
        content: str,
        limit: int = 5
    ):
        """
        Stream AI-generated tag suggestions for the given content.
        """
        prompt = f"""Analyze the following content and suggest {limit} relevant, concise, single-word tags. Separate tags with commas. Do not include any other text.

Content:
{content[:2000]}

TAGS:"""

        # Try Ollama first
        try:
            async for chunk in self._stream_raw_ollama_response(prompt):
                yield chunk
        except Exception as e:
            logger.warning(f"Ollama streaming tag suggestions failed: {str(e)}")
            
            # Fallback to Azure OpenAI if available
            if self.azure_client:
                try:
                    async for chunk in self._stream_raw_azure_response(prompt):
                        yield chunk
                except Exception as e:
                    logger.error(f"Azure OpenAI streaming tag suggestions failed: {str(e)}")
            else:
                yield json.dumps({"error": "No streaming provider available for tag suggestions"})

    async def _stream_raw_ollama_response(self, prompt: str):
        async with self.ollama_client.stream(
            "POST",
            "/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    decoded_chunk = chunk.decode('utf-8')
                    for line in decoded_chunk.splitlines():
                        if line.strip():
                            json_data = json.loads(line)
                            if "response" in json_data:
                                yield json_data["response"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Ollama stream: {chunk.decode('utf-8')}")
                    continue

    async def _stream_raw_azure_response(self, prompt: str):
        messages = [
            {
                "role": "system",
                "content": "You are a tag suggestion assistant. Provide only comma-separated tags."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        async with self.azure_client.stream(
            "POST",
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}",
            json={
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 100,
                "stream": True
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                try:
                    decoded_chunk = chunk.decode('utf-8')
                    for line in decoded_chunk.splitlines():
                        if line.startswith("data:"):
                            json_str = line[len("data:"):].strip()
                            if json_str == "[DONE]":
                                break
                            json_data = json.loads(json_str)
                            if "choices" in json_data and len(json_data["choices"]) > 0:
                                delta = json_data["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from Azure stream: {chunk.decode('utf-8')}")
                    continue

    async def _process_with_ollama(
        self, 
        content: str, 
        url: str,
        title: Optional[str]
    ) -> ProcessedContent:
        """
        Process with local Ollama (non-streaming)
        """
        prompt = f"""Analyze this content as a how-to guide and extract actionable information:
1. A clear, action-oriented title (max 100 chars)
2. Main objective/goal of this guide (what will the user achieve?)
3. 5-10 relevant skill/tool tags
4. Step-by-step instructions (numbered list)
5. Overall difficulty level (beginner/intermediate/advanced)
6. Estimated time to complete
7. Prerequisites or tools needed
8. Common problems/solutions mentioned
9. Clean, actionable content (remove ads, focus on instructions)

URL: {url}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [action-oriented title, e.g. "How to..."]
SUMMARY: [what the user will learn/achieve]
TAGS: skill1, tool1, technique1, category1
KEY_POINTS:
1. [First main step]
2. [Second main step]
3. [Third main step]
SENTIMENT: [difficulty: beginner/intermediate/advanced]
READING_TIME: [time to complete in minutes]
ENTITIES:
  Tools: Tool1, Tool2
  Skills: Skill1, Skill2
  Prerequisites: Prereq1, Prereq2
QUESTIONS:
- What problem does this solve?
- What are the key steps?
- What tools are needed?
PROCESSED:
[step-by-step guide extracted from content]"""

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
            },
            timeout=60.0
        )
        response.raise_for_status()
        llm_response = response.json().get("response", "")
        return self._parse_llm_response(llm_response)

    async def _process_with_azure(
        self, 
        content: str, 
        url: str,
        title: Optional[str]
    ) -> ProcessedContent:
        """
        Process with Azure OpenAI (non-streaming)
        """
        messages = [
            {
                "role": "system",
                "content": "You are a how-to guide extraction assistant. Focus on extracting actionable steps, instructions, and practical information from content."
            },
            {
                "role": "user",
                "content": f"""Analyze this content as a how-to guide and extract actionable information:
1. A clear, action-oriented title (max 100 chars)
2. Main objective/goal of this guide (what will the user achieve?)
3. 5-10 relevant skill/tool tags
4. Step-by-step instructions (numbered list)
5. Overall difficulty level (beginner/intermediate/advanced)
6. Estimated time to complete
7. Prerequisites or tools needed
8. Common problems/solutions mentioned
9. Clean, actionable content (remove ads, focus on instructions)

URL: {url}
Current Title: {title or 'None'}

Content:
{content[:4000]}

Respond in this exact format:
TITLE: [action-oriented title, e.g. "How to..."]
SUMMARY: [what the user will learn/achieve]
TAGS: skill1, tool1, technique1, category1
KEY_POINTS:
1. [First main step]
2. [Second main step]
3. [Third main step]
SENTIMENT: [difficulty: beginner/intermediate/advanced]
READING_TIME: [time to complete in minutes]
ENTITIES:
  Tools: Tool1, Tool2
  Skills: Skill1, Skill2
  Prerequisites: Prereq1, Prereq2
QUESTIONS:
- What problem does this solve?
- What are the key steps?
- What tools are needed?
PROCESSED:
[step-by-step guide extracted from content]"""
            }
        ]
        
        response = await self.azure_client.post(
            f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}",
            json={
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "stream": False
            },
            timeout=60.0
        )
        response.raise_for_status()
        llm_response = response.json()["choices"][0]["message"]["content"]
        return self._parse_llm_response(llm_response)

    def _parse_llm_response(self, response: str) -> ProcessedContent:
        """
        Parse LLM response into structured format
        """
        lines = response.strip().split('\n')
        
        title = ""
        summary = ""
        tags = []
        key_points = []
        sentiment = "intermediate"
        reading_time = 0
        entities = {"Tools": [], "Skills": [], "Prerequisites": []}
        questions = []
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
            elif line.startswith("KEY_POINTS:"):
                current_section = "key_points"
            elif line.startswith("SENTIMENT:"):
                sentiment = line[10:].strip()
                current_section = None
            elif line.startswith("READING_TIME:"):
                try:
                    reading_time = int(line[13:].strip().split(" ")[0])
                except ValueError:
                    reading_time = 0
                current_section = None
            elif line.startswith("ENTITIES:"):
                current_section = "entities"
            elif line.startswith("QUESTIONS:"):
                current_section = "questions"
            elif line.startswith("PROCESSED:"):
                current_section = "processed"
            elif current_section == "key_points" and line.startswith("-"):
                key_points.append(line[1:].strip())
            elif current_section == "entities":
                if line.startswith("Tools:"):
                    entities["Tools"] = [e.strip() for e in line[6:].strip().split(',') if e.strip()]
                elif line.startswith("Skills:"):
                    entities["Skills"] = [e.strip() for e in line[7:].strip().split(',') if e.strip()]
                elif line.startswith("Prerequisites:"):
                    entities["Prerequisites"] = [e.strip() for e in line[14:].strip().split(',') if e.strip()]
            elif current_section == "questions" and line.startswith("-"):
                questions.append(line[1:].strip())
            elif current_section == "processed" and line:
                processed_content.append(line)
        
        return ProcessedContent(
            title=title[:100],
            summary=summary[:200],
            content='\n'.join(processed_content),
            tags=tags[:10],
            key_points=key_points,
            sentiment=sentiment,
            reading_time=reading_time,
            entities=entities,
            questions=questions
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
            tags=tags,
            key_points=[],
            sentiment="intermediate",
            reading_time=0,
            entities={"Tools": [], "Skills": [], "Prerequisites": []},
            questions=[]
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.ollama_client.aclose()
        if self.azure_client:
            await self.azure_client.aclose()