"""
Pattern Detector Agent - Migrated to Crew.ai

This agent detects design patterns, anti-patterns, and code smells in code.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.code_tools import PatternDetectorTool, CodeMetricsTool
from app.tools.ai_tools import SummaryGeneratorTool

logger = logging.getLogger(__name__)


@register_agent("pattern_detector")
class PatternDetectorAgent(PRSNLBaseAgent):
    """
    Pattern Detector Agent
    
    Specializes in identifying design patterns, anti-patterns, and code smells
    in code to help improve code quality and maintainability.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Pattern Detection Specialist")
        goal = kwargs.pop("goal", 
            "Identify design patterns, anti-patterns, and code smells in code "
            "to provide actionable recommendations for code improvement"
        )
        backstory = kwargs.pop("backstory",
            "You are a code quality expert with deep knowledge of design patterns, "
            "anti-patterns, and code smells. Your expertise helps teams identify "
            "both positive patterns to reinforce and negative patterns to eliminate."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                PatternDetectorTool(),
                CodeMetricsTool(),
                SummaryGeneratorTool()
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
        When detecting patterns:
        1. Identify positive design patterns and their usage
        2. Detect anti-patterns and their impact
        3. Find code smells and their root causes
        4. Assess pattern appropriateness for context
        5. Provide specific refactoring recommendations
        6. Prioritize issues by impact and effort
        """


@register_agent("insight_generator")
class InsightGeneratorAgent(PRSNLBaseAgent):
    """
    Insight Generator Agent
    
    Generates actionable insights and recommendations from code analysis.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Code Insight Generator")
        goal = kwargs.pop("goal", 
            "Generate actionable insights and strategic recommendations "
            "from code analysis to guide development decisions"
        )
        backstory = kwargs.pop("backstory",
            "You are a technical strategist who excels at translating code "
            "analysis data into actionable business and technical insights."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                CodeMetricsTool()
            ]
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )


@register_agent("security_analyst")
class SecurityAnalystAgent(PRSNLBaseAgent):
    """
    Security Analyst Agent
    
    Focuses on security analysis and vulnerability detection in code.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Security Analyst")
        goal = kwargs.pop("goal", 
            "Identify security vulnerabilities and provide security "
            "recommendations for code repositories"
        )
        backstory = kwargs.pop("backstory",
            "You are a cybersecurity expert specializing in code security "
            "analysis and vulnerability assessment."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            from app.tools.code_tools import SecurityScannerTool
            tools = [
                SecurityScannerTool(),
                SummaryGeneratorTool()
            ]
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )