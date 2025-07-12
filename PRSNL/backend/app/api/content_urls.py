"""
API endpoints for the simplified permalink system.
Handles content URLs with /c/category/slug structure.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import ContentUrl, Item, UrlRedirect
from app.services.url_service import URLService
from app.services.slug_generator import SmartSlugGenerator

router = APIRouter(prefix="/api", tags=["content-urls"])


class ContentResponse(BaseModel):
    content: Dict[str, Any]
    contentUrl: Dict[str, Any]
    relatedContent: List[Dict[str, Any]] = []


class CategoryContentResponse(BaseModel):
    content: List[Dict[str, Any]]
    pagination: Dict[str, Any]


class LegacyRedirectResponse(BaseModel):
    newUrl: Optional[str] = None


# Route order is important: more specific routes must come before general ones
@router.get("/content/category/{category}", response_model=CategoryContentResponse)
async def get_category_content(
    category: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", regex="^(recent|popular|title|views)$"),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    """Get content for a specific category with pagination and filtering."""
    # Validate category
    if category not in SmartSlugGenerator.VALID_CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Build base query
    query = select(ContentUrl, Item).join(
        Item, ContentUrl.content_id == Item.id
    ).where(ContentUrl.category == category)
    
    # Add search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Item.title.ilike(search_term),
                Item.summary.ilike(search_term),
                ContentUrl.slug.ilike(search_term)
            )
        )
    
    # Add sorting
    if sort == "recent":
        query = query.order_by(desc(Item.created_at))
    elif sort == "popular":
        query = query.order_by(desc(ContentUrl.views), desc(Item.created_at))
    elif sort == "title":
        query = query.order_by(Item.title)
    elif sort == "views":
        query = query.order_by(desc(ContentUrl.views))
    
    # Get total count for pagination
    count_query = select(func.count(ContentUrl.id)).join(
        Item, ContentUrl.content_id == Item.id
    ).where(ContentUrl.category == category)
    
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            or_(
                Item.title.ilike(search_term),
                Item.summary.ilike(search_term),
                ContentUrl.slug.ilike(search_term)
            )
        )
    
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    rows = result.all()
    
    # Format content
    content = []
    for content_url, item in rows:
        content.append({
            "id": str(item.id),
            "title": item.title,
            "summary": item.summary,
            "url": f"/c/{content_url.category}/{content_url.slug}",
            "source_url": item.url,
            "platform": item.platform,
            "type": item.type,
            "thumbnail_url": item.thumbnail_url,
            "views": content_url.views,
            "category": content_url.category,
            "slug": content_url.slug,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })
    
    # Calculate pagination info
    total_pages = (total + limit - 1) // limit
    
    return CategoryContentResponse(
        content=content,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1
        }
    )


@router.get("/content/{category}/{slug}", response_model=ContentResponse)
async def get_content_by_url(
    category: str,
    slug: str,
    session: AsyncSession = Depends(get_db)
):
    """Get content by category and slug."""
    # Validate category
    if category not in SmartSlugGenerator.VALID_CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get content
    result = await URLService.get_content_by_url(category, slug, session)
    if not result:
        raise HTTPException(status_code=404, detail="Content not found")
    
    item, content_url = result
    
    # Get related content (same category, excluding current item)
    related_query = select(ContentUrl, Item).join(
        Item, ContentUrl.content_id == Item.id
    ).where(
        and_(
            ContentUrl.category == category,
            ContentUrl.content_id != item.id
        )
    ).order_by(desc(ContentUrl.views)).limit(5)
    
    related_result = await session.execute(related_query)
    related_items = [
        {
            "id": str(related_item.id),
            "title": related_item.title,
            "summary": related_item.summary,
            "url": f"/c/{related_content_url.category}/{related_content_url.slug}",
            "thumbnail_url": related_item.thumbnail_url,
            "views": related_content_url.views
        }
        for related_content_url, related_item in related_result.all()
    ]
    
    # Format response
    return ContentResponse(
        content={
            "id": str(item.id),
            "title": item.title,
            "summary": item.summary,
            "raw_content": item.raw_content,
            "processed_content": item.processed_content,
            "url": item.url,
            "platform": item.platform,
            "type": item.type,
            "video_url": item.video_url,
            "thumbnail_url": item.thumbnail_url,
            "transcription": item.transcription,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        },
        contentUrl={
            "id": str(content_url.id),
            "category": content_url.category,
            "slug": content_url.slug,
            "views": content_url.views,
            "meta_title": content_url.meta_title,
            "meta_description": content_url.meta_description,
            "canonical_url": content_url.canonical_url,
            "last_accessed": content_url.last_accessed.isoformat() if content_url.last_accessed else None
        },
        relatedContent=related_items
    )


@router.get("/legacy-redirect/items/{item_id}", response_model=LegacyRedirectResponse)
async def get_item_redirect(
    item_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get redirect URL for legacy item ID."""
    try:
        # Find the content URL for this item
        query = select(ContentUrl).where(ContentUrl.content_id == item_id)
        result = await session.execute(query)
        content_url = result.scalar_one_or_none()
        
        if content_url:
            new_url = f"/c/{content_url.category}/{content_url.slug}"
            return LegacyRedirectResponse(newUrl=new_url)
        
        return LegacyRedirectResponse(newUrl=None)
        
    except Exception:
        return LegacyRedirectResponse(newUrl=None)


