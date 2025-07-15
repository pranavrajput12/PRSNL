"""
Embeddings Cleanup API endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.services.embeddings_cleanup_service import embeddings_cleanup_service

router = APIRouter()


class CleanupRequest(BaseModel):
    """Request model for cleanup operations"""
    dry_run: bool = True
    max_deletions: int = 5000


class OldEmbeddingsCleanupRequest(BaseModel):
    """Request model for old embeddings cleanup"""
    days_old: int = 90
    dry_run: bool = True
    max_deletions: int = 10000


@router.get("/analyze", response_model=Dict[str, Any])
async def analyze_orphaned_embeddings(
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze orphaned embeddings without deleting them
    
    Returns detailed analysis of embeddings that can be cleaned up
    """
    try:
        analysis = await embeddings_cleanup_service.analyze_orphaned_embeddings()
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_cleanup_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive cleanup statistics and recommendations
    """
    try:
        stats = await embeddings_cleanup_service.get_cleanup_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics failed: {str(e)}")


@router.get("/active-sessions", response_model=Dict[str, Any])
async def check_active_codemirror_sessions(
    current_user: dict = Depends(get_current_user)
):
    """
    Check for active CodeMirror analysis sessions
    """
    try:
        active_sessions = await embeddings_cleanup_service.check_active_codemirror_sessions()
        return {
            "status": "success",
            "active_sessions": active_sessions,
            "safe_to_cleanup": len(active_sessions) == 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session check failed: {str(e)}")


@router.post("/cleanup-orphaned", response_model=Dict[str, Any])
async def cleanup_orphaned_embeddings(
    request: CleanupRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Clean up orphaned embeddings
    
    Args:
        request: Cleanup configuration
        
    Returns:
        Cleanup results
    """
    try:
        results = await embeddings_cleanup_service.cleanup_orphaned_embeddings(
            dry_run=request.dry_run,
            max_deletions=request.max_deletions
        )
        return {
            "status": "success",
            "cleanup_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/cleanup-old", response_model=Dict[str, Any])
async def cleanup_old_embeddings(
    request: OldEmbeddingsCleanupRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Clean up old embeddings from inactive items
    
    Args:
        request: Cleanup configuration
        
    Returns:
        Cleanup results
    """
    try:
        results = await embeddings_cleanup_service.cleanup_old_embeddings(
            days_old=request.days_old,
            dry_run=request.dry_run,
            max_deletions=request.max_deletions
        )
        return {
            "status": "success",
            "cleanup_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Old embeddings cleanup failed: {str(e)}")


@router.post("/add-cascade-constraints", response_model=Dict[str, Any])
async def add_cascade_constraints(
    current_user: dict = Depends(get_current_user)
):
    """
    Add CASCADE delete constraints to prevent orphaned embeddings
    
    Returns:
        Results of constraint additions
    """
    try:
        results = await embeddings_cleanup_service.add_cascade_constraints()
        return {
            "status": "success",
            "constraint_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Constraint addition failed: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def embeddings_cleanup_health():
    """
    Health check for embeddings cleanup service
    """
    try:
        # Initialize the service
        await embeddings_cleanup_service.initialize()
        
        # Get basic statistics
        stats = await embeddings_cleanup_service.get_cleanup_statistics()
        
        return {
            "status": "healthy",
            "service": "embeddings_cleanup",
            "database_connected": True,
            "summary": {
                "total_embeddings": stats.get("database_health", {}).get("total_embeddings", 0),
                "orphaned_count": stats.get("database_health", {}).get("orphaned_count", 0),
                "cleanup_needed": stats.get("cleanup_recommendations", {}).get("immediate_cleanup_needed", False)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Add to main router
def include_embeddings_cleanup_routes(main_router):
    """Include embeddings cleanup routes in main router"""
    main_router.include_router(
        router,
        prefix="/api/embeddings-cleanup",
        tags=["embeddings_cleanup"]
    )