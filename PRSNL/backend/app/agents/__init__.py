"""
Crew.ai Agents for PRSNL

This module contains all Crew.ai agent definitions migrated from the legacy agent system.
"""

from typing import List, Dict, Any
from crewai import Agent
from app.agents.base_agent import PRSNLBaseAgent

# Agent registry for dynamic loading
AGENT_REGISTRY: Dict[str, type] = {}

def register_agent(agent_type: str):
    """Decorator to register agents"""
    def decorator(agent_class):
        AGENT_REGISTRY[agent_type] = agent_class
        return agent_class
    return decorator

def get_agent(agent_type: str) -> type:
    """Get agent class by type"""
    return AGENT_REGISTRY.get(agent_type)

def list_agents() -> List[str]:
    """List all registered agent types"""
    return list(AGENT_REGISTRY.keys())

# Import all agent modules to trigger registration
from app.agents.knowledge import *
from app.agents.code import *
from app.agents.media import *
from app.agents.conversation import *

__all__ = [
    'PRSNLBaseAgent',
    'register_agent',
    'get_agent',
    'list_agents',
    'AGENT_REGISTRY'
]