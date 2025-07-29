"""
API endpoints for PersonaAnalysisCrew - Dreamscape Feature

Provides endpoints for triggering persona analysis, retrieving persona data,
and managing user persona insights.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.persona_analysis_crew import PersonaAnalysisCrew, PersonaAnalysisInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/persona", tags=["persona-analysis"])

# Initialize the persona analysis crew
persona_crew = PersonaAnalysisCrew()


class PersonaAnalysisRequest(BaseModel):
    """Request model for persona analysis"""
    user_id: UUID = Field(description="User ID to analyze")
    analysis_depth: str = Field(default="standard", description="Analysis depth: light, standard, deep")
    focus_areas: List[str] = Field(default=[], description="Specific areas to focus on")
    background: bool = Field(default=True, description="Run analysis in background")


class PersonaAnalysisResponse(BaseModel):
    """Response model for persona analysis"""
    user_id: UUID
    status: str
    message: str
    analysis_id: Optional[str] = None
    persona_data: Optional[Dict[str, Any]] = None


class PersonaUpdateRequest(BaseModel):
    """Request model for updating persona insights"""
    insights: Dict[str, Any] = Field(description="New insights to add")


@router.post("/analyze", response_model=PersonaAnalysisResponse)
async def analyze_user_persona(
    request: PersonaAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger persona analysis for a user
    
    This endpoint can run analysis in the background for better UX,
    or synchronously for immediate results.
    """
    try:
        logger.info(f"Received persona analysis request for user {request.user_id}")
        
        if request.background:
            # Run analysis in background
            background_tasks.add_task(
                _run_background_analysis,
                request.user_id,
                request.analysis_depth,
                request.focus_areas
            )
            
            return PersonaAnalysisResponse(
                user_id=request.user_id,
                status="started",
                message="Persona analysis started in background",
                analysis_id=str(request.user_id)  # Simple ID for now
            )
        else:
            # Run analysis synchronously
            persona_data = await persona_crew.analyze_user_persona(
                user_id=request.user_id,
                analysis_depth=request.analysis_depth,
                focus_areas=request.focus_areas
            )
            
            return PersonaAnalysisResponse(
                user_id=request.user_id,
                status="completed",
                message="Persona analysis completed",
                persona_data=persona_data
            )
            
    except Exception as e:
        logger.error(f"Error in persona analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing persona: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_persona(user_id: UUID):
    """
    Retrieve existing persona data for a user
    """
    try:
        persona_data = await persona_crew.get_user_persona(user_id)
        
        if not persona_data:
            raise HTTPException(
                status_code=404,
                detail="Persona not found for user"
            )
        
        return persona_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving persona: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving persona: {str(e)}"
        )


@router.put("/user/{user_id}/insights")
async def update_persona_insights(
    user_id: UUID,
    request: PersonaUpdateRequest
):
    """
    Update specific persona insights without full reanalysis
    """
    try:
        await persona_crew.update_persona_insights(user_id, request.insights)
        
        return {
            "user_id": user_id,
            "status": "updated",
            "message": "Persona insights updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating persona insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating insights: {str(e)}"
        )


@router.get("/user/{user_id}/summary")
async def get_persona_summary(user_id: UUID):
    """
    Get a concise summary of user persona for quick access
    """
    try:
        persona_data = await persona_crew.get_user_persona(user_id)
        
        if not persona_data:
            return {
                "user_id": user_id,
                "status": "not_analyzed",
                "message": "No persona data available"
            }
        
        # Extract key insights for summary
        summary = {
            "user_id": user_id,
            "life_phase": persona_data.get("life_phase"),
            "last_analyzed": persona_data.get("last_analyzed_at"),
            "technical_summary": _extract_technical_summary(persona_data),
            "lifestyle_summary": _extract_lifestyle_summary(persona_data),
            "learning_summary": _extract_learning_summary(persona_data),
            "key_recommendations": _extract_key_recommendations(persona_data)
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting persona summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving summary: {str(e)}"
        )


@router.post("/batch-analyze")
async def batch_analyze_personas(
    user_ids: List[UUID],
    background_tasks: BackgroundTasks,
    analysis_depth: str = "light"
):
    """
    Trigger persona analysis for multiple users in batch
    """
    try:
        logger.info(f"Starting batch persona analysis for {len(user_ids)} users")
        
        # Add batch analysis to background tasks
        background_tasks.add_task(
            _run_batch_analysis,
            user_ids,
            analysis_depth
        )
        
        return {
            "status": "started",
            "message": f"Batch analysis started for {len(user_ids)} users",
            "user_count": len(user_ids)
        }
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting batch analysis: {str(e)}"
        )


@router.get("/health")
async def persona_analysis_health():
    """
    Health check endpoint for persona analysis service
    """
    try:
        # Basic health check - could be expanded
        return {
            "status": "healthy",
            "service": "persona-analysis",
            "crew_agents": [
                "technical_agent",
                "lifestyle_agent", 
                "learning_agent",
                "cross_domain_agent",
                "orchestrator_agent"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Background task functions
async def _run_background_analysis(
    user_id: UUID,
    analysis_depth: str,
    focus_areas: List[str]
):
    """Run persona analysis in background"""
    try:
        logger.info(f"Starting background persona analysis for user {user_id}")
        
        await persona_crew.analyze_user_persona(
            user_id=user_id,
            analysis_depth=analysis_depth,
            focus_areas=focus_areas
        )
        
        logger.info(f"Completed background persona analysis for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in background analysis for user {user_id}: {e}")


async def _run_batch_analysis(user_ids: List[UUID], analysis_depth: str):
    """Run batch persona analysis in background"""
    try:
        logger.info(f"Starting batch analysis for {len(user_ids)} users")
        
        for user_id in user_ids:
            try:
                await persona_crew.analyze_user_persona(
                    user_id=user_id,
                    analysis_depth=analysis_depth
                )
                logger.info(f"Completed analysis for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error analyzing user {user_id}: {e}")
                continue  # Continue with other users
        
        logger.info(f"Completed batch analysis for {len(user_ids)} users")
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")


# Helper functions for summary extraction
def _extract_technical_summary(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract technical profile summary"""
    technical_profile = persona_data.get("technical_profile", {})
    
    return {
        "primary_languages": technical_profile.get("primary_languages", [])[:3],
        "top_domains": technical_profile.get("domains", [])[:2],
        "skill_level": "intermediate"  # Would be calculated from skill_levels
    }


def _extract_lifestyle_summary(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract lifestyle profile summary"""
    lifestyle_profile = persona_data.get("lifestyle_profile", {})
    
    return {
        "top_interests": lifestyle_profile.get("interests", [])[:3],
        "activity_preference": "evening",  # Would be calculated from patterns
        "content_preference": "article"  # Would be calculated from preferences
    }


def _extract_learning_summary(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract learning style summary"""
    learning_style = persona_data.get("learning_style", {})
    
    return {
        "preferred_format": learning_style.get("preferred_formats", ["hands-on"])[0],
        "attention_span": learning_style.get("attention_span", "medium"),
        "complexity_preference": learning_style.get("complexity_preference", "moderate")
    }


def _extract_key_recommendations(persona_data: Dict[str, Any]) -> List[str]:
    """Extract key recommendations from persona"""
    recommendations = persona_data.get("recommendations", [])
    return recommendations[:3]  # Top 3 recommendations