"""
Crew.ai Crews for PRSNL

This module contains all Crew definitions for orchestrating agents.
"""

from typing import List, Dict, Any, Type
from crewai import Crew

# Crew registry for dynamic loading
CREW_REGISTRY: Dict[str, Type[Crew]] = {}

def register_crew(crew_type: str):
    """Decorator to register crews"""
    def decorator(crew_class):
        CREW_REGISTRY[crew_type] = crew_class
        return crew_class
    return decorator

def get_crew(crew_type: str) -> Type[Crew]:
    """Get crew class by type"""
    return CREW_REGISTRY.get(crew_type)

def list_crews() -> List[str]:
    """List all registered crew types"""
    return list(CREW_REGISTRY.keys())

# Import all crew modules to trigger registration
from app.crews.knowledge_crew import *
from app.crews.code_crew import *
from app.crews.media_crew import *
# from app.crews.research_crew import *  # Module not created yet
from app.crews.conversation_crew import *
from app.crews.autonomous_crew import *

__all__ = [
    'register_crew',
    'get_crew',
    'list_crews',
    'CREW_REGISTRY'
]