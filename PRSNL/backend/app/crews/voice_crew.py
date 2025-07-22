"""
Voice Crew - Specialized CrewAI agents for voice interactions

This crew is optimized for real-time voice conversations with:
- Quick response generation
- Context awareness
- Personality consistency
- Knowledge base integration
"""

from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from langchain_openai import AzureChatOpenAI

from app.crews.base_crew import PRSNLBaseCrew as BaseCrew
from app.agents.base_agent import PRSNLBaseAgent as BaseAgent
from app.tools.knowledge_tools import KnowledgeGraphTool as KnowledgeSearchTool
# from app.tools.learning_tools import ContextAnalysisTool  # TODO: Create this tool
from app.config import settings

import logging
logger = logging.getLogger(__name__)


class VoiceResponseAgent(BaseAgent):
    """Quick response agent for immediate acknowledgment"""
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Voice Response Specialist",
            goal="Provide immediate, natural conversational responses",
            backstory="""You are Cortex's voice, responsible for creating natural, 
            flowing conversation. You acknowledge what the user says immediately
            and provide helpful, concise responses that feel like a real conversation.""",
            tools=[],
            llm=self.get_llm(model="gpt-4o-mini"),  # Fast model for quick responses
            verbose=False,
            max_iter=1  # Single iteration for speed
        )


class VoiceContextAgent(BaseAgent):
    """Analyzes context and intent from voice input"""
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Voice Context Analyzer",
            goal="Understand user intent and context from voice input",
            backstory="""You specialize in understanding the context and intent
            behind spoken words. You consider tone, previous conversation, and
            the user's knowledge base to provide relevant context.""",
            tools=[
                KnowledgeSearchTool().create_tool(),
                # ContextAnalysisTool().create_tool()  # TODO: Create this tool
            ],
            llm=self.get_llm(model="gpt-4o-mini"),
            verbose=False
        )


class VoicePersonalityAgent(BaseAgent):
    """Ensures Cortex personality consistency in voice"""
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Cortex Personality Guardian",
            goal="Maintain Cortex's unique personality in voice interactions",
            backstory="""You are the guardian of Cortex's personality. You ensure
            every response reflects Cortex's traits: intelligent, friendly, curious,
            and occasionally playful. You adapt the mood based on context while
            keeping responses natural and conversational.""",
            tools=[],
            llm=self.get_llm(model="gpt-4o-mini"),
            verbose=False
        )


class VoiceCrew(BaseCrew):
    """Specialized crew for voice interactions"""
    
    def __init__(self):
        super().__init__()
        self.response_agent = VoiceResponseAgent()
        self.context_agent = VoiceContextAgent()
        self.personality_agent = VoicePersonalityAgent()
    
    def create_crew(self) -> Crew:
        """Create the voice interaction crew"""
        
        # Define tasks
        tasks = [
            Task(
                description="""Analyze the user's voice input: {user_input}
                
                Consider:
                1. What is the user asking or saying?
                2. What's the intent behind their words?
                3. Any relevant context from their knowledge base?
                4. Previous conversation history: {conversation_history}
                
                Provide a brief context analysis.""",
                agent=self.context_agent.create_agent(),
                expected_output="Context analysis with intent and relevant information"
            ),
            
            Task(
                description="""Generate a natural conversational response to: {user_input}
                
                Requirements:
                1. Be conversational and natural
                2. Keep it concise for voice (2-3 sentences max)
                3. Use the context analysis provided
                4. Include relevant information from knowledge base if helpful
                
                Response should feel like talking to a knowledgeable friend.""",
                agent=self.response_agent.create_agent(),
                expected_output="Natural conversational response"
            ),
            
            Task(
                description="""Polish the response with Cortex's personality:
                
                Original response: [from previous task]
                Current mood: {mood}
                
                Ensure the response:
                1. Reflects Cortex's personality traits
                2. Matches the appropriate mood
                3. Sounds natural when spoken aloud
                4. Has appropriate energy level
                
                Return the final response and suggested emotion for TTS.""",
                agent=self.personality_agent.create_agent(),
                expected_output="Final response with personality and emotion suggestion"
            )
        ]
        
        return Crew(
            agents=[
                self.context_agent.create_agent(),
                self.response_agent.create_agent(),
                self.personality_agent.create_agent()
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=False
        )
    
    async def process_voice_input(
        self, 
        user_input: str,
        user_id: str,
        conversation_history: List[Dict[str, str]] = None,
        current_mood: str = "primary"
    ) -> Dict[str, Any]:
        """Process voice input and generate response"""
        
        try:
            crew = self.create_crew()
            
            # Format conversation history
            history_text = ""
            if conversation_history:
                for entry in conversation_history[-5:]:  # Last 5 exchanges
                    history_text += f"User: {entry.get('user', '')}\n"
                    history_text += f"Cortex: {entry.get('cortex', '')}\n"
            
            result = crew.kickoff(inputs={
                "user_input": user_input,
                "conversation_history": history_text or "No previous conversation",
                "mood": current_mood
            })
            
            # Parse the result to extract response and emotion
            response_text = str(result)
            suggested_emotion = "neutral"
            
            # Simple parsing for emotion hints in response
            if "excited" in response_text.lower() or "!" in response_text:
                suggested_emotion = "excited"
            elif "hmm" in response_text.lower() or "interesting" in response_text.lower():
                suggested_emotion = "thoughtful"
            elif "great" in response_text.lower() or "wonderful" in response_text.lower():
                suggested_emotion = "cheerful"
            
            return {
                "response": response_text,
                "emotion": suggested_emotion,
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Voice crew processing failed: {e}")
            # Fallback response
            return {
                "response": "I'm here and listening. Could you tell me more about that?",
                "emotion": "neutral",
                "confidence": 0.5
            }


class VoiceSimpleCrew(BaseCrew):
    """Ultra-fast single agent for simple voice responses"""
    
    def create_crew(self) -> Crew:
        """Create a simple, fast voice crew"""
        
        agent = Agent(
            role="Cortex Voice",
            goal="Respond naturally and quickly to voice input",
            backstory="""You are Cortex, an intelligent AI assistant. Respond
            naturally and conversationally to voice input. Keep responses brief
            and friendly.""",
            tools=[],
            llm=self.get_llm(model="gpt-4o-mini"),
            verbose=False,
            max_iter=1
        )
        
        task = Task(
            description="""Respond to: {user_input}
            
            Be natural, brief, and conversational.
            Previous context: {conversation_history}""",
            agent=agent,
            expected_output="Natural voice response"
        )
        
        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )