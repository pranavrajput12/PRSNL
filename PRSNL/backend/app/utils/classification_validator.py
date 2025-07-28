"""
Classification Validation Pipeline

Ensures consistent and reliable URL classification results
with fallback mechanisms and error handling.
"""

import logging
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from app.utils.url_classifier import URLClassifier
from app.utils.domain_classification_cache import domain_cache

logger = logging.getLogger(__name__)


class ClassificationValidator:
    """Validates and ensures consistent URL classification results"""
    
    @staticmethod
    def validate_and_classify(url: str, user_override: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Main classification pipeline with validation and fallbacks
        
        Args:
            url: URL to classify
            user_override: User-selected content type (takes precedence)
            
        Returns:
            Tuple of (final_type, metadata)
        """
        try:
            # Step 1: User override takes highest precedence
            if user_override and user_override != 'auto':
                logger.info(f"🎯 Using user override: {user_override} for {url}")
                return user_override, {
                    'classification_method': 'user_override',
                    'classification_confidence': 1.0,
                    'original_url': url
                }
            
            # Step 2: Enhanced URL classification
            classification = URLClassifier.classify_url(url)
            
            # Step 3: Validate classification result
            validated_type, confidence = ClassificationValidator._validate_classification(
                url, classification
            )
            
            # Step 4: Add comprehensive metadata
            metadata = {
                'classification_method': classification['metadata'].get('classification_method', 'pattern_match'),
                'classification_confidence': confidence,
                'original_url': url,
                'platform': classification.get('platform'),
                'domain': urlparse(url).netloc.lower().replace('www.', ''),
                'validation_passed': True
            }
            
            # Add type-specific metadata
            if validated_type == 'recipe':
                metadata.update(classification['metadata'].get('recipe', {}))
            
            logger.info(f"✅ Classification complete: {url} → {validated_type} ({confidence:.0%})")
            return validated_type, metadata
            
        except Exception as e:
            logger.error(f"❌ Classification failed for {url}: {e}")
            return ClassificationValidator._fallback_classification(url)
    
    @staticmethod
    def _validate_classification(url: str, classification: Dict) -> Tuple[str, float]:
        """
        Validate classification results and apply business rules
        
        Returns:
            Tuple of (validated_type, confidence_score)
        """
        content_type = classification.get('content_type', 'auto')
        confidence = classification['metadata'].get('classification_confidence', 0.5)
        
        # Rule 1: If auto or no specific type, analyze further
        if content_type == 'auto':
            content_type = ClassificationValidator._analyze_url_patterns(url)
            confidence = max(0.3, confidence)  # Lower confidence for pattern matching
        
        # Rule 2: Minimum confidence thresholds
        if confidence < 0.3:
            logger.warning(f"⚠️ Low confidence classification: {url} → {content_type} ({confidence:.0%})")
            content_type = 'article'  # Safe fallback
            confidence = 0.3
        
        # Rule 3: Recipe URL validation
        if content_type == 'recipe':
            if not ClassificationValidator._validate_recipe_url(url):
                logger.warning(f"⚠️ Recipe validation failed for: {url}")
                content_type = 'article'
                confidence = 0.4
        
        # Rule 4: Development content validation
        if content_type == 'development':
            if not ClassificationValidator._validate_development_url(url):
                logger.warning(f"⚠️ Development validation failed for: {url}")
                content_type = 'article'
                confidence = 0.4
        
        return content_type, confidence
    
    @staticmethod
    def _analyze_url_patterns(url: str) -> str:
        """Analyze URL patterns for content type hints"""
        url_lower = url.lower()
        
        # Recipe patterns
        recipe_indicators = ['recipe', 'recipes', 'cooking', 'food', 'ingredients']
        if any(indicator in url_lower for indicator in recipe_indicators):
            return 'recipe'
        
        # Development patterns
        dev_indicators = ['github', 'docs', 'documentation', 'api', 'tutorial']
        if any(indicator in url_lower for indicator in dev_indicators):
            return 'development'
        
        # Video patterns
        video_indicators = ['youtube', 'video', 'watch']
        if any(indicator in url_lower for indicator in video_indicators):
            return 'video'
        
        return 'article'  # Safe default
    
    @staticmethod
    def _validate_recipe_url(url: str) -> bool:
        """Validate that a recipe URL is likely to contain recipe content"""
        url_lower = url.lower()
        
        # If it's from a known recipe domain with high confidence, trust it
        domain = urlparse(url).netloc.lower().replace('www.', '')
        trusted_recipe_domains = [
            'allrecipes.com', 'foodnetwork.com', 'epicurious.com', 
            'bonappetit.com', 'seriouseats.com', 'simplyrecipes.com'
        ]
        
        if any(trusted_domain in domain for trusted_domain in trusted_recipe_domains):
            # For trusted domains, just check it's not a category page
            category_indicators = ['/category/', '/tag/', '/search', '/categories', '/topics']
            if any(indicator in url_lower for indicator in category_indicators):
                return False
            return True
        
        # For other domains, use stricter validation
        recipe_terms = ['recipe', 'recipes', 'cooking', 'food']
        if not any(term in url_lower for term in recipe_terms):
            return False
        
        # Should not be just a category page
        category_indicators = ['/category/', '/tag/', '/recipes/', '/search']
        if any(indicator in url_lower for indicator in category_indicators):
            return False
        
        # Should have specific recipe indicators
        specific_indicators = ['/recipe/', '-recipe-', 'recipe/', '.html', '/']
        return any(indicator in url_lower for indicator in specific_indicators)
    
    @staticmethod
    def _validate_development_url(url: str) -> bool:
        """Validate that a development URL is likely to contain dev content"""
        url_lower = url.lower()
        
        # GitHub repos should have proper structure
        if 'github.com' in url_lower:
            return bool(re.search(r'github\.com/[\w\-\.]+/[\w\-\.]+', url_lower))
        
        # Documentation sites should have specific paths
        if any(term in url_lower for term in ['docs.', 'documentation']):
            return True
        
        # Stack Overflow should have questions
        if 'stackoverflow.com' in url_lower:
            return '/questions/' in url_lower
        
        return True  # Default to valid for other dev sites
    
    @staticmethod
    def _fallback_classification(url: str) -> Tuple[str, Dict]:
        """
        Fallback classification when primary methods fail
        
        Returns:
            Tuple of (fallback_type, metadata)
        """
        logger.warning(f"🔄 Using fallback classification for: {url}")
        
        # Simple domain-based fallback
        try:
            domain = urlparse(url).netloc.lower()
            
            if any(recipe_domain in domain for recipe_domain in [
                'allrecipes', 'foodnetwork', 'epicurious', 'recipe', 'cooking', 'food'
            ]):
                return 'recipe', {
                    'classification_method': 'fallback_domain',
                    'classification_confidence': 0.6,
                    'validation_passed': False
                }
            
            if any(dev_domain in domain for dev_domain in [
                'github', 'stackoverflow', 'docs.', 'developer'
            ]):
                return 'development', {
                    'classification_method': 'fallback_domain',
                    'classification_confidence': 0.6,
                    'validation_passed': False
                }
            
        except Exception as e:
            logger.error(f"❌ Fallback classification failed: {e}")
        
        # Ultimate fallback
        return 'article', {
            'classification_method': 'ultimate_fallback',
            'classification_confidence': 0.3,
            'validation_passed': False,
            'error': 'Classification pipeline failed'
        }


# Convenience function for easy import
def classify_url_with_validation(url: str, user_override: Optional[str] = None) -> Tuple[str, Dict]:
    """
    Main entry point for validated URL classification
    
    Returns:
        Tuple of (content_type, metadata)
    """
    return ClassificationValidator.validate_and_classify(url, user_override)