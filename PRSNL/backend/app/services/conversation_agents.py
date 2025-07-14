"""
Specialized AI Agents for Conversation Intelligence Analysis

This module contains specialized agents that work together to provide
comprehensive conversation analysis. Each agent focuses on a specific
aspect of conversation intelligence to extract maximum value.
"""

import json
import logging
from typing import Dict, List, Any
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class TechnicalContentExtractor:
    """Specialized agent for extracting technical content and code solutions."""
    
    def __init__(self, ai_service: UnifiedAIService):
        self.ai_service = ai_service
    
    async def extract_technical_content(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract technical content, code snippets, and implementation details."""
        
        # Get messages with substantial technical content
        technical_messages = self._filter_technical_messages(messages)
        
        if not technical_messages:
            return {
                "code_snippets": [],
                "technologies": [],
                "implementation_patterns": [],
                "technical_recommendations": []
            }
        
        # Build focused technical prompt
        technical_content = self._build_technical_context(technical_messages)
        
        prompt = f"""
        Extract SPECIFIC technical content from this conversation. Focus on actual implementations, not theory.
        
        TECHNICAL CONVERSATION CONTENT:
        {technical_content}
        
        Extract:
        1. CODE IMPLEMENTATIONS - Actual working code snippets with purpose
        2. SPECIFIC TECHNOLOGIES - Exact libraries, frameworks, APIs mentioned with versions
        3. IMPLEMENTATION PATTERNS - Architectural decisions and design patterns used
        4. TECHNICAL RECOMMENDATIONS - Specific tools, approaches, and best practices
        
        Be EXTREMELY SPECIFIC. Instead of "use React", say "implement React functional components with useEffect for data fetching".
        Instead of "handle errors", say "implement try-catch blocks with specific error types and user feedback".
        
        Format as JSON:
        {{
            "code_snippets": [
                {{"language": "python", "purpose": "API endpoint", "code": "actual code", "context": "where to use"}}
            ],
            "technologies": [
                {{"name": "FastAPI", "version": "0.68+", "purpose": "backend API", "specific_use": "async endpoints"}}
            ],
            "implementation_patterns": [
                {{"pattern": "Repository Pattern", "purpose": "data access", "implementation": "specific steps"}}
            ],
            "technical_recommendations": [
                {{"category": "performance", "recommendation": "specific action", "reasoning": "why"}}
            ]
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=800,
            temperature=0.2
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "code_snippets": [],
                "technologies": [],
                "implementation_patterns": [],
                "technical_recommendations": []
            }
    
    def _filter_technical_messages(self, messages: List[Dict]) -> List[Dict]:
        """Filter messages containing substantial technical content."""
        technical_keywords = [
            'implementation', 'code', 'function', 'class', 'method', 'api', 'endpoint',
            'database', 'query', 'schema', 'algorithm', 'pattern', 'architecture',
            'library', 'framework', 'package', 'module', 'import', 'install',
            'configuration', 'setup', 'deploy', 'build', 'test', 'debug',
            'performance', 'optimization', 'scaling', 'security', 'authentication'
        ]
        
        technical_messages = []
        for msg in messages:
            content = msg['content_text'].lower()
            if (len(msg['content_text']) > 200 and 
                sum(1 for keyword in technical_keywords if keyword in content) >= 2):
                technical_messages.append(msg)
        
        # Sort by relevance (length + keyword density)
        return sorted(technical_messages, 
                     key=lambda x: len(x['content_text']) + 
                     sum(1 for k in technical_keywords if k in x['content_text'].lower()),
                     reverse=True)[:8]
    
    def _build_technical_context(self, messages: List[Dict]) -> str:
        """Build focused technical context from filtered messages."""
        context_parts = []
        for i, msg in enumerate(messages[:5]):  # Top 5 most technical
            role = msg['role'].upper()
            content = msg['content_text'][:1000]  # Limit per message
            context_parts.append(f"[{role} MESSAGE {i+1}]: {content}")
        
        return "\n\n".join(context_parts)


class LearningJourneyAnalyzer:
    """Specialized agent for analyzing learning progression and understanding evolution."""
    
    def __init__(self, ai_service: UnifiedAIService):
        self.ai_service = ai_service
    
    async def analyze_learning_progression(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze how understanding evolved throughout the conversation."""
        
        # Get user questions to track learning progression
        user_messages = [m for m in messages if m['role'] == 'user']
        ai_responses = [m for m in messages if m['role'] == 'assistant']
        
        if len(user_messages) < 2:
            return {
                "learning_stages": [],
                "knowledge_evolution": "Insufficient data",
                "breakthrough_moments": [],
                "confidence_progression": "unclear"
            }
        
        # Build learning progression context
        progression_context = self._build_learning_context(user_messages, ai_responses)
        
        prompt = f"""
        Analyze the ACTUAL learning progression in this conversation. Track how understanding evolved.
        
        LEARNING PROGRESSION DATA:
        {progression_context}
        
        Analyze:
        1. LEARNING STAGES - How did understanding progress step by step?
        2. BREAKTHROUGH MOMENTS - When did concepts "click"? What triggered understanding?
        3. KNOWLEDGE EVOLUTION - What specific knowledge was gained at each stage?
        4. CONFIDENCE PROGRESSION - How did confidence in the topic change?
        
        Focus on ACTUAL learning that happened, not generic patterns.
        
        Format as JSON:
        {{
            "learning_stages": [
                {{"stage": 1, "focus": "specific topic", "understanding_level": "beginner/intermediate/advanced", "key_insight": "what was learned"}}
            ],
            "breakthrough_moments": [
                {{"moment": "specific realization", "trigger": "what caused it", "impact": "how it changed understanding"}}
            ],
            "knowledge_evolution": "narrative of how knowledge grew",
            "confidence_progression": "how confidence changed throughout"
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=600,
            temperature=0.3
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "learning_stages": [],
                "knowledge_evolution": "Analysis failed",
                "breakthrough_moments": [],
                "confidence_progression": "unclear"
            }
    
    def _build_learning_context(self, user_messages: List[Dict], ai_responses: List[Dict]) -> str:
        """Build context showing learning progression through questions and answers."""
        context_parts = []
        
        # Interleave user questions with AI responses to show progression
        for i in range(min(len(user_messages), len(ai_responses), 6)):
            user_q = user_messages[i]['content_text'][:300]
            ai_resp = ai_responses[i]['content_text'][:300] if i < len(ai_responses) else "[No response]"
            
            context_parts.append(f"PROGRESSION {i+1}:")
            context_parts.append(f"User Question: {user_q}")
            context_parts.append(f"AI Response: {ai_resp}")
            context_parts.append("---")
        
        return "\n".join(context_parts)


class ActionableInsightsExtractor:
    """Specialized agent for extracting concrete, actionable insights and next steps."""
    
    def __init__(self, ai_service: UnifiedAIService):
        self.ai_service = ai_service
    
    async def extract_actionable_insights(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract concrete, implementable insights and action items."""
        
        # Get the most valuable solution-oriented messages
        solution_messages = self._filter_solution_messages(messages)
        
        if not solution_messages:
            return {
                "immediate_actions": [],
                "implementation_steps": [],
                "tools_and_resources": [],
                "best_practices": []
            }
        
        solution_context = self._build_solution_context(solution_messages)
        
        prompt = f"""
        Extract CONCRETE, ACTIONABLE insights from this solution-focused conversation content.
        
        SOLUTION-FOCUSED CONTENT:
        {solution_context}
        
        Extract SPECIFIC, IMPLEMENTABLE insights:
        
        1. IMMEDIATE ACTIONS - Tasks that can be started TODAY with specific steps
        2. IMPLEMENTATION STEPS - Step-by-step technical implementation guide
        3. TOOLS AND RESOURCES - Exact tools/libraries/APIs with specific use cases
        4. BEST PRACTICES - Specific coding/architecture guidelines with examples
        
        Be ACTIONABLE. Instead of "test your code", say "write unit tests for the user authentication function using pytest".
        Instead of "optimize performance", say "implement Redis caching for API responses that take >500ms".
        
        Format as JSON:
        {{
            "immediate_actions": [
                {{"action": "specific task", "time_estimate": "30 minutes", "difficulty": "easy/medium/hard"}}
            ],
            "implementation_steps": [
                {{"step": 1, "task": "specific implementation task", "code_example": "if applicable", "resources": ["links/docs"]}}
            ],
            "tools_and_resources": [
                {{"name": "exact tool name", "purpose": "specific use case", "setup": "how to install/configure"}}
            ],
            "best_practices": [
                {{"practice": "specific guideline", "example": "concrete example", "reasoning": "why it matters"}}
            ]
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=700,
            temperature=0.2
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "immediate_actions": [],
                "implementation_steps": [],
                "tools_and_resources": [],
                "best_practices": []
            }
    
    def _filter_solution_messages(self, messages: List[Dict]) -> List[Dict]:
        """Filter messages containing solutions, recommendations, and actionable content."""
        solution_keywords = [
            'solution', 'implement', 'create', 'build', 'setup', 'configure',
            'install', 'use', 'try', 'recommend', 'suggest', 'should',
            'step', 'process', 'approach', 'method', 'way', 'how to',
            'example', 'sample', 'template', 'pattern', 'practice'
        ]
        
        solution_messages = []
        for msg in messages:
            content = msg['content_text'].lower()
            if (msg['role'] == 'assistant' and len(msg['content_text']) > 150 and
                sum(1 for keyword in solution_keywords if keyword in content) >= 3):
                solution_messages.append(msg)
        
        # Sort by solution density and length
        return sorted(solution_messages,
                     key=lambda x: len(x['content_text']) + 
                     sum(2 for k in solution_keywords if k in x['content_text'].lower()),
                     reverse=True)[:6]
    
    def _build_solution_context(self, messages: List[Dict]) -> str:
        """Build context focused on solutions and actionable content."""
        context_parts = []
        for i, msg in enumerate(messages[:4]):
            content = msg['content_text'][:800]
            context_parts.append(f"[SOLUTION {i+1}]: {content}")
        
        return "\n\n".join(context_parts)


class KnowledgeGapIdentifier:
    """Specialized agent for identifying specific knowledge gaps and learning opportunities."""
    
    def __init__(self, ai_service: UnifiedAIService):
        self.ai_service = ai_service
    
    async def identify_knowledge_gaps(self, messages: List[Dict]) -> Dict[str, Any]:
        """Identify specific knowledge gaps and learning opportunities."""
        
        # Get questions that reveal knowledge gaps
        gap_revealing_messages = self._filter_gap_revealing_messages(messages)
        
        if not gap_revealing_messages:
            return {
                "knowledge_gaps": [],
                "learning_opportunities": [],
                "prerequisite_knowledge": [],
                "next_topics": []
            }
        
        gap_context = self._build_gap_context(gap_revealing_messages)
        
        prompt = f"""
        Identify SPECIFIC knowledge gaps from this conversation that reveal what's missing or unclear.
        
        KNOWLEDGE GAP INDICATORS:
        {gap_context}
        
        Identify:
        1. SPECIFIC KNOWLEDGE GAPS - What concepts/skills are missing?
        2. PREREQUISITE KNOWLEDGE - What foundational concepts need to be learned first?
        3. LEARNING OPPORTUNITIES - Specific topics/technologies to explore next
        4. IMPLEMENTATION GAPS - What practical skills need development?
        
        Be SPECIFIC. Instead of "learn more about APIs", say "understand REST API authentication with JWT tokens".
        Instead of "improve coding skills", say "practice async/await patterns in Python with real database operations".
        
        Format as JSON:
        {{
            "knowledge_gaps": [
                {{"gap": "specific missing knowledge", "impact": "how it limits current work", "priority": "high/medium/low"}}
            ],
            "prerequisite_knowledge": [
                {{"concept": "foundational topic", "reason": "why it's needed", "resources": ["where to learn"]}}
            ],
            "learning_opportunities": [
                {{"topic": "specific learning area", "benefit": "how it helps", "time_investment": "estimated hours"}}
            ],
            "implementation_gaps": [
                {{"skill": "practical skill needed", "current_level": "beginner/intermediate", "target_level": "what to achieve"}}
            ]
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=600,
            temperature=0.3
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "knowledge_gaps": [],
                "learning_opportunities": [],
                "prerequisite_knowledge": [],
                "implementation_gaps": []
            }
    
    def _filter_gap_revealing_messages(self, messages: List[Dict]) -> List[Dict]:
        """Filter messages that reveal knowledge gaps - questions, confusion, partial understanding."""
        gap_indicators = [
            '?', 'how', 'what', 'why', 'when', 'where', 'confused', 'unclear',
            'not sure', 'don\'t understand', 'help', 'stuck', 'problem', 'issue',
            'error', 'doesn\'t work', 'failing', 'wrong', 'not working'
        ]
        
        gap_messages = []
        
        # User questions and confusion
        for msg in messages:
            if msg['role'] == 'user':
                content = msg['content_text'].lower()
                if (len(msg['content_text']) > 50 and
                    sum(1 for indicator in gap_indicators if indicator in content) >= 1):
                    gap_messages.append(msg)
        
        # AI responses that indicate partial solutions or complexity
        for msg in messages:
            if msg['role'] == 'assistant':
                content = msg['content_text'].lower()
                complexity_indicators = [
                    'depends on', 'it varies', 'complex', 'advanced', 'prerequisite',
                    'first need to', 'before you can', 'requires understanding'
                ]
                if (len(msg['content_text']) > 200 and
                    sum(1 for indicator in complexity_indicators if indicator in content) >= 1):
                    gap_messages.append(msg)
        
        return gap_messages[:8]
    
    def _build_gap_context(self, messages: List[Dict]) -> str:
        """Build context that highlights knowledge gaps and confusion."""
        context_parts = []
        for i, msg in enumerate(messages[:6]):
            role = msg['role'].upper()
            content = msg['content_text'][:500]
            context_parts.append(f"[{role} GAP INDICATOR {i+1}]: {content}")
        
        return "\n\n".join(context_parts)