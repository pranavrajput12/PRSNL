"""
AI-powered Crew.ai tools for advanced analysis and generation
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.unified_ai_service import unified_ai_service
from app.tools import register_tool

logger = logging.getLogger(__name__)


class EnhancementSuggestionInput(BaseModel):
    """Input schema for enhancement suggestion tool"""
    content: str = Field(..., description="Content to enhance")
    content_type: Optional[str] = Field("general", description="Type of content")
    focus_areas: Optional[List[str]] = Field([], description="Areas to focus on")


@register_tool("enhancement_suggester")
class EnhancementSuggestionTool(BaseTool):
    name: str = "Enhancement Suggester"
    description: str = (
        "Suggests enhancements and improvements for content. "
        "Identifies gaps, proposes additions, and recommends related topics."
    )
    args_schema: Type[BaseModel] = EnhancementSuggestionInput
    
    def _run(
        self,
        content: str,
        content_type: str = "general",
        focus_areas: List[str] = []
    ) -> str:
        """Generate enhancement suggestions"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_suggest_enhancements(content, content_type, focus_areas)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Enhancement suggestion failed: {e}")
            return f"Failed to suggest enhancements: {str(e)}"
    
    async def _async_suggest_enhancements(
        self,
        content: str,
        content_type: str,
        focus_areas: List[str]
    ) -> str:
        """Async enhancement suggestion"""
        try:
            focus_str = f"Focus on: {', '.join(focus_areas)}" if focus_areas else ""
            
            prompt = f"""Analyze this {content_type} content and suggest enhancements:

Content: {content[:2000]}

{focus_str}

Provide:
1. Content gaps that should be filled
2. Additional topics to explore
3. Ways to improve clarity and depth
4. Related resources or references to add
5. Structural improvements

Format as JSON with keys: gaps, additional_topics, improvements, resources, structure"""

            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="You are an expert content enhancement advisor.",
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            try:
                suggestions = json.loads(response)
            except:
                suggestions = {"error": "Failed to parse suggestions"}
            
            output = "Enhancement Suggestions:\n\n"
            
            if suggestions.get("gaps"):
                output += "Content Gaps:\n"
                for gap in suggestions["gaps"][:5]:
                    output += f"- {gap}\n"
                output += "\n"
            
            if suggestions.get("additional_topics"):
                output += "Additional Topics to Explore:\n"
                for topic in suggestions["additional_topics"][:5]:
                    output += f"- {topic}\n"
                output += "\n"
            
            if suggestions.get("improvements"):
                output += "Improvement Suggestions:\n"
                for improvement in suggestions["improvements"][:5]:
                    output += f"- {improvement}\n"
                output += "\n"
            
            if suggestions.get("resources"):
                output += "Recommended Resources:\n"
                for resource in suggestions["resources"][:3]:
                    output += f"- {resource}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Async enhancement suggestion failed: {e}")
            raise


class SummaryGeneratorInput(BaseModel):
    """Input schema for summary generator tool"""
    content: str = Field(..., description="Content to summarize")
    summary_type: Optional[str] = Field("brief", description="Type of summary: brief, detailed, key_points, technical, eli5")
    max_length: Optional[int] = Field(500, description="Maximum summary length")


@register_tool("summary_generator")
class SummaryGeneratorTool(BaseTool):
    name: str = "Summary Generator"
    description: str = (
        "Generates various types of summaries for content. "
        "Can create brief, detailed, technical, or simplified summaries."
    )
    args_schema: Type[BaseModel] = SummaryGeneratorInput
    
    def _run(
        self,
        content: str,
        summary_type: str = "brief",
        max_length: int = 500
    ) -> str:
        """Generate summary"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_generate_summary(content, summary_type, max_length)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Failed to generate summary: {str(e)}"
    
    async def _async_generate_summary(
        self,
        content: str,
        summary_type: str,
        max_length: int
    ) -> str:
        """Async summary generation"""
        try:
            summary = await unified_ai_service.generate_summary(
                content=content,
                summary_type=summary_type
            )
            
            # Truncate if needed
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            output = f"Summary ({summary_type}):\n\n{summary}"
            return output
            
        except Exception as e:
            logger.error(f"Async summary generation failed: {e}")
            raise


class EntityExtractorInput(BaseModel):
    """Input schema for entity extractor tool"""
    content: str = Field(..., description="Content to extract entities from")
    entity_types: Optional[List[str]] = Field(
        ["person", "organization", "location", "technology", "concept"],
        description="Types of entities to extract"
    )


@register_tool("entity_extractor")
class EntityExtractorTool(BaseTool):
    name: str = "Entity Extractor"
    description: str = (
        "Extracts named entities from content including people, "
        "organizations, locations, technologies, and concepts."
    )
    args_schema: Type[BaseModel] = EntityExtractorInput
    
    def _run(
        self,
        content: str,
        entity_types: List[str] = ["person", "organization", "location", "technology", "concept"]
    ) -> str:
        """Extract entities from content"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_extract_entities(content, entity_types)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return f"Failed to extract entities: {str(e)}"
    
    async def _async_extract_entities(
        self,
        content: str,
        entity_types: List[str]
    ) -> str:
        """Async entity extraction"""
        try:
            # Use AI to extract entities
            prompt = f"""Extract entities from this content. Focus on these types: {', '.join(entity_types)}

Content: {content[:3000]}

Return as JSON with entity types as keys and lists of entities as values."""

            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="You are an expert at named entity recognition.",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                entities = json.loads(response)
            except:
                return "Failed to extract entities"
            
            output = "Extracted Entities:\n\n"
            
            for entity_type in entity_types:
                if entity_type in entities and entities[entity_type]:
                    output += f"{entity_type.title()}s:\n"
                    for entity in entities[entity_type][:10]:
                        output += f"- {entity}\n"
                    output += "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Async entity extraction failed: {e}")
            raise


