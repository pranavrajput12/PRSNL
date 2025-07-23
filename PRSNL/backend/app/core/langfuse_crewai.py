"""Langfuse callback handler for CrewAI integration"""
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from crewai.tools.agent_tools import AgentTools
from langfuse import Langfuse

from app.config import settings
from app.core.langfuse_client import LangfuseClient

logger = logging.getLogger(__name__)


class LangfuseCrewAIHandler:
    """Custom callback handler for CrewAI with Langfuse integration"""
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        self.langfuse = LangfuseClient.get_client()
        self.session_id = session_id
        self.user_id = user_id
        self.active_traces = {}
        
    def on_agent_start(self, agent_name: str, task: str, **kwargs) -> None:
        """Called when an agent starts working on a task"""
        if not self.langfuse:
            return
            
        try:
            # Create a new trace for this agent task
            trace = self.langfuse.trace(
                name=f"agent_{agent_name}",
                session_id=self.session_id,
                user_id=self.user_id,
                metadata={
                    "agent_name": agent_name,
                    "task": task,
                    "start_time": datetime.utcnow().isoformat(),
                    **kwargs
                }
            )
            self.active_traces[agent_name] = trace
            logger.debug(f"Started Langfuse trace for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Error starting Langfuse trace: {e}")
    
    def on_agent_finish(self, agent_name: str, result: Any, **kwargs) -> None:
        """Called when an agent completes its task"""
        if not self.langfuse or agent_name not in self.active_traces:
            return
            
        try:
            trace = self.active_traces[agent_name]
            trace.update(
                output=str(result),
                metadata={
                    **trace.metadata,
                    "end_time": datetime.utcnow().isoformat(),
                    "status": "completed",
                    **kwargs
                }
            )
            del self.active_traces[agent_name]
            logger.debug(f"Completed Langfuse trace for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Error completing Langfuse trace: {e}")
    
    def on_agent_error(self, agent_name: str, error: Exception, **kwargs) -> None:
        """Called when an agent encounters an error"""
        if not self.langfuse or agent_name not in self.active_traces:
            return
            
        try:
            trace = self.active_traces[agent_name]
            trace.update(
                metadata={
                    **trace.metadata,
                    "end_time": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": str(error),
                    **kwargs
                }
            )
            del self.active_traces[agent_name]
            logger.debug(f"Error traced in Langfuse for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Error updating Langfuse trace with error: {e}")
    
    def on_tool_start(self, tool_name: str, agent_name: str, input_data: Any, **kwargs) -> None:
        """Called when a tool is invoked"""
        if not self.langfuse:
            return
            
        try:
            # Create a span within the agent's trace
            if agent_name in self.active_traces:
                trace = self.active_traces[agent_name]
                span = trace.span(
                    name=f"tool_{tool_name}",
                    input=input_data,
                    metadata={
                        "tool_name": tool_name,
                        "agent_name": agent_name,
                        **kwargs
                    }
                )
                # Store span reference
                self.active_traces[f"{agent_name}_tool_{tool_name}"] = span
        except Exception as e:
            logger.error(f"Error creating tool span in Langfuse: {e}")
    
    def on_tool_finish(self, tool_name: str, agent_name: str, output: Any, **kwargs) -> None:
        """Called when a tool completes"""
        if not self.langfuse:
            return
            
        span_key = f"{agent_name}_tool_{tool_name}"
        if span_key in self.active_traces:
            try:
                span = self.active_traces[span_key]
                span.end(output=output, metadata={**span.metadata, **kwargs})
                del self.active_traces[span_key]
            except Exception as e:
                logger.error(f"Error ending tool span in Langfuse: {e}")
    
    def on_crew_start(self, crew_name: str, **kwargs) -> None:
        """Called when a crew starts execution"""
        if not self.langfuse:
            return
            
        try:
            # Create main trace for crew execution
            trace = self.langfuse.trace(
                name=f"crew_{crew_name}",
                session_id=self.session_id,
                user_id=self.user_id,
                metadata={
                    "crew_name": crew_name,
                    "start_time": datetime.utcnow().isoformat(),
                    **kwargs
                }
            )
            self.active_traces["_crew_main"] = trace
            logger.info(f"Started Langfuse trace for crew: {crew_name}")
        except Exception as e:
            logger.error(f"Error starting crew trace in Langfuse: {e}")
    
    def on_crew_finish(self, crew_name: str, result: Any, **kwargs) -> None:
        """Called when a crew completes execution"""
        if not self.langfuse or "_crew_main" not in self.active_traces:
            return
            
        try:
            trace = self.active_traces["_crew_main"]
            trace.update(
                output=str(result),
                metadata={
                    **trace.metadata,
                    "end_time": datetime.utcnow().isoformat(),
                    "status": "completed",
                    **kwargs
                }
            )
            del self.active_traces["_crew_main"]
            
            # Flush to ensure all data is sent
            self.langfuse.flush()
            logger.info(f"Completed Langfuse trace for crew: {crew_name}")
        except Exception as e:
            logger.error(f"Error completing crew trace in Langfuse: {e}")
    
    def flush(self) -> None:
        """Flush any pending events"""
        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.error(f"Error flushing Langfuse: {e}")


def create_langfuse_callbacks(session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create CrewAI callbacks that integrate with Langfuse
    
    Returns a dictionary of callbacks that can be passed to Crew
    """
    handler = LangfuseCrewAIHandler(session_id=session_id, user_id=user_id)
    
    return {
        "on_agent_start": handler.on_agent_start,
        "on_agent_finish": handler.on_agent_finish,
        "on_agent_error": handler.on_agent_error,
        "on_tool_start": handler.on_tool_start,
        "on_tool_finish": handler.on_tool_finish,
        "on_crew_start": handler.on_crew_start,
        "on_crew_finish": handler.on_crew_finish,
    }