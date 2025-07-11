"""
Vision AI API endpoints
Handles image and screenshot processing
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import Optional, Dict, Any
import aiofiles
import os
import tempfile
from datetime import datetime
import uuid
import json

from app.services.vision_processor import vision_processor
from app.db.database import get_db_pool
from app.core.exceptions import InvalidInput, InternalServerError

router = APIRouter()

@router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Analyze an image using vision AI
    Extracts text, description, objects, and tags
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise InvalidInput("File must be an image")
            
        # Create secure temporary file
        temp_dir = tempfile.mkdtemp(prefix='prsnl_vision_')
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        
        # Save uploaded file
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            
        try:
            # Process image
            result = await vision_processor.process_image(temp_path)
            
            if save_to_db and result.get("text"):
                # Save to database as a captured item
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    # Create item
                    item_id = await conn.fetchval("""
                        INSERT INTO items (
                            title, 
                            raw_content, 
                            summary,
                            metadata,
                            status,
                            created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """, 
                        f"Image: {file.filename}",
                        result.get("text", ""),
                        result.get("description", ""),
                        json.dumps({"type": "screenshot", "vision_analysis": result}),
                        "completed",
                        datetime.utcnow()
                    )
                    
                    # Add tags
                    if result.get("tags"):
                        for tag_name in result["tags"]:
                            # Insert or get tag
                            tag_id = await conn.fetchval("""
                                INSERT INTO tags (name)
                                VALUES ($1)
                                ON CONFLICT (name) DO UPDATE
                                SET name = EXCLUDED.name
                                RETURNING id
                            """, tag_name.lower())
                            
                            # Link to item
                            await conn.execute("""
                                INSERT INTO item_tags (item_id, tag_id)
                                VALUES ($1, $2)
                                ON CONFLICT DO NOTHING
                            """, item_id, tag_id)
                            
                result["item_id"] = str(item_id)
                
            return {
                "success": True,
                "data": result
            }
            
        finally:
            # Clean up temp file and directory
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
    except Exception as e:
        raise InternalServerError(f"Vision analysis failed: {str(e)}")

@router.post("/vision/screenshot")
async def process_screenshot(
    file: UploadFile = File(...),
    url: Optional[str] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a screenshot (from clipboard or drag-drop)
    Automatically extracts and saves content
    """
    try:
        # Read file content
        content = await file.read()
        
        # Process screenshot
        result = await vision_processor.process_screenshot(content)
        
        # Always save screenshots to database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Create item with extracted content
            item_id = await conn.fetchval("""
                INSERT INTO items (
                    title, 
                    url,
                    raw_content, 
                    summary,
                    metadata,
                    status,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                title or f"Screenshot from {url or 'clipboard'}",
                url,
                result.get("text", ""),
                result.get("description", ""),
                json.dumps({"type": "screenshot", "vision_analysis": result}),
                "completed",
                datetime.utcnow()
            )
            
            # Add detected tags and objects as tags
            all_tags = set()
            if result.get("tags"):
                all_tags.update(result["tags"])
            if result.get("objects"):
                all_tags.update(result["objects"][:5])  # Limit object tags
                
            for tag_name in all_tags:
                # Insert or get tag
                tag_id = await conn.fetchval("""
                    INSERT INTO tags (name)
                    VALUES ($1)
                    ON CONFLICT (name) DO UPDATE
                    SET name = EXCLUDED.name
                    RETURNING id
                """, tag_name.lower())
                
                # Link to item
                await conn.execute("""
                    INSERT INTO item_tags (item_id, tag_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, item_id, tag_id)
        
        return {
            "success": True,
            "item_id": str(item_id),
            "analysis": result
        }
        
    except Exception as e:
        raise InternalServerError(f"Screenshot processing failed: {str(e)}")

@router.get("/vision/status")
async def get_vision_status() -> Dict[str, Any]:
    """Get status of vision AI providers"""
    try:
        # Get usage report from AI router
        usage = vision_processor.ai_router.get_usage_report()
        
        return {
            "providers": {
                "azure_openai": {
                    "available": bool(vision_processor.azure_endpoint),
                    "supports_vision": True
                },
                "tesseract": {
                    "available": True,
                    "supports_vision": False,
                    "ocr_only": True
                }
            },
            "usage": usage
        }
    except Exception as e:
        raise InternalServerError(f"Failed to get vision status: {str(e)}")