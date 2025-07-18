"""
Conversation Intelligence Crew - Orchestrates conversation analysis workflows

This crew handles comprehensive conversation analysis including participant dynamics,
learning patterns, actionable insights, and knowledge gap identification.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew
from app.agents.conversation import (
    ConversationAnalystAgent,
    LearningAnalyzerAgent,
    InsightExtractorAgent,
    KnowledgeGapDetectorAgent,
    AdvancedKnowledgeGapDetectorAgent
)
from app.config import settings

logger = logging.getLogger(__name__)


@register_crew("conversation_intelligence")
class ConversationIntelligenceCrew(PRSNLBaseCrew):
    """Crew for comprehensive conversation analysis and intelligence extraction"""
    
    @agent
    def conversation_analyst(self) -> Agent:
        """Conversation Analyst agent"""
        agent_instance = ConversationAnalystAgent()
        return agent_instance.get_agent()
    
    @agent
    def learning_analyzer(self) -> Agent:
        """Learning Analyzer agent"""
        agent_instance = LearningAnalyzerAgent()
        return agent_instance.get_agent()
    
    @agent
    def insight_extractor(self) -> Agent:
        """Insight Extractor agent"""
        agent_instance = InsightExtractorAgent()
        return agent_instance.get_agent()
    
    @agent
    def knowledge_gap_detector(self) -> Agent:
        """Knowledge Gap Detector agent"""
        agent_instance = KnowledgeGapDetectorAgent()
        return agent_instance.get_agent()
    
    @task
    def analyze_conversation_task(self) -> Task:
        """Task for analyzing conversation structure and content"""
        return Task(
            description=(
                "Analyze the conversation to extract insights, identify patterns, "
                "and understand participant dynamics. Focus on key topics, "
                "decision points, and information flow. Conversation: {conversation_text}"
            ),
            expected_output=(
                "Comprehensive conversation analysis including:\n"
                "1. Conversation structure and type identification\n"
                "2. Participant dynamics and communication patterns\n"
                "3. Key topics and themes discussed\n"
                "4. Decision points and outcomes\n"
                "5. Information flow and knowledge transfer\n"
                "6. Emotional undertones and engagement levels\n"
                "7. Action items and commitments identified\n"
                "8. Structured summary with key takeaways"
            ),
            agent=self.conversation_analyst()
        )
    
    @task
    def analyze_learning_patterns_task(self) -> Task:
        """Task for analyzing learning patterns and progression"""
        return Task(
            description=(
                "Analyze the conversation for learning patterns, knowledge "
                "acquisition, and skill development indicators. Identify "
                "learning objectives, outcomes, and progression patterns."
            ),
            expected_output=(
                "Learning pattern analysis including:\n"
                "1. Learning objectives and outcomes identified\n"
                "2. Knowledge acquisition progression tracking\n"
                "3. Skill development indicators\n"
                "4. Misconceptions and corrections\n"
                "5. Questioning patterns and curiosity indicators\n"
                "6. Teaching and mentoring moments\n"
                "7. Confidence levels and uncertainty patterns\n"
                "8. Learning preferences and styles\n"
                "9. Knowledge retention indicators"
            ),
            agent=self.learning_analyzer()
        )
    
    @task
    def extract_insights_task(self) -> Task:
        """Task for extracting actionable insights and knowledge"""
        return Task(
            description=(
                "Extract actionable insights and valuable knowledge from the "
                "conversation analysis. Focus on business intelligence, "
                "strategic recommendations, and decision support."
            ),
            expected_output=(
                "Actionable insights report including:\n"
                "1. Strategic insights and business intelligence\n"
                "2. Actionable recommendations prioritized\n"
                "3. Problem-solving approaches identified\n"
                "4. Innovation opportunities recognized\n"
                "5. Lessons learned and best practices\n"
                "6. Success factors and enablers\n"
                "7. Risk assessment and mitigation strategies\n"
                "8. Knowledge assets and intellectual property\n"
                "9. Improvement opportunities and next steps"
            ),
            agent=self.insight_extractor()
        )
    
    @task
    def identify_knowledge_gaps_task(self) -> Task:
        """Task for identifying knowledge gaps and learning opportunities"""
        return Task(
            description=(
                "Identify knowledge gaps, learning opportunities, and areas "
                "where additional information or expertise is needed. Generate "
                "recommendations for addressing these gaps."
            ),
            expected_output=(
                "Knowledge gap analysis including:\n"
                "1. Unanswered questions and unresolved topics\n"
                "2. Information needs and research requirements\n"
                "3. Expertise gaps and consultation needs\n"
                "4. Learning opportunities and skill development areas\n"
                "5. Assumptions requiring validation\n"
                "6. Conflicting information requiring resolution\n"
                "7. Missing context and background information\n"
                "8. Prioritized gap remediation recommendations\n"
                "9. Learning and development action plan"
            ),
            agent=self.knowledge_gap_detector()
        )
    
    @task
    def synthesize_intelligence_task(self) -> Task:
        """Task for synthesizing all analysis into comprehensive intelligence"""
        return Task(
            description=(
                "Synthesize all conversation analysis results into a comprehensive "
                "intelligence report. Integrate insights from conversation analysis, "
                "learning patterns, actionable insights, and knowledge gaps to "
                "provide holistic understanding and strategic recommendations."
            ),
            expected_output=(
                "Comprehensive conversation intelligence report including:\n"
                "1. Executive summary of key findings\n"
                "2. Integrated analysis of conversation dynamics\n"
                "3. Learning and development insights\n"
                "4. Strategic recommendations and action items\n"
                "5. Knowledge management recommendations\n"
                "6. Risk assessment and mitigation strategies\n"
                "7. Follow-up questions and investigation needs\n"
                "8. Long-term implications and opportunities\n"
                "9. Implementation roadmap with priorities"
            ),
            agent=self.conversation_analyst()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Conversation Intelligence crew"""
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


