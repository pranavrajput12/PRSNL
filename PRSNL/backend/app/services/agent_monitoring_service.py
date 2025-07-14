"""
Agent Monitoring Service

Phase 2: Real-time monitoring and performance tracking for Celery agents
with WebSocket notifications and detailed metrics collection.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass
from collections import defaultdict

from app.db.database import get_db_connection
from app.services.websocket_manager import websocket_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Container for agent performance metrics"""
    agent_type: str
    task_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    success_rate: Optional[float] = None
    error_count: int = 0
    retry_count: int = 0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    queue_name: str = "default"
    priority: int = 0


@dataclass
class WorkflowMetrics:
    """Container for workflow-level metrics"""
    workflow_id: str
    workflow_type: str
    total_agents: int
    completed_agents: int
    failed_agents: int
    start_time: datetime
    end_time: Optional[datetime] = None
    overall_success_rate: float = 0.0
    bottleneck_agent: Optional[str] = None
    total_duration_ms: Optional[int] = None


class AgentMonitoringService:
    """
    Real-time monitoring service for Celery agents with performance tracking,
    WebSocket notifications, and intelligent alerting.
    """
    
    def __init__(self):
        self.active_agents: Dict[str, AgentMetrics] = {}
        self.active_workflows: Dict[str, WorkflowMetrics] = {}
        self.performance_history: Dict[str, List[AgentMetrics]] = defaultdict(list)
        self.alert_thresholds = {
            "max_duration_ms": 300000,  # 5 minutes
            "min_success_rate": 0.8,
            "max_error_rate": 0.2,
            "max_retry_count": 3,
            "max_memory_mb": 1024,
            "max_cpu_percent": 80
        }
    
    async def start_agent_monitoring(self, task_id: str, agent_type: str, queue_name: str = "default", priority: int = 0) -> None:
        """Start monitoring a new agent task"""
        try:
            metrics = AgentMetrics(
                agent_type=agent_type,
                task_id=task_id,
                status="started",
                start_time=datetime.utcnow(),
                queue_name=queue_name,
                priority=priority
            )
            
            self.active_agents[task_id] = metrics
            
            # Store in database
            await self._store_agent_metrics(metrics)
            
            # Send WebSocket notification
            await self._send_agent_notification("agent_started", metrics)
            
            logger.info(f"Started monitoring agent {agent_type} with task ID {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to start agent monitoring: {e}")
    
    async def update_agent_progress(self, task_id: str, progress: int, status: str, message: Optional[str] = None) -> None:
        """Update agent progress and status"""
        try:
            if task_id not in self.active_agents:
                logger.warning(f"Task {task_id} not found in active agents")
                return
            
            metrics = self.active_agents[task_id]
            metrics.status = status
            
            # Update database
            async with get_db_connection() as db:
                await db.execute("""
                    UPDATE task_progress 
                    SET current_value = $2, message = $3, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = $1
                """, task_id, progress, message)
            
            # Send WebSocket notification
            await self._send_progress_notification(task_id, progress, status, message)
            
        except Exception as e:
            logger.error(f"Failed to update agent progress: {e}")
    
    async def complete_agent_monitoring(self, task_id: str, status: str = "completed", result: Optional[Dict[str, Any]] = None) -> None:
        """Complete agent monitoring and calculate final metrics"""
        try:
            if task_id not in self.active_agents:
                logger.warning(f"Task {task_id} not found in active agents")
                return
            
            metrics = self.active_agents[task_id]
            metrics.end_time = datetime.utcnow()
            metrics.status = status
            metrics.duration_ms = int((metrics.end_time - metrics.start_time).total_seconds() * 1000)
            
            # Calculate success rate for this agent type
            await self._calculate_agent_success_rate(metrics)
            
            # Store final metrics
            await self._store_agent_metrics(metrics, final=True)
            
            # Add to performance history
            self.performance_history[metrics.agent_type].append(metrics)
            
            # Check for performance alerts
            await self._check_performance_alerts(metrics)
            
            # Send completion notification
            await self._send_agent_notification("agent_completed", metrics)
            
            # Remove from active agents
            del self.active_agents[task_id]
            
            logger.info(f"Completed monitoring agent {metrics.agent_type} in {metrics.duration_ms}ms")
            
        except Exception as e:
            logger.error(f"Failed to complete agent monitoring: {e}")
    
    async def start_workflow_monitoring(self, workflow_id: str, workflow_type: str, total_agents: int) -> None:
        """Start monitoring a workflow"""
        try:
            workflow_metrics = WorkflowMetrics(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                total_agents=total_agents,
                completed_agents=0,
                failed_agents=0,
                start_time=datetime.utcnow()
            )
            
            self.active_workflows[workflow_id] = workflow_metrics
            
            # Store in database
            await self._store_workflow_metrics(workflow_metrics)
            
            # Send WebSocket notification
            await self._send_workflow_notification("workflow_started", workflow_metrics)
            
        except Exception as e:
            logger.error(f"Failed to start workflow monitoring: {e}")
    
    async def update_workflow_progress(self, workflow_id: str, completed_agents: int, failed_agents: int) -> None:
        """Update workflow progress"""
        try:
            if workflow_id not in self.active_workflows:
                logger.warning(f"Workflow {workflow_id} not found in active workflows")
                return
            
            workflow_metrics = self.active_workflows[workflow_id]
            workflow_metrics.completed_agents = completed_agents
            workflow_metrics.failed_agents = failed_agents
            
            # Calculate progress percentage
            total_processed = completed_agents + failed_agents
            progress_percent = (total_processed / workflow_metrics.total_agents) * 100 if workflow_metrics.total_agents > 0 else 0
            
            # Send progress notification
            await self._send_workflow_progress_notification(workflow_id, progress_percent, workflow_metrics)
            
        except Exception as e:
            logger.error(f"Failed to update workflow progress: {e}")
    
    async def complete_workflow_monitoring(self, workflow_id: str, status: str = "completed") -> None:
        """Complete workflow monitoring"""
        try:
            if workflow_id not in self.active_workflows:
                logger.warning(f"Workflow {workflow_id} not found in active workflows")
                return
            
            workflow_metrics = self.active_workflows[workflow_id]
            workflow_metrics.end_time = datetime.utcnow()
            workflow_metrics.total_duration_ms = int((workflow_metrics.end_time - workflow_metrics.start_time).total_seconds() * 1000)
            
            # Calculate overall success rate
            total_processed = workflow_metrics.completed_agents + workflow_metrics.failed_agents
            workflow_metrics.overall_success_rate = workflow_metrics.completed_agents / total_processed if total_processed > 0 else 0
            
            # Store final metrics
            await self._store_workflow_metrics(workflow_metrics, final=True)
            
            # Send completion notification
            await self._send_workflow_notification("workflow_completed", workflow_metrics)
            
            # Remove from active workflows
            del self.active_workflows[workflow_id]
            
        except Exception as e:
            logger.error(f"Failed to complete workflow monitoring: {e}")
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics for all active agents and workflows"""
        try:
            # Get active agent summaries
            active_agent_summary = {}
            for task_id, metrics in self.active_agents.items():
                agent_type = metrics.agent_type
                if agent_type not in active_agent_summary:
                    active_agent_summary[agent_type] = {
                        "count": 0,
                        "statuses": defaultdict(int),
                        "avg_duration_ms": 0,
                        "queue_distribution": defaultdict(int)
                    }
                
                active_agent_summary[agent_type]["count"] += 1
                active_agent_summary[agent_type]["statuses"][metrics.status] += 1
                active_agent_summary[agent_type]["queue_distribution"][metrics.queue_name] += 1
                
                if metrics.duration_ms:
                    current_duration = active_agent_summary[agent_type]["avg_duration_ms"]
                    count = active_agent_summary[agent_type]["count"]
                    active_agent_summary[agent_type]["avg_duration_ms"] = (current_duration * (count - 1) + metrics.duration_ms) / count
            
            # Get workflow summaries
            active_workflow_summary = {}
            for workflow_id, metrics in self.active_workflows.items():
                workflow_type = metrics.workflow_type
                if workflow_type not in active_workflow_summary:
                    active_workflow_summary[workflow_type] = {
                        "count": 0,
                        "total_agents": 0,
                        "avg_completion_rate": 0
                    }
                
                active_workflow_summary[workflow_type]["count"] += 1
                active_workflow_summary[workflow_type]["total_agents"] += metrics.total_agents
                
                completion_rate = (metrics.completed_agents / metrics.total_agents) if metrics.total_agents > 0 else 0
                current_rate = active_workflow_summary[workflow_type]["avg_completion_rate"]
                count = active_workflow_summary[workflow_type]["count"]
                active_workflow_summary[workflow_type]["avg_completion_rate"] = (current_rate * (count - 1) + completion_rate) / count
            
            # Get performance trends
            performance_trends = await self._calculate_performance_trends()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "active_agents": {
                    "total_count": len(self.active_agents),
                    "by_type": dict(active_agent_summary)
                },
                "active_workflows": {
                    "total_count": len(self.active_workflows),
                    "by_type": dict(active_workflow_summary)
                },
                "performance_trends": performance_trends,
                "alert_status": await self._get_current_alerts()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {"error": str(e)}
    
    async def get_agent_performance_report(self, agent_type: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for agents"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with get_db_connection() as db:
                if agent_type:
                    metrics = await db.fetch("""
                        SELECT * FROM agent_performance_metrics 
                        WHERE agent_type = $1 AND created_at >= $2
                        ORDER BY created_at DESC
                    """, agent_type, start_time)
                else:
                    metrics = await db.fetch("""
                        SELECT * FROM agent_performance_metrics 
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, start_time)
            
            # Process metrics for report
            report = {
                "period": f"Last {hours} hours",
                "total_tasks": len(metrics),
                "agent_types": {},
                "performance_summary": {},
                "trends": {}
            }
            
            # Group by agent type
            by_agent_type = defaultdict(list)
            for metric in metrics:
                by_agent_type[metric["agent_type"]].append(metric)
            
            # Calculate metrics for each agent type
            for agent_type, agent_metrics in by_agent_type.items():
                completed = [m for m in agent_metrics if m["status"] == "completed"]
                failed = [m for m in agent_metrics if m["status"] == "failed"]
                
                avg_duration = sum(m["duration_ms"] for m in completed if m["duration_ms"]) / len(completed) if completed else 0
                success_rate = len(completed) / len(agent_metrics) if agent_metrics else 0
                
                report["agent_types"][agent_type] = {
                    "total_tasks": len(agent_metrics),
                    "completed": len(completed),
                    "failed": len(failed),
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_duration,
                    "avg_retry_count": sum(m["retry_count"] for m in agent_metrics) / len(agent_metrics) if agent_metrics else 0
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _store_agent_metrics(self, metrics: AgentMetrics, final: bool = False) -> None:
        """Store agent metrics in database"""
        try:
            async with get_db_connection() as db:
                if final:
                    await db.execute("""
                        INSERT INTO agent_performance_metrics (
                            task_id, agent_type, status, start_time, end_time,
                            duration_ms, success_rate, error_count, retry_count,
                            memory_usage_mb, cpu_usage_percent, queue_name, priority
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (task_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            end_time = EXCLUDED.end_time,
                            duration_ms = EXCLUDED.duration_ms,
                            success_rate = EXCLUDED.success_rate,
                            error_count = EXCLUDED.error_count,
                            retry_count = EXCLUDED.retry_count
                    """,
                        metrics.task_id,
                        metrics.agent_type,
                        metrics.status,
                        metrics.start_time,
                        metrics.end_time,
                        metrics.duration_ms,
                        metrics.success_rate,
                        metrics.error_count,
                        metrics.retry_count,
                        metrics.memory_usage_mb,
                        metrics.cpu_usage_percent,
                        metrics.queue_name,
                        metrics.priority
                    )
                else:
                    await db.execute("""
                        INSERT INTO agent_performance_metrics (
                            task_id, agent_type, status, start_time, queue_name, priority
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (task_id) DO UPDATE SET
                            status = EXCLUDED.status
                    """,
                        metrics.task_id,
                        metrics.agent_type,
                        metrics.status,
                        metrics.start_time,
                        metrics.queue_name,
                        metrics.priority
                    )
        except Exception as e:
            logger.error(f"Failed to store agent metrics: {e}")
    
    async def _store_workflow_metrics(self, metrics: WorkflowMetrics, final: bool = False) -> None:
        """Store workflow metrics in database"""
        try:
            async with get_db_connection() as db:
                await db.execute("""
                    INSERT INTO workflow_performance_metrics (
                        workflow_id, workflow_type, total_agents, completed_agents,
                        failed_agents, start_time, end_time, overall_success_rate,
                        total_duration_ms, bottleneck_agent
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (workflow_id) DO UPDATE SET
                        completed_agents = EXCLUDED.completed_agents,
                        failed_agents = EXCLUDED.failed_agents,
                        end_time = EXCLUDED.end_time,
                        overall_success_rate = EXCLUDED.overall_success_rate,
                        total_duration_ms = EXCLUDED.total_duration_ms,
                        bottleneck_agent = EXCLUDED.bottleneck_agent
                """,
                    metrics.workflow_id,
                    metrics.workflow_type,
                    metrics.total_agents,
                    metrics.completed_agents,
                    metrics.failed_agents,
                    metrics.start_time,
                    metrics.end_time,
                    metrics.overall_success_rate,
                    metrics.total_duration_ms,
                    metrics.bottleneck_agent
                )
        except Exception as e:
            logger.error(f"Failed to store workflow metrics: {e}")
    
    async def _calculate_agent_success_rate(self, metrics: AgentMetrics) -> None:
        """Calculate success rate for agent type"""
        try:
            # Get recent performance for this agent type
            recent_history = self.performance_history[metrics.agent_type][-10:]  # Last 10 tasks
            
            if recent_history:
                successful = sum(1 for m in recent_history if m.status == "completed")
                metrics.success_rate = successful / len(recent_history)
            else:
                metrics.success_rate = 1.0 if metrics.status == "completed" else 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate success rate: {e}")
            metrics.success_rate = 0.0
    
    async def _check_performance_alerts(self, metrics: AgentMetrics) -> None:
        """Check if performance metrics trigger any alerts"""
        try:
            alerts = []
            
            # Check duration
            if metrics.duration_ms and metrics.duration_ms > self.alert_thresholds["max_duration_ms"]:
                alerts.append({
                    "type": "duration_exceeded",
                    "agent_type": metrics.agent_type,
                    "task_id": metrics.task_id,
                    "duration_ms": metrics.duration_ms,
                    "threshold_ms": self.alert_thresholds["max_duration_ms"]
                })
            
            # Check success rate
            if metrics.success_rate and metrics.success_rate < self.alert_thresholds["min_success_rate"]:
                alerts.append({
                    "type": "low_success_rate",
                    "agent_type": metrics.agent_type,
                    "success_rate": metrics.success_rate,
                    "threshold": self.alert_thresholds["min_success_rate"]
                })
            
            # Check retry count
            if metrics.retry_count > self.alert_thresholds["max_retry_count"]:
                alerts.append({
                    "type": "high_retry_count",
                    "agent_type": metrics.agent_type,
                    "task_id": metrics.task_id,
                    "retry_count": metrics.retry_count,
                    "threshold": self.alert_thresholds["max_retry_count"]
                })
            
            # Send alerts if any
            for alert in alerts:
                await self._send_alert_notification(alert)
                
        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")
    
    async def _send_agent_notification(self, event_type: str, metrics: AgentMetrics) -> None:
        """Send agent event notification via WebSocket"""
        try:
            notification = {
                "type": "agent_monitoring",
                "event": event_type,
                "data": {
                    "task_id": metrics.task_id,
                    "agent_type": metrics.agent_type,
                    "status": metrics.status,
                    "duration_ms": metrics.duration_ms,
                    "queue_name": metrics.queue_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await websocket_manager.broadcast(json.dumps(notification))
            
        except Exception as e:
            logger.error(f"Failed to send agent notification: {e}")
    
    async def _send_progress_notification(self, task_id: str, progress: int, status: str, message: Optional[str]) -> None:
        """Send progress notification via WebSocket"""
        try:
            notification = {
                "type": "agent_progress",
                "data": {
                    "task_id": task_id,
                    "progress": progress,
                    "status": status,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await websocket_manager.broadcast(json.dumps(notification))
            
        except Exception as e:
            logger.error(f"Failed to send progress notification: {e}")
    
    async def _send_workflow_notification(self, event_type: str, metrics: WorkflowMetrics) -> None:
        """Send workflow event notification via WebSocket"""
        try:
            notification = {
                "type": "workflow_monitoring",
                "event": event_type,
                "data": {
                    "workflow_id": metrics.workflow_id,
                    "workflow_type": metrics.workflow_type,
                    "total_agents": metrics.total_agents,
                    "completed_agents": metrics.completed_agents,
                    "failed_agents": metrics.failed_agents,
                    "overall_success_rate": metrics.overall_success_rate,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await websocket_manager.broadcast(json.dumps(notification))
            
        except Exception as e:
            logger.error(f"Failed to send workflow notification: {e}")
    
    async def _send_workflow_progress_notification(self, workflow_id: str, progress_percent: float, metrics: WorkflowMetrics) -> None:
        """Send workflow progress notification via WebSocket"""
        try:
            notification = {
                "type": "workflow_progress",
                "data": {
                    "workflow_id": workflow_id,
                    "progress_percent": progress_percent,
                    "completed_agents": metrics.completed_agents,
                    "failed_agents": metrics.failed_agents,
                    "total_agents": metrics.total_agents,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await websocket_manager.broadcast(json.dumps(notification))
            
        except Exception as e:
            logger.error(f"Failed to send workflow progress notification: {e}")
    
    async def _send_alert_notification(self, alert: Dict[str, Any]) -> None:
        """Send performance alert notification"""
        try:
            notification = {
                "type": "performance_alert",
                "alert": alert,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket_manager.broadcast(json.dumps(notification))
            logger.warning(f"Performance alert: {alert}")
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    async def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        try:
            trends = {}
            
            for agent_type, history in self.performance_history.items():
                if len(history) < 2:
                    continue
                
                recent_metrics = history[-10:]  # Last 10 tasks
                
                # Calculate trend metrics
                avg_duration = sum(m.duration_ms for m in recent_metrics if m.duration_ms) / len(recent_metrics)
                success_rate = sum(1 for m in recent_metrics if m.status == "completed") / len(recent_metrics)
                avg_retries = sum(m.retry_count for m in recent_metrics) / len(recent_metrics)
                
                trends[agent_type] = {
                    "avg_duration_ms": avg_duration,
                    "success_rate": success_rate,
                    "avg_retry_count": avg_retries,
                    "sample_size": len(recent_metrics)
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to calculate performance trends: {e}")
            return {}
    
    async def _get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts"""
        try:
            alerts = []
            
            # Check for stuck agents (running too long)
            current_time = datetime.utcnow()
            for task_id, metrics in self.active_agents.items():
                duration_ms = (current_time - metrics.start_time).total_seconds() * 1000
                if duration_ms > self.alert_thresholds["max_duration_ms"]:
                    alerts.append({
                        "type": "stuck_agent",
                        "task_id": task_id,
                        "agent_type": metrics.agent_type,
                        "duration_ms": duration_ms
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get current alerts: {e}")
            return []


# Create singleton instance
agent_monitoring_service = AgentMonitoringService()