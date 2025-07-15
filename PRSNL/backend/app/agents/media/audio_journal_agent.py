"""
Audio Journal Agent - Migrated to Crew.ai

This agent processes audio journal entries, transcribes content, and extracts insights.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.media_tools import AudioTranscriptionTool
from app.tools.ai_tools import (
    SummaryGeneratorTool,
    EntityExtractorTool,
    TagSuggesterTool,
    EnhancementSuggestionTool
)
from app.tools.knowledge_tools import ConnectionFinderTool

logger = logging.getLogger(__name__)


@register_agent("audio_journal_processor")
class AudioJournalAgent(PRSNLBaseAgent):
    """
    Audio Journal Agent
    
    Specializes in processing audio journal entries, extracting personal insights,
    and creating structured knowledge from reflective audio content.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Audio Journal Processor")
        goal = kwargs.pop("goal", 
            "Process audio journal entries to extract insights, emotions, and patterns "
            "that support personal growth and knowledge development"
        )
        backstory = kwargs.pop("backstory",
            "You are a skilled listener and analyst who specializes in understanding "
            "personal reflections and journal entries. Your empathetic approach to "
            "content analysis helps extract meaningful insights from audio recordings "
            "while respecting the personal nature of journal content. You excel at "
            "identifying patterns, emotions, and growth opportunities in reflective "
            "audio content, making you invaluable for personal knowledge management."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                AudioTranscriptionTool(),
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                TagSuggesterTool(),
                EnhancementSuggestionTool(),
                ConnectionFinderTool()
            ]
        
        # Call parent constructor
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
    
    def get_specialized_instructions(self) -> str:
        """Get specialized instructions for this agent"""
        return """
        When processing audio journals:
        1. Transcribe audio content with high accuracy
        2. Identify emotional tone and sentiment
        3. Extract personal insights and reflections
        4. Identify recurring themes and patterns
        5. Recognize goals, challenges, and achievements
        6. Extract actionable items and commitments
        7. Identify learning moments and growth areas
        8. Create relevant tags for personal organization
        9. Find connections to previous journal entries
        10. Generate reflection prompts and questions
        11. Assess mood and emotional state
        12. Identify relationships and social connections mentioned
        
        Maintain sensitivity to personal content while creating
        valuable insights that support self-reflection and growth.
        """
    
    def analyze_emotional_content(self, transcription: str) -> Dict[str, Any]:
        """Analyze emotional content and sentiment in the journal entry"""
        emotional_analysis = {
            "overall_sentiment": "neutral",
            "emotions_detected": [],
            "emotional_intensity": 0.5,
            "mood_indicators": [],
            "emotional_journey": [],
            "concerns_raised": [],
            "positive_moments": []
        }
        
        # Simple emotion detection based on keywords
        emotion_keywords = {
            "happy": ["happy", "joy", "excited", "pleased", "grateful", "wonderful"],
            "sad": ["sad", "disappointed", "down", "upset", "hurt", "loss"],
            "anxious": ["worried", "nervous", "anxious", "stressed", "overwhelmed"],
            "angry": ["angry", "frustrated", "annoyed", "irritated", "mad"],
            "confident": ["confident", "proud", "accomplished", "successful", "strong"],
            "confused": ["confused", "uncertain", "lost", "unclear", "puzzled"]
        }
        
        text_lower = transcription.lower()
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                emotional_analysis["emotions_detected"].append(emotion)
        
        # Determine overall sentiment
        positive_emotions = ["happy", "confident"]
        negative_emotions = ["sad", "anxious", "angry", "confused"]
        
        positive_count = sum(1 for e in emotional_analysis["emotions_detected"] if e in positive_emotions)
        negative_count = sum(1 for e in emotional_analysis["emotions_detected"] if e in negative_emotions)
        
        if positive_count > negative_count:
            emotional_analysis["overall_sentiment"] = "positive"
            emotional_analysis["emotional_intensity"] = 0.7
        elif negative_count > positive_count:
            emotional_analysis["overall_sentiment"] = "negative"
            emotional_analysis["emotional_intensity"] = 0.8
        
        return emotional_analysis
    
    def extract_personal_insights(self, transcription: str) -> Dict[str, Any]:
        """Extract personal insights and reflections"""
        insights = {
            "key_realizations": [],
            "goals_mentioned": [],
            "challenges_identified": [],
            "achievements_noted": [],
            "learning_moments": [],
            "decisions_made": [],
            "relationships_discussed": [],
            "future_plans": []
        }
        
        # Pattern matching for different types of insights
        insight_patterns = {
            "realizations": ["I realized", "I understand", "I see now", "it occurred to me"],
            "goals": ["I want to", "my goal is", "I plan to", "I hope to"],
            "challenges": ["struggling with", "difficult", "challenge", "problem"],
            "achievements": ["accomplished", "achieved", "succeeded", "completed"],
            "learning": ["I learned", "discovered", "found out", "now I know"],
            "decisions": ["I decided", "I chose", "I'm going to", "I will"],
            "relationships": ["talked to", "met with", "relationship", "friend", "family"],
            "future": ["tomorrow", "next week", "planning", "looking forward"]
        }
        
        text_lower = transcription.lower()
        
        for category, patterns in insight_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Extract context around the pattern
                    start_idx = text_lower.find(pattern)
                    if start_idx != -1:
                        # Get surrounding context (50 chars before and after)
                        context_start = max(0, start_idx - 50)
                        context_end = min(len(transcription), start_idx + len(pattern) + 100)
                        context = transcription[context_start:context_end].strip()
                        
                        if category == "realizations":
                            insights["key_realizations"].append(context)
                        elif category == "goals":
                            insights["goals_mentioned"].append(context)
                        elif category == "challenges":
                            insights["challenges_identified"].append(context)
                        elif category == "achievements":
                            insights["achievements_noted"].append(context)
                        elif category == "learning":
                            insights["learning_moments"].append(context)
                        elif category == "decisions":
                            insights["decisions_made"].append(context)
                        elif category == "relationships":
                            insights["relationships_discussed"].append(context)
                        elif category == "future":
                            insights["future_plans"].append(context)
        
        return insights
    
    def identify_recurring_themes(self, current_entry: Dict[str, Any], previous_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify recurring themes across journal entries"""
        themes = {
            "recurring_topics": [],
            "pattern_analysis": {},
            "theme_evolution": [],
            "consistency_indicators": [],
            "new_themes": []
        }
        
        # Simple theme tracking based on keywords
        current_tags = current_entry.get("tags", [])
        current_entities = current_entry.get("entities", [])
        
        if previous_entries:
            # Find common themes
            all_previous_tags = []
            all_previous_entities = []
            
            for entry in previous_entries:
                all_previous_tags.extend(entry.get("tags", []))
                all_previous_entities.extend(entry.get("entities", []))
            
            # Find recurring tags
            for tag in current_tags:
                if tag in all_previous_tags:
                    themes["recurring_topics"].append(tag)
                else:
                    themes["new_themes"].append(tag)
        
        return themes
    
    def generate_reflection_prompts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate follow-up reflection prompts based on the journal entry"""
        prompts = []
        
        # Extract insights and emotions
        insights = analysis_results.get("personal_insights", {})
        emotions = analysis_results.get("emotional_analysis", {})
        
        # Generate prompts based on challenges
        challenges = insights.get("challenges_identified", [])
        if challenges:
            prompts.append({
                "type": "problem_solving",
                "prompt": "What specific steps could you take to address the challenges you mentioned?",
                "category": "action_planning"
            })
        
        # Generate prompts based on achievements
        achievements = insights.get("achievements_noted", [])
        if achievements:
            prompts.append({
                "type": "celebration",
                "prompt": "How did you feel when you accomplished this? What contributed to your success?",
                "category": "gratitude"
            })
        
        # Generate prompts based on emotions
        dominant_emotions = emotions.get("emotions_detected", [])
        if "anxious" in dominant_emotions:
            prompts.append({
                "type": "anxiety_processing",
                "prompt": "What specific thoughts or situations are contributing to your anxiety? How can you address them?",
                "category": "emotional_processing"
            })
        
        # Generate prompts based on goals
        goals = insights.get("goals_mentioned", [])
        if goals:
            prompts.append({
                "type": "goal_refinement",
                "prompt": "What would success look like for this goal? What's the first small step you could take?",
                "category": "goal_setting"
            })
        
        # Add general reflection prompts
        prompts.extend([
            {
                "type": "gratitude",
                "prompt": "What three things are you most grateful for today?",
                "category": "positivity"
            },
            {
                "type": "learning",
                "prompt": "What's one thing you learned about yourself from this reflection?",
                "category": "self_awareness"
            },
            {
                "type": "growth",
                "prompt": "How have you grown or changed since your last journal entry?",
                "category": "personal_development"
            }
        ])
        
        return prompts[:5]  # Return top 5 prompts
    
    def create_personal_metadata(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for personal knowledge management"""
        metadata = {
            "entry_date": datetime.now().isoformat(),
            "mood_score": 0.5,
            "energy_level": "medium",
            "key_themes": [],
            "people_mentioned": [],
            "locations_mentioned": [],
            "activities_discussed": [],
            "privacy_level": "private",
            "follow_up_needed": False,
            "action_items": []
        }
        
        # Extract mood score from emotional analysis
        emotional_analysis = analysis_results.get("emotional_analysis", {})
        if emotional_analysis.get("overall_sentiment") == "positive":
            metadata["mood_score"] = 0.8
        elif emotional_analysis.get("overall_sentiment") == "negative":
            metadata["mood_score"] = 0.3
        
        # Extract people mentioned
        entities = analysis_results.get("entities", {})
        if "people" in entities:
            metadata["people_mentioned"] = entities["people"]
        
        # Extract locations
        if "locations" in entities:
            metadata["locations_mentioned"] = entities["locations"]
        
        # Check for action items
        insights = analysis_results.get("personal_insights", {})
        if insights.get("decisions_made") or insights.get("future_plans"):
            metadata["follow_up_needed"] = True
            metadata["action_items"] = insights.get("decisions_made", []) + insights.get("future_plans", [])
        
        return metadata


@register_agent("therapeutic_audio_processor")
class TherapeuticAudioProcessorAgent(AudioJournalAgent):
    """
    Specialized agent for processing therapeutic or counseling audio sessions
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add therapeutic-specific context
        self.backstory += (
            " You have additional training in therapeutic communication patterns "
            "and can identify therapeutic progress indicators while maintaining "
            "strict confidentiality and ethical standards."
        )
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for therapeutic audio processing"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional therapeutic audio processing:
        13. Identify therapeutic progress indicators
        14. Recognize coping strategies and techniques discussed
        15. Track therapeutic goals and outcomes
        16. Identify breakthrough moments and insights
        17. Monitor therapeutic alliance and rapport
        18. Assess risk factors and safety concerns
        19. Identify referral needs or resource requirements
        20. Maintain strict confidentiality and ethical standards
        
        Always prioritize client safety and therapeutic benefit
        while maintaining professional boundaries.
        """
    
    def assess_therapeutic_progress(self, session_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess therapeutic progress indicators"""
        progress_indicators = {
            "emotional_regulation": "stable",
            "insight_development": "moderate",
            "coping_skills": "developing",
            "goal_progress": "on_track",
            "therapeutic_alliance": "strong",
            "risk_assessment": "low",
            "recommendations": []
        }
        
        # Analyze emotional content for regulation
        emotional_analysis = session_analysis.get("emotional_analysis", {})
        if emotional_analysis.get("emotional_intensity", 0.5) < 0.3:
            progress_indicators["emotional_regulation"] = "improving"
        elif emotional_analysis.get("emotional_intensity", 0.5) > 0.8:
            progress_indicators["emotional_regulation"] = "needs_attention"
        
        return progress_indicators