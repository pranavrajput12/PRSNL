"""
Learning Analyzer Agent - Migrated to Crew.ai

This agent analyzes learning patterns and progression in conversations.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool
from app.tools.knowledge_tools import ConnectionFinderTool

logger = logging.getLogger(__name__)


@register_agent("learning_analyzer")
class LearningAnalyzerAgent(PRSNLBaseAgent):
    """
    Learning Analyzer Agent
    
    Specializes in analyzing learning patterns, progression, and outcomes
    in conversational content to support learning and development.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Learning Pattern Analyzer")
        goal = kwargs.pop("goal", 
            "Analyze learning patterns and progression in conversations "
            "to identify growth opportunities and learning outcomes"
        )
        backstory = kwargs.pop("backstory",
            "You are an educational psychologist and learning specialist "
            "who excels at identifying learning patterns in conversations. "
            "Your expertise helps understand how knowledge is acquired, "
            "retained, and applied through dialogue and discussion."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                ConnectionFinderTool()
            ]
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
    
    def get_specialized_instructions(self) -> str:
        return """
        When analyzing learning patterns:
        1. Identify learning objectives and outcomes
        2. Track knowledge acquisition progression
        3. Recognize skill development indicators
        4. Identify misconceptions and corrections
        5. Analyze questioning patterns and curiosity
        6. Track confidence levels and uncertainty
        7. Identify breakthrough moments and insights
        8. Recognize teaching and mentoring patterns
        9. Assess knowledge retention indicators
        10. Identify learning preferences and styles
        """