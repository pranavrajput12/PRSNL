"""
Base Crew class for PRSNL Crew.ai crews

Provides common functionality and patterns for all PRSNL crews.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from uuid import uuid4

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

from app.config import settings
from app.db.database import get_db_pool
from app.services.job_persistence_service import JobPersistenceService

logger = logging.getLogger(__name__)


class PRSNLBaseCrew:
    """Base class for all PRSNL Crew.ai crews"""
    
    def __init__(self):
        self.job_id = None
        self.start_time = None
        self.agents = []
        self.tasks = []
        self.memory = True
        self.verbose = True
        
    async def create_job(self, job_type: str, input_data: Dict[str, Any]) -> str:
        """Create a job in the persistence system"""
        self.job_id = f"crew_{job_type}_{uuid4()}"
        self.start_time = datetime.utcnow()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.create_job(
                job_id=self.job_id,
                job_type=job_type,
                input_data=input_data,
                metadata={
                    "crew_type": self.__class__.__name__,
                    "process_type": self.get_process_type()
                }
            )
        
        return self.job_id
    
    async def update_job_progress(self, progress: int, stage: str, message: str = None):
        """Update job progress"""
        if not self.job_id:
            return
            
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.update_job_progress(
                job_id=self.job_id,
                progress_percentage=progress,
                current_stage=stage,
                stage_message=message
            )
    
    async def complete_job(self, result_data: Dict[str, Any]):
        """Mark job as completed"""
        if not self.job_id:
            return
            
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.complete_job(
                job_id=self.job_id,
                result_data=result_data
            )
    
    async def fail_job(self, error_message: str, error_details: Dict[str, Any] = None):
        """Mark job as failed"""
        if not self.job_id:
            return
            
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.fail_job(
                job_id=self.job_id,
                error_message=error_message,
                error_details=error_details or {}
            )
    
    def get_process_type(self) -> str:
        """Get the process type for this crew"""
        return "sequential"  # Default, override in subclasses
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get Azure OpenAI configuration for Crew.ai"""
        return {
            "model": settings.AZURE_OPENAI_DEPLOYMENT,
            "api_key": settings.AZURE_OPENAI_API_KEY,
            "api_base": settings.AZURE_OPENAI_ENDPOINT,
            "api_version": settings.AZURE_OPENAI_API_VERSION,
            "api_type": "azure"
        }
    
    def create_callback_handlers(self) -> Dict[str, Any]:
        """Create callback handlers for crew execution"""
        async def on_task_complete(task: Task, output: str):
            logger.info(f"Task completed: {task.description[:50]}...")
            await self.update_job_progress(
                progress=50,  # Adjust based on task count
                stage=f"Completed: {task.description[:50]}",
                message=output[:200]
            )
        
        async def on_crew_complete(output: str):
            logger.info(f"Crew completed: {self.__class__.__name__}")
            execution_time = (datetime.utcnow() - self.start_time).total_seconds()
            await self.complete_job({
                "output": output,
                "execution_time": execution_time,
                "completed_at": datetime.utcnow().isoformat()
            })
        
        return {
            "on_task_complete": on_task_complete,
            "on_crew_complete": on_crew_complete
        }


class CrewFactory:
    """Factory for creating PRSNL crews"""
    
    @staticmethod
    def create_crew(crew_type: str, **kwargs) -> PRSNLBaseCrew:
        """Create a crew by type"""
        from app.crews import get_crew
        
        crew_class = get_crew(crew_type)
        if not crew_class:
            raise ValueError(f"Unknown crew type: {crew_type}")
        
        return crew_class(**kwargs)
    
    @staticmethod
    def create_knowledge_crew(**kwargs) -> 'KnowledgeCurationCrew':
        """Create a Knowledge Curation crew"""
        from app.crews.knowledge_crew import KnowledgeCurationCrew
        return KnowledgeCurationCrew(**kwargs)
    
    @staticmethod
    def create_code_crew(**kwargs) -> 'CodeIntelligenceCrew':
        """Create a Code Intelligence crew"""
        from app.crews.code_crew import CodeIntelligenceCrew
        return CodeIntelligenceCrew(**kwargs)
    
    @staticmethod
    def create_media_crew(**kwargs) -> 'MediaProcessingCrew':
        """Create a Media Processing crew"""
        from app.crews.media_crew import MediaProcessingCrew
        return MediaProcessingCrew(**kwargs)
    
    @staticmethod
    def create_research_crew(**kwargs) -> 'ResearchCrew':
        """Create a Research crew"""
        from app.crews.research_crew import ResearchCrew
        return ResearchCrew(**kwargs)
    
    @staticmethod
    def create_autonomous_crew(goal: str, **kwargs) -> 'AutonomousCrew':
        """Create an Autonomous crew that figures out its own agents and tasks"""
        from app.crews.autonomous_crew import AutonomousCrew
        return AutonomousCrew(goal=goal, **kwargs)