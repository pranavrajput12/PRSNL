"""
Crew.ai Tools for PRSNL

This module contains all Crew.ai tool definitions that wrap existing PRSNL services.
"""

from typing import List, Dict, Any, Type
from crewai.tools import BaseTool

# Tool registry for dynamic loading
TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {}

def register_tool(tool_name: str):
    """Decorator to register tools"""
    def decorator(tool_class):
        TOOL_REGISTRY[tool_name] = tool_class
        return tool_class
    return decorator

def get_tool(tool_name: str) -> Type[BaseTool]:
    """Get tool class by name"""
    return TOOL_REGISTRY.get(tool_name)

def list_tools() -> List[str]:
    """List all registered tool names"""
    return list(TOOL_REGISTRY.keys())

# Import all tool modules to trigger registration
from app.tools.web_tools import *
from app.tools.knowledge_tools import *
from app.tools.ai_tools import *
from app.tools.code_tools import *
from app.tools.media_tools import *
from app.tools.research_tools import *

__all__ = [
    'register_tool',
    'get_tool', 
    'list_tools',
    'TOOL_REGISTRY'
]