"""
Knowledge Curation Crew - Orchestrates knowledge-related agents

This crew handles all knowledge curation, organization, and enrichment tasks.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew
from app.agents.knowledge import (
    KnowledgeCuratorAgent,
    ResearchSynthesizerAgent,
    ContentExplorerAgent,
    LearningPathAgent
)

logger = logging.getLogger(__name__)


@register_crew("knowledge_curation")
class KnowledgeCurationCrew(PRSNLBaseCrew):
    """Crew for comprehensive knowledge curation"""
    
    def knowledge_curator(self) -> Agent:
        """Knowledge Curator agent"""
        agent_instance = KnowledgeCuratorAgent()
        return agent_instance.get_agent()
    
    @agent
    def research_synthesizer(self) -> Agent:
        """Research Synthesizer agent"""
        agent_instance = ResearchSynthesizerAgent()
        return agent_instance.get_agent()
    
    @agent
    def content_explorer(self) -> Agent:
        """Content Explorer agent"""
        agent_instance = ContentExplorerAgent()
        return agent_instance.get_agent()
    
    @agent
    def learning_path_creator(self) -> Agent:
        """Learning Path Creator agent"""
        agent_instance = LearningPathAgent()
        return agent_instance.get_agent()
    
    @task
    def curate_knowledge_task(self) -> Task:
        """Task for curating knowledge from a source"""
        return Task(
            description=(
                "Analyze and curate knowledge from the provided source. "
                "Extract key information, categorize content, identify entities, "
                "and create a comprehensive knowledge structure. "
                "Source: {source_url}"
            ),
            expected_output=(
                "A comprehensive knowledge curation report including:\n"
                "1. Categorization and tags\n"
                "2. Summary and key points\n"
                "3. Extracted entities and relationships\n"
                "4. Quality assessment\n"
                "5. Enhancement suggestions"
            ),
            agent=self.knowledge_curator()
        )
    
    @task
    def synthesize_research_task(self) -> Task:
        """Task for synthesizing research from multiple sources"""
        return Task(
            description=(
                "Synthesize research findings from the curated knowledge. "
                "Identify patterns, contradictions, and gaps. "
                "Create a coherent narrative that integrates all sources."
            ),
            expected_output=(
                "A research synthesis report including:\n"
                "1. Integrated findings\n"
                "2. Identified patterns and themes\n"
                "3. Contradictions and their resolution\n"
                "4. Knowledge gaps\n"
                "5. Recommendations for further research"
            ),
            agent=self.research_synthesizer()
        )
    
    @task
    def explore_related_content_task(self) -> Task:
        """Task for exploring related content"""
        return Task(
            description=(
                "Explore and discover related content based on the curated knowledge. "
                "Find additional sources, related topics, and complementary information."
            ),
            expected_output=(
                "A content exploration report including:\n"
                "1. Related topics and sources\n"
                "2. Complementary information\n"
                "3. Recommended reading list\n"
                "4. Knowledge expansion opportunities"
            ),
            agent=self.content_explorer()
        )
    
    @task
    def create_learning_path_task(self) -> Task:
        """Task for creating a learning path"""
        return Task(
            description=(
                "Create a structured learning path based on the curated and synthesized knowledge. "
                "Design a progression from basics to advanced topics."
            ),
            expected_output=(
                "A structured learning path including:\n"
                "1. Learning objectives\n"
                "2. Prerequisite knowledge\n"
                "3. Step-by-step progression\n"
                "4. Resources for each step\n"
                "5. Assessment checkpoints"
            ),
            agent=self.learning_path_creator()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Knowledge Curation crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "azure_openai",
                "config": {
                    "model": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    "api_key": settings.AZURE_OPENAI_API_KEY,
                    "api_base": settings.AZURE_OPENAI_ENDPOINT,
                    "api_version": settings.AZURE_OPENAI_API_VERSION
                }
            }
        )


@register_crew("deep_knowledge_analysis")
class DeepKnowledgeAnalysisCrew(KnowledgeCurationCrew):
    """Extended crew for deep knowledge analysis"""
    
    def get_process_type(self) -> str:
        """Use hierarchical process for complex analysis"""
        return "hierarchical"
    
    @task
    def deep_analysis_task(self) -> Task:
        """Task for deep knowledge analysis"""
        return Task(
            description=(
                "Perform deep analysis of the curated knowledge. "
                "Examine philosophical implications, theoretical frameworks, "
                "and interdisciplinary connections. Challenge assumptions "
                "and explore alternative perspectives."
            ),
            expected_output=(
                "A deep analysis report including:\n"
                "1. Theoretical frameworks applied\n"
                "2. Philosophical implications\n"
                "3. Interdisciplinary connections\n"
                "4. Alternative perspectives\n"
                "5. Critical evaluation"
            ),
            agent=self.research_synthesizer()  # Reuse for deep thinking
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Deep Knowledge Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks + [self.deep_analysis_task()],
            process=Process.hierarchical,
            manager_llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )


@register_crew("knowledge_web")
class KnowledgeWebCrew(PRSNLBaseCrew):
    """Crew for building interconnected knowledge webs"""
    
    @agent
    def web_builder(self) -> Agent:
        """Agent specialized in building knowledge connections"""
        from app.tools.knowledge_tools import KnowledgeGraphTool, ConnectionFinderTool
        
        return Agent(
            role="Knowledge Web Builder",
            goal="Build comprehensive knowledge webs with rich interconnections",
            backstory=(
                "You are a master of seeing connections between disparate pieces "
                "of information. Your expertise in graph theory and knowledge "
                "representation allows you to create rich, navigable knowledge structures."
            ),
            tools=[KnowledgeGraphTool(), ConnectionFinderTool()],
            llm=self.get_llm_config(),
            memory=True
        )
    
    @task
    def build_knowledge_web_task(self) -> Task:
        """Task for building knowledge web"""
        return Task(
            description=(
                "Build a comprehensive knowledge web from the provided content. "
                "Create nodes for key concepts, establish relationships, "
                "and identify connection patterns. Content: {content}"
            ),
            expected_output=(
                "A knowledge web structure including:\n"
                "1. Node definitions (concepts, entities)\n"
                "2. Relationship mappings\n"
                "3. Connection strength metrics\n"
                "4. Cluster identification\n"
                "5. Navigation recommendations"
            ),
            agent=self.web_builder()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Knowledge Web crew"""
        return Crew(
            agents=[self.web_builder()],
            tasks=[self.build_knowledge_web_task()],
            process=Process.sequential,
            verbose=True
        )