"""
Conversation Analyst Agent - Migrated to Crew.ai

This agent analyzes conversations to extract insights, patterns, and knowledge.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.ai_tools import (
    SummaryGeneratorTool,
    EntityExtractorTool,
    TagSuggesterTool,
    QuestionGeneratorTool
)
from app.tools.knowledge_tools import ConnectionFinderTool

logger = logging.getLogger(__name__)


@register_agent("conversation_analyst")
class ConversationAnalystAgent(PRSNLBaseAgent):
    """
    Conversation Analyst Agent
    
    Specializes in analyzing conversations to extract insights,
    identify patterns, and create structured knowledge from dialogue.
    """
    
    def __init__(self, **kwargs):
        role = kwargs.pop("role", "Conversation Analyst")
        goal = kwargs.pop("goal", 
            "Analyze conversations to extract insights, identify patterns, "
            "and transform dialogue into structured, actionable knowledge"
        )
        backstory = kwargs.pop("backstory",
            "You are an expert in conversation analysis and natural language "
            "understanding. Your ability to identify subtle patterns, extract "
            "key insights, and understand the deeper meaning in human dialogue "
            "makes you invaluable for knowledge extraction from conversations. "
            "You excel at seeing beyond the surface level to understand intent, "
            "emotions, and the underlying knowledge being shared."
        )
        
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                TagSuggesterTool(),
                QuestionGeneratorTool(),
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
        When analyzing conversations:
        1. Identify key topics and themes discussed
        2. Extract important insights and conclusions
        3. Recognize decision points and outcomes
        4. Identify questions asked and answers provided
        5. Detect emotional undertones and context
        6. Find patterns in communication style
        7. Extract actionable items and commitments
        8. Identify knowledge gaps and learning opportunities
        9. Recognize expertise levels and authority
        10. Map relationship dynamics and influences
        11. Create structured summaries and takeaways
        12. Generate follow-up questions and actions
        
        Focus on extracting maximum value from conversational
        content while preserving context and nuance.
        """
    
    def analyze_conversation_structure(self, conversation: str) -> Dict[str, Any]:
        """Analyze the structure and flow of a conversation"""
        structure = {
            "conversation_type": "unknown",
            "participant_count": 0,
            "turn_taking_pattern": "balanced",
            "topic_progression": [],
            "decision_points": [],
            "information_flow": "bidirectional",
            "engagement_level": "medium"
        }
        
        # Simple analysis based on conversation markers
        if "Q:" in conversation and "A:" in conversation:
            structure["conversation_type"] = "q_and_a"
            structure["information_flow"] = "unidirectional"
        elif "meeting" in conversation.lower() or "agenda" in conversation.lower():
            structure["conversation_type"] = "meeting"
        elif "interview" in conversation.lower():
            structure["conversation_type"] = "interview"
        elif "discussion" in conversation.lower():
            structure["conversation_type"] = "discussion"
        
        # Count participants (simplified)
        participant_indicators = ["Person A", "Person B", "Speaker", "Participant"]
        structure["participant_count"] = sum(1 for indicator in participant_indicators if indicator in conversation)
        
        # Detect decision points
        decision_keywords = ["decided", "agreed", "resolved", "concluded", "determined"]
        for keyword in decision_keywords:
            if keyword in conversation.lower():
                structure["decision_points"].append(f"Decision point involving {keyword}")
        
        return structure
    
    def extract_conversation_insights(self, conversation: str) -> Dict[str, Any]:
        """Extract key insights from the conversation"""
        insights = {
            "key_topics": [],
            "main_insights": [],
            "action_items": [],
            "decisions_made": [],
            "questions_raised": [],
            "expertise_demonstrated": [],
            "learning_moments": [],
            "conflicts_or_disagreements": []
        }
        
        # Extract key topics (simplified keyword extraction)
        topic_keywords = ["about", "regarding", "concerning", "topic", "subject"]
        for keyword in topic_keywords:
            if keyword in conversation.lower():
                insights["key_topics"].append(f"Topic related to {keyword}")
        
        # Extract action items
        action_keywords = ["need to", "should", "must", "will", "going to", "action"]
        for keyword in action_keywords:
            if keyword in conversation.lower():
                insights["action_items"].append(f"Action item: {keyword}")
        
        # Extract decisions
        decision_keywords = ["decided", "agreed", "resolved", "concluded"]
        for keyword in decision_keywords:
            if keyword in conversation.lower():
                insights["decisions_made"].append(f"Decision: {keyword}")
        
        # Extract questions
        question_indicators = ["?", "what", "how", "why", "when", "where", "who"]
        for indicator in question_indicators:
            if indicator in conversation.lower():
                insights["questions_raised"].append(f"Question involving {indicator}")
        
        return insights
    
    def analyze_participant_dynamics(self, conversation: str) -> Dict[str, Any]:
        """Analyze dynamics between conversation participants"""
        dynamics = {
            "communication_style": {},
            "influence_patterns": {},
            "expertise_levels": {},
            "engagement_patterns": {},
            "collaboration_indicators": []
        }
        
        # Simplified analysis
        if "I think" in conversation:
            dynamics["communication_style"]["opinion_sharing"] = "present"
        if "I know" in conversation:
            dynamics["communication_style"]["knowledge_assertion"] = "present"
        if "question" in conversation.lower():
            dynamics["communication_style"]["inquiry"] = "present"
        
        # Detect collaboration
        collaboration_keywords = ["together", "collaborate", "team", "we", "us"]
        for keyword in collaboration_keywords:
            if keyword in conversation.lower():
                dynamics["collaboration_indicators"].append(f"Collaboration: {keyword}")
        
        return dynamics
    
    def identify_knowledge_transfer(self, conversation: str) -> Dict[str, Any]:
        """Identify knowledge transfer patterns in the conversation"""
        transfer_patterns = {
            "teaching_moments": [],
            "learning_indicators": [],
            "knowledge_sharing": [],
            "expertise_demonstration": [],
            "clarification_requests": [],
            "knowledge_gaps": []
        }
        
        # Teaching moments
        teaching_keywords = ["let me explain", "here's how", "the way to", "you should"]
        for keyword in teaching_keywords:
            if keyword in conversation.lower():
                transfer_patterns["teaching_moments"].append(f"Teaching: {keyword}")
        
        # Learning indicators
        learning_keywords = ["I learned", "now I understand", "I see", "that makes sense"]
        for keyword in learning_keywords:
            if keyword in conversation.lower():
                transfer_patterns["learning_indicators"].append(f"Learning: {keyword}")
        
        # Knowledge sharing
        sharing_keywords = ["I found", "in my experience", "from what I know"]
        for keyword in sharing_keywords:
            if keyword in conversation.lower():
                transfer_patterns["knowledge_sharing"].append(f"Sharing: {keyword}")
        
        # Clarification requests
        clarification_keywords = ["can you clarify", "what do you mean", "I don't understand"]
        for keyword in clarification_keywords:
            if keyword in conversation.lower():
                transfer_patterns["clarification_requests"].append(f"Clarification: {keyword}")
        
        return transfer_patterns
    
    def generate_conversation_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the conversation"""
        summary = {
            "overview": "",
            "key_points": [],
            "outcomes": [],
            "participants": [],
            "topics_covered": [],
            "action_items": [],
            "follow_up_needed": [],
            "knowledge_gained": []
        }
        
        # Generate overview
        conversation_type = analysis_results.get("structure", {}).get("conversation_type", "discussion")
        participant_count = analysis_results.get("structure", {}).get("participant_count", 2)
        
        summary["overview"] = (
            f"This {conversation_type} involved {participant_count} participants "
            f"discussing various topics with knowledge sharing and decision-making."
        )
        
        # Extract key points from insights
        insights = analysis_results.get("insights", {})
        summary["key_points"] = insights.get("main_insights", [])
        summary["outcomes"] = insights.get("decisions_made", [])
        summary["action_items"] = insights.get("action_items", [])
        
        # Extract knowledge transfer information
        transfer = analysis_results.get("knowledge_transfer", {})
        summary["knowledge_gained"] = transfer.get("learning_indicators", [])
        
        return summary


@register_agent("technical_conversation_analyst")
class TechnicalConversationAnalystAgent(ConversationAnalystAgent):
    """
    Specialized agent for analyzing technical conversations
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add technical context
        self.backstory += (
            " You have additional expertise in technical communication patterns, "
            "code discussions, and technical problem-solving conversations."
        )
    
    def get_specialized_instructions(self) -> str:
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional technical conversation analysis:
        13. Identify technical concepts and terminology
        14. Recognize code-related discussions
        15. Extract technical solutions and approaches
        16. Identify technical challenges and blockers
        17. Recognize architecture and design discussions
        18. Extract technical requirements and specifications
        19. Identify technical debt and improvement opportunities
        20. Recognize technical expertise and authority
        """
    
    def analyze_technical_content(self, conversation: str) -> Dict[str, Any]:
        """Analyze technical content in the conversation"""
        technical_analysis = {
            "technical_topics": [],
            "code_discussions": [],
            "technical_solutions": [],
            "technical_challenges": [],
            "tools_mentioned": [],
            "technical_decisions": []
        }
        
        # Technical keywords
        technical_keywords = ["code", "algorithm", "architecture", "database", "API", "framework"]
        for keyword in technical_keywords:
            if keyword in conversation.lower():
                technical_analysis["technical_topics"].append(keyword)
        
        # Code discussions
        code_indicators = ["function", "class", "method", "variable", "bug", "debug"]
        for indicator in code_indicators:
            if indicator in conversation.lower():
                technical_analysis["code_discussions"].append(indicator)
        
        # Tools mentioned
        tool_keywords = ["git", "docker", "kubernetes", "jenkins", "aws", "azure"]
        for tool in tool_keywords:
            if tool in conversation.lower():
                technical_analysis["tools_mentioned"].append(tool)
        
        return technical_analysis