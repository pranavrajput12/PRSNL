"""
Base Agent class for PRSNL Crew.ai agents

Provides common functionality and patterns for all PRSNL agents.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent
from app.config import settings
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class PRSNLBaseAgent:
    """Base class for all PRSNL Crew.ai agents"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[Any]] = None,
        memory: bool = True,
        verbose: bool = True,
        max_iter: int = 5,
        max_execution_time: Optional[int] = 300,
        **kwargs
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.memory = memory
        self.verbose = verbose
        self.max_iter = max_iter
        self.max_execution_time = max_execution_time
        self.additional_config = kwargs
        
        # Create the Crew.ai agent
        self._agent = None
        
    def get_agent(self) -> Agent:
        """Get or create the Crew.ai agent instance"""
        if not self._agent:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.tools,
                llm=self._get_llm_config(),
                memory=self.memory,
                verbose=self.verbose,
                max_iter=self.max_iter,
                max_execution_time=self.max_execution_time,
                **self.additional_config
            )
        return self._agent
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get Azure OpenAI configuration for Crew.ai"""
        return {
            "model": settings.AZURE_OPENAI_DEPLOYMENT,
            "api_key": settings.AZURE_OPENAI_API_KEY,
            "api_base": settings.AZURE_OPENAI_ENDPOINT,
            "api_version": settings.AZURE_OPENAI_API_VERSION,
            "api_type": "azure",
            "temperature": 0.7
        }
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent"""
        self.tools.append(tool)
        if self._agent:
            self._agent.tools = self.tools
    
    def update_goal(self, new_goal: str) -> None:
        """Update the agent's goal"""
        self.goal = new_goal
        if self._agent:
            self._agent.goal = new_goal
    
    def get_memory(self) -> Optional[Any]:
        """Get agent's memory if available"""
        if self._agent and hasattr(self._agent, 'memory'):
            return self._agent.memory
        return None
    
    def clear_memory(self) -> None:
        """Clear agent's memory"""
        if self._agent and hasattr(self._agent, 'memory'):
            self._agent.memory.clear()
    
    def __repr__(self) -> str:
        return f"<PRSNLAgent: {self.role}>"


class AgentFactory:
    """Factory for creating PRSNL agents"""
    
    @staticmethod
    def create_agent(
        agent_type: str,
        **kwargs
    ) -> PRSNLBaseAgent:
        """Create an agent by type"""
        from app.agents import get_agent
        
        agent_class = get_agent(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return agent_class(**kwargs)
    
    @staticmethod
    def create_knowledge_curator(**kwargs) -> PRSNLBaseAgent:
        """Create a Knowledge Curator agent"""
        from app.agents.knowledge.knowledge_curator import KnowledgeCuratorAgent
        return KnowledgeCuratorAgent(**kwargs)
    
    @staticmethod
    def create_code_analyst(**kwargs) -> PRSNLBaseAgent:
        """Create a Code Analyst agent"""
        from app.agents.code.code_analyst import CodeAnalystAgent
        return CodeAnalystAgent(**kwargs)
    
    @staticmethod
    def create_media_processor(**kwargs) -> PRSNLBaseAgent:
        """Create a Media Processor agent"""
        from app.agents.media.media_processor import MediaProcessorAgent
        return MediaProcessorAgent(**kwargs)
    
    @staticmethod
    def create_conversation_analyst(**kwargs) -> PRSNLBaseAgent:
        """Create a Conversation Analyst agent"""
        from app.agents.conversation.conversation_analyst import ConversationAnalystAgent
        return ConversationAnalystAgent(**kwargs)