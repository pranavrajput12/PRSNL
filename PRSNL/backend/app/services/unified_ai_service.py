"""
Unified AI Service Layer for all AI-powered features
Uses Azure OpenAI for all LLM operations
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from openai import AsyncAzureOpenAI
import numpy as np
from app.config import settings
from app.services.cache import cache_service, CacheKeys
import hashlib
from app.services.ai_validation_service import ai_validation_service

logger = logging.getLogger(__name__)


class UnifiedAIService:
    """Centralized AI service for all features"""
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT  # gpt-4.1
        # Embedding model deployment - configured
        self.embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT  # text-embedding-ada-002
        self.embedding_available = bool(self.embedding_deployment and settings.AZURE_OPENAI_API_KEY)
        
    async def generate_embeddings(self, texts: List[str], cache_key_prefix: str = "emb") -> List[List[float]]:
        """Generate embeddings for multiple texts with caching"""
        if not self.embedding_available:
            logger.warning("Embedding model not configured. Returning empty embeddings.")
            # Return zero vectors as fallback
            return [[0.0] * 1536 for _ in texts]
            
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache first
        for i, text in enumerate(texts):
            cache_key = f"{cache_key_prefix}:{hashlib.sha256(text.encode()).hexdigest()}"
            cached = await cache_service.get(cache_key)
            if cached:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            try:
                # Process in batches of 16 for efficiency
                batch_size = 16
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i+batch_size]
                    response = await self.client.embeddings.create(
                        model=self.embedding_deployment,
                        input=batch
                    )
                    
                    for j, embedding in enumerate(response.data):
                        idx = uncached_indices[i+j]
                        emb_vector = embedding.embedding
                        embeddings[idx] = emb_vector
                        
                        # Cache the embedding
                        cache_key = f"{cache_key_prefix}:{hashlib.sha256(texts[idx].encode()).hexdigest()}"
                        await cache_service.set(cache_key, emb_vector, expire=86400)  # 24 hours
                        
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                # Return None for failed embeddings
                for idx in uncached_indices:
                    if embeddings[idx] is None:
                        embeddings[idx] = [0.0] * 1536  # Default embedding size
        
        return embeddings
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict] = None
    ) -> str:
        """Generate completion with Azure OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add response format if specified (for JSON mode)
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI completion error: {e}")
            raise
    
    async def analyze_content(self, content: str, url: Optional[str] = None, enable_key_points: bool = True, enable_entities: bool = True) -> Dict[str, Any]:
        """
        Comprehensive content analysis workflow
        Returns: title, summary, category, tags, key_points, entities
        """
        system_prompt = """You are an expert content analyst. Analyze the given content and provide a comprehensive analysis in JSON format."""
        
        prompt = f"""Analyze this content and provide a detailed analysis:

URL: {url or 'N/A'}
Content: {content[:3000]}...

Provide analysis in this exact JSON format:
{{
    "title": "The original title or a clear, descriptive title based on the content (max 100 chars, do NOT add 'Analysis' or similar suffixes)",
    "summary": "A concise 2-3 sentence summary",
    "detailed_summary": "A comprehensive paragraph summary",
    "category": "One of: article, tutorial, reference, news, discussion, video, other",
    "tags": ["up to 10 relevant tags", "lowercase", "specific"],
    "key_points": ["3-5 main takeaways", "actionable insights"],
    "entities": {{
        "people": ["mentioned people"],
        "organizations": ["mentioned orgs"],
        "technologies": ["mentioned tech/tools"],
        "concepts": ["key concepts discussed"]
    }},
    "sentiment": "positive|neutral|negative|mixed",
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_reading_time": 5
}}"""
        
        try:
            response = await self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            logger.debug(f"AI response: {response}")
            
            # Validate the AI output
            try:
                validated_response = await ai_validation_service.validate_content_analysis(response)
                logger.debug(f"Validated response: {validated_response}")
                return validated_response
            except Exception as validation_error:
                logger.error(f"Validation error: {validation_error}")
                # Return fallback response
                return await ai_validation_service.validate_content_analysis(None)
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            # Return validated default analysis on failure
            return await ai_validation_service.validate_content_analysis(None)
    
    async def find_duplicates_semantic(
        self,
        content: str,
        embeddings_to_compare: List[Tuple[str, List[float]]],
        threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """Find semantic duplicates using embeddings"""
        # Generate embedding for new content
        new_embedding = (await self.generate_embeddings([content]))[0]
        
        duplicates = []
        for item_id, embedding in embeddings_to_compare:
            # Calculate cosine similarity
            similarity = np.dot(new_embedding, embedding) / (
                np.linalg.norm(new_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= threshold:
                duplicates.append({
                    "item_id": item_id,
                    "similarity": float(similarity),
                    "is_exact": similarity > 0.95
                })
        
        return sorted(duplicates, key=lambda x: x["similarity"], reverse=True)
    
    async def generate_tags(
        self, 
        content: str, 
        limit: int = 10,
        existing_tags: Optional[List[str]] = None
    ) -> List[str]:
        """Generate validated tags for content"""
        system_prompt = """You are an expert at generating relevant, searchable tags for content. 
        Generate specific, lowercase tags that capture the essence of the content."""
        
        existing_tags_str = f"\nExisting tags in system: {', '.join(existing_tags)}" if existing_tags else ""
        
        prompt = f"""Generate {limit} relevant tags for this content:{existing_tags_str}

Content: {content[:2000]}

Rules:
1. Tags should be lowercase, single or compound words
2. Be specific rather than generic
3. Include technical terms if relevant
4. Consider the content type and domain

Respond in JSON format:
{{
    "tags": ["tag1", "tag2", "tag3", ...],
    "confidence_scores": {{"tag1": 0.9, "tag2": 0.8, ...}}
}}"""
        
        try:
            response = await self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            # Validate tags
            validated_tags = await ai_validation_service.validate_tags(response)
            return validated_tags[:limit]
            
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            return ["general", "content"]
    
    async def generate_summary(
        self,
        content: str,
        summary_type: str = "brief",
        context: Optional[Dict] = None
    ) -> str:
        """Generate different types of summaries"""
        system_prompts = {
            "brief": "You are a concise summarizer. Provide brief, clear summaries.",
            "detailed": "You are a comprehensive summarizer. Provide detailed summaries with context.",
            "key_points": "You are an analyst. Extract and list the key points clearly.",
            "technical": "You are a technical writer. Focus on technical details and implications.",
            "eli5": "You are a teacher. Explain complex topics in simple terms."
        }
        
        prompts = {
            "brief": f"Summarize this in 2-3 sentences:\n\n{content[:2000]}",
            "detailed": f"Provide a comprehensive summary with main themes:\n\n{content[:3000]}",
            "key_points": f"Extract 5-7 key points as a bulleted list:\n\n{content[:2000]}",
            "technical": f"Summarize the technical aspects and implications:\n\n{content[:2000]}",
            "eli5": f"Explain this in simple terms a beginner would understand:\n\n{content[:2000]}"
        }
        
        # Add context if provided
        if context:
            context_str = f"\n\nContext: {json.dumps(context)}\n"
            prompts[summary_type] = prompts[summary_type].replace("\n\n", context_str + "\n\n", 1)
        
        try:
            # For structured summary types, request JSON format
            if summary_type in ["key_points", "technical"]:
                prompt_with_format = prompts.get(summary_type, prompts["brief"]) + \
                    '\n\nProvide response in JSON format: {"brief": "2-3 sentence summary", "detailed": "detailed summary", "key_takeaways": ["point1", "point2", "point3"]}'
                
                response = await self.complete(
                    prompt=prompt_with_format,
                    system_prompt=system_prompts.get(summary_type, system_prompts["brief"]),
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
                
                # Validate structured summary
                validated = await ai_validation_service.validate_summary(response)
                return validated.get('brief', response.strip())
            else:
                # For simple summaries, return plain text
                response = await self.complete(
                    prompt=prompts.get(summary_type, prompts["brief"]),
                    system_prompt=system_prompts.get(summary_type, system_prompts["brief"]),
                    temperature=0.3,
                    max_tokens=500
                )
                return response.strip()
                
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Unable to generate summary at this time."
    
    async def discover_relationships(
        self,
        content1: str,
        content2: str,
        metadata1: Optional[Dict] = None,
        metadata2: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Discover relationships between two pieces of content"""
        system_prompt = """You are an expert at identifying relationships between content. 
        Analyze the relationship and provide detailed insights."""
        
        prompt = f"""Analyze the relationship between these two pieces of content:

Content 1: {content1[:1000]}
Metadata 1: {json.dumps(metadata1) if metadata1 else 'N/A'}

Content 2: {content2[:1000]}
Metadata 2: {json.dumps(metadata2) if metadata2 else 'N/A'}

Provide analysis in JSON format:
{{
    "relationship_type": "one of: prerequisite|extends|related|contradicts|implements|references|part_of|alternative",
    "confidence": 0.0-1.0,
    "direction": "1->2|2->1|bidirectional",
    "explanation": "Clear explanation of the relationship",
    "shared_concepts": ["list of shared concepts"],
    "learning_path_order": "1->2|2->1|parallel|independent",
    "complementary_aspects": ["how they complement each other"]
}}"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response)
    
    async def generate_insights(
        self,
        items_data: List[Dict[str, Any]],
        timeframe: str = "week"
    ) -> Dict[str, Any]:
        """Generate insights from a collection of items"""
        # Prepare item summaries
        items_summary = []
        for item in items_data[:50]:  # Limit to prevent token overflow
            items_summary.append({
                "title": item.get("title", ""),
                "category": item.get("category", ""),
                "tags": item.get("tags", []),
                "created": item.get("created_at", ""),
                "summary": item.get("summary", "")[:100]
            })
        
        system_prompt = """You are a knowledge management insights analyst. 
        Analyze patterns and generate actionable insights."""
        
        prompt = f"""Analyze these items from the past {timeframe} and generate insights:

Items: {json.dumps(items_summary, indent=2)}

Generate comprehensive insights in JSON format:
{{
    "trending_topics": [
        {{"topic": "name", "count": 0, "growth": "+X%", "context": "why it's trending"}}
    ],
    "content_patterns": {{
        "most_captured_type": "article|video|etc",
        "peak_capture_times": ["time patterns"],
        "content_diversity_score": 0.0-1.0,
        "explanation": "pattern analysis"
    }},
    "learning_velocity": {{
        "items_per_day": 0.0,
        "knowledge_depth": "expanding|deepening|stagnant",
        "recommended_focus": "suggestion for learning"
    }},
    "knowledge_gaps": [
        {{"area": "topic", "suggestion": "what to explore", "reason": "why it matters"}}
    ],
    "connections_discovered": 0,
    "recommended_reviews": [
        "Items that should be reviewed based on patterns"
    ],
    "emerging_themes": [
        {{"theme": "name", "evidence": ["supporting items"], "potential": "future direction"}}
    ]
}}"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response)
    
    async def categorize_content(
        self,
        content: str,
        existing_categories: List[str],
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Smart categorization with confidence scores"""
        system_prompt = """You are an expert content categorizer. 
        Analyze content and assign appropriate categories with confidence scores."""
        
        prompt = f"""Categorize this content:

Content: {content[:2000]}

Existing categories: {', '.join(existing_categories)}

Rules:
1. Prefer existing categories when appropriate
2. Suggest new categories only when necessary
3. Provide confidence scores for each category
4. Can assign multiple categories if relevant

Respond in JSON format:
{{
    "primary_category": {{"name": "category", "confidence": 0.0-1.0}},
    "secondary_categories": [
        {{"name": "category", "confidence": 0.0-1.0}}
    ],
    "suggested_new_category": {{"name": "new_category", "reason": "why needed", "confidence": 0.0-1.0}},
    "reasoning": "explanation of categorization"
}}"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response)
        
        # Filter by confidence threshold
        if result["primary_category"]["confidence"] < confidence_threshold:
            result["primary_category"] = {"name": "uncategorized", "confidence": 1.0}
        
        result["secondary_categories"] = [
            cat for cat in result.get("secondary_categories", [])
            if cat["confidence"] >= confidence_threshold
        ]
        
        return result
    
    async def generate_learning_path(
        self,
        topic: str,
        current_knowledge: List[Dict[str, Any]],
        skill_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Generate personalized learning path"""
        knowledge_summary = [
            {"title": item["title"], "tags": item.get("tags", [])}
            for item in current_knowledge[:20]
        ]
        
        system_prompt = """You are an expert learning path designer. 
        Create personalized, practical learning paths."""
        
        prompt = f"""Design a learning path for: {topic}

Current skill level: {skill_level}
Existing knowledge: {json.dumps(knowledge_summary)}

Create a structured learning path in JSON format:
{{
    "learning_objectives": ["clear objectives"],
    "prerequisites": ["required knowledge before starting"],
    "learning_path": [
        {{
            "phase": "Foundation|Core|Advanced|Mastery",
            "topics": ["specific topics to learn"],
            "estimated_time": "X hours/days",
            "resources_needed": ["types of resources"],
            "practice_projects": ["hands-on projects"],
            "milestones": ["checkpoints to validate learning"]
        }}
    ],
    "knowledge_gaps": ["what's missing from current knowledge"],
    "recommended_pace": "intensive|regular|relaxed",
    "success_metrics": ["how to measure progress"],
    "next_steps": ["what to explore after completion"]
}}"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response)
    
    async def stream_chat_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: List[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Stream chat responses using Azure OpenAI"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if history:
            for msg in history:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            # Use Azure OpenAI streaming
            stream = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in stream_chat_response: {e}")
            yield f"Error generating response: {str(e)}"


# Singleton instance
unified_ai_service = UnifiedAIService()