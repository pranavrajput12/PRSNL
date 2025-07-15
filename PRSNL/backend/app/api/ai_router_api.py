"""
AI Router API endpoints
Provides insights and control over AI routing decisions
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.services.ai_router import ai_router

router = APIRouter()


class RoutingTestRequest(BaseModel):
    """Request model for testing routing decisions"""
    content: str
    task_type: str = "text_generation"
    priority: int = 5


@router.get("/status", response_model=Dict[str, Any])
async def get_router_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current AI router status and statistics
    
    Returns:
        Router status including provider health and usage
    """
    try:
        # Get basic usage report
        usage_report = ai_router.get_usage_report()
        
        # Get recommendations
        recommendations = ai_router.recommend_optimization()
        
        return {
            "status": "operational",
            "usage": usage_report,
            "recommendations": recommendations,
            "provider_health": {
                provider.value: ai_router.provider_health[provider]
                for provider in ai_router.provider_health
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get router status: {str(e)}")


@router.get("/enhanced-insights", response_model=Dict[str, Any])
async def get_enhanced_routing_insights(
    current_user: dict = Depends(get_current_user)
):
    """
    Get enhanced routing insights with ReAct agent analysis
    
    Returns:
        Comprehensive routing report including enhanced insights
    """
    try:
        report = ai_router.get_enhanced_routing_report()
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced insights: {str(e)}")


@router.post("/test-routing", response_model=Dict[str, Any])
async def test_routing_decision(
    request: RoutingTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Test routing decision for a sample task
    
    Args:
        request: Test task configuration
        
    Returns:
        Routing decision with reasoning
    """
    try:
        from app.services.ai_router import AITask, TaskType
        
        # Create test task
        task_type_map = {
            "text_generation": TaskType.TEXT_GENERATION,
            "embedding": TaskType.EMBEDDING,
            "vision": TaskType.VISION,
            "streaming": TaskType.STREAMING
        }
        
        task = AITask(
            type=task_type_map.get(request.task_type, TaskType.TEXT_GENERATION),
            content=request.content,
            priority=request.priority
        )
        
        # Check if enhanced routing is available
        enhanced_available = False
        enhanced_decision = None
        
        try:
            from app.services.ai_router_enhanced import enhanced_ai_router
            if enhanced_ai_router.enabled:
                enhanced_available = True
                # Get enhanced routing decision
                enhanced_decision = await enhanced_ai_router.route_task_enhanced(task)
        except ImportError:
            pass
        
        # Get basic routing decision
        basic_provider = await ai_router.route_task(task)
        
        response = {
            "status": "success",
            "basic_routing": {
                "provider": basic_provider.value,
                "reasoning": "Cost-performance optimization"
            },
            "enhanced_routing_available": enhanced_available
        }
        
        if enhanced_decision:
            response["enhanced_routing"] = {
                "provider": enhanced_decision.provider.value,
                "complexity": enhanced_decision.complexity.value,
                "reasoning": enhanced_decision.reasoning,
                "confidence": enhanced_decision.confidence,
                "estimated_tokens": enhanced_decision.estimated_tokens,
                "recommended_model": enhanced_decision.recommended_model,
                "optimization_notes": enhanced_decision.optimization_notes
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing test failed: {str(e)}")


@router.get("/providers", response_model=Dict[str, Any])
async def get_provider_info():
    """
    Get information about available AI providers
    
    Returns:
        Provider configurations and capabilities
    """
    try:
        providers = {}
        
        for provider, config in ai_router.providers.items():
            providers[provider.value] = {
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "max_tokens_per_request": config.max_tokens_per_request,
                "supports_streaming": config.supports_streaming,
                "supports_vision": config.supports_vision,
                "supports_embeddings": config.supports_embeddings,
                "avg_response_time_ms": config.avg_response_time_ms,
                "success_rate": config.success_rate
            }
        
        return {
            "status": "success",
            "providers": providers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


# Add to main router
def include_ai_router_routes(main_router):
    """Include AI router routes in main router"""
    main_router.include_router(
        router,
        prefix="/api/ai-router",
        tags=["ai_router"]
    )