@router.get("/legacy-redirect/videos/{video_id}", response_model=LegacyRedirectResponse)
async def get_video_redirect(
    video_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get redirect URL for legacy video ID."""
    try:
        # Find the content URL for this video
        query = select(ContentUrl).where(ContentUrl.content_id == video_id)
        result = await session.execute(query)
        content_url = result.scalar_one_or_none()
        
        if content_url:
            new_url = f"/c/{content_url.category}/{content_url.slug}"
            return LegacyRedirectResponse(newUrl=new_url)
        
        return LegacyRedirectResponse(newUrl=None)
        
    except Exception:
        return LegacyRedirectResponse(newUrl=None)


@router.post("/content/{category}/{slug}/migrate")
async def migrate_item_to_new_url(
    category: str,
    slug: str,
    session: AsyncSession = Depends(get_db)
):
    """Migrate an existing item to new URL structure (admin endpoint)."""
    # This would be used for batch migration scripts
    # Implementation depends on specific migration needs
    pass


@router.get("/admin/content-urls/stats")
async def get_content_url_stats(
    session: AsyncSession = Depends(get_db)
):
    """Get statistics about content URLs (admin endpoint)."""
    # Count by category
    category_stats = {}
    for category in SmartSlugGenerator.VALID_CATEGORIES:
        count_query = select(func.count()).select_from(ContentUrl).where(
            ContentUrl.category == category
        )
        result = await session.execute(count_query)
        category_stats[category] = result.scalar()
    
    # Total URLs
    total_query = select(func.count()).select_from(ContentUrl)
    total_result = await session.execute(total_query)
    total_urls = total_result.scalar()
    
    # Redirect stats
    redirect_query = select(func.count()).select_from(UrlRedirect).where(
        UrlRedirect.active == True
    )
    redirect_result = await session.execute(redirect_query)
    total_redirects = redirect_result.scalar()
    
    return {
        "totalUrls": total_urls,
        "categoryStats": category_stats,
        "totalRedirects": total_redirects
    }


@router.get("/content/popular")
async def get_popular_content(
    category: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db)
):
    """Get popular content across categories or within a specific category."""
    popular_items = await URLService.get_popular_content(session, category, limit)
    
    content = []
    for item, content_url in popular_items:
        content.append({
            "id": str(item.id),
            "title": item.title,
            "summary": item.summary,
            "url": f"/c/{content_url.category}/{content_url.slug}",
            "thumbnail_url": item.thumbnail_url,
            "views": content_url.views,
            "category": content_url.category,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })
    
    return {"content": content}


@router.get("/content/search")
async def search_content(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    """Search content across all categories."""
    results = await URLService.search_content_urls(session, q, limit)
    
    content = []
    for item, content_url in results:
        content.append({
            "id": str(item.id),
            "title": item.title,
            "summary": item.summary,
            "url": f"/c/{content_url.category}/{content_url.slug}",
            "thumbnail_url": item.thumbnail_url,
            "views": content_url.views,
            "category": content_url.category,
            "slug": content_url.slug,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })
    
    return {"content": content, "query": q, "total": len(content)}