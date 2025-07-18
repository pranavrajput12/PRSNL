"""
Floating Chat Crew - Specialized lightweight crew for floating chat interactions

This crew provides context-aware, quick responses for the floating chat component.
Optimized for speed and contextual understanding while maintaining quality.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew
from app.config import settings

logger = logging.getLogger(__name__)


@register_crew("floating_chat")
class FloatingChatCrew(PRSNLBaseCrew):
    """Lightweight crew optimized for quick floating chat responses"""
    
    @agent
    def context_aware_assistant(self) -> Agent:
        """Context-aware assistant optimized for quick responses"""
        return Agent(
            role="Context-Aware Assistant",
            goal="Provide quick, helpful, and contextually relevant responses for floating chat interactions",
            backstory=(
                "You are PRSNL's floating chat assistant, designed to provide "
                "instant help based on the user's current page and context. "
                "You excel at understanding what the user is looking at and "
                "providing relevant, concise answers from their knowledge base. "
                "You're friendly, efficient, and always aware of the user's current context."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,  # Keep quiet for speed
            allow_delegation=False  # Single agent for speed
        )
    
    @agent
    def page_context_analyzer(self) -> Agent:
        """Specialized agent for analyzing page context"""
        return Agent(
            role="Page Context Analyzer",
            goal="Quickly understand and utilize the user's current page context",
            backstory=(
                "You are a specialist in understanding web page context and "
                "user intent. You can quickly analyze what page the user is on, "
                "what they might be trying to accomplish, and how to best help them "
                "with relevant information from their knowledge base."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,
            allow_delegation=False
        )
    
    @task
    def analyze_context_task(self) -> Task:
        """Task for analyzing user context and intent"""
        return Task(
            description=(
                "Analyze the user's current context including:\n"
                "- Current page: {page_type} at {page_url}\n"
                "- Page title: {page_title}\n"
                "- User query: {user_message}\n"
                "- Available context: {context_info}\n\n"
                "Determine what the user needs help with based on their context."
            ),
            expected_output=(
                "Context analysis including:\n"
                "1. User's likely intent based on current page\n"
                "2. Relevant context elements to utilize\n"
                "3. Recommended response approach\n"
                "4. Key information to emphasize\n"
                "5. Suggested quick actions if applicable"
            ),
            agent=self.page_context_analyzer()
        )
    
    @task
    def generate_response_task(self) -> Task:
        """Task for generating contextual chat response"""
        return Task(
            description=(
                "Generate a helpful, concise response based on the context analysis "
                "and available knowledge base information. User message: {user_message}\n"
                "Knowledge base items: {knowledge_items}\n"
                "Context analysis: Use output from analyze_context_task\n\n"
                "Provide a direct, helpful answer that acknowledges the user's context."
            ),
            expected_output=(
                "A concise, helpful response that:\n"
                "1. Directly addresses the user's question\n"
                "2. Incorporates relevant context from their current page\n"
                "3. References specific knowledge base items when relevant\n"
                "4. Suggests follow-up actions if helpful\n"
                "5. Maintains a friendly, assistant-like tone\n"
                "6. Is optimized for quick reading (2-3 sentences max unless complex)\n"
                "7. Includes source citations when using knowledge base items"
            ),
            agent=self.context_aware_assistant(),
            context=[self.analyze_context_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Floating Chat crew with optimized settings"""
        return Crew(
            agents=[
                self.page_context_analyzer(),
                self.context_aware_assistant()
            ],
            tasks=[
                self.analyze_context_task(),
                self.generate_response_task()
            ],
            process=Process.sequential,
            verbose=False,  # Minimize logging for speed
            memory=False,   # Disable memory for speed (each interaction is independent)
            max_execution_time=30,  # 30 second timeout for floating chat
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


@register_crew("floating_chat_simple")
class FloatingChatSimpleCrew(PRSNLBaseCrew):
    """Ultra-lightweight single-agent crew for fastest possible responses"""
    
    @agent
    def quick_assistant(self) -> Agent:
        """Ultra-fast assistant for immediate responses"""
        return Agent(
            role="Quick Assistant",
            goal="Provide immediate, contextual help with minimal processing time",
            backstory=(
                "You are PRSNL's instant assistant. Your superpower is providing "
                "quick, accurate answers based on the user's current context and "
                "available knowledge. You understand that speed matters in floating "
                "chat, so you're direct, helpful, and efficient. You always acknowledge "
                "what page the user is on when relevant."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,
            allow_delegation=False,
            max_execution_time=15  # 15 second max for ultra-fast responses
        )
    
    @task
    def quick_response_task(self) -> Task:
        """Single task for quick contextual responses"""
        return Task(
            description=(
                "Provide a quick, helpful response to the user's question.\n\n"
                "Context:\n"
                "- Current page: {page_type} - {page_title}\n"
                "- User on: {page_url}\n"
                "- Question: {user_message}\n"
                "- Available knowledge: {knowledge_items}\n\n"
                "Give a direct, contextual answer that helps the user immediately."
            ),
            expected_output=(
                "A brief, helpful response (1-2 sentences) that:\n"
                "- Directly answers the user's question\n"
                "- References their current context when relevant\n"
                "- Uses knowledge base information when available\n"
                "- Suggests next steps if appropriate\n"
                "- Maintains a friendly, assistant tone"
            ),
            agent=self.quick_assistant()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the simplest possible floating chat crew"""
        return Crew(
            agents=[self.quick_assistant()],
            tasks=[self.quick_response_task()],
            process=Process.sequential,
            verbose=False,
            memory=False,
            max_execution_time=15  # Ultra-fast timeout
        )


@register_crew("floating_chat_contextual")
class FloatingChatContextualCrew(PRSNLBaseCrew):
    """Context-enhanced crew for more intelligent floating chat responses"""
    
    @agent
    def context_specialist(self) -> Agent:
        """Specialist in understanding user context and intent"""
        return Agent(
            role="Context Specialist",
            goal="Deeply understand user context to provide the most relevant assistance",
            backstory=(
                "You are an expert at understanding user context and intent. "
                "You excel at interpreting what users are trying to accomplish "
                "based on their current page, recent activity, and question patterns. "
                "You help the assistant provide more intelligent, context-aware responses."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,
            allow_delegation=False
        )
    
    @agent
    def knowledge_retriever(self) -> Agent:
        """Specialist in finding relevant knowledge base information"""
        return Agent(
            role="Knowledge Retriever",
            goal="Find the most relevant knowledge base information for the user's question",
            backstory=(
                "You are a knowledge retrieval specialist who excels at finding "
                "the most relevant information from the user's knowledge base. "
                "You understand how to match user questions with available content "
                "and can identify the most helpful sources for their specific context."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,
            allow_delegation=False
        )
    
    @agent
    def response_synthesizer(self) -> Agent:
        """Specialist in crafting perfect floating chat responses"""
        return Agent(
            role="Response Synthesizer",
            goal="Create the perfect response by combining context understanding and knowledge retrieval",
            backstory=(
                "You are a master at synthesizing information into perfect responses. "
                "You take context analysis and relevant knowledge to create responses "
                "that are exactly what the user needs - concise, helpful, and contextual. "
                "You excel at the art of saying just enough to be helpful without overwhelming."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=False,
            allow_delegation=False
        )
    
    @task
    def understand_context_task(self) -> Task:
        """Task for deep context understanding"""
        return Task(
            description=(
                "Analyze the user's context to understand their intent and needs:\n"
                "- Page: {page_type} ({page_title})\n"
                "- URL: {page_url}\n"
                "- Question: {user_message}\n"
                "- Additional context: {context_info}\n\n"
                "What is the user trying to accomplish? What would be most helpful?"
            ),
            expected_output=(
                "Context understanding including:\n"
                "1. User's primary intent\n"
                "2. What they're likely trying to accomplish\n"
                "3. Most helpful response approach\n"
                "4. Key context elements to emphasize\n"
                "5. Suggested information types to include"
            ),
            agent=self.context_specialist()
        )
    
    @task
    def retrieve_knowledge_task(self) -> Task:
        """Task for retrieving relevant knowledge"""
        return Task(
            description=(
                "Find the most relevant knowledge base information for the user's question.\n"
                "Question: {user_message}\n"
                "Available items: {knowledge_items}\n"
                "Context insight: Use output from understand_context_task\n\n"
                "Select and summarize the most relevant information."
            ),
            expected_output=(
                "Relevant knowledge summary including:\n"
                "1. Most relevant knowledge base items\n"
                "2. Key information that answers the user's question\n"
                "3. Source citations and references\n"
                "4. Additional related information that might be helpful\n"
                "5. Confidence level in the information relevance"
            ),
            agent=self.knowledge_retriever(),
            context=[self.understand_context_task()]
        )
    
    @task
    def synthesize_response_task(self) -> Task:
        """Task for creating the final response"""
        return Task(
            description=(
                "Create the perfect floating chat response by combining context "
                "understanding with relevant knowledge. User question: {user_message}\n\n"
                "Use insights from context analysis and knowledge retrieval to craft "
                "a response that perfectly meets the user's needs."
            ),
            expected_output=(
                "A perfect floating chat response that:\n"
                "1. Directly addresses the user's question\n"
                "2. Incorporates their current context naturally\n"
                "3. References the most relevant knowledge base items\n"
                "4. Provides exactly the right amount of detail\n"
                "5. Suggests relevant next actions when appropriate\n"
                "6. Maintains an friendly, helpful tone\n"
                "7. Is optimized for quick consumption\n"
                "8. Includes proper source citations"
            ),
            agent=self.response_synthesizer(),
            context=[self.understand_context_task(), self.retrieve_knowledge_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the contextual floating chat crew"""
        return Crew(
            agents=[
                self.context_specialist(),
                self.knowledge_retriever(),
                self.response_synthesizer()
            ],
            tasks=[
                self.understand_context_task(),
                self.retrieve_knowledge_task(),
                self.synthesize_response_task()
            ],
            process=Process.sequential,
            verbose=False,
            memory=True,  # Enable memory for better context understanding
            max_execution_time=45,  # Slightly longer for more thorough analysis
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