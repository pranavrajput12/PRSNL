"""
Knowledge Curator Agent - Migrated to Crew.ai

This agent curates and organizes knowledge from diverse sources.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.web_tools import WebScraperTool, ContentAnalyzerTool
from app.tools.knowledge_tools import KnowledgeGraphTool, ConnectionFinderTool
from app.tools.ai_tools import EnhancementSuggestionTool

logger = logging.getLogger(__name__)


@register_agent("knowledge_curator")
class KnowledgeCuratorAgent(PRSNLBaseAgent):
    """
    Knowledge Curator Agent
    
    Specializes in curating, categorizing, and enriching knowledge
    from various sources to build a comprehensive knowledge base.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Knowledge Curator")
        goal = kwargs.pop("goal", 
            "Curate, categorize, and enrich knowledge from diverse sources "
            "to build a comprehensive and interconnected knowledge base"
        )
        backstory = kwargs.pop("backstory",
            "You are an expert knowledge curator with decades of experience "
            "in information science and knowledge management. You have a keen "
            "eye for identifying valuable information, creating meaningful "
            "connections, and organizing knowledge in ways that maximize "
            "understanding and discovery. Your expertise spans multiple domains, "
            "allowing you to see patterns and relationships that others might miss."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                WebScraperTool(),
                ContentAnalyzerTool(),
                KnowledgeGraphTool(),
                ConnectionFinderTool(),
                EnhancementSuggestionTool()
            ]
        
        # Call parent constructor
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
        
    def get_specialized_instructions(self) -> str:
        """Get specialized instructions for this agent"""
        return """
        When curating knowledge:
        1. Analyze content thoroughly for key themes and concepts
        2. Identify entities (people, organizations, technologies, concepts)
        3. Create meaningful categories and tags
        4. Find connections to existing knowledge
        5. Suggest enhancements and related topics
        6. Assess quality and reliability of information
        7. Generate comprehensive summaries at multiple levels
        8. Extract actionable insights and key takeaways
        
        Focus on creating a rich, interconnected knowledge structure
        that facilitates learning and discovery.
        """
    
    def calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate quality score for curated content"""
        score = 0.0
        
        # Score based on completeness
        if analysis.get("summary"):
            score += 0.2
        if analysis.get("key_points"):
            score += 0.2
        if analysis.get("entities"):
            score += 0.15
        if analysis.get("tags"):
            score += 0.15
        if analysis.get("category") != "uncategorized":
            score += 0.1
        
        # Score based on depth
        key_points_count = len(analysis.get("key_points", []))
        if key_points_count >= 5:
            score += 0.1
        elif key_points_count >= 3:
            score += 0.05
        
        # Score based on entity extraction
        entity_count = sum(len(v) for v in analysis.get("entities", {}).values())
        if entity_count >= 10:
            score += 0.1
        elif entity_count >= 5:
            score += 0.05
        
        return min(score, 1.0)
    
    def prepare_task_context(self, content: str, url: str, existing_tags: List[str]) -> Dict[str, Any]:
        """Prepare context for the curation task"""
        return {
            "content": content[:4000],  # Limit for AI processing
            "url": url,
            "existing_tags": existing_tags,
            "timestamp": datetime.utcnow().isoformat(),
            "specialized_instructions": self.get_specialized_instructions()
        }


@register_agent("knowledge_curator_enhanced")
class EnhancedKnowledgeCuratorAgent(KnowledgeCuratorAgent):
    """
    Enhanced version with additional capabilities for 
    complex knowledge curation scenarios
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add more sophisticated tools
        from app.tools.research_tools import AcademicSearchTool, CitationExtractorTool
        self.add_tool(AcademicSearchTool())
        self.add_tool(CitationExtractorTool())
        
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for advanced curation"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional advanced curation tasks:
        9. Extract and validate citations and references
        10. Identify academic sources and research papers
        11. Create bibliography and reading lists
        12. Assess scholarly impact and credibility
        13. Generate research summaries and literature reviews
        14. Identify research gaps and future directions
        """