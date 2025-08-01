"""
Entity Extraction API endpoints
Provides endpoints for knowledge graph entity extraction and management
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user_optional
from app.services.entity_extraction_service import entity_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["entity-extraction"])


# Request/Response Models
class EntityExtractionRequest(BaseModel):
    content_id: UUID = Field(..., description="UUID of the content item")
    content_type: Optional[str] = Field(None, description="Type of content (conversation, video, code, etc.)")
    content_text: str = Field(..., description="Text content to analyze")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class EntityExtractionResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None


class EntityStatsResponse(BaseModel):
    entity_statistics: List[dict]
    relationship_statistics: List[dict]
    total_entities: int
    total_relationships: int


@router.post("/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    current_user=Depends(get_current_user_optional)
):
    """
    Extract entities from content and create knowledge graph entries.
    """
    try:
        logger.info(f"Starting entity extraction for content {request.content_id}")
        
        result = await entity_extraction_service.extract_entities_from_content(
            content_id=request.content_id,
            content_type=request.content_type or 'article',
            content_text=request.content_text,
            metadata=request.metadata
        )
        
        if result.get("success"):
            return EntityExtractionResponse(
                success=True,
                data=result,
                message=f"Successfully extracted {len(result['entities_created'])} entities and {len(result['relationships_created'])} relationships"
            )
        else:
            return EntityExtractionResponse(
                success=False,
                data=result,
                message=f"Entity extraction failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error in entity extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.get("/stats", response_model=EntityStatsResponse)
async def get_entity_statistics(
    current_user=Depends(get_current_user_optional)
):
    """
    Get statistics about extracted entities and relationships.
    """
    try:
        stats = await entity_extraction_service.get_entity_statistics()
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {stats['error']}"
            )
        
        return EntityStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity statistics: {str(e)}"
        )


@router.get("/health")
async def entity_extraction_health():
    """
    Health check for entity extraction service.
    """
    try:
        # Test basic functionality
        stats = await entity_extraction_service.get_entity_statistics()
        
        return {
            "status": "healthy",
            "service": "entity_extraction",
            "total_entities": stats.get("total_entities", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "available_content_types": [
                "conversation", "video", "code", "github_repo", 
                "github_document", "article", "note", "timeline"
            ]
        }
        
    except Exception as e:
        logger.error(f"Entity extraction health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "entity_extraction",
            "error": str(e)
        }


@router.get("/content-types")
async def get_supported_content_types():
    """
    Get list of supported content types for entity extraction.
    """
    return {
        "supported_content_types": {
            "conversation": {
                "description": "Chat conversations and dialogue",
                "entity_types": ["conversation_turn", "text_entity", "knowledge_concept"],
                "relationship_types": ["discusses", "explains", "builds_on"]
            },
            "video": {
                "description": "Video content with transcripts",
                "entity_types": ["video_segment", "audio_entity", "knowledge_concept"],
                "relationship_types": ["demonstrates", "explains", "references"]
            },
            "code": {
                "description": "Source code and programming content",
                "entity_types": ["code_function", "code_class", "code_module", "text_entity"],
                "relationship_types": ["implements", "references", "depends_on"]
            },
            "github_repo": {
                "description": "GitHub repository content",
                "entity_types": ["code_function", "code_class", "code_module"],
                "relationship_types": ["implements", "extends", "contains"]
            },
            "article": {
                "description": "Articles and documentation",
                "entity_types": ["text_entity", "knowledge_concept"],
                "relationship_types": ["explains", "references", "related_to"]
            },
            "note": {
                "description": "Personal notes and thoughts",
                "entity_types": ["text_entity", "knowledge_concept"],
                "relationship_types": ["related_to", "builds_on", "references"]
            }
        }
    }


# Test endpoint for development
@router.post("/test")
async def test_entity_extraction():
    """
    Test entity extraction with sample content.
    """
    try:
        from uuid import uuid4
        
        # Sample test content
        test_content = """
        This is a conversation about React 18 features. We discussed concurrent rendering,
        automatic batching, and the new Suspense capabilities. The useTransition hook
        allows for better user experience by marking updates as non-urgent. We also
        talked about how these features improve performance in large applications.
        """
        
        test_id = uuid4()
        
        result = await entity_extraction_service.extract_entities_from_content(
            content_id=test_id,
            content_type="conversation",
            content_text=test_content,
            metadata={"test": True}
        )
        
        return {
            "test_result": result,
            "message": "Entity extraction test completed"
        }
        
    except Exception as e:
        logger.error(f"Error in entity extraction test: {e}")
        return {
            "error": str(e),
            "message": "Entity extraction test failed"
        }