"""
AI Validation Service using Guardrails-AI
Ensures all AI outputs conform to expected schemas and quality standards
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

try:
    from guardrails import Guard
    from guardrails.validators import (
        ValidLength,
        ValidJson,
        TwoWords,
        ValidChoices,
        ValidRange,
        EndsWith,
        LowerCase,
        IsHighQualitySentence,
        ValidUrl
    )
    GUARDRAILS_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Guardrails-AI not installed. AI validation will be limited.")
    GUARDRAILS_AVAILABLE = False
    Guard = None

logger = logging.getLogger(__name__)


class ContentCategory(str, Enum):
    ARTICLE = "article"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    NEWS = "news"
    DISCUSSION = "discussion"
    VIDEO = "video"
    DEVELOPMENT = "development"
    OTHER = "other"


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Pydantic models for validation
class ContentAnalysisSchema(BaseModel):
    """Schema for content analysis validation"""
    title: str = Field(..., min_length=5, max_length=100, description="Clear, descriptive title")
    summary: str = Field(..., min_length=20, max_length=500, description="Concise summary")
    detailed_summary: str = Field(..., min_length=50, max_length=2000, description="Detailed summary")
    category: ContentCategory
    tags: List[str] = Field(..., min_items=1, max_items=10)
    key_points: List[str] = Field(..., min_items=3, max_items=7)
    entities: Dict[str, List[str]]
    sentiment: SentimentType
    difficulty_level: DifficultyLevel
    estimated_reading_time: int = Field(..., ge=1, le=120)
    
    @validator('tags')
    def validate_tags(cls, v):
        # Ensure tags are lowercase and properly formatted
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator('key_points')
    def validate_key_points(cls, v):
        # Ensure key points are meaningful (at least 10 chars each)
        return [point for point in v if len(point) >= 10]


class SummarySchema(BaseModel):
    """Schema for summary validation"""
    brief: str = Field(..., min_length=50, max_length=300)
    detailed: str = Field(..., min_length=100, max_length=1000)
    key_takeaways: List[str] = Field(..., min_items=3, max_items=5)


class TagGenerationSchema(BaseModel):
    """Schema for tag generation validation"""
    tags: List[str] = Field(..., min_items=1, max_items=15)
    confidence_scores: Optional[Dict[str, float]] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove duplicates and ensure lowercase
        unique_tags = list(dict.fromkeys([tag.lower().strip() for tag in v if tag.strip()]))
        return unique_tags[:10]  # Limit to 10 tags


class AIValidationService:
    """Validates AI outputs using Guardrails-AI"""
    
    def __init__(self):
        self.guards = {}
        if GUARDRAILS_AVAILABLE:
            self._initialize_guards()
    
    def _initialize_guards(self):
        """Initialize Guardrails guards for different validation scenarios"""
        
        # Content Analysis Guard
        self.guards['content_analysis'] = Guard.from_pydantic(
            output_class=ContentAnalysisSchema,
            description="Validates content analysis output"
        )
        
        # Summary Guard
        self.guards['summary'] = Guard.from_pydantic(
            output_class=SummarySchema,
            description="Validates summary generation"
        )
        
        # Tag Generation Guard
        self.guards['tags'] = Guard.from_pydantic(
            output_class=TagGenerationSchema,
            description="Validates tag generation"
        )
        
        # Add custom validators
        self._add_custom_validators()
    
    def _add_custom_validators(self):
        """Add custom validators to guards"""
        if not GUARDRAILS_AVAILABLE:
            return
        
        # Content analysis validators
        if 'content_analysis' in self.guards:
            # Title should not end with generic terms
            self.guards['content_analysis'].use(
                EndsWith(["analysis", "summary", "overview"], negate=True),
                on="title"
            )
            
            # Tags should be lowercase
            self.guards['content_analysis'].use(
                LowerCase(),
                on="tags"
            )
    
    async def validate_content_analysis(self, ai_output: Union[str, Dict, None]) -> Dict[str, Any]:
        """Validate content analysis output"""
        if ai_output is None:
            logger.warning("AI output is None, returning default analysis")
            return self._get_default_content_analysis()
            
        if not GUARDRAILS_AVAILABLE:
            # Fallback validation using Pydantic only
            try:
                if isinstance(ai_output, str):
                    ai_output = json.loads(ai_output)
                validated = ContentAnalysisSchema(**ai_output)
                result = validated.dict(by_alias=True, exclude_unset=False, exclude_none=False)
                
                # Convert enum values to strings for JSON serialization
                if 'category' in result and hasattr(result['category'], 'value'):
                    result['category'] = result['category'].value
                if 'sentiment' in result and hasattr(result['sentiment'], 'value'):
                    result['sentiment'] = result['sentiment'].value
                if 'difficulty_level' in result and hasattr(result['difficulty_level'], 'value'):
                    result['difficulty_level'] = result['difficulty_level'].value
                    
                return result
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                return self._get_default_content_analysis()
        
        try:
            # Use Guardrails for validation
            result = self.guards['content_analysis'].parse(
                ai_output if isinstance(ai_output, str) else json.dumps(ai_output)
            )
            
            if result.validated_output:
                return result.validated_output
            else:
                logger.warning(f"Validation failed: {result.error}")
                return self._get_default_content_analysis()
                
        except Exception as e:
            logger.error(f"Guardrails validation error: {e}")
            return self._get_default_content_analysis()
    
    async def validate_summary(self, ai_output: Union[str, Dict]) -> Dict[str, Any]:
        """Validate summary output"""
        if not GUARDRAILS_AVAILABLE:
            # Fallback validation
            try:
                if isinstance(ai_output, str):
                    # Try to parse as JSON first
                    try:
                        ai_output = json.loads(ai_output)
                    except:
                        # If not JSON, treat as plain text summary
                        ai_output = {
                            "brief": ai_output[:300],
                            "detailed": ai_output[:1000],
                            "key_takeaways": ["Summary provided", "Content analyzed", "Key points extracted"]
                        }
                
                validated = SummarySchema(**ai_output)
                return validated.dict()
            except Exception as e:
                logger.error(f"Summary validation failed: {e}")
                return self._get_default_summary()
        
        try:
            result = self.guards['summary'].parse(
                ai_output if isinstance(ai_output, str) else json.dumps(ai_output)
            )
            
            if result.validated_output:
                return result.validated_output
            else:
                logger.warning(f"Summary validation failed: {result.error}")
                return self._get_default_summary()
                
        except Exception as e:
            logger.error(f"Summary validation error: {e}")
            return self._get_default_summary()
    
    async def validate_tags(self, ai_output: Union[str, List[str], Dict]) -> List[str]:
        """Validate tag generation output"""
        if not GUARDRAILS_AVAILABLE:
            # Fallback validation
            try:
                if isinstance(ai_output, str):
                    # Try to parse as JSON
                    try:
                        ai_output = json.loads(ai_output)
                    except:
                        # If not JSON, split by common delimiters
                        ai_output = [tag.strip() for tag in ai_output.split(',')]
                
                if isinstance(ai_output, list):
                    ai_output = {"tags": ai_output}
                
                validated = TagGenerationSchema(**ai_output)
                return validated.tags
            except Exception as e:
                logger.error(f"Tag validation failed: {e}")
                return ["general", "content"]
        
        try:
            result = self.guards['tags'].parse(
                ai_output if isinstance(ai_output, str) else json.dumps(ai_output)
            )
            
            if result.validated_output:
                return result.validated_output.get('tags', ["general"])
            else:
                logger.warning(f"Tag validation failed: {result.error}")
                return ["general", "content"]
                
        except Exception as e:
            logger.error(f"Tag validation error: {e}")
            return ["general", "content"]
    
    def validate_json_structure(self, ai_output: str, expected_structure: Dict) -> Dict[str, Any]:
        """Validate that AI output matches expected JSON structure"""
        try:
            parsed = json.loads(ai_output)
            
            # Check all required keys are present
            for key in expected_structure:
                if key not in parsed:
                    logger.warning(f"Missing required key: {key}")
                    parsed[key] = self._get_default_value(expected_structure[key])
            
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON output: {e}")
            return expected_structure
    
    def _get_default_value(self, value_type: Any) -> Any:
        """Get default value based on type"""
        if value_type == str:
            return ""
        elif value_type == list:
            return []
        elif value_type == dict:
            return {}
        elif value_type == int:
            return 0
        elif value_type == float:
            return 0.0
        else:
            return None
    
    def _get_default_content_analysis(self) -> Dict[str, Any]:
        """Return default content analysis structure"""
        return {
            "title": "Untitled Content",
            "summary": "Content analysis unavailable",
            "detailed_summary": "Unable to analyze content at this time",
            "category": "other",
            "tags": ["general"],
            "key_points": ["Content captured", "Analysis pending", "Review required"],
            "entities": {
                "people": [],
                "organizations": [],
                "technologies": [],
                "concepts": []
            },
            "sentiment": "neutral",
            "difficulty_level": "intermediate",
            "estimated_reading_time": 5
        }
    
    def _get_default_summary(self) -> Dict[str, Any]:
        """Return default summary structure"""
        return {
            "brief": "Summary generation failed. Content has been captured for review.",
            "detailed": "The content has been captured but automatic summarization was not successful. Please review the original content.",
            "key_takeaways": ["Content captured", "Manual review recommended", "Original content preserved"]
        }
    
    async def validate_and_repair(self, ai_output: Union[str, Dict], output_type: str) -> Dict[str, Any]:
        """Validate and attempt to repair AI output based on type"""
        validators = {
            'content_analysis': self.validate_content_analysis,
            'summary': self.validate_summary,
            'tags': self.validate_tags
        }
        
        if output_type in validators:
            return await validators[output_type](ai_output)
        else:
            logger.warning(f"Unknown output type: {output_type}")
            return ai_output if isinstance(ai_output, dict) else {"content": ai_output}


# Singleton instance
ai_validation_service = AIValidationService()