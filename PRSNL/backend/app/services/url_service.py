"""
URL Service for PRSNL Simplified Permalink System

Manages URL generation, redirects, and SEO optimization for the /c/category/slug structure.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ContentUrl, Item, UrlRedirect
from app.services.slug_generator import SmartSlugGenerator
from app.utils.url_classifier import URLClassifier


class URLService:
    """Service for managing simplified URLs and redirects."""
    
    @classmethod
    async def create_content_url(
        cls,
        item: Item,
        custom_slug: Optional[str] = None,
        custom_category: Optional[str] = None
    ) -> ContentUrl:
        """
        Create a new ContentUrl for an Item.
        
        Args:
            item: The Item to create URL for
            custom_slug: Optional custom slug (will be validated)
            custom_category: Optional custom category
            
        Returns:
            Created ContentUrl object
        """
        async for session in get_db():
            try:
                # Determine category
                if custom_category and custom_category in SmartSlugGenerator.VALID_CATEGORIES:
                    category = custom_category
                else:
                    category = SmartSlugGenerator._classify_content_category(item)
                
                # Generate or validate slug
                if custom_slug and SmartSlugGenerator.validate_slug(custom_slug):
                    # Check if custom slug is unique
                    if not await SmartSlugGenerator._slug_exists(session, custom_slug, category, str(item.id)):
                        slug = custom_slug
                    else:
                        # Make custom slug unique
                        slug = await SmartSlugGenerator._ensure_unique_slug(custom_slug, category, str(item.id))
                else:
                    # Generate slug from title
                    slug = await SmartSlugGenerator.generate_unique_slug(item.title, category, str(item.id))
                
                # Generate SEO metadata
                seo_data = cls._generate_seo_metadata(item, category, slug)
                
                # Create ContentUrl
                content_url = ContentUrl(
                    content_id=item.id,
                    slug=slug,
                    category=category,
                    meta_title=seo_data['title'],
                    meta_description=seo_data['description'],
                    canonical_url=seo_data['canonical_url']
                )
                
                session.add(content_url)
                await session.commit()
                await session.refresh(content_url)
                
                return content_url
                
            finally:
                await session.close()
    
    @classmethod
    async def get_content_by_url(cls, category: str, slug: str, session: AsyncSession) -> Optional[Tuple[Item, ContentUrl]]:
        """
        Get content by category and slug.
        
        Args:
            category: Content category
            slug: Content slug
            session: Database session
            
        Returns:
            Tuple of (Item, ContentUrl) or None if not found
        """
        query = select(ContentUrl, Item).join(
            Item, ContentUrl.content_id == Item.id
        ).where(
            and_(
                ContentUrl.category == category,
                ContentUrl.slug == slug
            )
        )
        
        result = await session.execute(query)
        row = result.first()
        
        if row:
            content_url, item = row
            # Update view count and last accessed
            await cls._update_access_stats(session, content_url.id)
            return item, content_url
        
        return None
    
    @classmethod
    async def _update_access_stats(cls, session: AsyncSession, content_url_id: str):
        """Update view count and last accessed time."""
        await session.execute(
            update(ContentUrl)
            .where(ContentUrl.id == content_url_id)
            .values(
                views=ContentUrl.views + 1,
                last_accessed=datetime.utcnow()
            )
        )
        await session.commit()
    
    @classmethod
    def _generate_seo_metadata(cls, item: Item, category: str, slug: str) -> Dict[str, str]:
        """Generate SEO metadata for content."""
        # Generate title (max 60 chars for SEO)
        title = item.title
        if len(title) > 57:  # Leave room for " | PRSNL"
            title = title[:57].strip()
        title = f"{title} | PRSNL"
        
        # Generate description (max 160 chars)
        description = item.summary or ""
        if not description and item.raw_content:
            # Extract first sentence or paragraph
            content = re.sub(r'<[^>]+>', '', item.raw_content)  # Remove HTML
            sentences = re.split(r'[.!?]+', content)
            description = sentences[0].strip() if sentences else ""
        
        if len(description) > 160:
            description = description[:157] + "..."
        
        # Fallback description
        if not description:
            category_labels = {
                'dev': 'Development content',
                'learn': 'Learning resource',
                'media': 'Media content',
                'ideas': 'Personal note'
            }
            description = f"{category_labels.get(category, 'Content')} from PRSNL knowledge base"
        
        # Canonical URL
        canonical_url = f"/c/{category}/{slug}"
        
        return {
            'title': title,
            'description': description,
            'canonical_url': canonical_url
        }
    
    @classmethod
    async def create_redirect(
        cls,
        old_path: str,
        new_path: str,
        redirect_type: int = 301
    ) -> UrlRedirect:
        """
        Create a URL redirect.
        
        Args:
            old_path: Old URL path
            new_path: New URL path
            redirect_type: 301 (permanent) or 302 (temporary)
            
        Returns:
            Created UrlRedirect object
        """
        async for session in get_db():
            try:
                redirect = UrlRedirect(
                    old_path=old_path,
                    new_path=new_path,
                    redirect_type=redirect_type
                )
                
                session.add(redirect)
                await session.commit()
                await session.refresh(redirect)
                
                return redirect
                
            finally:
                await session.close()
    
    @classmethod
    async def find_redirect(cls, path: str) -> Optional[UrlRedirect]:
        """
        Find a redirect for the given path.
        
        Args:
            path: URL path to check
            
        Returns:
            UrlRedirect object or None
        """
        async for session in get_db():
            try:
                query = select(UrlRedirect).where(
                    and_(
                        UrlRedirect.old_path == path,
                        UrlRedirect.active == True
                    )
                )
                
                result = await session.execute(query)
                redirect = result.scalar_one_or_none()
                
                if redirect:
                    # Update hit count and last used
                    await session.execute(
                        update(UrlRedirect)
                        .where(UrlRedirect.id == redirect.id)
                        .values(
                            hit_count=UrlRedirect.hit_count + 1,
                            last_used=datetime.utcnow()
                        )
                    )
                    await session.commit()
                
                return redirect
                
            finally:
                await session.close()
    
    @classmethod
    async def migrate_item_to_new_url(cls, item: Item) -> Optional[ContentUrl]:
        """
        Migrate an existing item to the new URL structure.
        
        Args:
            item: Item to migrate
            
        Returns:
            Created ContentUrl or None if already exists
        """
        async for session in get_db():
            try:
                # Check if URL already exists
                existing = await session.execute(
                    select(ContentUrl).where(ContentUrl.content_id == item.id)
                )
                if existing.scalar_one_or_none():
                    return None  # Already migrated
                
                # Create new URL
                content_url = await cls.create_content_url(item)
                
                # Create redirect from old URLs if they exist
                old_paths = []
                
                # Add /items/[id] redirect
                old_paths.append(f"/items/{item.id}")
                
                # Add /videos/[id] redirect if it's a video
                if item.platform in ['youtube', 'vimeo'] or item.type == 'video':
                    old_paths.append(f"/videos/{item.id}")
                
                # Create redirects
                new_path = f"/c/{content_url.category}/{content_url.slug}"
                for old_path in old_paths:
                    try:
                        await cls.create_redirect(old_path, new_path, 301)
                    except Exception:
                        # Redirect might already exist, skip
                        pass
                
                return content_url
                
            finally:
                await session.close()
    
    @classmethod
    async def bulk_migrate_items(cls, limit: int = 100) -> Dict[str, int]:
        """
        Migrate multiple items to new URL structure.
        
        Args:
            limit: Maximum number of items to migrate in one batch
            
        Returns:
            Dictionary with migration statistics
        """
        async for session in get_db():
            try:
                # Find items without ContentUrls
                query = select(Item).outerjoin(
                    ContentUrl, Item.id == ContentUrl.content_id
                ).where(
                    ContentUrl.id.is_(None)
                ).limit(limit)
                
                result = await session.execute(query)
                items = result.scalars().all()
                
                stats = {
                    'total_found': len(items),
                    'migrated': 0,
                    'errors': 0
                }
                
                for item in items:
                    try:
                        content_url = await cls.migrate_item_to_new_url(item)
                        if content_url:
                            stats['migrated'] += 1
                    except Exception as e:
                        print(f"Error migrating item {item.id}: {e}")
                        stats['errors'] += 1
                
                return stats
                
            finally:
                await session.close()
    
    @classmethod
    async def update_content_url(
        cls,
        content_url: ContentUrl,
        new_slug: Optional[str] = None,
        new_category: Optional[str] = None
    ) -> ContentUrl:
        """
        Update an existing ContentUrl.
        
        Args:
            content_url: ContentUrl to update
            new_slug: New slug (optional)
            new_category: New category (optional)
            
        Returns:
            Updated ContentUrl
        """
        async for session in get_db():
            try:
                old_path = f"/c/{content_url.category}/{content_url.slug}"
                
                # Update fields
                if new_category and new_category in SmartSlugGenerator.VALID_CATEGORIES:
                    content_url.category = new_category
                
                if new_slug and SmartSlugGenerator.validate_slug(new_slug):
                    # Ensure uniqueness
                    if not await SmartSlugGenerator._slug_exists(
                        session, new_slug, content_url.category, str(content_url.content_id)
                    ):
                        content_url.slug = new_slug
                
                # Update canonical URL
                content_url.canonical_url = f"/c/{content_url.category}/{content_url.slug}"
                
                await session.commit()
                
                # Create redirect from old URL if path changed
                new_path = content_url.canonical_url
                if old_path != new_path:
                    await cls.create_redirect(old_path, new_path, 301)
                
                return content_url
                
            finally:
                await session.close()
    
    @classmethod
    async def get_popular_content(cls, session: AsyncSession, category: Optional[str] = None, limit: int = 10) -> List[Tuple[Item, ContentUrl]]:
        """
        Get popular content based on view counts.
        
        Args:
            session: Database session
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of (Item, ContentUrl) tuples
        """
        query = select(ContentUrl, Item).join(
            Item, ContentUrl.content_id == Item.id
        ).order_by(ContentUrl.views.desc())
        
        if category:
            query = query.where(ContentUrl.category == category)
        
        query = query.limit(limit)
        
        result = await session.execute(query)
        rows = result.all()
        
        return [(item, content_url) for content_url, item in rows]
    
    @classmethod
    async def search_content_urls(cls, session: AsyncSession, query: str, limit: int = 20) -> List[Tuple[Item, ContentUrl]]:
        """
        Search content by URL, title, or slug.
        
        Args:
            session: Database session
            query: Search query
            limit: Maximum results
            
        Returns:
            List of (Item, ContentUrl) tuples
        """
        search_query = select(ContentUrl, Item).join(
            Item, ContentUrl.content_id == Item.id
        ).where(
            or_(
                ContentUrl.slug.ilike(f"%{query}%"),
                ContentUrl.meta_title.ilike(f"%{query}%"),
                Item.title.ilike(f"%{query}%")
            )
        ).order_by(ContentUrl.views.desc()).limit(limit)
        
        result = await session.execute(search_query)
        rows = result.all()
        
        return [(item, content_url) for content_url, item in rows]
    
    @classmethod
    def generate_sitemap_urls(cls, base_url: str = "https://prsnl.app") -> List[Dict[str, str]]:
        """
        Generate sitemap URLs for all content.
        
        Args:
            base_url: Base URL for the site
            
        Returns:
            List of URL dictionaries for sitemap
        """
        # This would be implemented to generate XML sitemap data
        # For now, return the structure
        return [
            {"loc": f"{base_url}/", "priority": "1.0"},
            {"loc": f"{base_url}/c/dev", "priority": "0.8"},
            {"loc": f"{base_url}/c/learn", "priority": "0.8"},
            {"loc": f"{base_url}/c/media", "priority": "0.8"},
            {"loc": f"{base_url}/c/ideas", "priority": "0.8"},
            {"loc": f"{base_url}/p/timeline", "priority": "0.7"},
            {"loc": f"{base_url}/p/insights", "priority": "0.7"},
            {"loc": f"{base_url}/p/chat", "priority": "0.7"},
            {"loc": f"{base_url}/s/settings", "priority": "0.5"},
        ]