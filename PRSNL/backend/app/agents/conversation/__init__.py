"""Conversation analysis Crew.ai agents"""

from app.agents.conversation.conversation_analyst import ConversationAnalystAgent
from app.agents.conversation.learning_analyzer import LearningAnalyzerAgent
from app.agents.conversation.insight_extractor import InsightExtractorAgent
from app.agents.conversation.knowledge_gap_detector import KnowledgeGapDetectorAgent, AdvancedKnowledgeGapDetectorAgent

__all__ = [
    'ConversationAnalystAgent',
    'LearningAnalyzerAgent',
    'InsightExtractorAgent',
    'KnowledgeGapDetectorAgent',
    'AdvancedKnowledgeGapDetectorAgent'
]