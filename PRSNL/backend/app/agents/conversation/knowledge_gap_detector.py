"""
Knowledge Gap Detector Agent - Migrated to Crew.ai

This agent identifies knowledge gaps and learning opportunities from conversations.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool, QuestionGeneratorTool
from app.tools.knowledge_tools import ConnectionFinderTool, KnowledgeGraphTool

logger = logging.getLogger(__name__)


@register_agent("knowledge_gap_detector")
class KnowledgeGapDetectorAgent(PRSNLBaseAgent):
    """
    Knowledge Gap Detector Agent
    
    Specializes in identifying knowledge gaps, learning opportunities,
    and areas where understanding can be improved in conversations.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Knowledge Gap Detector")
        goal = kwargs.pop("goal", 
            "Identify knowledge gaps and learning opportunities from conversations "
            "to enhance understanding and support continuous learning"
        )
        backstory = kwargs.pop("backstory",
            "You are a learning specialist and knowledge engineer who excels at "
            "identifying gaps in understanding and knowledge. Your expertise lies "
            "in recognizing where additional information, clarification, or "
            "learning is needed to improve comprehension and decision-making. "
            "You help organizations and individuals identify what they don't know "
            "and create pathways for addressing these gaps."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                QuestionGeneratorTool(),
                ConnectionFinderTool(),
                KnowledgeGraphTool()
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
        When identifying knowledge gaps:
        1. Identify unanswered questions and unresolved topics
        2. Recognize areas where more information is needed
        3. Identify assumptions that need validation
        4. Detect incomplete explanations or reasoning
        5. Recognize missing context or background information
        6. Identify areas where expertise is lacking
        7. Detect contradictions or conflicting information
        8. Recognize opportunities for deeper understanding
        9. Identify missing connections between concepts
        10. Detect areas where clarification is needed
        11. Recognize learning opportunities and skill gaps
        12. Identify research needs and information sources
        """
    
    def detect_knowledge_gaps(self, conversation: str) -> Dict[str, Any]:
        """Detect various types of knowledge gaps in the conversation"""
        gaps = {
            "unanswered_questions": [],
            "incomplete_explanations": [],
            "missing_context": [],
            "assumptions_needing_validation": [],
            "conflicting_information": [],
            "expertise_gaps": [],
            "learning_opportunities": [],
            "research_needs": []
        }
        
        # Detect unanswered questions
        question_indicators = ["?", "not sure", "don't know", "unclear", "uncertain"]
        for indicator in question_indicators:
            if indicator in conversation.lower():
                gaps["unanswered_questions"].append(f"Question indicator: {indicator}")
        
        # Detect incomplete explanations
        incomplete_indicators = ["partially", "somewhat", "to some extent", "I think", "maybe"]
        for indicator in incomplete_indicators:
            if indicator in conversation.lower():
                gaps["incomplete_explanations"].append(f"Incomplete: {indicator}")
        
        # Detect missing context
        context_indicators = ["background", "context", "history", "previous", "earlier"]
        for indicator in context_indicators:
            if indicator in conversation.lower():
                gaps["missing_context"].append(f"Context need: {indicator}")
        
        # Detect assumptions
        assumption_indicators = ["assume", "presumably", "probably", "I believe"]
        for indicator in assumption_indicators:
            if indicator in conversation.lower():
                gaps["assumptions_needing_validation"].append(f"Assumption: {indicator}")
        
        # Detect conflicts
        conflict_indicators = ["but", "however", "on the other hand", "disagree", "contradiction"]
        for indicator in conflict_indicators:
            if indicator in conversation.lower():
                gaps["conflicting_information"].append(f"Conflict: {indicator}")
        
        # Detect expertise gaps
        expertise_indicators = ["expert", "specialist", "need help", "don't understand"]
        for indicator in expertise_indicators:
            if indicator in conversation.lower():
                gaps["expertise_gaps"].append(f"Expertise need: {indicator}")
        
        # Detect learning opportunities
        learning_indicators = ["learn", "understand", "study", "research", "investigate"]
        for indicator in learning_indicators:
            if indicator in conversation.lower():
                gaps["learning_opportunities"].append(f"Learning: {indicator}")
        
        return gaps
    
    def identify_information_needs(self, conversation: str) -> Dict[str, Any]:
        """Identify specific information needs from the conversation"""
        needs = {
            "factual_information": [],
            "procedural_knowledge": [],
            "conceptual_understanding": [],
            "technical_details": [],
            "best_practices": [],
            "case_studies": [],
            "expert_opinions": [],
            "data_and_metrics": []
        }
        
        # Factual information needs
        fact_indicators = ["what is", "define", "explain", "facts about"]
        for indicator in fact_indicators:
            if indicator in conversation.lower():
                needs["factual_information"].append(f"Fact need: {indicator}")
        
        # Procedural knowledge needs
        procedure_indicators = ["how to", "steps", "process", "method", "procedure"]
        for indicator in procedure_indicators:
            if indicator in conversation.lower():
                needs["procedural_knowledge"].append(f"Procedure need: {indicator}")
        
        # Conceptual understanding needs
        concept_indicators = ["concept", "theory", "principle", "understanding", "why"]
        for indicator in concept_indicators:
            if indicator in conversation.lower():
                needs["conceptual_understanding"].append(f"Concept need: {indicator}")
        
        # Technical details needs
        technical_indicators = ["technical", "implementation", "architecture", "code"]
        for indicator in technical_indicators:
            if indicator in conversation.lower():
                needs["technical_details"].append(f"Technical need: {indicator}")
        
        # Best practices needs
        practice_indicators = ["best practice", "recommendation", "guideline", "standard"]
        for indicator in practice_indicators:
            if indicator in conversation.lower():
                needs["best_practices"].append(f"Practice need: {indicator}")
        
        # Case studies needs
        case_indicators = ["example", "case study", "real-world", "experience"]
        for indicator in case_indicators:
            if indicator in conversation.lower():
                needs["case_studies"].append(f"Case need: {indicator}")
        
        # Expert opinions needs
        expert_indicators = ["expert opinion", "advice", "recommendation", "guidance"]
        for indicator in expert_indicators:
            if indicator in conversation.lower():
                needs["expert_opinions"].append(f"Expert need: {indicator}")
        
        # Data and metrics needs
        data_indicators = ["data", "metrics", "statistics", "numbers", "measurement"]
        for indicator in data_indicators:
            if indicator in conversation.lower():
                needs["data_and_metrics"].append(f"Data need: {indicator}")
        
        return needs
    
    def generate_learning_recommendations(self, gaps: Dict[str, Any], needs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate learning recommendations based on identified gaps and needs"""
        recommendations = {
            "immediate_actions": [],
            "research_topics": [],
            "learning_resources": [],
            "expert_consultations": [],
            "skill_development": [],
            "knowledge_sharing": [],
            "follow_up_questions": []
        }
        
        # Generate immediate actions
        if gaps.get("unanswered_questions"):
            recommendations["immediate_actions"].append("Address unanswered questions first")
        
        if gaps.get("conflicting_information"):
            recommendations["immediate_actions"].append("Resolve conflicting information")
        
        # Generate research topics
        if needs.get("factual_information"):
            recommendations["research_topics"].append("Factual information research needed")
        
        if needs.get("technical_details"):
            recommendations["research_topics"].append("Technical deep-dive required")
        
        # Generate learning resources
        if needs.get("conceptual_understanding"):
            recommendations["learning_resources"].append("Conceptual learning materials")
        
        if needs.get("procedural_knowledge"):
            recommendations["learning_resources"].append("Step-by-step guides and tutorials")
        
        # Generate expert consultations
        if gaps.get("expertise_gaps"):
            recommendations["expert_consultations"].append("Subject matter expert consultation")
        
        if needs.get("expert_opinions"):
            recommendations["expert_consultations"].append("Expert opinion gathering")
        
        # Generate skill development
        if gaps.get("learning_opportunities"):
            recommendations["skill_development"].append("Skill building opportunities")
        
        # Generate knowledge sharing
        if gaps.get("incomplete_explanations"):
            recommendations["knowledge_sharing"].append("Knowledge sharing sessions")
        
        # Generate follow-up questions
        recommendations["follow_up_questions"] = [
            "What specific information is missing?",
            "Who are the subject matter experts?",
            "What are the priority learning areas?",
            "How can we validate assumptions?",
            "What resources are available?",
            "What is the timeline for addressing gaps?"
        ]
        
        return recommendations
    
    def prioritize_gaps(self, gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize knowledge gaps by impact and urgency"""
        prioritized = []
        
        # High priority gaps
        high_priority_types = ["conflicting_information", "expertise_gaps", "unanswered_questions"]
        for gap_type in high_priority_types:
            if gaps.get(gap_type):
                prioritized.append({
                    "type": gap_type,
                    "priority": "high",
                    "items": gaps[gap_type],
                    "rationale": "Critical for decision-making and understanding"
                })
        
        # Medium priority gaps
        medium_priority_types = ["incomplete_explanations", "assumptions_needing_validation"]
        for gap_type in medium_priority_types:
            if gaps.get(gap_type):
                prioritized.append({
                    "type": gap_type,
                    "priority": "medium",
                    "items": gaps[gap_type],
                    "rationale": "Important for quality and accuracy"
                })
        
        # Low priority gaps
        low_priority_types = ["missing_context", "learning_opportunities", "research_needs"]
        for gap_type in low_priority_types:
            if gaps.get(gap_type):
                prioritized.append({
                    "type": gap_type,
                    "priority": "low",
                    "items": gaps[gap_type],
                    "rationale": "Beneficial for long-term improvement"
                })
        
        return prioritized
    
    def create_knowledge_gap_report(self, conversation: str) -> Dict[str, Any]:
        """Create a comprehensive knowledge gap report"""
        gaps = self.detect_knowledge_gaps(conversation)
        needs = self.identify_information_needs(conversation)
        recommendations = self.generate_learning_recommendations(gaps, needs)
        prioritized = self.prioritize_gaps(gaps)
        
        report = {
            "summary": {
                "total_gaps_identified": sum(len(gap_list) for gap_list in gaps.values()),
                "total_information_needs": sum(len(need_list) for need_list in needs.values()),
                "priority_gaps": len([p for p in prioritized if p["priority"] == "high"])
            },
            "knowledge_gaps": gaps,
            "information_needs": needs,
            "recommendations": recommendations,
            "prioritized_gaps": prioritized,
            "next_steps": [
                "Address high-priority gaps first",
                "Gather required information and expertise",
                "Validate assumptions and resolve conflicts",
                "Create learning and development plan",
                "Establish knowledge sharing mechanisms"
            ]
        }
        
        return report


@register_agent("advanced_knowledge_gap_detector")
class AdvancedKnowledgeGapDetectorAgent(KnowledgeGapDetectorAgent):
    """
    Advanced Knowledge Gap Detector with enhanced capabilities
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Enhanced backstory for advanced capabilities
        self.backstory += (
            " You have advanced capabilities in knowledge graph analysis, "
            "semantic understanding, and can identify subtle gaps that "
            "others might miss. Your expertise includes organizational "
            "learning patterns and knowledge management strategies."
        )
    
    def get_specialized_instructions(self) -> str:
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Advanced knowledge gap detection:
        13. Identify systemic knowledge gaps across teams
        14. Recognize organizational learning patterns
        15. Detect knowledge silos and sharing barriers
        16. Identify critical knowledge dependencies
        17. Recognize knowledge decay and obsolescence
        18. Detect expertise concentration risks
        19. Identify knowledge transfer needs
        20. Recognize learning culture gaps
        """
    
    def analyze_knowledge_ecosystem(self, conversation: str) -> Dict[str, Any]:
        """Analyze the broader knowledge ecosystem"""
        ecosystem = {
            "knowledge_sources": [],
            "knowledge_flows": [],
            "knowledge_barriers": [],
            "knowledge_brokers": [],
            "knowledge_repositories": [],
            "learning_networks": []
        }
        
        # Identify knowledge sources
        source_indicators = ["expert", "documentation", "database", "system", "repository"]
        for indicator in source_indicators:
            if indicator in conversation.lower():
                ecosystem["knowledge_sources"].append(f"Source: {indicator}")
        
        # Identify knowledge flows
        flow_indicators = ["shared", "communicated", "transferred", "documented"]
        for indicator in flow_indicators:
            if indicator in conversation.lower():
                ecosystem["knowledge_flows"].append(f"Flow: {indicator}")
        
        # Identify barriers
        barrier_indicators = ["silo", "isolated", "restricted", "limited access"]
        for indicator in barrier_indicators:
            if indicator in conversation.lower():
                ecosystem["knowledge_barriers"].append(f"Barrier: {indicator}")
        
        return ecosystem