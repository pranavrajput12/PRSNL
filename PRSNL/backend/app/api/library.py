"""
Library API endpoints for three-tier categorization system.

Provides statistics, filtering, and content browsing capabilities
organized by Content Types → Categories → Tags.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query, Depends, HTTPException
import asyncpg
from pydantic import BaseModel

from app.db.database import get_db_connection


router = APIRouter(prefix="/library", tags=["library"])


# ===========================
# RESPONSE MODELS
# ===========================

class ContentTypeStats(BaseModel):
    type: str
    count: int
    categories: List[Dict[str, Any]] = []
    recentTags: List[str] = []


class CategoryStats(BaseModel):
    id: str
    count: int
    contentTypes: List[str] = []


class TagStats(BaseModel):
    tag: str
    count: int
    contentTypes: List[str] = []
    categories: List[str] = []


class ContentItem(BaseModel):
    id: str
    title: str
    type: str
    category: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    author: Optional[str] = None
    status: str = "active"


class ContentResponse(BaseModel):
    items: List[ContentItem]
    total: int
    has_more: bool


class SearchResponse(ContentResponse):
    facets: Optional[Dict[str, Dict[str, int]]] = None


# ===========================
# STATISTICS ENDPOINTS
# ===========================

@router.get("/stats/content-types", response_model=List[ContentTypeStats])
async def get_content_type_stats(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get content type statistics with counts and category distribution."""
    try:
        # Base query for content type stats
        query = """
            WITH type_counts AS (
                SELECT 
                    i.type,
                    COUNT(DISTINCT i.id) as count
                FROM items i
                WHERE i.status IN ('completed', 'bookmark', 'pending')
        """
        
        params = []
        param_count = 0
        
        # Add category filter
        if category:
            param_count += 1
            query += f" AND i.category = ${param_count}"
            params.append(category)
        
        # Add tags filter
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            param_count += 1
            query += f"""
                AND EXISTS (
                    SELECT 1 FROM item_tags it
                    JOIN tags t ON it.tag_id = t.id
                    WHERE it.item_id = i.id AND t.name = ANY(${param_count})
                )
            """
            params.append(tag_list)
        
        query += """
                GROUP BY i.type
            )
            SELECT 
                tc.type,
                tc.count,
                COALESCE(
                    (SELECT json_agg(cat_obj) FROM (
                        SELECT DISTINCT ON (category) json_build_object(
                            'id', category,
                            'count', COUNT(*)
                        ) as cat_obj
                        FROM items
                        WHERE type = tc.type 
                            AND status IN ('completed', 'bookmark', 'pending')
                            AND category IS NOT NULL
                        GROUP BY category
                    ) cats),
                    '[]'::json
                ) as categories,
                COALESCE(
                    (SELECT ARRAY_AGG(DISTINCT t.name) 
                     FROM items i
                     JOIN item_tags it ON i.id = it.item_id
                     JOIN tags t ON it.tag_id = t.id
                     WHERE i.type = tc.type 
                        AND i.status IN ('completed', 'bookmark', 'pending')
                        AND i.created_at > NOW() - INTERVAL '30 days'
                     LIMIT 10),
                    '{}'::text[]
                ) as recent_tags
            FROM type_counts tc
            ORDER BY tc.count DESC
        """
        
        rows = await db_connection.fetch(query, *params)
        
        result = []
        for row in rows:
            # Parse categories JSON if it's a string
            categories = row['categories']
            if isinstance(categories, str):
                import json
                categories = json.loads(categories)
            
            result.append(ContentTypeStats(
                type=row['type'],
                count=row['count'],
                categories=categories if isinstance(categories, list) else [],
                recentTags=row['recent_tags'][:10] if row['recent_tags'] else []
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch content type stats: {str(e)}")


@router.get("/stats/categories", response_model=List[CategoryStats])
async def get_category_stats(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get category statistics with counts and content type distribution."""
    try:
        query = """
            WITH category_counts AS (
                SELECT 
                    i.category,
                    COUNT(DISTINCT i.id) as count,
                    ARRAY_AGG(DISTINCT i.type) as content_types
                FROM items i
                WHERE i.status IN ('completed', 'bookmark', 'pending')
                    AND i.category IS NOT NULL
        """
        
        params = []
        param_count = 0
        
        # Add content type filter
        if content_type:
            param_count += 1
            query += f" AND i.type = ${param_count}"
            params.append(content_type)
        
        # Add tags filter
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            param_count += 1
            query += f"""
                AND EXISTS (
                    SELECT 1 FROM item_tags it
                    JOIN tags t ON it.tag_id = t.id
                    WHERE it.item_id = i.id AND t.name = ANY(${param_count})
                )
            """
            params.append(tag_list)
        
        query += """
                GROUP BY i.category
            )
            SELECT 
                category as id,
                count,
                content_types
            FROM category_counts
            ORDER BY count DESC
        """
        
        rows = await db_connection.fetch(query, *params)
        
        return [
            CategoryStats(
                id=row['id'],
                count=row['count'],
                contentTypes=row['content_types']
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category stats: {str(e)}")


@router.get("/stats/tags", response_model=List[TagStats])
async def get_tag_stats(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Get stats for specific tag"),
    related_to: Optional[str] = Query(None, description="Get tags related to this tag"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tags to return"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get tag statistics with usage counts and distributions."""
    try:
        if tag:
            # Get stats for a specific tag
            query = """
                SELECT 
                    t.name as tag,
                    COUNT(DISTINCT i.id) as count,
                    ARRAY_AGG(DISTINCT i.type) as content_types,
                    ARRAY_AGG(DISTINCT i.category) FILTER (WHERE i.category IS NOT NULL) as categories
                FROM tags t
                JOIN item_tags it ON t.id = it.tag_id
                JOIN items i ON it.item_id = i.id
                WHERE t.name = $1
                    AND i.status IN ('completed', 'bookmark', 'pending')
                GROUP BY t.name
            """
            rows = await db_connection.fetch(query, tag)
        
        elif related_to:
            # Get tags that co-occur with the specified tag
            query = """
                WITH target_items AS (
                    SELECT DISTINCT it.item_id
                    FROM tags t
                    JOIN item_tags it ON t.id = it.tag_id
                    WHERE t.name = $1
                )
                SELECT 
                    t.name as tag,
                    COUNT(DISTINCT i.id) as count,
                    ARRAY_AGG(DISTINCT i.type) as content_types,
                    ARRAY_AGG(DISTINCT i.category) FILTER (WHERE i.category IS NOT NULL) as categories
                FROM tags t
                JOIN item_tags it ON t.id = it.tag_id
                JOIN items i ON it.item_id = i.id
                JOIN target_items ti ON i.id = ti.item_id
                WHERE t.name != $1
                    AND i.status IN ('completed', 'bookmark', 'pending')
                GROUP BY t.name
                ORDER BY count DESC
                LIMIT $2
            """
            rows = await db_connection.fetch(query, related_to, limit)
        
        else:
            # Get general tag stats with optional filters
            query = """
                SELECT 
                    t.name as tag,
                    COUNT(DISTINCT i.id) as count,
                    ARRAY_AGG(DISTINCT i.type) as content_types,
                    ARRAY_AGG(DISTINCT i.category) FILTER (WHERE i.category IS NOT NULL) as categories
                FROM tags t
                JOIN item_tags it ON t.id = it.tag_id
                JOIN items i ON it.item_id = i.id
                WHERE i.status IN ('completed', 'bookmark', 'pending')
            """
            
            params = []
            param_count = 0
            
            if content_type:
                param_count += 1
                query += f" AND i.type = ${param_count}"
                params.append(content_type)
            
            if category:
                param_count += 1
                query += f" AND i.category = ${param_count}"
                params.append(category)
            
            query += f"""
                GROUP BY t.name
                ORDER BY count DESC
                LIMIT ${param_count + 1}
            """
            params.append(limit)
            
            rows = await db_connection.fetch(query, *params)
        
        return [
            TagStats(
                tag=row['tag'],
                count=row['count'],
                contentTypes=row['content_types'],
                categories=row['categories'] or []
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tag stats: {str(e)}")


# ===========================
# CONTENT FILTERING ENDPOINTS
# ===========================

@router.get("/content", response_model=ContentResponse)
async def get_filtered_content(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    status: Optional[str] = Query("active", description="Filter by status"),
    date_start: Optional[datetime] = Query(None, description="Start date filter"),
    date_end: Optional[datetime] = Query(None, description="End date filter"),
    sort_by: str = Query("updated_date", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(24, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get filtered content items with pagination."""
    try:
        # Map sort fields to database columns
        sort_mapping = {
            "updated_date": "bi.updated_at",
            "created_date": "bi.created_at",
            "title": "bi.title",
            "type": "bi.type"
        }
        sort_column = sort_mapping.get(sort_by, "bi.updated_at")
        sort_direction = "DESC" if sort_order == "desc" else "ASC"
        
        # Build the base query first
        base_query = """
            SELECT DISTINCT
                i.id,
                i.title,
                i.type,
                i.category,
                i.created_at,
                i.updated_at,
                i.url,
                i.summary as description,
                i.thumbnail_url as thumbnail,
                i.metadata->>'author' as author,
                CASE 
                    WHEN i.status = 'archived' THEN 'archived'
                    WHEN i.status = 'draft' THEN 'draft'
                    ELSE 'active'
                END as status
            FROM items i
            WHERE i.status IN ('completed', 'bookmark', 'pending')
        """
        
        params = []
        param_count = 0
        
        # Apply filters
        if content_type:
            param_count += 1
            base_query += f" AND i.type = ${param_count}"
            params.append(content_type)
        
        if category:
            param_count += 1
            base_query += f" AND i.category = ${param_count}"
            params.append(category)
        
        if status and status != "all":
            if status == "archived":
                base_query += " AND i.status = 'archived'"
            elif status == "draft":
                base_query += " AND i.status = 'draft'"
        
        if date_start:
            param_count += 1
            base_query += f" AND i.created_at >= ${param_count}"
            params.append(date_start)
        
        if date_end:
            param_count += 1
            base_query += f" AND i.created_at <= ${param_count}"
            params.append(date_end)
        
        # Apply tag filter
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            param_count += 1
            base_query += f"""
                AND EXISTS (
                    SELECT 1 FROM item_tags it
                    JOIN tags t ON it.tag_id = t.id
                    WHERE it.item_id = i.id AND t.name = ANY(${param_count})
                )
            """
            params.append(tag_list)
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as counted"
        total_count = await db_connection.fetchval(count_query, *params)
        
        # Now build the full query with tags
        query = f"""
            WITH base_items AS ({base_query})
            SELECT 
                bi.*,
                ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM base_items bi
            LEFT JOIN item_tags it ON bi.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            GROUP BY bi.id, bi.title, bi.type, bi.category, bi.created_at, 
                     bi.updated_at, bi.url, bi.description, bi.thumbnail, 
                     bi.author, bi.status
            ORDER BY {sort_column} {sort_direction}
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])
        
        # Fetch items
        rows = await db_connection.fetch(query, *params)
        
        items = [
            ContentItem(
                id=str(row['id']),
                title=row['title'],
                type=row['type'],
                category=row['category'],
                tags=row['tags'] or [],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                url=row['url'],
                description=row['description'],
                thumbnail=row['thumbnail'],
                author=row['author'],
                status=row['status']
            )
            for row in rows
        ]
        
        return ContentResponse(
            items=items,
            total=total_count,
            has_more=(offset + limit) < total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")


@router.get("/content/{item_id}/related", response_model=List[ContentItem])
async def get_related_content(
    item_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Maximum related items"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get related content based on categories and tags."""
    try:
        # First get the item's category and tags
        item_query = """
            SELECT 
                i.category,
                i.type,
                ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM items i
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE i.id = $1
            GROUP BY i.id, i.category, i.type
        """
        
        item_data = await db_connection.fetchrow(item_query, item_id)
        if not item_data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Find related items by shared tags and category
        query = """
            WITH item_tags AS (
                SELECT tag_id FROM item_tags WHERE item_id = $1
            ),
            scored_items AS (
                SELECT 
                    i.id,
                    i.title,
                    i.type,
                    i.category,
                    i.created_at,
                    i.updated_at,
                    i.url,
                    i.summary as description,
                    i.thumbnail_url as thumbnail,
                    i.metadata->>'author' as author,
                    'active' as status,
                    ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL) as tags,
                    -- Scoring: same category = 2 points, each shared tag = 1 point
                    CASE WHEN i.category = $2 THEN 2 ELSE 0 END +
                    COUNT(it.tag_id) FILTER (WHERE it.tag_id IN (SELECT tag_id FROM item_tags)) as score
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.id != $1
                    AND i.status IN ('completed', 'bookmark', 'pending')
                    AND (
                        i.category = $2 OR
                        EXISTS (
                            SELECT 1 FROM item_tags it2
                            WHERE it2.item_id = i.id 
                            AND it2.tag_id IN (SELECT tag_id FROM item_tags)
                        )
                    )
                GROUP BY i.id, i.title, i.type, i.category, i.created_at, 
                         i.updated_at, i.url, i.summary, i.thumbnail_url, 
                         i.metadata
            )
            SELECT * FROM scored_items
            WHERE score > 0
            ORDER BY score DESC, updated_at DESC
            LIMIT $3
        """
        
        rows = await db_connection.fetch(
            query,
            item_id,
            item_data['category'],
            limit
        )
        
        return [
            ContentItem(
                id=str(row['id']),
                title=row['title'],
                type=row['type'],
                category=row['category'],
                tags=row['tags'] or [],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                url=row['url'],
                description=row['description'],
                thumbnail=row['thumbnail'],
                author=row['author'],
                status=row['status']
            )
            for row in rows
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch related content: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_content(
    q: str = Query(..., min_length=2, description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(24, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Search content with faceted results."""
    try:
        # Build search query with facets
        search_pattern = f"%{q}%"
        
        query = """
            WITH search_results AS (
                SELECT DISTINCT
                    i.id,
                    i.title,
                    i.type,
                    i.category,
                    i.created_at,
                    i.updated_at,
                    i.url,
                    i.summary as description,
                    i.thumbnail_url as thumbnail,
                    i.metadata->>'author' as author,
                    'active' as status,
                    ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL) as tags,
                    -- Relevance scoring
                    CASE 
                        WHEN i.title ILIKE $1 THEN 3
                        WHEN i.summary ILIKE $1 THEN 2
                        WHEN i.content ILIKE $1 THEN 1
                        ELSE 0
                    END as relevance
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id
                WHERE i.status IN ('completed', 'bookmark', 'pending')
                    AND (
                        i.title ILIKE $1 OR
                        i.summary ILIKE $1 OR
                        i.content ILIKE $1 OR
                        i.url ILIKE $1
                    )
        """
        
        params = [search_pattern]
        param_count = 1
        
        # Apply filters
        if content_type:
            param_count += 1
            query += f" AND i.type = ${param_count}"
            params.append(content_type)
        
        if category:
            param_count += 1
            query += f" AND i.category = ${param_count}"
            params.append(category)
        
        query += """
                GROUP BY i.id, i.title, i.type, i.category, i.created_at, 
                         i.updated_at, i.url, i.summary, i.thumbnail_url, 
                         i.metadata, i.content
        """
        
        # Apply tag filter after grouping
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            param_count += 1
            query = f"""
                WITH search_results AS ({query})
                SELECT * FROM search_results
                WHERE tags && ${param_count}
            """
            params.append(tag_list)
        else:
            query = f"WITH search_results AS ({query}) SELECT * FROM search_results"
        
        # Get facets
        facet_query = f"""
            WITH results AS ({query})
            SELECT 
                jsonb_build_object(
                    'contentTypes', (
                        SELECT jsonb_object_agg(type, count)
                        FROM (
                            SELECT type, COUNT(*) as count
                            FROM results
                            GROUP BY type
                        ) ct
                    ),
                    'categories', (
                        SELECT jsonb_object_agg(category, count)
                        FROM (
                            SELECT category, COUNT(*) as count
                            FROM results
                            WHERE category IS NOT NULL
                            GROUP BY category
                        ) cat
                    ),
                    'tags', (
                        SELECT jsonb_object_agg(tag, count)
                        FROM (
                            SELECT unnest(tags) as tag, COUNT(*) as count
                            FROM results
                            WHERE tags IS NOT NULL
                            GROUP BY tag
                            ORDER BY count DESC
                            LIMIT 20
                        ) t
                    )
                ) as facets
        """
        
        facets_row = await db_connection.fetchrow(facet_query, *params)
        facets = facets_row['facets'] if facets_row else {}
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as counted"
        total_count = await db_connection.fetchval(count_query, *params)
        
        # Get items with pagination
        param_count += 1
        query += f" ORDER BY relevance DESC, updated_at DESC LIMIT ${param_count}"
        params.append(limit)
        
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        rows = await db_connection.fetch(query, *params)
        
        items = [
            ContentItem(
                id=str(row['id']),
                title=row['title'],
                type=row['type'],
                category=row['category'],
                tags=row['tags'] or [],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                url=row['url'],
                description=row['description'],
                thumbnail=row['thumbnail'],
                author=row['author'],
                status=row['status']
            )
            for row in rows
        ]
        
        return SearchResponse(
            items=items,
            total=total_count,
            has_more=(offset + limit) < total_count,
            facets={
                'contentTypes': facets.get('contentTypes', {}),
                'categories': facets.get('categories', {}),
                'tags': facets.get('tags', {})
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")