"""
Insight Extractor Agent - Migrated to Crew.ai

This agent extracts actionable insights from conversations.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool

logger = logging.getLogger(__name__)


@register_agent("insight_extractor")
class InsightExtractorAgent(PRSNLBaseAgent):
    """
    Insight Extractor Agent
    
    Specializes in extracting actionable insights and valuable
    knowledge from conversational content.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Actionable Insight Extractor")
        goal = kwargs.pop("goal", 
            "Extract actionable insights and valuable knowledge from conversations "
            "to support decision-making and knowledge management"
        )
        backstory = kwargs.pop("backstory",
            "You are a business intelligence specialist who excels at "
            "extracting actionable insights from conversations and meetings. "
            "Your ability to identify valuable knowledge and translate it "
            "into actionable recommendations makes you invaluable for "
            "organizational learning and decision support."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                EntityExtractorTool()
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
        When extracting insights:
        1. Identify actionable recommendations
        2. Extract business or strategic insights
        3. Recognize problem-solving approaches
        4. Identify innovation opportunities
        5. Extract lessons learned
        6. Recognize success factors
        7. Identify risks and mitigation strategies
        8. Extract best practices and methodologies
        9. Recognize improvement opportunities
        10. Identify knowledge assets and intellectual property
        """