@register_crew("advanced_conversation_intelligence")
class AdvancedConversationIntelligenceCrew(ConversationIntelligenceCrew):
    """Enhanced crew for advanced conversation intelligence with specialized agents"""
    
    @agent
    def advanced_conversation_analyst(self) -> Agent:
        """Advanced Conversation Analyst agent"""
        from app.agents.conversation.conversation_analyst import TechnicalConversationAnalystAgent
        agent_instance = TechnicalConversationAnalystAgent()
        return agent_instance.get_agent()
    
    @agent
    def advanced_knowledge_gap_detector(self) -> Agent:
        """Advanced Knowledge Gap Detector agent"""
        agent_instance = AdvancedKnowledgeGapDetectorAgent()
        return agent_instance.get_agent()
    
    @agent
    def conversation_strategist(self) -> Agent:
        """Conversation Strategist agent for high-level strategic analysis"""
        return Agent(
            role="Conversation Strategist",
            goal="Provide strategic analysis and recommendations based on conversation intelligence",
            backstory=(
                "You are a strategic analyst who specializes in extracting "
                "business value from conversation intelligence. Your expertise "
                "lies in connecting conversation insights to business outcomes "
                "and organizational strategy."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @task
    def strategic_analysis_task(self) -> Task:
        """Task for strategic analysis and business impact assessment"""
        return Task(
            description=(
                "Perform strategic analysis of the conversation intelligence "
                "to identify business impact, competitive advantages, and "
                "organizational implications. Focus on strategic value creation."
            ),
            expected_output=(
                "Strategic analysis report including:\n"
                "1. Business impact assessment\n"
                "2. Competitive advantage identification\n"
                "3. Organizational learning implications\n"
                "4. Strategic opportunity assessment\n"
                "5. Resource allocation recommendations\n"
                "6. Innovation potential evaluation\n"
                "7. Risk and opportunity matrix\n"
                "8. Strategic implementation roadmap"
            ),
            agent=self.conversation_strategist()
        )
    
    @task
    def technical_conversation_analysis_task(self) -> Task:
        """Task for technical conversation analysis"""
        return Task(
            description=(
                "Analyze technical aspects of the conversation including "
                "technical concepts, code discussions, architecture patterns, "
                "and technical decision-making processes."
            ),
            expected_output=(
                "Technical conversation analysis including:\n"
                "1. Technical concepts and terminology identified\n"
                "2. Code-related discussions and solutions\n"
                "3. Architecture and design patterns\n"
                "4. Technical challenges and blockers\n"
                "5. Technical expertise and authority patterns\n"
                "6. Technical debt and improvement opportunities\n"
                "7. Tool and technology recommendations\n"
                "8. Technical decision impact assessment"
            ),
            agent=self.advanced_conversation_analyst()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Advanced Conversation Intelligence crew"""
        # Use advanced agents
        agents = [
            self.advanced_conversation_analyst(),
            self.learning_analyzer(),
            self.insight_extractor(),
            self.advanced_knowledge_gap_detector(),
            self.conversation_strategist()
        ]
        
        # Include specialized tasks
        tasks = [
            self.analyze_conversation_task(),
            self.technical_conversation_analysis_task(),
            self.analyze_learning_patterns_task(),
            self.extract_insights_task(),
            self.identify_knowledge_gaps_task(),
            self.strategic_analysis_task(),
            self.synthesize_intelligence_task()
        ]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_llm=self.get_llm_config(),
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


@register_crew("meeting_intelligence")
class MeetingIntelligenceCrew(PRSNLBaseCrew):
    """Specialized crew for meeting and discussion analysis"""
    
    @agent
    def meeting_analyst(self) -> Agent:
        """Meeting-focused conversation analyst"""
        agent_instance = ConversationAnalystAgent(
            role="Meeting Analyst",
            goal="Analyze meetings to extract key decisions, action items, and insights",
            backstory=(
                "You are a specialist in meeting analysis who excels at "
                "extracting structured information from meeting discussions. "
                "Your expertise helps teams understand what was decided, "
                "what needs to be done, and what insights emerged."
            )
        )
        return agent_instance.get_agent()
    
    @agent
    def action_item_extractor(self) -> Agent:
        """Action item extraction specialist"""
        return Agent(
            role="Action Item Extractor",
            goal="Extract and organize action items from meeting discussions",
            backstory=(
                "You are an expert at identifying and organizing action items "
                "from meetings. Your skill lies in recognizing commitments, "
                "deadlines, and responsibilities from conversational content."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @task
    def extract_meeting_structure_task(self) -> Task:
        """Task for extracting meeting structure and flow"""
        return Task(
            description=(
                "Extract the structure and flow of the meeting including "
                "agenda items, discussion topics, and meeting progression."
            ),
            expected_output=(
                "Meeting structure analysis including:\n"
                "1. Meeting type and purpose\n"
                "2. Agenda items and topics covered\n"
                "3. Discussion flow and progression\n"
                "4. Time allocation and pacing\n"
                "5. Participant engagement patterns\n"
                "6. Meeting effectiveness assessment"
            ),
            agent=self.meeting_analyst()
        )
    
    @task
    def extract_action_items_task(self) -> Task:
        """Task for extracting action items and commitments"""
        return Task(
            description=(
                "Extract all action items, commitments, and follow-up tasks "
                "from the meeting discussion. Identify owners, deadlines, "
                "and dependencies."
            ),
            expected_output=(
                "Action items summary including:\n"
                "1. Complete list of action items\n"
                "2. Assigned owners and responsibilities\n"
                "3. Deadlines and timelines\n"
                "4. Dependencies and blockers\n"
                "5. Priority levels and urgency\n"
                "6. Follow-up requirements\n"
                "7. Success criteria and deliverables"
            ),
            agent=self.action_item_extractor()
        )
    
    @task
    def meeting_summary_task(self) -> Task:
        """Task for generating comprehensive meeting summary"""
        return Task(
            description=(
                "Generate a comprehensive meeting summary that captures "
                "key discussions, decisions, and outcomes in a structured format."
            ),
            expected_output=(
                "Meeting summary including:\n"
                "1. Meeting overview and objectives\n"
                "2. Key decisions made\n"
                "3. Important discussions and insights\n"
                "4. Action items and next steps\n"
                "5. Outstanding questions and issues\n"
                "6. Meeting effectiveness and recommendations\n"
                "7. Follow-up meeting requirements"
            ),
            agent=self.meeting_analyst()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Meeting Intelligence crew"""
        return Crew(
            agents=[self.meeting_analyst(), self.action_item_extractor()],
            tasks=[
                self.extract_meeting_structure_task(),
                self.extract_action_items_task(),
                self.meeting_summary_task()
            ],
            process=Process.sequential,
            verbose=True,
            memory=True
        )