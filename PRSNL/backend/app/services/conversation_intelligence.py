"""
Conversation Intelligence Agent - Advanced AI analysis for imported conversations

This service processes AI chat conversations to extract deep insights, learning patterns,
and actionable knowledge for the PRSNL knowledge base.
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import asyncio

from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.multimodal_embedding_service import multimodal_embedding_service

logger = logging.getLogger(__name__)

class ConversationIntelligenceAgent:
    """
    AI-powered agent that analyzes conversations to extract:
    - Comprehensive summaries
    - Learning journeys
    - Key concepts and insights
    - Knowledge gaps
    - Actionable next steps
    """
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    async def process_conversation(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Main entry point for processing a conversation with full intelligence analysis.
        """
        try:
            # Load conversation and messages
            conversation, messages = await self._load_conversation_data(conversation_id)
            
            if not conversation or not messages:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Run all analysis tasks in parallel for efficiency
            results = await asyncio.gather(
                self._generate_comprehensive_summary(conversation, messages),
                self._analyze_learning_journey(messages),
                self._extract_key_concepts_and_topics(messages),
                self._analyze_conversation_flow(messages),
                self._identify_knowledge_gaps(messages),
                self._extract_actionable_insights(messages),
                self._analyze_user_context(messages),
                self._extract_code_and_solutions(messages)
            )
            
            # Unpack results
            summary = results[0]
            learning_journey = results[1]
            concepts = results[2]
            flow_analysis = results[3]
            knowledge_gaps = results[4]
            actionable_insights = results[5]
            user_context = results[6]
            code_solutions = results[7]
            
            # Update conversation with intelligence data
            await self._update_conversation_intelligence(
                conversation_id,
                summary=summary['full_summary'],
                key_topics=concepts['topics'],
                learning_points=learning_journey['key_learnings'],
                user_journey=learning_journey['journey_narrative'],
                knowledge_gaps=knowledge_gaps['gaps']
            )
            
            # Process individual messages for insights
            await self._process_message_insights(conversation_id, messages)
            
            # Create enhanced search embeddings
            await self._create_intelligent_embeddings(
                conversation_id, 
                summary, 
                concepts, 
                learning_journey
            )
            
            return {
                'conversation_id': str(conversation_id),
                'summary': summary,
                'learning_journey': learning_journey,
                'concepts': concepts,
                'flow_analysis': flow_analysis,
                'knowledge_gaps': knowledge_gaps,
                'actionable_insights': actionable_insights,
                'user_context': user_context,
                'code_solutions': code_solutions,
                'processing_status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error in conversation intelligence processing: {e}")
            await self._mark_processing_failed(conversation_id, str(e))
            raise
    
    async def _load_conversation_data(self, conversation_id: UUID) -> Tuple[Dict, List[Dict]]:
        """Load conversation and its messages from database."""
        async for conn in get_db_connection():
            conversation = await conn.fetchrow("""
                SELECT * FROM ai_conversation_imports WHERE id = $1
            """, conversation_id)
            
            messages = await conn.fetch("""
                SELECT * FROM ai_conversation_messages 
                WHERE conversation_id = $1 
                ORDER BY sequence_number ASC
            """, conversation_id)
            
            return dict(conversation) if conversation else None, [dict(m) for m in messages]
    
    async def _generate_comprehensive_summary(
        self, 
        conversation: Dict, 
        messages: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a comprehensive, intelligent summary of the entire conversation."""
        
        # Build conversation context
        conversation_text = self._build_conversation_text(messages)
        
        prompt = f"""
        Analyze this {conversation['platform']} conversation and provide a comprehensive summary.
        
        Title: {conversation['title']}
        Platform: {conversation['platform']}
        Message Count: {len(messages)}
        
        Conversation:
        {conversation_text[:8000]}  # Limit for token constraints
        
        Provide a detailed summary that includes:
        1. Main objective - What was the user trying to achieve?
        2. Key topics discussed - Major subjects and concepts
        3. Solutions provided - Concrete answers and solutions
        4. Learning outcomes - What the user learned
        5. Conversation tone - Technical level, complexity
        6. Noteworthy insights - Unique or valuable information
        
        Format as JSON:
        {{
            "full_summary": "2-3 paragraph comprehensive summary",
            "one_line_summary": "Single sentence capturing the essence",
            "main_objective": "What the user wanted",
            "key_solutions": ["solution1", "solution2"],
            "complexity_level": "beginner|intermediate|advanced",
            "value_score": 0-10
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "full_summary": response,
                "one_line_summary": conversation['title'],
                "main_objective": "Unknown",
                "key_solutions": [],
                "complexity_level": "intermediate",
                "value_score": 5
            }
    
    async def _analyze_learning_journey(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze how the user's understanding evolved throughout the conversation."""
        
        # Extract user messages
        user_messages = [m for m in messages if m['role'] == 'user']
        
        if not user_messages:
            return {
                "journey_narrative": "No user messages found",
                "key_learnings": [],
                "understanding_progression": []
            }
        
        # Build progression text
        progression_text = "\n\n".join([
            f"Message {i+1}: {m['content_text'][:200]}"
            for i, m in enumerate(user_messages[:10])  # First 10 user messages
        ])
        
        prompt = f"""
        Analyze this user's learning journey through their questions and responses.
        
        User Questions/Responses:
        {progression_text}
        
        Analyze:
        1. Starting knowledge level - What did they know initially?
        2. Knowledge progression - How did their understanding evolve?
        3. Key learning moments - When did understanding click?
        4. Final understanding - Where did they end up?
        5. Confidence growth - How did their confidence change?
        
        Format as JSON:
        {{
            "journey_narrative": "Narrative description of the learning journey",
            "starting_point": "Initial knowledge state",
            "ending_point": "Final knowledge state",
            "key_learnings": ["learning1", "learning2"],
            "understanding_progression": [
                {{"stage": 1, "description": "Initial confusion about X"}},
                {{"stage": 2, "description": "Understanding Y concept"}}
            ],
            "confidence_score_start": 1-10,
            "confidence_score_end": 1-10
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=600,
            temperature=0.4
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "journey_narrative": "Learning journey analysis failed",
                "key_learnings": [],
                "understanding_progression": []
            }
    
    async def _extract_key_concepts_and_topics(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract and categorize key concepts, topics, and technical terms."""
        
        # Combine all message content
        all_content = " ".join([m['content_text'] for m in messages[:20]])
        
        prompt = f"""
        Extract key concepts, topics, and technical terms from this conversation.
        
        Content sample:
        {all_content[:6000]}
        
        Identify:
        1. Main topics - Primary subjects discussed
        2. Technical concepts - Programming concepts, frameworks, tools
        3. Problem domains - What kind of problems were addressed
        4. Technologies mentioned - Languages, libraries, platforms
        5. Concept relationships - How concepts connect
        
        Format as JSON:
        {{
            "topics": ["topic1", "topic2"],
            "technical_concepts": ["concept1", "concept2"],
            "technologies": {{"languages": [], "frameworks": [], "tools": []}},
            "problem_domains": ["domain1", "domain2"],
            "concept_map": [
                {{"from": "concept1", "to": "concept2", "relationship": "depends on"}}
            ]
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=500,
            temperature=0.2
        )
        
        try:
            return json.loads(response.strip())
        except:
            # Extract topics using simple pattern matching as fallback
            topics = self._extract_topics_fallback(all_content)
            return {
                "topics": topics,
                "technical_concepts": [],
                "technologies": {"languages": [], "frameworks": [], "tools": []},
                "problem_domains": [],
                "concept_map": []
            }
    
    async def _analyze_conversation_flow(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze how the conversation flowed and progressed."""
        
        # Build flow representation
        flow_data = []
        for i, msg in enumerate(messages[:15]):
            flow_data.append({
                "position": i + 1,
                "role": msg['role'],
                "preview": msg['content_text'][:100]
            })
        
        prompt = f"""
        Analyze the flow and progression of this conversation.
        
        Message Flow:
        {json.dumps(flow_data, indent=2)}
        
        Analyze:
        1. Conversation pattern - Q&A, tutorial, debugging, exploration?
        2. Topic transitions - How did topics change?
        3. Depth progression - Did it get more complex?
        4. Resolution points - Where were problems solved?
        5. Follow-up patterns - How did questions build on each other?
        
        Format as JSON:
        {{
            "conversation_type": "q&a|tutorial|debugging|exploration|discussion",
            "flow_pattern": "linear|branching|circular|exploratory",
            "topic_transitions": ["Started with X", "Moved to Y"],
            "complexity_curve": "increasing|stable|decreasing|variable",
            "resolution_points": [3, 7, 10],
            "interaction_quality": "high|medium|low"
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=400,
            temperature=0.3
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "conversation_type": "q&a",
                "flow_pattern": "linear",
                "topic_transitions": [],
                "complexity_curve": "stable",
                "resolution_points": [],
                "interaction_quality": "medium"
            }
    
    async def _identify_knowledge_gaps(self, messages: List[Dict]) -> Dict[str, Any]:
        """Identify gaps in understanding and areas needing more exploration."""
        
        # Focus on user questions and AI clarifications
        user_questions = [m['content_text'] for m in messages if m['role'] == 'user']
        ai_clarifications = [
            m['content_text'] 
            for m in messages 
            if m['role'] == 'assistant' and any(
                phrase in m['content_text'].lower() 
                for phrase in ['you might also', 'additionally', 'however', 'but note']
            )
        ]
        
        prompt = f"""
        Identify knowledge gaps and areas for further exploration based on this conversation.
        
        User Questions (showing potential gaps):
        {' | '.join(user_questions[:10])}
        
        AI Clarifications (showing complexity):
        {' | '.join(ai_clarifications[:5])}
        
        Identify:
        1. Unresolved questions - What wasn't fully answered?
        2. Implied gaps - What background knowledge was missing?
        3. Next learning steps - What should be learned next?
        4. Related topics - What related areas to explore?
        5. Depth opportunities - Where to go deeper?
        
        Format as JSON:
        {{
            "gaps": ["gap1", "gap2"],
            "missing_prerequisites": ["prerequisite1"],
            "recommended_next_topics": ["topic1", "topic2"],
            "depth_opportunities": ["area1", "area2"],
            "confidence_score": 0.0-1.0
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=400,
            temperature=0.4
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "gaps": [],
                "missing_prerequisites": [],
                "recommended_next_topics": [],
                "depth_opportunities": [],
                "confidence_score": 0.5
            }
    
    async def _extract_actionable_insights(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract actionable insights and next steps from the conversation."""
        
        # Focus on solution-oriented messages
        solution_messages = [
            m for m in messages 
            if m['role'] == 'assistant' and len(m['content_text']) > 200
        ][:5]
        
        prompt = f"""
        Extract actionable insights and next steps from this conversation.
        
        Key messages:
        {self._build_conversation_text(solution_messages[:3])}
        
        Extract:
        1. Action items - Concrete things to do
        2. Best practices mentioned - Guidelines to follow
        3. Tools/resources recommended - What to use
        4. Warnings/pitfalls - What to avoid
        5. Implementation steps - How to apply learnings
        
        Format as JSON:
        {{
            "action_items": ["action1", "action2"],
            "best_practices": ["practice1", "practice2"],
            "recommended_resources": [{{"type": "tool", "name": "X", "purpose": "Y"}}],
            "warnings": ["warning1"],
            "implementation_roadmap": ["step1", "step2"]
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "action_items": [],
                "best_practices": [],
                "recommended_resources": [],
                "warnings": [],
                "implementation_roadmap": []
            }
    
    async def _analyze_user_context(self, messages: List[Dict]) -> Dict[str, Any]:
        """Understand the user's context, goals, and background."""
        
        user_messages = [m for m in messages if m['role'] == 'user'][:8]
        
        prompt = f"""
        Analyze the user's context and background from their messages.
        
        User messages:
        {self._build_conversation_text(user_messages)}
        
        Determine:
        1. Experience level - Beginner, intermediate, advanced?
        2. Primary goal - What are they trying to achieve?
        3. Use case - Personal project, work, learning?
        4. Technical background - What do they already know?
        5. Learning style - How do they ask questions?
        
        Format as JSON:
        {{
            "experience_level": "beginner|intermediate|advanced",
            "primary_goal": "Description of main objective",
            "use_case": "personal|professional|educational|research",
            "apparent_skills": ["skill1", "skill2"],
            "learning_style": "systematic|exploratory|practical|theoretical",
            "engagement_level": "high|medium|low"
        }}
        """
        
        response = await self.ai_service.complete(
            prompt=prompt,
            max_tokens=300,
            temperature=0.4
        )
        
        try:
            return json.loads(response.strip())
        except:
            return {
                "experience_level": "intermediate",
                "primary_goal": "Unknown",
                "use_case": "personal",
                "apparent_skills": [],
                "learning_style": "exploratory",
                "engagement_level": "medium"
            }
    
    async def _extract_code_and_solutions(self, messages: List[Dict]) -> Dict[str, Any]:
        """Extract code snippets, technical solutions, and implementation details."""
        
        code_snippets = []
        solutions = []
        
        for msg in messages:
            if msg['role'] == 'assistant':
                # Extract code blocks
                code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', msg['content_text'], re.DOTALL)
                for code in code_blocks:
                    code_snippets.append({
                        "code": code[:500],  # Limit size
                        "context": msg['content_text'][:200]
                    })
                
                # Extract solution patterns
                if any(word in msg['content_text'].lower() for word in ['solution', 'fix', 'solve', 'approach']):
                    solutions.append(msg['content_text'][:300])
        
        return {
            "code_snippets": code_snippets[:10],  # Limit to 10
            "solution_count": len(solutions),
            "has_implementation": len(code_snippets) > 0,
            "primary_language": self._detect_primary_language(code_snippets),
            "solution_types": self._categorize_solutions(solutions)
        }
    
    async def _process_message_insights(self, conversation_id: UUID, messages: List[Dict]):
        """Process individual messages to extract insights."""
        
        async for conn in get_db_connection():
            for msg in messages:
                if msg['role'] == 'assistant' and len(msg['content_text']) > 100:
                    # Extract key points from this message
                    summary = self._summarize_message(msg['content_text'])
                    key_points = self._extract_key_points(msg['content_text'])
                    concepts = self._extract_concepts(msg['content_text'])
                    
                    # Update message with insights
                    await conn.execute("""
                        UPDATE ai_conversation_messages
                        SET summary = $1,
                            key_points = $2,
                            concepts_introduced = $3
                        WHERE id = $4
                    """, 
                        summary,
                        key_points,
                        concepts,
                        msg['id']
                    )
    
    async def _create_intelligent_embeddings(
        self, 
        conversation_id: UUID,
        summary: Dict,
        concepts: Dict,
        learning_journey: Dict
    ):
        """Create enhanced embeddings for intelligent search."""
        
        try:
            # Get the item_id that's linked to this conversation
            async for conn in get_db_connection():
                item_id = await conn.fetchval("""
                    SELECT item_id FROM ai_conversation_search_items 
                    WHERE conversation_id = $1
                """, conversation_id)
                
                if not item_id:
                    logger.warning(f"No linked item found for conversation {conversation_id}")
                    return
            
            # Build rich embedding text
            embedding_text = f"""
            {summary.get('full_summary', '')}
            
            Topics: {', '.join(concepts.get('topics', []))}
            Technologies: {', '.join(concepts.get('technologies', {}).get('languages', []))}
            Learning: {', '.join(learning_journey.get('key_learnings', []))}
            """
            
            # Create and store embedding
            await multimodal_embedding_service.initialize()
            embedding_data = await multimodal_embedding_service.create_text_embedding(embedding_text)
            
            # Store with the correct item_id
            await multimodal_embedding_service.store_embedding(
                str(item_id),
                embedding_data
            )
            
        except Exception as e:
            logger.error(f"Error creating intelligent embeddings: {e}")
            # Don't fail the whole process if embeddings fail
    
    async def _update_conversation_intelligence(
        self,
        conversation_id: UUID,
        summary: str,
        key_topics: List[str],
        learning_points: List[str],
        user_journey: str,
        knowledge_gaps: List[str]
    ):
        """Update conversation with intelligence analysis results."""
        
        async for conn in get_db_connection():
            await conn.execute("""
                UPDATE ai_conversation_imports
                SET summary = $1,
                    key_topics = $2,
                    learning_points = $3,
                    user_journey = $4,
                    knowledge_gaps = $5,
                    processing_status = 'completed',
                    updated_at = NOW()
                WHERE id = $6
            """,
                summary,
                key_topics,
                learning_points,
                user_journey,
                knowledge_gaps,
                conversation_id
            )
    
    async def _mark_processing_failed(self, conversation_id: UUID, error: str):
        """Mark conversation processing as failed."""
        
        async for conn in get_db_connection():
            await conn.execute("""
                UPDATE ai_conversation_imports
                SET processing_status = 'failed',
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{processing_error}', 
                        $1::jsonb
                    ),
                    updated_at = NOW()
                WHERE id = $2
            """,
                json.dumps({"error": error, "timestamp": datetime.now().isoformat()}),
                conversation_id
            )
    
    # Helper methods
    def _build_conversation_text(self, messages: List[Dict]) -> str:
        """Build readable conversation text from messages."""
        
        text_parts = []
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content_text'][:500]  # Limit each message
            text_parts.append(f"{role}: {content}")
        
        return "\n\n".join(text_parts)
    
    def _extract_topics_fallback(self, text: str) -> List[str]:
        """Simple keyword extraction as fallback."""
        
        # Common tech keywords
        keywords = re.findall(
            r'\b(python|javascript|react|api|database|function|class|method|error|bug|' +
            r'performance|optimization|algorithm|data structure|frontend|backend|' +
            r'machine learning|ai|deployment|testing|debugging)\b',
            text.lower()
        )
        
        # Count frequencies and return top topics
        from collections import Counter
        topic_counts = Counter(keywords)
        return [topic for topic, _ in topic_counts.most_common(10)]
    
    def _summarize_message(self, text: str) -> str:
        """Create a one-line summary of a message."""
        
        # Simple extractive summary - first substantial sentence
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                return sentence.strip()[:150]
        
        return text[:150]
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from message text."""
        
        key_points = []
        
        # Look for numbered lists
        numbered = re.findall(r'\d+\.\s*([^\n]+)', text)
        key_points.extend(numbered[:5])
        
        # Look for bullet points
        bullets = re.findall(r'[-*]\s*([^\n]+)', text)
        key_points.extend(bullets[:5])
        
        return key_points[:8]  # Limit to 8 points
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract technical concepts mentioned."""
        
        # Look for quoted terms and code-like words
        quoted = re.findall(r'`([^`]+)`', text)
        technical = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text)  # CamelCase
        
        concepts = list(set(quoted + technical))
        return concepts[:10]
    
    def _detect_primary_language(self, code_snippets: List[Dict]) -> str:
        """Detect the primary programming language from code snippets."""
        
        if not code_snippets:
            return "unknown"
        
        language_hints = {
            'python': ['def ', 'import ', 'print(', 'self.'],
            'javascript': ['const ', 'let ', 'function ', '=>'],
            'typescript': ['interface ', 'type ', ': string', ': number'],
            'java': ['public class', 'private ', 'void ', 'new '],
            'go': ['func ', 'package ', ':= ', 'fmt.'],
            'rust': ['fn ', 'let mut', 'impl ', '::'],
        }
        
        language_scores = {}
        for lang, hints in language_hints.items():
            score = sum(
                1 for snippet in code_snippets
                for hint in hints
                if hint in snippet.get('code', '')
            )
            if score > 0:
                language_scores[lang] = score
        
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return "unknown"
    
    def _categorize_solutions(self, solutions: List[str]) -> List[str]:
        """Categorize types of solutions provided."""
        
        categories = []
        
        solution_text = ' '.join(solutions).lower()
        
        if 'error' in solution_text or 'fix' in solution_text:
            categories.append('debugging')
        if 'implement' in solution_text or 'create' in solution_text:
            categories.append('implementation')
        if 'optimize' in solution_text or 'performance' in solution_text:
            categories.append('optimization')
        if 'refactor' in solution_text or 'improve' in solution_text:
            categories.append('refactoring')
        if 'explain' in solution_text or 'understand' in solution_text:
            categories.append('explanation')
        
        return categories or ['general']


# Singleton instance
conversation_intelligence = ConversationIntelligenceAgent()