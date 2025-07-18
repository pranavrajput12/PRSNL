"""
Development Content API endpoints
Handles development-specific content operations
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.exceptions import InternalServerError, InvalidInput
from app.db.database import get_db_pool

router = APIRouter()

# Pydantic Models
class DevelopmentCategory(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    icon: str = "📁"
    color: str = "#10b981"
    created_at: datetime
    item_count: Optional[int] = 0

class DevelopmentItem(BaseModel):
    id: UUID
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None
    type: str
    programming_language: Optional[str] = None
    project_category: Optional[str] = None
    difficulty_level: Optional[int] = None
    is_career_related: bool = False
    learning_path: Optional[str] = None
    code_snippets: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = []

class DevelopmentStats(BaseModel):
    total_items: int
    by_language: Dict[str, int]
    by_category: Dict[str, int]
    by_difficulty: Dict[str, int]
    career_related_count: int
    repository_count: int
    recent_activity: List[Dict[str, Any]]

class CodeSnippet(BaseModel):
    title: str
    language: str
    code: str
    description: Optional[str] = None
    tags: List[str] = []

class CreateDevelopmentItem(BaseModel):
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    programming_language: Optional[str] = None
    project_category: Optional[str] = None
    difficulty_level: Optional[int] = None
    is_career_related: bool = False
    learning_path: Optional[str] = None
    tags: List[str] = []

# API Endpoints

@router.get("/development/categories", response_model=List[DevelopmentCategory])
async def get_development_categories():
    """Get all development categories with item counts"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    dc.*,
                    COALESCE(item_counts.count, 0) as item_count
                FROM development_categories dc
                LEFT JOIN (
                    SELECT project_category, COUNT(*) as count
                    FROM items 
                    WHERE type = 'development' AND project_category IS NOT NULL
                    GROUP BY project_category
                ) item_counts ON dc.name = item_counts.project_category
                ORDER BY dc.name
            """
            
            rows = await conn.fetch(query)
            return [
                DevelopmentCategory(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    icon=row["icon"],
                    color=row["color"],
                    created_at=row["created_at"],
                    item_count=row["item_count"]
                )
                for row in rows
            ]
    except Exception as e:
        raise InternalServerError(f"Failed to fetch development categories: {str(e)}")

@router.get("/development/languages")
async def get_programming_languages():
    """Get all programming languages found in development content"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    programming_language,
                    COUNT(*) as count
                FROM items 
                WHERE type = 'development' 
                AND programming_language IS NOT NULL
                GROUP BY programming_language
                ORDER BY count DESC, programming_language
            """
            
            rows = await conn.fetch(query)
            return {
                "languages": [
                    {
                        "name": row["programming_language"],
                        "count": row["count"]
                    }
                    for row in rows
                ]
            }
    except Exception as e:
        raise InternalServerError(f"Failed to fetch programming languages: {str(e)}")

@router.get("/development/docs", response_model=List[DevelopmentItem])
async def get_development_docs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None, ge=1, le=5),
    career_related: Optional[bool] = Query(None),
    learning_path: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),  # 'knowledge', 'tools', 'repositories', 'progress'
):
    """Get development documents with advanced filtering"""
    try:
        # Build dynamic query with filters
        conditions = ["i.type = 'development'"]
        params = []
        param_count = 1
        
        if category:
            conditions.append(f"i.project_category = ${param_count}")
            params.append(category)
            param_count += 1
            
        if language:
            conditions.append(f"i.programming_language = ${param_count}")
            params.append(language)
            param_count += 1
            
        if difficulty:
            conditions.append(f"i.difficulty_level = ${param_count}")
            params.append(difficulty)
            param_count += 1
            
        if career_related is not None:
            conditions.append(f"i.is_career_related = ${param_count}")
            params.append(career_related)
            param_count += 1
            
        if learning_path:
            conditions.append(f"i.learning_path = ${param_count}")
            params.append(learning_path)
            param_count += 1
            
        if search:
            conditions.append(f"to_tsvector('english', i.title || ' ' || COALESCE(i.summary, '')) @@ plainto_tsquery('english', ${param_count})")
            params.append(search)
            param_count += 1
            
        # Enhanced content type filtering for refined page organization
        if content_type:
            if content_type == 'knowledge':
                # Knowledge Base: Internal docs, guides, tutorials, learning materials
                # Excludes external URLs and repositories, focuses on documentation with content
                conditions.append("""(
                    (i.url IS NULL OR NOT i.url LIKE 'http%' OR 
                     (i.summary IS NOT NULL AND LENGTH(i.summary) > 50)) AND
                    (i.url IS NULL OR 
                     (i.url NOT LIKE '%github.com%' AND 
                      i.url NOT LIKE '%gitlab.com%' AND 
                      i.url NOT LIKE '%bitbucket.%'))
                )""")
            elif content_type == 'tools':
                # Tools & Links: External tools, utilities, services (not repositories)
                # Focuses on external URLs that are not code repositories
                conditions.append("""(
                    i.url IS NOT NULL AND 
                    i.url LIKE 'http%' AND
                    i.url NOT LIKE '%github.com%' AND 
                    i.url NOT LIKE '%gitlab.com%' AND 
                    i.url NOT LIKE '%bitbucket.%'
                )""")
            elif content_type == 'repositories':
                # Open Source Integrations: GitHub/GitLab repositories that are libraries/frameworks
                # Only integration repositories, not general documentation or tools
                conditions.append("""(
                    i.url IS NOT NULL AND 
                    (i.url LIKE '%github.com%' OR i.url LIKE '%gitlab.com%' OR i.url LIKE '%bitbucket.%') AND
                    (i.project_category IS NOT NULL OR
                     EXISTS (
                         SELECT 1 FROM item_tags it2 
                         JOIN tags t2 ON it2.tag_id = t2.id 
                         WHERE it2.item_id = i.id AND 
                         t2.name ILIKE ANY(ARRAY['%library%', '%framework%', '%integration%', '%tool%', '%sdk%', '%api%'])
                     ))
                )""")
            elif content_type == 'progress':
                # Learning Progress: Items with learning paths, difficulty levels, or progress indicators
                # Focuses on personal learning journey and skill development tracking
                conditions.append("""(
                    i.learning_path IS NOT NULL OR 
                    i.difficulty_level IS NOT NULL OR
                    i.is_career_related = TRUE OR
                    EXISTS (
                        SELECT 1 FROM item_tags it2 
                        JOIN tags t2 ON it2.tag_id = t2.id 
                        WHERE it2.item_id = i.id AND 
                        t2.name ILIKE ANY(ARRAY['%progress%', '%learning%', '%skill%', '%course%', '%certification%', '%goal%'])
                    ) OR
                    i.title ILIKE ANY(ARRAY['%learn%', '%skill%', '%course%'])
                )""")
        
        # Add limit and offset
        params.extend([limit, offset])
        
        query = f"""
            SELECT 
                i.*,
                ARRAY_REMOVE(ARRAY_AGG(t.name), NULL) as tags
            FROM items i
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE {' AND '.join(conditions)}
            GROUP BY i.id
            ORDER BY i.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [
            DevelopmentItem(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                summary=row["summary"],
                type=row["type"],
                programming_language=row["programming_language"],
                project_category=row["project_category"],
                difficulty_level=row["difficulty_level"],
                is_career_related=row["is_career_related"],
                learning_path=row["learning_path"],
                code_snippets=row["code_snippets"] if isinstance(row["code_snippets"], list) else [],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                tags=row["tags"] or []
            )
            for row in rows
        ]
    except Exception as e:
        raise InternalServerError(f"Failed to fetch development docs: {str(e)}")

