"""
Smart Slug Generator for PRSNL Permalink System

Generates SEO-friendly, unique slugs for content with collision detection.
Optimized for the simplified /c/category/slug URL structure.
"""

import asyncio
import re
from typing import Dict, List, Optional

from nanoid import generate
from slugify import slugify
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ContentUrl, Item


class SmartSlugGenerator:
    """Generates unique, SEO-friendly slugs for content URLs."""
    
    # Categories for the simplified URL structure
    VALID_CATEGORIES = ['dev', 'learn', 'media', 'ideas']
    
    # Common stop words to remove for better SEO
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'how', 'what', 'when', 'where', 'why'
    }
    
    # Custom replacements for better readability
    CUSTOM_REPLACEMENTS = {
        '&': 'and',
        '@': 'at',
        '+': 'plus',
        '%': 'percent',
        '#': 'hash',
        '🎯': 'target',
        '💡': 'idea',
        '🚀': 'rocket',
        '⚡': 'fast',
        '🔥': 'hot',
        '💎': 'gem',
        '🎨': 'design',
        '🔧': 'tool',
        '📊': 'analytics',
        '📈': 'growth',
        '🛡️': 'security',
        '🌟': 'star',
        '💻': 'code'
    }
    
    @classmethod
    async def generate_unique_slug(
        cls, 
        title: str, 
        category: str, 
        content_id: Optional[str] = None
    ) -> str:
        """
        Generate a unique slug for the given title and category.
        
        Args:
            title: The content title to generate slug from
            category: The content category (dev, learn, media, ideas)
            content_id: Optional content ID (for updates, to exclude from collision check)
            
        Returns:
            Unique slug string
        """
        if category not in cls.VALID_CATEGORIES:
            category = 'dev'  # Default fallback
            
        # Generate base slug
        base_slug = cls._generate_base_slug(title)
        
        # Check for collisions and make unique
        unique_slug = await cls._ensure_unique_slug(base_slug, category, content_id)
        
        return unique_slug
    
    @classmethod
    def _generate_base_slug(cls, title: str) -> str:
        """Generate the base slug from title using python-slugify for better Unicode handling."""
        if not title or not title.strip():
            return 'untitled'
        
        # Apply custom emoji replacements first (without adding extra spaces)
        processed_title = title
        for search, replace in cls.CUSTOM_REPLACEMENTS.items():
            processed_title = processed_title.replace(search, replace)
        
        # Use python-slugify for robust slug generation
        slug = slugify(
            processed_title,
            max_length=60,
            word_boundary=True,
            lowercase=True,
            separator='-',
            replacements=[
                ['&', 'and'],
                ['@', 'at'],
                ['+', 'plus'],
                ['%', 'percent']
            ],
            stopwords=cls.STOP_WORDS if len(processed_title.split()) > 2 else None
        )
        
        return slug or 'untitled'
    
    @classmethod
    async def _ensure_unique_slug(
        cls, 
        base_slug: str, 
        category: str, 
        content_id: Optional[str] = None
    ) -> str:
        """Ensure slug is unique within the category."""
        async for session in get_db():
            try:
                counter = 1
                candidate_slug = base_slug
                
                while await cls._slug_exists(session, candidate_slug, category, content_id):
                    # Use nanoid for better collision handling after a few attempts
                    if counter <= 5:
                        candidate_slug = f"{base_slug}-{counter}"
                    else:
                        # Use nanoid for unique suffix after 5 collisions
                        unique_suffix = generate(size=6)  # Generates something like "V1StGX"
                        candidate_slug = f"{base_slug}-{unique_suffix}"
                    
                    counter += 1
                    
                    # Sanity check to prevent infinite loops
                    if counter > 20:
                        # Final fallback with guaranteed uniqueness
                        candidate_slug = f"{base_slug}-{generate(size=10)}"
                        break
                
                return candidate_slug
                
            finally:
                await session.close()
    
    @classmethod
    async def _slug_exists(
        cls, 
        session: AsyncSession, 
        slug: str, 
        category: str, 
        exclude_content_id: Optional[str] = None
    ) -> bool:
        """Check if slug already exists in the given category."""
        query = select(ContentUrl).where(
            and_(
                ContentUrl.slug == slug,
                ContentUrl.category == category
            )
        )
        
        # Exclude current content if updating
        if exclude_content_id:
            query = query.where(ContentUrl.content_id != exclude_content_id)
        
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    
    @classmethod
    async def generate_slug_for_item(cls, item: Item) -> Dict[str, str]:
        """
        Generate category and slug for an existing Item.
        
        Args:
            item: The Item object to generate URL for
            
        Returns:
            Dictionary with 'category' and 'slug' keys
        """
        # Determine category based on content
        category = cls._classify_content_category(item)
        
        # Generate unique slug
        slug = await cls.generate_unique_slug(item.title, category, str(item.id))
        
        return {
            'category': category,
            'slug': slug
        }
    
    @classmethod
    def _classify_content_category(cls, item: Item) -> str:
        """Classify content into one of the four categories."""
        
        # PRIORITIZE ITEM TYPE (reflects user choice or final determination)
        if item.type in ['video', 'image', 'audio']:
            return 'media'
        
        if item.type in ['development', 'github_repo', 'github_document']:
            return 'dev'
        
        # Handle other specific types
        if item.type in ['article', 'text', 'note']:
            # These could be learning content, check for educational keywords
            text_to_check = f"{item.title} {item.summary or ''} {item.raw_content or ''}".lower()
            if any(keyword in text_to_check for keyword in [
                'tutorial', 'course', 'learn', 'guide', 'how to', 'documentation', 'education'
            ]):
                return 'learn'
            # Otherwise default to ideas for articles/text/notes
            return 'ideas'
        
        if item.type in ['bookmark', 'link']:
            # Links could be anything, use URL-based detection
            pass  # Continue to URL-based detection below
        
        if item.platform in ['youtube', 'vimeo', 'video']:
            return 'media'
        
        # Fallback: Check URL patterns for ambiguous types like 'article', 'bookmark', 'link'
        if item.url and item.type in ['article', 'bookmark', 'link']:
            url_lower = item.url.lower()
            
            # Development content URLs (only for non-development types)
            if any(pattern in url_lower for pattern in [
                'github.com', 'stackoverflow.com', 'docs.', 'api.', 
                'developer.', 'programming', 'coding', 'software'
            ]):
                return 'dev'
            
            # Learning content URLs
            if any(pattern in url_lower for pattern in [
                'tutorial', 'course', 'learn', 'guide', 'education',
                'academy', 'training', 'workshop'
            ]):
                return 'learn'
            
            # Media content URLs
            if any(pattern in url_lower for pattern in [
                'youtube.com', 'video', 'audio', 'podcast', 'media',
                'image', 'photo', 'presentation'
            ]):
                return 'media'
        
        # Check title and content for keywords
        text_to_check = f"{item.title} {item.summary or ''} {item.raw_content or ''}".lower()
        
        if any(keyword in text_to_check for keyword in [
            'programming', 'code', 'development', 'software', 'api', 'framework'
        ]):
            return 'dev'
        
        if any(keyword in text_to_check for keyword in [
            'tutorial', 'course', 'learn', 'guide', 'how to', 'documentation'
        ]):
            return 'learn'
        
        if any(keyword in text_to_check for keyword in [
            'video', 'audio', 'image', 'media', 'presentation', 'demo'
        ]):
            return 'media'
        
        # Default to ideas for personal notes, thoughts, etc.
        return 'ideas'
    
    @classmethod
    async def bulk_generate_slugs(cls, items: List[Item]) -> Dict[str, Dict[str, str]]:
        """
        Generate slugs for multiple items in batch.
        
        Args:
            items: List of Item objects
            
        Returns:
            Dictionary mapping item IDs to {'category': str, 'slug': str}
        """
        results = {}
        
        for item in items:
            try:
                url_data = await cls.generate_slug_for_item(item)
                results[str(item.id)] = url_data
            except Exception as e:
                print(f"Error generating slug for item {item.id}: {e}")
                # Fallback
                results[str(item.id)] = {
                    'category': 'ideas',
                    'slug': cls._generate_base_slug(item.title)
                }
        
        return results
    
    @classmethod
    def validate_slug(cls, slug: str) -> bool:
        """Validate that a slug meets requirements."""
        if not slug or len(slug) > 60:
            return False
        
        # Check format: lowercase letters, numbers, and hyphens only
        # Must not start or end with hyphen
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return bool(re.match(pattern, slug))
    
    @classmethod
    def suggest_slug_improvements(cls, title: str) -> List[str]:
        """Suggest alternative slug variations for a title."""
        base_slug = cls._generate_base_slug(title)
        
        suggestions = [base_slug]
        
        # Add variations
        words = base_slug.split('-')
        if len(words) > 1:
            # Shorter version (first 3 words)
            suggestions.append('-'.join(words[:3]))
            
            # Remove articles and common words
            important_words = [w for w in words if w not in cls.STOP_WORDS and len(w) > 2]
            if len(important_words) > 1:
                suggestions.append('-'.join(important_words[:4]))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen and cls.validate_slug(suggestion):
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Return top 5 suggestions