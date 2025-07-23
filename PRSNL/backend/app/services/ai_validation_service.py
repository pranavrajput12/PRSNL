"""
AI Validation Service for PRSNL
Provides validation capabilities for AI-generated content
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIValidationService:
    """Service for validating AI-generated content and responses."""
    
    def __init__(self):
        self.enabled = True
        logger.info("AI Validation Service initialized")
    
    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate an AI response for quality and safety.
        
        Args:
            response: The AI response to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation - can be extended
        if not response:
            return False
        
        # For content analysis responses, check for title OR summary OR content
        title = response.get('title', '')
        summary = response.get('summary', '')
        content = response.get('content', response.get('text', ''))
        
        # Valid if we have any meaningful content
        if title and len(title.strip()) > 0:
            return True
        if summary and len(summary.strip()) > 0:
            return True
        if content and len(content.strip()) > 0:
            return True
            
        return False
    
    async def validate_content(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate content before processing.
        
        Args:
            content: The content to validate
            content_type: Optional content type for specific validation
            
        Returns:
            Dict with validation results
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Basic length check
        if not content or len(content.strip()) == 0:
            validation_result['valid'] = False
            validation_result['issues'].append('Content is empty')
            
        # Length limits
        if len(content) > 1_000_000:  # 1MB text limit
            validation_result['valid'] = False
            validation_result['issues'].append('Content exceeds maximum length')
            
        return validation_result
    
    async def sanitize_content(self, content: str) -> str:
        """
        Sanitize content for safe processing.
        
        Args:
            content: The content to sanitize
            
        Returns:
            Sanitized content
        """
        # Basic sanitization
        if not content:
            return ""
            
        # Remove excessive whitespace
        sanitized = ' '.join(content.split())
        
        return sanitized
    
    async def validate_content_analysis(self, response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate content analysis response from AI service
        
        Args:
            response: AI response to validate (can be None for fallback)
            
        Returns:
            Validated content analysis response or fallback response
        """
        if response is None:
            # Return default fallback response
            return {
                "title": "Content Analysis Unavailable",
                "summary": "Unable to analyze content at this time.",
                "key_points": [],
                "tags": [],
                "entities": [],
                "insights": [],
                "error": "Analysis service temporarily unavailable"
            }
        
        # Handle string response (convert to dict or return fallback)
        if isinstance(response, str):
            logger.warning(f"AI returned string instead of JSON: {response[:100]}...")
            try:
                import json
                response = json.loads(response)
                logger.info("Successfully parsed string response as JSON")
            except json.JSONDecodeError:
                logger.error("Failed to parse string response as JSON, returning fallback")
                return {
                    "title": "Content Analysis Error",
                    "summary": response[:200] if len(response) > 50 else "Unable to process AI response.",
                    "key_points": [],
                    "tags": [],
                    "entities": [],
                    "insights": [],
                    "error": "AI returned non-JSON response"
                }
        
        # Validate the response using existing validation (now guaranteed to be dict)
        if not await self.validate_response(response):
            # Return fallback if validation fails
            return {
                "title": "Content Analysis Error",
                "summary": "Content analysis failed validation.",
                "key_points": [],
                "tags": [],
                "entities": [],
                "insights": [],
                "error": "Analysis response failed validation"
            }
        
        # Ensure required fields are present
        validated_response = {
            "title": response.get("title", "Untitled Content"),
            "summary": response.get("summary", ""),
            "key_points": response.get("key_points", []),
            "tags": response.get("tags", []),
            "entities": response.get("entities", []),
            "insights": response.get("insights", []),
            "content_type": response.get("content_type", "unknown"),
            "workflow_used": response.get("workflow_used", False)
        }
        
        return validated_response
    
    async def validate_tags(self, response: str) -> list:
        """
        Validate and parse tags from AI response
        
        Args:
            response: AI response string (potentially JSON)
            
        Returns:
            List of validated tags
        """
        try:
            import json
            
            # Try to parse as JSON
            if isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = response
            
            # Extract tags from different possible formats
            tags = []
            if isinstance(parsed, dict):
                tags = parsed.get("tags", [])
            elif isinstance(parsed, list):
                tags = parsed
            
            # Validate and clean tags
            validated_tags = []
            for tag in tags:
                if isinstance(tag, str) and len(tag.strip()) > 0:
                    clean_tag = tag.strip().lower()
                    if len(clean_tag) <= 50 and clean_tag not in validated_tags:
                        validated_tags.append(clean_tag)
                elif isinstance(tag, dict) and "name" in tag:
                    clean_tag = tag["name"].strip().lower()
                    if len(clean_tag) <= 50 and clean_tag not in validated_tags:
                        validated_tags.append(clean_tag)
            
            return validated_tags[:10]  # Limit to 10 tags
            
        except Exception as e:
            logger.error(f"Tag validation failed: {e}")
            return ["general", "content"]  # Fallback tags
    
    async def validate_summary(self, response: str) -> dict:
        """
        Validate and parse summary from AI response
        
        Args:
            response: AI response string (potentially JSON)
            
        Returns:
            Dictionary with validated summary
        """
        try:
            import json
            
            # Try to parse as JSON
            if isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = response
            
            if isinstance(parsed, dict):
                return {
                    "brief": parsed.get("brief", "Summary not available"),
                    "detailed": parsed.get("detailed", ""),
                    "key_takeaways": parsed.get("key_takeaways", [])
                }
            else:
                # If not a dict, treat as plain text summary
                return {
                    "brief": str(parsed)[:200] if str(parsed) else "Summary not available",
                    "detailed": "",
                    "key_takeaways": []
                }
                
        except Exception as e:
            logger.error(f"Summary validation failed: {e}")
            return {
                "brief": "Summary processing failed",
                "detailed": "",
                "key_takeaways": []
            }


# Singleton instance
ai_validation_service = AIValidationService()