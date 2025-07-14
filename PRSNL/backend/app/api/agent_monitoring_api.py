"""
Agent Monitoring API

Phase 2: API endpoints for real-time agent monitoring and performance tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.services.agent_monitoring_service import agent_monitoring_service
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent-monitoring", tags=["agent-monitoring"])


class AgentMonitoringRequest(BaseModel):
    task_id: str
    agent_type: str
    queue_name: Optional[str] = "default"
    priority: Optional[int] = 0


class AgentProgressUpdate(BaseModel):
    task_id: str
    progress: int
    status: str
    message: Optional[str] = None


class WorkflowMonitoringRequest(BaseModel):
    workflow_id: str
    workflow_type: str
    total_agents: int


@router.post("/agents/start")
async def start_agent_monitoring(
    request: AgentMonitoringRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start monitoring a new agent task."""
    try:
        await agent_monitoring_service.start_agent_monitoring(
            task_id=request.task_id,
            agent_type=request.agent_type,
            queue_name=request.queue_name,
            priority=request.priority
        )
        
        return {
            "status": "started",
            "task_id": request.task_id,
            "agent_type": request.agent_type,
            "message": "Agent monitoring started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start agent monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/progress")
async def update_agent_progress(
    request: AgentProgressUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update agent progress and status."""
    try:
        await agent_monitoring_service.update_agent_progress(
            task_id=request.task_id,
            progress=request.progress,
            status=request.status,
            message=request.message
        )
        
        return {
            "status": "updated",
            "task_id": request.task_id,
            "progress": request.progress,
            "message": "Agent progress updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update agent progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{task_id}/complete")
async def complete_agent_monitoring(
    task_id: str,
    status: str = "completed",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Complete agent monitoring and finalize metrics."""
    try:
        await agent_monitoring_service.complete_agent_monitoring(
            task_id=task_id,
            status=status
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "message": "Agent monitoring completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to complete agent monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/start")
async def start_workflow_monitoring(
    request: WorkflowMonitoringRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start monitoring a workflow."""
    try:
        await agent_monitoring_service.start_workflow_monitoring(
            workflow_id=request.workflow_id,
            workflow_type=request.workflow_type,
            total_agents=request.total_agents
        )
        
        return {
            "status": "started",
            "workflow_id": request.workflow_id,
            "workflow_type": request.workflow_type,
            "message": "Workflow monitoring started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/workflows/{workflow_id}/progress")
async def update_workflow_progress(
    workflow_id: str,
    completed_agents: int,
    failed_agents: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update workflow progress."""
    try:
        await agent_monitoring_service.update_workflow_progress(
            workflow_id=workflow_id,
            completed_agents=completed_agents,
            failed_agents=failed_agents
        )
        
        return {
            "status": "updated",
            "workflow_id": workflow_id,
            "completed_agents": completed_agents,
            "failed_agents": failed_agents,
            "message": "Workflow progress updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update workflow progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/complete")
async def complete_workflow_monitoring(
    workflow_id: str,
    status: str = "completed",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Complete workflow monitoring."""
    try:
        await agent_monitoring_service.complete_workflow_monitoring(
            workflow_id=workflow_id,
            status=status
        )
        
        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "message": "Workflow monitoring completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to complete workflow monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/real-time")
async def get_real_time_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current real-time metrics for all active agents and workflows."""
    try:
        metrics = await agent_monitoring_service.get_real_time_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance")
async def get_performance_metrics(
    agent_type: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),  # 1 hour to 1 week
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance metrics for agents over a specified time period."""
    try:
        metrics = await agent_monitoring_service.get_agent_performance_report(
            agent_type=agent_type,
            hours=hours
        )
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/active")
async def get_active_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of currently active agents."""
    try:
        async with get_db_connection() as db:
            active_agents = await db.fetch("""
                SELECT 
                    task_id,
                    agent_type,
                    status,
                    start_time,
                    queue_name,
                    priority,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)) * 1000 as current_duration_ms
                FROM agent_performance_metrics
                WHERE end_time IS NULL
                ORDER BY start_time ASC
            """)
            
            return {
                "active_agents": [dict(agent) for agent in active_agents],
                "total_count": len(active_agents)
            }
            
    except Exception as e:
        logger.error(f"Failed to get active agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/active")
async def get_active_workflows(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of currently active workflows."""
    try:
        async with get_db_connection() as db:
            active_workflows = await db.fetch("""
                SELECT 
                    workflow_id,
                    workflow_type,
                    total_agents,
                    completed_agents,
                    failed_agents,
                    start_time,
                    ROUND((completed_agents + failed_agents)::NUMERIC / total_agents * 100, 2) as progress_percent,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)) * 1000 as current_duration_ms
                FROM workflow_performance_metrics
                WHERE end_time IS NULL
                ORDER BY start_time ASC
            """)
            
            return {
                "active_workflows": [dict(workflow) for workflow in active_workflows],
                "total_count": len(active_workflows)
            }
            
    except Exception as e:
        logger.error(f"Failed to get active workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance summary for all agent types."""
    try:
        async with get_db_connection() as db:
            # Agent performance summary
            agent_summary = await db.fetch("""
                SELECT * FROM agent_performance_summary
                ORDER BY total_tasks DESC
            """)
            
            # Workflow performance summary
            workflow_summary = await db.fetch("""
                SELECT * FROM workflow_performance_summary
                ORDER BY total_workflows DESC
            """)
            
            # Performance alerts
            alerts_summary = await db.fetch("""
                SELECT * FROM performance_alerts_summary
                ORDER BY total_alerts DESC
            """)
            
            return {
                "agent_performance": [dict(agent) for agent in agent_summary],
                "workflow_performance": [dict(workflow) for workflow in workflow_summary],
                "alerts_summary": [dict(alert) for alert in alerts_summary]
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/trends")
async def get_performance_trends(
    agent_type: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance trends over time."""
    try:
        async with get_db_connection() as db:
            trends = await db.fetch("""
                SELECT * FROM get_agent_performance_trends($1, $2)
                ORDER BY hour_bucket DESC, agent_type
            """, agent_type, hours)
            
            return {
                "trends": [dict(trend) for trend in trends],
                "period_hours": hours,
                "agent_type_filter": agent_type
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/anomalies")
async def detect_performance_anomalies(
    duration_threshold_ms: int = Query(default=300000, ge=60000),  # Min 1 minute
    success_rate_threshold: float = Query(default=0.8, ge=0.0, le=1.0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Detect performance anomalies based on thresholds."""
    try:
        async with get_db_connection() as db:
            anomalies = await db.fetch("""
                SELECT * FROM detect_performance_anomalies($1, $2)
                ORDER BY issue_type, agent_type
            """, duration_threshold_ms, success_rate_threshold)
            
            return {
                "anomalies": [dict(anomaly) for anomaly in anomalies],
                "thresholds": {
                    "duration_threshold_ms": duration_threshold_ms,
                    "success_rate_threshold": success_rate_threshold
                },
                "detection_time": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to detect performance anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_performance_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance alerts with optional filtering."""
    try:
        async with get_db_connection() as db:
            query = """
                SELECT 
                    id,
                    alert_type,
                    agent_type,
                    task_id,
                    workflow_id,
                    alert_data,
                    severity,
                    status,
                    created_at,
                    resolved_at
                FROM performance_alerts
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND status = $" + str(len(params) + 1)
                params.append(status)
            
            if severity:
                query += " AND severity = $" + str(len(params) + 1)
                params.append(severity)
            
            query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            alerts = await db.fetch(query, *params)
            
            return {
                "alerts": [dict(alert) for alert in alerts],
                "filters": {
                    "status": status,
                    "severity": severity,
                    "limit": limit
                },
                "total_count": len(alerts)
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_performance_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Resolve a performance alert."""
    try:
        async with get_db_connection() as db:
            result = await db.execute("""
                UPDATE performance_alerts 
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND status = 'active'
            """, alert_id)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
            return {
                "status": "resolved",
                "alert_id": alert_id,
                "resolved_at": datetime.utcnow().isoformat(),
                "message": "Alert resolved successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve performance alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/data/cleanup")
async def cleanup_old_performance_data(
    retention_days: int = Query(default=30, ge=7, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clean up old performance data beyond retention period."""
    try:
        async with get_db_connection() as db:
            deleted_count = await db.fetchval("""
                SELECT cleanup_old_performance_data($1)
            """, retention_days)
            
            return {
                "status": "completed",
                "deleted_records": deleted_count,
                "retention_days": retention_days,
                "cleanup_time": datetime.utcnow().isoformat(),
                "message": f"Cleaned up {deleted_count} old performance records"
            }
            
    except Exception as e:
        logger.error(f"Failed to cleanup old performance data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))