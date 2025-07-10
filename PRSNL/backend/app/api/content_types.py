from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.db.database import get_db_pool
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Define content type metadata
CONTENT_TYPE_DEFINITIONS = {
    "article": {
        "name": "article",
        "display_name": "Article",
        "icon": "file-text",
        "description": "Written articles and blog posts",
        "color": "#3B82F6"
    },
    "video": {
        "name": "video",
        "display_name": "Video",
        "icon": "play-circle",
        "description": "Video content from various platforms",
        "color": "#EF4444"
    },
    "document": {
        "name": "document",
        "display_name": "Document",
        "icon": "file",
        "description": "PDF files and other documents",
        "color": "#10B981"
    },
    "image": {
        "name": "image",
        "display_name": "Image",
        "icon": "image",
        "description": "Images and visual content",
        "color": "#8B5CF6"
    },
    "note": {
        "name": "note",
        "display_name": "Note",
        "icon": "edit",
        "description": "Personal notes and highlights",
        "color": "#F59E0B"
    },
    "link": {
        "name": "link",
        "display_name": "Link",
        "icon": "link",
        "description": "Simple bookmarked links",
        "color": "#6B7280"
    },
    "tutorial": {
        "name": "tutorial",
        "display_name": "Tutorial",
        "icon": "book-open",
        "description": "Educational tutorials and guides",
        "color": "#06B6D4"
    },
    "audio": {
        "name": "audio",
        "display_name": "Audio",
        "icon": "headphones",
        "description": "Audio files and podcasts",
        "color": "#EC4899"
    },
    "code": {
        "name": "code",
        "display_name": "Code",
        "icon": "code",
        "description": "Code snippets and repositories",
        "color": "#84CC16"
    },
    "development": {
        "name": "development",
        "display_name": "Development",
        "icon": "terminal",
        "description": "Development documentation, tutorials, and code resources",
        "color": "#10B981"
    },
    "auto": {
        "name": "auto",
        "display_name": "Auto-Detect",
        "icon": "zap",
        "description": "Automatically detect content type",
        "color": "#F59E0B"
    }
}

@router.get("/content-types")
async def get_content_types() -> Dict[str, Any]:
    """Get all available content types with their metadata."""
    try:
        pool = await get_db_pool()
        
        # Get actual types used in the database
        async with pool.acquire() as conn:
            # Get distinct types from items table
            rows = await conn.fetch("""
                SELECT DISTINCT type, COUNT(*) as count
                FROM items
                WHERE type IS NOT NULL
                GROUP BY type
                ORDER BY type
            """)
            
            used_types = {row['type']: row['count'] for row in rows}
            
            # Build response with metadata
            content_types = []
            for type_name, count in used_types.items():
                # Get definition or create default
                definition = CONTENT_TYPE_DEFINITIONS.get(type_name, {
                    "name": type_name,
                    "display_name": type_name.title(),
                    "icon": "file",
                    "description": f"{type_name.title()} content",
                    "color": "#6B7280"
                })
                
                # Add count to definition
                type_info = definition.copy()
                type_info["count"] = count
                content_types.append(type_info)
            
            # Also include types with 0 items if they're defined
            for type_name, definition in CONTENT_TYPE_DEFINITIONS.items():
                if type_name not in used_types:
                    type_info = definition.copy()
                    type_info["count"] = 0
                    content_types.append(type_info)
            
            return {
                "content_types": content_types,
                "total": len(content_types)
            }
            
    except Exception as e:
        logger.error(f"Error fetching content types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-types/{type_name}")
async def get_content_type(type_name: str) -> Dict[str, Any]:
    """Get metadata for a specific content type."""
    definition = CONTENT_TYPE_DEFINITIONS.get(type_name)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Content type '{type_name}' not found")
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get count for this type
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM items WHERE type = $1
            """, type_name)
            
            result = definition.copy()
            result["count"] = count
            return result
            
    except Exception as e:
        logger.error(f"Error fetching content type {type_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))