class QuestionGeneratorInput(BaseModel):
    """Input schema for question generator tool"""
    content: str = Field(..., description="Content to generate questions from")
    question_types: Optional[List[str]] = Field(
        ["comprehension", "critical", "exploratory"],
        description="Types of questions to generate"
    )
    count: Optional[int] = Field(5, description="Number of questions to generate")


@register_tool("question_generator")
class QuestionGeneratorTool(BaseTool):
    name: str = "Question Generator"
    description: str = (
        "Generates thoughtful questions based on content. "
        "Can create comprehension, critical thinking, and exploratory questions."
    )
    args_schema: Type[BaseModel] = QuestionGeneratorInput
    
    def _run(
        self,
        content: str,
        question_types: List[str] = ["comprehension", "critical", "exploratory"],
        count: int = 5
    ) -> str:
        """Generate questions from content"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_generate_questions(content, question_types, count)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return f"Failed to generate questions: {str(e)}"
    
    async def _async_generate_questions(
        self,
        content: str,
        question_types: List[str],
        count: int
    ) -> str:
        """Async question generation"""
        try:
            type_descriptions = {
                "comprehension": "test understanding of key concepts",
                "critical": "encourage critical thinking and analysis",
                "exploratory": "explore implications and connections"
            }
            
            type_str = ", ".join([f"{qt} ({type_descriptions.get(qt, qt)})" for qt in question_types])
            
            prompt = f"""Generate {count} thoughtful questions based on this content.
Include these types: {type_str}

Content: {content[:2000]}

Return as JSON with a 'questions' array, each item having 'question' and 'type' fields."""

            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="You are an expert educator who creates insightful questions.",
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response)
                questions = result.get("questions", [])
            except:
                return "Failed to generate questions"
            
            output = f"Generated Questions ({len(questions)}):\n\n"
            
            for i, q in enumerate(questions[:count], 1):
                output += f"{i}. {q.get('question', 'N/A')}\n"
                output += f"   Type: {q.get('type', 'unknown')}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Async question generation failed: {e}")
            raise


class TagSuggesterInput(BaseModel):
    """Input schema for tag suggester tool"""
    content: str = Field(..., description="Content to analyze for tag suggestions")
    content_type: Optional[str] = Field("general", description="Type of content")
    max_tags: Optional[int] = Field(10, description="Maximum number of tags to suggest")


@register_tool("tag_suggester")
class TagSuggesterTool(BaseTool):
    name: str = "Tag Suggester"
    description: str = (
        "Suggests relevant tags for content based on its topics, themes, and context. "
        "Useful for content categorization and organization."
    )
    args_schema: Type[BaseModel] = TagSuggesterInput
    
    def _run(
        self,
        content: str,
        content_type: str = "general",
        max_tags: int = 10
    ) -> str:
        """Generate tag suggestions for content"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_suggest_tags(content, content_type, max_tags)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Tag suggestion failed: {e}")
            return f"Failed to suggest tags: {str(e)}"
    
    async def _async_suggest_tags(
        self,
        content: str,
        content_type: str,
        max_tags: int
    ) -> str:
        """Async tag suggestion"""
        try:
            prompt = f"""Analyze this {content_type} content and suggest up to {max_tags} relevant tags.

Content: {content[:2000]}

Consider:
- Main topics and themes
- Key concepts and entities
- Category or domain
- Technical terms (if applicable)
- Relevant keywords

Return as JSON with a 'tags' array, each item having 'tag' and 'relevance_score' (0-1) fields.
Sort by relevance score (highest first)."""

            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="You are an expert content curator who creates precise, relevant tags.",
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response)
                tags = result.get("tags", [])
            except:
                return "Failed to suggest tags"
            
            output = f"Suggested Tags ({len(tags)}):\n\n"
            
            for i, tag_info in enumerate(tags[:max_tags], 1):
                tag = tag_info.get('tag', 'N/A')
                score = tag_info.get('relevance_score', 0)
                output += f"{i}. {tag} (relevance: {score:.2f})\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Async tag suggestion failed: {e}")
            raise