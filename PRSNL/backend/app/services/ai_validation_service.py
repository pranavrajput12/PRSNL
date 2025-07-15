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
            
        # Check for content
        content = response.get('content', response.get('text', ''))
        if not content or len(content.strip()) == 0:
            return False
            
        return True
    
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
        
        # Validate the response using existing validation
        if not self.validate_response(response):
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


# Singleton instance
ai_validation_service = AIValidationService()