@router.get("/development/stats", response_model=DevelopmentStats)
async def get_development_stats():
    """Get development content statistics"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Total items
            total_query = "SELECT COUNT(*) as count FROM items WHERE type = 'development'"
            total_result = await conn.fetchrow(total_query)
            total_items = total_result["count"]
            
            # By language
            lang_query = """
                SELECT programming_language, COUNT(*) as count
                FROM items 
                WHERE type = 'development' AND programming_language IS NOT NULL
                GROUP BY programming_language
                ORDER BY count DESC
            """
            lang_rows = await conn.fetch(lang_query)
            by_language = {row["programming_language"]: row["count"] for row in lang_rows}
            
            # By category
            cat_query = """
                SELECT project_category, COUNT(*) as count
                FROM items 
                WHERE type = 'development' AND project_category IS NOT NULL
                GROUP BY project_category
                ORDER BY count DESC
            """
            cat_rows = await conn.fetch(cat_query)
            by_category = {row["project_category"]: row["count"] for row in cat_rows}
            
            # By difficulty
            diff_query = """
                SELECT difficulty_level, COUNT(*) as count
                FROM items 
                WHERE type = 'development' AND difficulty_level IS NOT NULL
                GROUP BY difficulty_level
                ORDER BY difficulty_level
            """
            diff_rows = await conn.fetch(diff_query)
            by_difficulty = {str(row["difficulty_level"]): row["count"] for row in diff_rows}
            
            # Career related count
            career_query = "SELECT COUNT(*) as count FROM items WHERE type = 'development' AND is_career_related = TRUE"
            career_result = await conn.fetchrow(career_query)
            career_related_count = career_result["count"]
            
            # Repository count
            repo_query = "SELECT COUNT(*) as count FROM items WHERE repository_metadata IS NOT NULL"
            repo_result = await conn.fetchrow(repo_query)
            repository_count = repo_result["count"]
            
            # Recent activity (last 10 items)
            recent_query = """
                SELECT i.id, i.title, i.programming_language, i.project_category, i.created_at,
                       CASE 
                           WHEN cu.slug IS NOT NULL THEN '/c/' || cu.category || '/' || cu.slug
                           ELSE NULL
                       END as permalink
                FROM items i
                LEFT JOIN content_urls cu ON i.id = cu.item_id
                WHERE i.type = 'development'
                ORDER BY i.created_at DESC
                LIMIT 10
            """
            recent_rows = await conn.fetch(recent_query)
            
            recent_activity = [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "programming_language": row["programming_language"],
                    "project_category": row["project_category"],
                    "created_at": row["created_at"].isoformat(),
                    "permalink": row["permalink"]
                }
                for row in recent_rows
            ]
            
            return DevelopmentStats(
                total_items=total_items,
                by_language=by_language,
                by_category=by_category,
                by_difficulty=by_difficulty,
                career_related_count=career_related_count,
                repository_count=repository_count,
                recent_activity=recent_activity
            )
    except Exception as e:
        raise InternalServerError(f"Failed to fetch development stats: {str(e)}")

@router.get("/development/repositories")
async def get_repositories(limit: int = Query(50, ge=1, le=100)):
    """Get all saved repositories"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT id, title, url, repository_metadata, created_at
                FROM items 
                WHERE repository_metadata IS NOT NULL 
                ORDER BY created_at DESC
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)
            
            items = []
            for row in rows:
                items.append({
                    "id": str(row["id"]),
                    "title": row["title"],
                    "url": row["url"],
                    "repository_metadata": row["repository_metadata"],
                    "created_at": row["created_at"].isoformat()
                })
            
            return {"items": items}
    except Exception as e:
        raise InternalServerError(f"Failed to fetch repositories: {str(e)}")

