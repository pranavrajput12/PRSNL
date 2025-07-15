"""
Research Synthesizer Agent - Migrated to Crew.ai

This agent synthesizes research from multiple sources into coherent insights.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool
from app.tools.knowledge_tools import KnowledgeGraphTool, ConnectionFinderTool
from app.tools.research_tools import CitationExtractorTool, SourceValidatorTool

logger = logging.getLogger(__name__)


@register_agent("research_synthesizer")
class ResearchSynthesizerAgent(PRSNLBaseAgent):
    """
    Research Synthesizer Agent
    
    Specializes in synthesizing research findings from multiple sources,
    identifying patterns, resolving contradictions, and creating coherent narratives.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Research Synthesizer")
        goal = kwargs.pop("goal", 
            "Synthesize research findings from multiple sources into coherent, "
            "actionable insights while identifying patterns, gaps, and contradictions"
        )
        backstory = kwargs.pop("backstory",
            "You are a distinguished research scientist with expertise in "
            "meta-analysis and systematic reviews. Your ability to see patterns "
            "across disparate studies and synthesize complex findings into "
            "clear narratives has made you a sought-after expert. You excel at "
            "identifying research gaps, resolving contradictions, and creating "
            "comprehensive literature reviews that advance understanding."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                KnowledgeGraphTool(),
                ConnectionFinderTool(),
                CitationExtractorTool(),
                SourceValidatorTool()
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
        When synthesizing research:
        1. Identify common themes and patterns across sources
        2. Note contradictions and attempt to resolve them
        3. Assess the quality and reliability of each source
        4. Create a coherent narrative that integrates findings
        5. Identify research gaps and unanswered questions
        6. Extract and validate citations
        7. Build a knowledge graph of concepts and relationships
        8. Provide actionable insights and recommendations
        9. Suggest areas for future research
        
        Focus on creating synthesis that advances understanding
        and provides clear direction for knowledge application.
        """
    
    def assess_source_quality(self, source_metadata: Dict[str, Any]) -> float:
        """Assess the quality of a research source"""
        score = 0.0
        
        # Check for key quality indicators
        if source_metadata.get("peer_reviewed"):
            score += 0.3
        if source_metadata.get("citations_count", 0) > 10:
            score += 0.2
        if source_metadata.get("journal_impact_factor", 0) > 2.0:
            score += 0.2
        if source_metadata.get("methodology_score", 0) > 0.7:
            score += 0.2
        if source_metadata.get("recency_years", 10) < 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def identify_contradictions(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify contradictions in research findings"""
        contradictions = []
        
        # Simple contradiction detection based on opposing claims
        for i, finding1 in enumerate(findings):
            for finding2 in findings[i+1:]:
                if self._are_contradictory(finding1, finding2):
                    contradictions.append({
                        "finding1": finding1,
                        "finding2": finding2,
                        "type": "direct_contradiction",
                        "resolution_suggestion": self._suggest_resolution(finding1, finding2)
                    })
        
        return contradictions
    
    def _are_contradictory(self, finding1: Dict, finding2: Dict) -> bool:
        """Check if two findings are contradictory"""
        # Simplified logic - in practice would use more sophisticated NLP
        claim1 = finding1.get("claim", "").lower()
        claim2 = finding2.get("claim", "").lower()
        
        # Check for opposing keywords
        opposing_pairs = [
            ("increase", "decrease"),
            ("positive", "negative"),
            ("effective", "ineffective"),
            ("significant", "insignificant")
        ]
        
        for word1, word2 in opposing_pairs:
            if (word1 in claim1 and word2 in claim2) or (word2 in claim1 and word1 in claim2):
                return True
        
        return False
    
    def _suggest_resolution(self, finding1: Dict, finding2: Dict) -> str:
        """Suggest resolution for contradictory findings"""
        return (
            "Consider contextual differences, methodological variations, "
            "or population differences that might explain the contradiction."
        )


@register_agent("academic_research_synthesizer")
class AcademicResearchSynthesizerAgent(ResearchSynthesizerAgent):
    """
    Enhanced version specialized for academic research synthesis
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add academic-specific tools
        from app.tools.research_tools import AcademicSearchTool, PeerReviewAnalyzerTool
        self.add_tool(AcademicSearchTool())
        self.add_tool(PeerReviewAnalyzerTool())
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for academic synthesis"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional academic synthesis tasks:
        10. Evaluate methodology rigor and statistical validity
        11. Assess peer review quality and journal reputation
        12. Create formal literature review sections
        13. Generate proper academic citations (APA/MLA/Chicago)
        14. Identify seminal papers and trace citation networks
        15. Evaluate reproducibility and replication status
        16. Assess conflicts of interest and funding sources
        """
    
    def create_literature_review_structure(self) -> Dict[str, List[str]]:
        """Create structure for formal literature review"""
        return {
            "introduction": [
                "Research question and objectives",
                "Scope and limitations",
                "Search methodology"
            ],
            "theoretical_framework": [
                "Key theories and models",
                "Evolution of understanding",
                "Current paradigms"
            ],
            "methodology_review": [
                "Common methodologies",
                "Strengths and limitations",
                "Emerging approaches"
            ],
            "findings_synthesis": [
                "Major findings by theme",
                "Contradictions and resolutions",
                "Consensus areas"
            ],
            "gaps_and_future": [
                "Identified research gaps",
                "Future research directions",
                "Methodological recommendations"
            ],
            "conclusion": [
                "Key takeaways",
                "Practical implications",
                "Theoretical contributions"
            ]
        }