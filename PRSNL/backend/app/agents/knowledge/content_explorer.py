"""
Content Explorer Agent - Migrated to Crew.ai

This agent explores and discovers related content based on existing knowledge.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.web_tools import WebScraperTool, LinkExtractorTool
from app.tools.knowledge_tools import ConnectionFinderTool, TagSuggesterTool
from app.tools.ai_tools import EnhancementSuggestionTool

logger = logging.getLogger(__name__)


@register_agent("content_explorer")
class ContentExplorerAgent(PRSNLBaseAgent):
    """
    Content Explorer Agent
    
    Specializes in discovering and exploring related content,
    finding complementary information, and expanding knowledge boundaries.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Content Explorer")
        goal = kwargs.pop("goal", 
            "Discover and explore related content to expand knowledge boundaries, "
            "find complementary information, and identify new learning opportunities"
        )
        backstory = kwargs.pop("backstory",
            "You are a digital archaeologist and information explorer with an "
            "insatiable curiosity. Your talent for finding hidden connections "
            "and discovering relevant content in the vast digital landscape is "
            "unmatched. You have a sixth sense for identifying valuable information "
            "that others might overlook and a knack for following digital trails "
            "that lead to knowledge treasures."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                WebScraperTool(),
                LinkExtractorTool(),
                ConnectionFinderTool(),
                TagSuggesterTool(),
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
        When exploring content:
        1. Follow links and references to discover related material
        2. Identify content gaps and areas for expansion
        3. Find complementary perspectives and viewpoints
        4. Discover authoritative sources on the topic
        5. Explore adjacent fields and interdisciplinary connections
        6. Identify trending or emerging aspects of the topic
        7. Find practical applications and case studies
        8. Discover communities and experts in the field
        9. Locate multimedia content (videos, podcasts, infographics)
        10. Create a knowledge expansion roadmap
        
        Be thorough but focused, ensuring all discoveries are
        relevant and add value to the knowledge base.
        """
    
    def calculate_relevance_score(self, content: str, reference: str) -> float:
        """Calculate relevance score between content and reference"""
        # Simplified scoring - in practice would use embeddings
        score = 0.0
        
        content_lower = content.lower()
        reference_lower = reference.lower()
        
        # Extract key terms (simplified)
        content_terms = set(content_lower.split())
        reference_terms = set(reference_lower.split())
        
        # Calculate overlap
        overlap = len(content_terms & reference_terms)
        total = len(content_terms | reference_terms)
        
        if total > 0:
            score = overlap / total
        
        return min(score * 2, 1.0)  # Amplify and cap at 1.0
    
    def prioritize_discoveries(self, discoveries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize discovered content by relevance and value"""
        # Score each discovery
        for discovery in discoveries:
            score = 0.0
            
            # Relevance score
            score += discovery.get("relevance_score", 0) * 0.4
            
            # Authority score
            if discovery.get("source_type") == "academic":
                score += 0.2
            elif discovery.get("source_type") == "official":
                score += 0.15
            
            # Recency bonus
            if discovery.get("days_old", 365) < 90:
                score += 0.1
            
            # Multimedia bonus
            if discovery.get("has_media"):
                score += 0.1
            
            # Community engagement
            if discovery.get("engagement_score", 0) > 0.7:
                score += 0.1
            
            discovery["priority_score"] = score
        
        # Sort by priority score
        return sorted(discoveries, key=lambda x: x["priority_score"], reverse=True)
    
    def create_exploration_map(self, 
                             central_topic: str,
                             discovered_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a map of content exploration"""
        exploration_map = {
            "central_topic": central_topic,
            "layers": {
                "core": [],      # Directly related
                "adjacent": [],  # Related fields
                "frontier": []   # Emerging/experimental
            },
            "connections": [],
            "exploration_paths": []
        }
        
        # Categorize discoveries
        for content in discovered_content:
            relevance = content.get("relevance_score", 0)
            
            if relevance > 0.8:
                exploration_map["layers"]["core"].append(content)
            elif relevance > 0.5:
                exploration_map["layers"]["adjacent"].append(content)
            else:
                exploration_map["layers"]["frontier"].append(content)
        
        # Identify connections
        for i, content1 in enumerate(discovered_content):
            for content2 in discovered_content[i+1:]:
                if self._are_connected(content1, content2):
                    exploration_map["connections"].append({
                        "from": content1["title"],
                        "to": content2["title"],
                        "type": "related"
                    })
        
        # Suggest exploration paths
        exploration_map["exploration_paths"] = [
            {
                "name": "Depth-first",
                "description": "Explore core content thoroughly before expanding",
                "sequence": ["core", "adjacent", "frontier"]
            },
            {
                "name": "Breadth-first",
                "description": "Survey all layers before deep diving",
                "sequence": ["sample all", "identify interests", "deep dive"]
            },
            {
                "name": "Connection-following",
                "description": "Follow the strongest connections between content",
                "sequence": ["follow connections", "explore clusters"]
            }
        ]
        
        return exploration_map
    
    def _are_connected(self, content1: Dict, content2: Dict) -> bool:
        """Check if two pieces of content are connected"""
        # Simplified - check for shared tags or entities
        tags1 = set(content1.get("tags", []))
        tags2 = set(content2.get("tags", []))
        
        return len(tags1 & tags2) > 0


@register_agent("deep_web_explorer")
class DeepWebExplorerAgent(ContentExplorerAgent):
    """
    Enhanced version for deep web and specialized content exploration
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add specialized tools for deep exploration
        from app.tools.web_tools import DeepWebScraperTool, ArchiveSearchTool
        self.add_tool(DeepWebScraperTool())
        self.add_tool(ArchiveSearchTool())
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for deep exploration"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional deep exploration tasks:
        11. Search academic databases and repositories
        12. Explore archived versions of content
        13. Find content in specialized forums and communities
        14. Discover content in multiple languages
        15. Access open datasets and research data
        16. Find pre-prints and working papers
        17. Explore patent databases for related innovations
        18. Search government and NGO repositories
        """