@router.post("/development/snippet")
async def save_code_snippet(
    snippet: CodeSnippet,
):
    """Save a code snippet as development content"""
    try:
        # Create the item
        query = """
            INSERT INTO items (
                title, processed_content, type, programming_language, 
                project_category, difficulty_level, code_snippets
            ) VALUES ($1, $2, 'development', $3, 'Code Snippets', 2, $4)
            RETURNING id
        """
        
        code_snippet_data = [{
            "title": snippet.title,
            "language": snippet.language,
            "code": snippet.code,
            "description": snippet.description,
            "created_at": datetime.utcnow().isoformat()
        }]
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                query, 
                snippet.title, 
                f"```{snippet.language}\n{snippet.code}\n```\n\n{snippet.description or ''}",
                snippet.language,
                code_snippet_data
            )
            
            # Add tags if provided
            if snippet.tags:
                item_id = result["id"]
                for tag_name in snippet.tags:
                    # Insert or get tag
                    tag_query = """
                        INSERT INTO tags (name) VALUES ($1) 
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """
                    tag_result = await conn.fetchrow(tag_query, tag_name)
                    
                    # Link tag to item
                    link_query = """
                        INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """
                    await conn.execute(link_query, item_id, tag_result["id"])
        
        return {
            "success": True,
            "message": "Code snippet saved successfully",
            "item_id": str(result["id"])
        }
    except Exception as e:
        raise InternalServerError(f"Failed to save code snippet: {str(e)}")

