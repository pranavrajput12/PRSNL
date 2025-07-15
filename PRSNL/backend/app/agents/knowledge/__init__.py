"""Knowledge-related Crew.ai agents"""

from app.agents.knowledge.knowledge_curator import KnowledgeCuratorAgent
from app.agents.knowledge.research_synthesizer import ResearchSynthesizerAgent
from app.agents.knowledge.content_explorer import ContentExplorerAgent
from app.agents.knowledge.learning_path import LearningPathAgent

__all__ = [
    'KnowledgeCuratorAgent',
    'ResearchSynthesizerAgent', 
    'ContentExplorerAgent',
    'LearningPathAgent'
]