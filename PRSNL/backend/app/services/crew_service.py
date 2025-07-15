"""
Main Crew.ai Service for PRSNL

This service manages all Crew.ai operations and integrations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from uuid import uuid4

from crewai import Agent, Crew, Task, Process

from app.config import settings
from app.db.database import get_db_pool
from app.services.job_persistence_service import JobPersistenceService
from app.services.agent_monitoring_service import AgentMonitoringService
from app.crews.base_crew import CrewFactory
from app.agents.base_agent import AgentFactory
from app.crews.autonomous_crew import autonomous_manager, WorkflowPriority

logger = logging.getLogger(__name__)


class CrewService:
    """Main service for managing Crew.ai operations"""
    
    def __init__(self):
        self.monitoring_service = AgentMonitoringService()
        self.active_crews: Dict[str, Crew] = {}
        
    async def execute_crew(
        self,
        crew_type: str,
        inputs: Dict[str, Any],
        user_id: Optional[str] = None,
        async_execution: bool = True
    ) -> Dict[str, Any]:
        """Execute a crew with given inputs"""
        try:
            # Create crew
            crew_instance = CrewFactory.create_crew(crew_type)
            
            # Create job
            job_id = await crew_instance.create_job(
                job_type=f"crew_{crew_type}",
                input_data={
                    "crew_type": crew_type,
                    "inputs": inputs,
                    "user_id": user_id
                }
            )
            
            # Store active crew
            self.active_crews[job_id] = crew_instance
            
            # Execute crew
            if async_execution:
                # Run in background
                asyncio.create_task(
                    self._execute_crew_async(crew_instance, inputs, job_id)
                )
                
                return {
                    "job_id": job_id,
                    "status": "processing",
                    "message": f"Crew {crew_type} started execution"
                }
            else:
                # Run synchronously
                result = await self._execute_crew_async(crew_instance, inputs, job_id)
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "result": result
                }
                
        except Exception as e:
            logger.error(f"Failed to execute crew {crew_type}: {e}")
            raise
    
    async def _execute_crew_async(
        self,
        crew_instance: Any,
        inputs: Dict[str, Any],
        job_id: str
    ) -> Dict[str, Any]:
        """Execute crew asynchronously"""
        try:
            # Get the actual crew
            crew = crew_instance.crew()
            
            # Monitor execution start
            await self.monitoring_service.record_agent_execution(
                agent_id=f"crew_{crew_instance.__class__.__name__}",
                execution_id=job_id,
                input_data=inputs,
                status="started"
            )
            
            # Execute crew with inputs
            # Crew.ai expects inputs to match task placeholders
            result = crew.kickoff(inputs=inputs)
            
            # Process result
            processed_result = self._process_crew_result(result)
            
            # Complete job
            await crew_instance.complete_job(processed_result)
            
            # Monitor execution completion
            await self.monitoring_service.update_execution_status(
                execution_id=job_id,
                status="completed",
                output_data=processed_result
            )
            
            # Clean up
            self.active_crews.pop(job_id, None)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            
            # Fail job
            await crew_instance.fail_job(
                error_message=str(e),
                error_details={"type": type(e).__name__}
            )
            
            # Monitor failure
            await self.monitoring_service.update_execution_status(
                execution_id=job_id,
                status="failed",
                error_message=str(e)
            )
            
            # Clean up
            self.active_crews.pop(job_id, None)
            
            raise
    
    def _process_crew_result(self, result: Any) -> Dict[str, Any]:
        """Process and format crew execution result"""
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            return {"output": result}
        elif hasattr(result, "__dict__"):
            return result.__dict__
        else:
            return {"raw_output": str(result)}
    
    async def create_autonomous_crew(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an autonomous crew that figures out its own agents and tasks"""
        try:
            # Use the global autonomous manager
            request = {
                "id": f"autonomous_{uuid4()}",
                "goal": goal,
                "context": context or {},
                "user_id": user_id,
                "resources": {"cpu": 0.3, "memory": 0.3, "agents": 3}
            }
            
            # Process through autonomous manager
            result = await autonomous_manager.process_request(request)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create autonomous crew: {e}")
            raise
    
    async def get_crew_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a crew execution"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            job = await job_service.get_job(job_id)
            
            if not job:
                return {"error": "Job not found"}
            
            return {
                "job_id": job_id,
                "status": job["status"],
                "progress": job.get("progress_percentage", 0),
                "current_stage": job.get("current_stage"),
                "stage_message": job.get("stage_message"),
                "created_at": job["created_at"],
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
                "result": job.get("result_data") if job["status"] == "completed" else None,
                "error": job.get("error_message") if job["status"] == "failed" else None
            }
    
    async def list_available_crews(self) -> List[Dict[str, Any]]:
        """List all available crew types"""
        from app.crews import list_crews, get_crew
        
        crews = []
        for crew_type in list_crews():
            crew_class = get_crew(crew_type)
            crews.append({
                "type": crew_type,
                "name": crew_class.__name__,
                "description": crew_class.__doc__.strip() if crew_class.__doc__ else "No description",
                "process": getattr(crew_class, "process_type", "sequential")
            })
        
        return crews
    
    async def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agent types"""
        from app.agents import list_agents, get_agent
        
        agents = []
        for agent_type in list_agents():
            agent_class = get_agent(agent_type)
            agents.append({
                "type": agent_type,
                "name": agent_class.__name__,
                "description": agent_class.__doc__.strip() if agent_class.__doc__ else "No description"
            })
        
        return agents
    
    async def create_custom_crew(
        self,
        name: str,
        agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        process: str = "sequential",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a custom crew with specified agents and tasks"""
        try:
            # Create agents
            crew_agents = []
            for agent_config in agents:
                agent = AgentFactory.create_agent(
                    agent_type=agent_config["type"],
                    **agent_config.get("params", {})
                )
                crew_agents.append(agent.get_agent())
            
            # Create tasks
            crew_tasks = []
            for i, task_config in enumerate(tasks):
                task = Task(
                    description=task_config["description"],
                    expected_output=task_config.get("expected_output", "Complete the task successfully"),
                    agent=crew_agents[task_config.get("agent_index", i % len(crew_agents))]
                )
                crew_tasks.append(task)
            
            # Create crew
            process_type = Process.sequential if process == "sequential" else Process.hierarchical
            
            custom_crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                process=process_type,
                verbose=True,
                memory=True
            )
            
            # Create job
            job_id = f"custom_crew_{name}_{uuid4()}"
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                job_service = JobPersistenceService(conn)
                await job_service.create_job(
                    job_id=job_id,
                    job_type="custom_crew",
                    input_data={
                        "name": name,
                        "agents": agents,
                        "tasks": tasks,
                        "process": process,
                        "user_id": user_id
                    }
                )
            
            # Execute
            asyncio.create_task(
                self._execute_custom_crew(custom_crew, job_id, {})
            )
            
            return {
                "job_id": job_id,
                "status": "processing",
                "message": f"Custom crew '{name}' started execution"
            }
            
        except Exception as e:
            logger.error(f"Failed to create custom crew: {e}")
            raise
    
    async def _execute_custom_crew(
        self,
        crew: Crew,
        job_id: str,
        inputs: Dict[str, Any]
    ):
        """Execute a custom crew"""
        try:
            # Execute
            result = crew.kickoff(inputs=inputs)
            
            # Process result
            processed_result = self._process_crew_result(result)
            
            # Update job
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                job_service = JobPersistenceService(conn)
                await job_service.complete_job(job_id, processed_result)
                
        except Exception as e:
            logger.error(f"Custom crew execution failed: {e}")
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                job_service = JobPersistenceService(conn)
                await job_service.fail_job(
                    job_id,
                    str(e),
                    {"type": type(e).__name__}
                )
    
    async def compose_dynamic_crew(
        self,
        task_requirements: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compose a dynamic crew based on task requirements"""
        try:
            # Use the dynamic crew composer
            crew_config = autonomous_manager.composer.compose_dynamic_crew(task_requirements)
            
            # Create job for tracking
            job_id = f"dynamic_crew_{uuid4()}"
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                job_service = JobPersistenceService(conn)
                await job_service.create_job(
                    job_id=job_id,
                    job_type="dynamic_crew",
                    input_data={
                        "task_requirements": task_requirements,
                        "crew_config": crew_config,
                        "user_id": user_id
                    }
                )
            
            return {
                "job_id": job_id,
                "crew_config": crew_config,
                "status": "composed",
                "message": "Dynamic crew composed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to compose dynamic crew: {e}")
            raise
    
    async def optimize_autonomous_system(self) -> Dict[str, Any]:
        """Optimize the autonomous system performance"""
        try:
            optimization_result = await autonomous_manager.optimize_system()
            
            return {
                "optimization_status": optimization_result["optimization_status"],
                "improvements": optimization_result["improvements"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize autonomous system: {e}")
            raise
    
    async def get_autonomous_system_status(self) -> Dict[str, Any]:
        """Get autonomous system status and metrics"""
        try:
            performance_data = autonomous_manager.collect_performance_data()
            resource_status = autonomous_manager.resource_manager.resource_pool
            
            return {
                "system_status": "operational",
                "performance_metrics": performance_data,
                "resource_utilization": resource_status,
                "active_workflows": len(autonomous_manager.active_workflows),
                "total_processed": len(autonomous_manager.workflow_history),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get autonomous system status: {e}")
            raise
    
    async def get_workflow_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        try:
            history = autonomous_manager.workflow_history
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            page_history = history[start_idx:end_idx]
            
            return [
                {
                    "request_id": item["request_id"],
                    "status": item["result"]["status"],
                    "timestamp": item["timestamp"],
                    "duration": item.get("duration", 0),
                    "workflow_type": item["plan"].get("workflow_id", "unknown")
                }
                for item in page_history
            ]
            
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}")
            raise
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel an active workflow"""
        try:
            if workflow_id in autonomous_manager.active_workflows:
                # Mark as cancelled
                autonomous_manager.active_workflows[workflow_id]["status"] = "cancelled"
                
                # Clean up resources
                workflow_info = autonomous_manager.active_workflows.pop(workflow_id)
                if "resources" in workflow_info:
                    autonomous_manager.resource_manager.release_resources(
                        workflow_id,
                        workflow_info["resources"]
                    )
                
                return {
                    "workflow_id": workflow_id,
                    "status": "cancelled",
                    "message": "Workflow cancelled successfully"
                }
            else:
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "message": "Workflow not found or already completed"
                }
                
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            raise
    
    async def get_available_capabilities(self) -> Dict[str, Any]:
        """Get available agent capabilities and crew types"""
        try:
            from app.crews import list_crews
            from app.agents import list_agents
            
            return {
                "crews": {
                    "available": list_crews(),
                    "autonomous": [
                        "autonomous_orchestrator",
                        "dynamic_crew_composer",
                        "self_improving_crew"
                    ]
                },
                "agents": {
                    "available": list_agents(),
                    "categories": {
                        "knowledge": [
                            "knowledge_curator",
                            "research_synthesizer",
                            "content_explorer",
                            "learning_path"
                        ],
                        "code": [
                            "code_analyst",
                            "pattern_detector",
                            "insight_generator",
                            "security_analyst"
                        ],
                        "conversation": [
                            "conversation_analyst",
                            "learning_analyzer",
                            "insight_extractor",
                            "knowledge_gap_detector"
                        ],
                        "media": [
                            "ocr_image_agent",
                            "video_processor_agent",
                            "audio_journal_agent"
                        ]
                    }
                },
                "autonomous_modes": [mode.value for mode in autonomous_manager.orchestrator.mode.__class__],
                "workflow_priorities": [priority.value for priority in WorkflowPriority]
            }
            
        except Exception as e:
            logger.error(f"Failed to get available capabilities: {e}")
            raise


# Global instance
crew_service = CrewService()