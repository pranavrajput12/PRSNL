"""
Crew.ai API Endpoints

This module provides REST API endpoints for all Crew.ai operations
including autonomous workflows, dynamic crew composition, and system management.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.crew_service import crew_service
from app.core.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crew", tags=["crew"])


# Pydantic Models
class CrewExecutionRequest(BaseModel):
    """Request model for crew execution"""
    crew_type: str = Field(..., description="Type of crew to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input data for crew execution")
    async_execution: bool = Field(default=True, description="Execute asynchronously")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class AutonomousCrewRequest(BaseModel):
    """Request model for autonomous crew creation"""
    goal: str = Field(..., description="Goal for the autonomous crew")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Context information")
    mode: str = Field(default="hybrid", description="Autonomous mode: reactive, proactive, hybrid, scheduled")
    priority: str = Field(default="medium", description="Workflow priority: critical, high, medium, low")


class DynamicCrewRequest(BaseModel):
    """Request model for dynamic crew composition"""
    task_requirements: Dict[str, Any] = Field(..., description="Task requirements for crew composition")
    max_crew_size: int = Field(default=5, description="Maximum crew size")
    process_type: str = Field(default="sequential", description="Process type: sequential or hierarchical")
    collaboration_mode: str = Field(default="coordinated", description="Collaboration mode")


class CustomCrewRequest(BaseModel):
    """Request model for custom crew creation"""
    name: str = Field(..., description="Name of the custom crew")
    agents: List[Dict[str, Any]] = Field(..., description="Agent configurations")
    tasks: List[Dict[str, Any]] = Field(..., description="Task definitions")
    process: str = Field(default="sequential", description="Process type")


class CrewResponse(BaseModel):
    """Response model for crew operations"""
    job_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    system_status: str
    performance_metrics: Dict[str, Any]
    resource_utilization: Dict[str, Any]
    active_workflows: int
    total_processed: int
    timestamp: str


# Core Crew Operations
@router.post("/execute", response_model=CrewResponse)
async def execute_crew(
    request: CrewExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Execute a crew with specified inputs"""
    try:
        result = await crew_service.execute_crew(
            crew_type=request.crew_type,
            inputs=request.inputs,
            user_id=current_user.get("user_id"),
            async_execution=request.async_execution
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message=result.get("message", "Crew execution initiated"),
            result=result.get("result")
        )
        
    except Exception as e:
        logger.error(f"Crew execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_crew_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of a crew execution"""
    try:
        status = await crew_service.get_crew_status(job_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crew status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available/crews")
async def list_available_crews(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all available crew types"""
    try:
        crews = await crew_service.list_available_crews()
        return crews
        
    except Exception as e:
        logger.error(f"Failed to list available crews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available/agents")
async def list_available_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all available agent types"""
    try:
        agents = await crew_service.list_available_agents()
        return agents
        
    except Exception as e:
        logger.error(f"Failed to list available agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Autonomous Crew Operations
@router.post("/autonomous", response_model=CrewResponse)
async def create_autonomous_crew(
    request: AutonomousCrewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Create and execute an autonomous crew"""
    try:
        result = await crew_service.create_autonomous_crew(
            goal=request.goal,
            context=request.context,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result.get("request_id", "unknown"),
            status=result.get("status", "unknown"),
            message="Autonomous crew created and executing",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Autonomous crew creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dynamic", response_model=CrewResponse)
async def compose_dynamic_crew(
    request: DynamicCrewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Compose a dynamic crew based on task requirements"""
    try:
        result = await crew_service.compose_dynamic_crew(
            task_requirements=request.task_requirements,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message=result["message"],
            result=result.get("crew_config")
        )
        
    except Exception as e:
        logger.error(f"Dynamic crew composition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=CrewResponse)
async def create_custom_crew(
    request: CustomCrewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Create a custom crew with specified agents and tasks"""
    try:
        result = await crew_service.create_custom_crew(
            name=request.name,
            agents=request.agents,
            tasks=request.tasks,
            process=request.process,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except Exception as e:
        logger.error(f"Custom crew creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System Management
@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SystemStatusResponse:
    """Get autonomous system status and metrics"""
    try:
        status = await crew_service.get_autonomous_system_status()
        
        return SystemStatusResponse(
            system_status=status["system_status"],
            performance_metrics=status["performance_metrics"],
            resource_utilization=status["resource_utilization"],
            active_workflows=status["active_workflows"],
            total_processed=status["total_processed"],
            timestamp=status["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/optimize")
async def optimize_system(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Optimize the autonomous system performance"""
    try:
        # Run optimization in background
        background_tasks.add_task(crew_service.optimize_autonomous_system)
        
        return {
            "status": "optimization_started",
            "message": "System optimization started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/capabilities")
async def get_system_capabilities(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available system capabilities"""
    try:
        capabilities = await crew_service.get_available_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get system capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow Management
@router.get("/workflows")
async def get_workflow_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get workflow execution history"""
    try:
        history = await crew_service.get_workflow_history(limit=limit, offset=offset)
        return history
        
    except Exception as e:
        logger.error(f"Failed to get workflow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel an active workflow"""
    try:
        result = await crew_service.cancel_workflow(workflow_id)
        
        if result["status"] == "not_found":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Monitoring
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for crew system"""
    try:
        # Basic health check
        system_status = await crew_service.get_autonomous_system_status()
        
        return {
            "status": "healthy",
            "system_operational": system_status["system_status"] == "operational",
            "active_workflows": system_status["active_workflows"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Specialized Crew Endpoints
@router.post("/knowledge/curate")
async def curate_knowledge(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Execute knowledge curation crew"""
    try:
        result = await crew_service.execute_crew(
            crew_type="knowledge_curation",
            inputs=request,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message="Knowledge curation started",
            result=result.get("result")
        )
        
    except Exception as e:
        logger.error(f"Knowledge curation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/analyze")
async def analyze_code(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Execute code analysis crew"""
    try:
        result = await crew_service.execute_crew(
            crew_type="code_analysis",
            inputs=request,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message="Code analysis started",
            result=result.get("result")
        )
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/analyze")
async def analyze_conversation(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Execute conversation analysis crew"""
    try:
        result = await crew_service.execute_crew(
            crew_type="conversation_intelligence",
            inputs=request,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message="Conversation analysis started",
            result=result.get("result")
        )
        
    except Exception as e:
        logger.error(f"Conversation analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/process")
async def process_media(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> CrewResponse:
    """Execute media processing crew"""
    try:
        result = await crew_service.execute_crew(
            crew_type="media_processing",
            inputs=request,
            user_id=current_user.get("user_id")
        )
        
        return CrewResponse(
            job_id=result["job_id"],
            status=result["status"],
            message="Media processing started",
            result=result.get("result")
        )
        
    except Exception as e:
        logger.error(f"Media processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Advanced Operations
@router.post("/batch/execute")
async def execute_batch_crews(
    requests: List[CrewExecutionRequest],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[CrewResponse]:
    """Execute multiple crews in batch"""
    try:
        results = []
        
        for request in requests:
            try:
                result = await crew_service.execute_crew(
                    crew_type=request.crew_type,
                    inputs=request.inputs,
                    user_id=current_user.get("user_id"),
                    async_execution=request.async_execution
                )
                
                results.append(CrewResponse(
                    job_id=result["job_id"],
                    status=result["status"],
                    message=result.get("message", "Crew execution initiated"),
                    result=result.get("result")
                ))
                
            except Exception as e:
                logger.error(f"Batch crew execution failed for {request.crew_type}: {e}")
                results.append(CrewResponse(
                    job_id="failed",
                    status="error",
                    message=str(e),
                    error=str(e)
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/create")
async def create_crew_pipeline(
    pipeline_config: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a crew pipeline with multiple stages"""
    try:
        # Pipeline creation would involve:
        # 1. Parse pipeline configuration
        # 2. Create crew sequence
        # 3. Set up inter-crew communication
        # 4. Execute pipeline
        
        # For now, return a simple response
        return {
            "pipeline_id": f"pipeline_{datetime.utcnow().isoformat()}",
            "status": "created",
            "message": "Crew pipeline created (feature in development)",
            "stages": len(pipeline_config.get("stages", [])),
            "estimated_duration": "30_minutes"
        }
        
    except Exception as e:
        logger.error(f"Pipeline creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Metrics and Analytics
@router.get("/metrics/performance")
async def get_performance_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed performance metrics"""
    try:
        status = await crew_service.get_autonomous_system_status()
        
        return {
            "performance_metrics": status["performance_metrics"],
            "resource_utilization": status["resource_utilization"],
            "system_health": {
                "status": status["system_status"],
                "active_workflows": status["active_workflows"],
                "total_processed": status["total_processed"]
            },
            "timestamp": status["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/usage")
async def get_usage_metrics(
    days: int = Query(7, ge=1, le=90),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get usage metrics for specified period"""
    try:
        # This would analyze usage patterns over time
        # For now, return basic metrics
        
        return {
            "period_days": days,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "most_used_crews": [],
            "resource_usage_trends": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))