@router.get("/development/learning-paths")
async def get_learning_paths(
):
    """Get all learning paths with progress"""
    try:
        query = """
            SELECT 
                learning_path,
                COUNT(*) as total_items,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_items,
                AVG(difficulty_level) as avg_difficulty
            FROM items 
            WHERE type = 'development' 
            AND learning_path IS NOT NULL
            GROUP BY learning_path
            ORDER BY total_items DESC
        """
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        return {
            "learning_paths": [
                {
                    "name": row["learning_path"],
                    "total_items": row["total_items"],
                    "completed_items": row["completed_items"],
                    "progress_percentage": round((row["completed_items"] / row["total_items"]) * 100, 1) if row["total_items"] > 0 else 0,
                    "avg_difficulty": round(float(row["avg_difficulty"]) if row["avg_difficulty"] else 0, 1)
                }
                for row in rows
            ]
        }
    except Exception as e:
        raise InternalServerError(f"Failed to fetch learning paths: {str(e)}")

@router.post("/development/categorize")
async def auto_categorize_development_content(
    item_id: str,
):
    """Auto-categorize development content using AI analysis"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get the item
            item_query = "SELECT * FROM items WHERE id = $1 AND type = 'development'"
            item = await conn.fetchrow(item_query, item_id)
            
            if not item:
                raise HTTPException(status_code=404, detail="Development item not found")
            
            # Simple categorization logic (can be enhanced with AI)
            content = (item["processed_content"] or "").lower()
            title = item["title"].lower()
            
            # Determine category
            category = None
            if any(word in content + title for word in ['react', 'vue', 'angular', 'frontend', 'ui', 'css', 'html']):
                category = 'Frontend'
            elif any(word in content + title for word in ['api', 'server', 'database', 'backend', 'node', 'python', 'django']):
                category = 'Backend'
            elif any(word in content + title for word in ['docker', 'kubernetes', 'aws', 'deployment', 'ci/cd', 'devops']):
                category = 'DevOps'
            elif any(word in content + title for word in ['mobile', 'android', 'ios', 'react native', 'flutter']):
                category = 'Mobile'
            elif any(word in content + title for word in ['ml', 'ai', 'machine learning', 'neural', 'tensorflow', 'pytorch']):
                category = 'AI/ML'
            elif any(word in content + title for word in ['data', 'analytics', 'pandas', 'numpy', 'visualization']):
                category = 'Data Science'
            else:
                category = 'Documentation'  # Default
            
            # Update the item
            update_query = """
                UPDATE items 
                SET project_category = $1, updated_at = NOW()
                WHERE id = $2
            """
            await conn.execute(update_query, category, item_id)
        
        return {
            "success": True,
            "message": f"Item categorized as {category}",
            "category": category
        }
    except Exception as e:
        raise InternalServerError(f"Failed to categorize development content: {str(e)}")