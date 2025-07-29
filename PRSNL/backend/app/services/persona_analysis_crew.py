"""
PersonaAnalysisCrew - Multi-Agent System for Dreamscape Feature

This Crew AI implementation analyzes user behavior patterns to build
comprehensive multi-dimensional personas for intelligent personalization.

Agents:
1. TechnicalProfileAgent - Analyzes coding/tech behavior
2. LifestylePatternAgent - Identifies lifestyle and interests
3. LearningStyleAgent - Determines learning preferences
4. CrossDomainAgent - Discovers cross-domain connections
5. PersonaOrchestratorAgent - Synthesizes all insights

Created: January 2025
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db_pool
from app.services.behavior_tracking_service import BehaviorTrackingService

logger = logging.getLogger(__name__)


class PersonaAnalysisInput(BaseModel):
    """Input model for persona analysis"""
    user_id: UUID = Field(description="User ID to analyze")
    analysis_depth: str = Field(default="standard", description="Analysis depth: light, standard, deep")
    focus_areas: List[str] = Field(default=[], description="Specific areas to focus on")


class BehaviorDataTool(BaseTool):
    """Tool for accessing user behavior data"""
    
    name: str = "behavior_data_tool"
    description: str = "Retrieves user behavior data for analysis"
    behavior_service: BehaviorTrackingService = None
    
    def __init__(self):
        super().__init__()
        self.behavior_service = BehaviorTrackingService()
    
    def _run(self, user_id: str, days: int = 30) -> str:
        """Get behavior data for a user"""
        try:
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(
                self.behavior_service.get_user_behavior_summary(UUID(user_id), days)
            )
            return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Error retrieving behavior data: {e}")
            return f"Error: {str(e)}"


class ContentAnalysisTool(BaseTool):
    """Tool for analyzing user's content interactions"""
    
    name: str = "content_analysis_tool"
    description: str = "Analyzes user's content interaction patterns"
    
    def _run(self, user_id: str) -> str:
        """Analyze content interaction patterns"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._analyze_content_patterns(UUID(user_id)))
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return f"Error: {str(e)}"
    
    async def _analyze_content_patterns(self, user_id: UUID) -> str:
        """Analyze detailed content patterns"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    # Content type analysis
                    content_analysis = await connection.fetch("""
                        SELECT 
                            ub.item_type,
                            COUNT(*) as interactions,
                            AVG(ub.duration_seconds) as avg_engagement,
                            COUNT(DISTINCT ub.item_id) as unique_items,
                            MIN(ub.created_at) as first_interaction,
                            MAX(ub.created_at) as last_interaction
                        FROM user_behaviors ub
                        WHERE ub.user_id = $1 
                            AND ub.item_type IS NOT NULL
                            AND ub.created_at >= NOW() - INTERVAL '60 days'
                        GROUP BY ub.item_type
                        ORDER BY interactions DESC
                    """, user_id)
                    
                    # Tags analysis
                    tags_analysis = await connection.fetch("""
                        SELECT 
                            t.name as tag,
                            COUNT(DISTINCT ub.item_id) as tagged_items,
                            COUNT(ub.id) as total_interactions,
                            AVG(ub.duration_seconds) as avg_engagement
                        FROM user_behaviors ub
                        JOIN item_tags it ON ub.item_id = it.item_id
                        JOIN tags t ON it.tag_id = t.id
                        WHERE ub.user_id = $1
                            AND ub.created_at >= NOW() - INTERVAL '60 days'
                        GROUP BY t.name
                        ORDER BY total_interactions DESC
                        LIMIT 20
                    """, user_id)
                    
                    # Search patterns
                    search_patterns = await connection.fetch("""
                        SELECT 
                            ub.context->>'query' as search_query,
                            COUNT(*) as frequency,
                            array_agg(DISTINCT ub.context->>'source') as sources
                        FROM user_behaviors ub
                        WHERE ub.user_id = $1 
                            AND ub.action_type = 'search'
                            AND ub.context->>'query' IS NOT NULL
                            AND ub.created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY ub.context->>'query'
                        ORDER BY frequency DESC
                        LIMIT 10
                    """, user_id)
                    
                    return json.dumps({
                        "content_types": [dict(row) for row in content_analysis],
                        "popular_tags": [dict(row) for row in tags_analysis],
                        "search_patterns": [dict(row) for row in search_patterns]
                    }, default=str)
                    
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return json.dumps({"error": str(e)})


class PersonaAnalysisCrew:
    """Crew AI system for multi-dimensional persona analysis"""
    
    def __init__(self):
        # Configure Azure OpenAI for CrewAI agents
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI API key not configured")
        if not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI endpoint not configured")
            
        # Use the configured API version from settings
        api_version = settings.AZURE_OPENAI_API_VERSION
        
        # Set environment variables for LiteLLM Azure OpenAI compatibility
        # LiteLLM requires specific environment variable naming
        os.environ["AZURE_API_KEY"] = settings.AZURE_OPENAI_API_KEY
        os.environ["AZURE_API_BASE"] = settings.AZURE_OPENAI_ENDPOINT
        os.environ["AZURE_API_VERSION"] = api_version
        os.environ["AZURE_API_TYPE"] = "azure"
        
        # Create LLM instance specifically configured for Azure OpenAI
        # Use AzureChatOpenAI with correct Azure configuration
        from langchain_openai import AzureChatOpenAI
        
        # Use azure/ prefix for LiteLLM compatibility
        model_name = f"azure/{settings.AZURE_OPENAI_DEPLOYMENT}"
        
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=api_version,
            temperature=0.7,
            max_tokens=2000,
            model_name=model_name  # Use azure/ prefix for LiteLLM
        )
        
        self.behavior_service = BehaviorTrackingService()
        self.behavior_tool = BehaviorDataTool()
        self.content_tool = ContentAnalysisTool()
        
        # Initialize agents
        self.technical_agent = self._create_technical_agent()
        self.lifestyle_agent = self._create_lifestyle_agent()
        self.learning_agent = self._create_learning_agent()
        self.cross_domain_agent = self._create_cross_domain_agent()
        self.orchestrator_agent = self._create_orchestrator_agent()
    
    def _create_technical_agent(self) -> Agent:
        """Agent focused on technical skills and programming behavior"""
        return Agent(
            role="Technical Profile Analyst",
            goal="Analyze user's technical skills, programming languages, tools, and development patterns",
            backstory="""You are an expert in analyzing technical behavior patterns. 
            You understand programming languages, development tools, frameworks, and can 
            identify skill levels and growth trajectories from user interactions with 
            technical content.""",
            tools=[self.behavior_tool, self.content_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _create_lifestyle_agent(self) -> Agent:
        """Agent focused on lifestyle patterns and interests"""
        return Agent(
            role="Lifestyle Pattern Analyst",
            goal="Identify user's lifestyle patterns, interests, and activity preferences",
            backstory="""You are an expert in behavioral psychology and lifestyle analysis.
            You can identify patterns in user activity, interests, hobbies, and lifestyle
            choices from their content consumption and interaction patterns.""",
            tools=[self.behavior_tool, self.content_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _create_learning_agent(self) -> Agent:
        """Agent focused on learning style and educational preferences"""
        return Agent(
            role="Learning Style Analyst",
            goal="Determine user's learning preferences, study habits, and educational patterns",
            backstory="""You are an expert in educational psychology and learning analytics.
            You can identify how users prefer to learn, their attention spans, complexity
            preferences, and optimal learning conditions from their behavior patterns.""",
            tools=[self.behavior_tool, self.content_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _create_cross_domain_agent(self) -> Agent:
        """Agent focused on finding cross-domain connections"""
        return Agent(
            role="Cross-Domain Connection Analyst",
            goal="Discover connections between different domains and identify cross-pollination opportunities",
            backstory="""You are an expert in systems thinking and pattern recognition.
            You excel at finding unexpected connections between seemingly unrelated domains,
            identifying how skills and interests can combine in innovative ways.""",
            tools=[self.behavior_tool, self.content_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _create_orchestrator_agent(self) -> Agent:
        """Master agent that synthesizes all insights"""
        return Agent(
            role="Persona Orchestrator",
            goal="Synthesize insights from all agents into a comprehensive user persona",
            backstory="""You are a master analyst who excels at synthesizing complex
            information from multiple sources. You create comprehensive, actionable
            user personas that capture technical, lifestyle, learning, and cross-domain
            insights in a coherent, useful format.""",
            tools=[],
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
    
    async def analyze_user_persona(
        self, 
        user_id: UUID,
        analysis_depth: str = "standard",
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive persona analysis for a user
        
        Args:
            user_id: User to analyze
            analysis_depth: How deep to analyze (light, standard, deep)
            focus_areas: Specific areas to focus on
        
        Returns:
            Comprehensive persona analysis
        """
        try:
            logger.info(f"Starting persona analysis for user {user_id}")
            
            # Create tasks for each agent
            technical_task = Task(
                description=f"""
                Analyze the technical profile for user {user_id}. Focus on:
                1. Programming languages and frameworks used
                2. Development tools and environments
                3. Technical skill levels and progression
                4. Project types and complexity preferences
                5. Learning velocity in technical domains
                
                Provide a comprehensive technical profile with:
                - Primary languages and skill levels
                - Preferred tools and technologies
                - Domain expertise areas
                - Learning patterns and growth trajectory
                """,
                agent=self.technical_agent,
                expected_output="Detailed technical profile with skills, tools, and learning patterns"
            )
            
            lifestyle_task = Task(
                description=f"""
                Analyze the lifestyle patterns for user {user_id}. Focus on:
                1. Activity patterns and timing preferences
                2. Interest areas and hobbies
                3. Content consumption habits
                4. Social interaction patterns
                5. Work-life balance indicators
                
                Provide a comprehensive lifestyle profile with:
                - Primary interests and hobbies
                - Activity timing preferences
                - Content format preferences
                - Social engagement patterns
                """,
                agent=self.lifestyle_agent,
                expected_output="Detailed lifestyle profile with interests, patterns, and preferences"
            )
            
            learning_task = Task(
                description=f"""
                Analyze the learning style for user {user_id}. Focus on:
                1. Learning format preferences (video, text, hands-on)
                2. Attention span and session patterns
                3. Complexity tolerance and progression speed
                4. Practice vs theory preferences
                5. Feedback and validation needs
                
                Provide a comprehensive learning profile with:
                - Preferred learning formats and methods
                - Optimal session characteristics
                - Difficulty progression preferences
                - Motivation and goal patterns
                """,
                agent=self.learning_agent,
                expected_output="Detailed learning style profile with methods, pacing, and preferences"
            )
            
            cross_domain_task = Task(
                description=f"""
                Analyze cross-domain connections for user {user_id}. Focus on:
                1. Connections between technical and personal interests
                2. Skill transfer opportunities
                3. Innovation potential from domain intersections
                4. Project ideas from combined interests
                5. Unique patterns and insights
                
                Provide cross-domain insights with:
                - Identified domain connections
                - Potential synergies and opportunities
                - Project and innovation suggestions
                - Unique behavioral patterns
                """,
                agent=self.cross_domain_agent,
                expected_output="Cross-domain connections and innovation opportunities"
            )
            
            synthesis_task = Task(
                description=f"""
                Synthesize all persona insights for user {user_id} into a comprehensive profile.
                Use the outputs from technical, lifestyle, learning, and cross-domain analyses.
                
                Create a master persona that includes:
                1. Overall user archetype and characteristics
                2. Key strengths and growth areas
                3. Optimal content and experience recommendations
                4. Personalization strategies
                5. Life phase and trajectory insights
                
                Format as a structured persona profile suitable for AI personalization.
                """,
                agent=self.orchestrator_agent,
                expected_output="Comprehensive user persona with actionable insights",
                context=[technical_task, lifestyle_task, learning_task, cross_domain_task]
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[
                    self.technical_agent,
                    self.lifestyle_agent, 
                    self.learning_agent,
                    self.cross_domain_agent,
                    self.orchestrator_agent
                ],
                tasks=[
                    technical_task,
                    lifestyle_task,
                    learning_task,
                    cross_domain_task,
                    synthesis_task
                ],
                verbose=True,
                process="sequential"  # Execute tasks in order
            )
            
            # Execute the crew analysis
            result = crew.kickoff()
            
            # Process and structure the results
            persona_data = await self._process_crew_results(user_id, result)
            
            # Save to database
            await self._save_persona_to_database(user_id, persona_data)
            
            logger.info(f"Completed persona analysis for user {user_id}")
            return persona_data
            
        except Exception as e:
            logger.error(f"Error in persona analysis: {e}")
            raise
    
    async def _process_crew_results(self, user_id: UUID, crew_result: Any) -> Dict[str, Any]:
        """Process crew results into structured persona data"""
        try:
            # Extract insights from crew result
            insights = str(crew_result) if crew_result else ""
            
            # Get additional behavioral metrics
            behavior_summary = await self.behavior_service.get_user_behavior_summary(user_id)
            learning_velocity = await self.behavior_service.get_learning_velocity(user_id)
            interest_evolution = await self.behavior_service.detect_interest_evolution(user_id)
            
            # Structure the persona data
            persona_data = {
                "user_id": str(user_id),
                "analysis_timestamp": datetime.now().isoformat(),
                "crew_insights": insights,
                "technical_profile": self._extract_technical_profile(insights, behavior_summary),
                "lifestyle_profile": self._extract_lifestyle_profile(insights, behavior_summary),
                "learning_style": self._extract_learning_style(insights, behavior_summary),
                "cross_domain_insights": self._extract_cross_domain_insights(insights),
                "life_phase": self._determine_life_phase(behavior_summary, learning_velocity),
                "interests_evolution": interest_evolution,
                "behavioral_metrics": {
                    "learning_velocity": learning_velocity,
                    "engagement_score": self._calculate_engagement_score(behavior_summary),
                    "diversity_score": self._calculate_diversity_score(behavior_summary)
                },
                "recommendations": self._generate_recommendations(insights, behavior_summary)
            }
            
            return persona_data
            
        except Exception as e:
            logger.error(f"Error processing crew results: {e}")
            return {"error": str(e), "user_id": str(user_id)}
    
    def _extract_technical_profile(self, insights: str, behavior_data: Dict) -> Dict[str, Any]:
        """Extract technical profile from insights"""
        # This would use more sophisticated NLP in production
        # For now, we'll extract from behavior data and make reasonable inferences
        
        content_prefs = behavior_data.get("content_preferences", [])
        tech_content = [c for c in content_prefs if c.get("item_type") in ["code", "article", "repository"]]
        
        return {
            "primary_languages": self._infer_languages_from_content(tech_content),
            "skill_levels": self._infer_skill_levels(behavior_data),
            "domains": self._infer_technical_domains(content_prefs),
            "tools": self._infer_preferred_tools(behavior_data),
            "learning_velocity": behavior_data.get("behavioral_insights", {}).get("engagement_insights", [])
        }
    
    def _extract_lifestyle_profile(self, insights: str, behavior_data: Dict) -> Dict[str, Any]:
        """Extract lifestyle profile from insights"""
        activity_patterns = behavior_data.get("activity_patterns", [])
        
        return {
            "interests": self._infer_interests_from_behavior(behavior_data),
            "activity_patterns": self._analyze_activity_timing(activity_patterns),
            "content_preferences": self._analyze_content_preferences(behavior_data)
        }
    
    def _extract_learning_style(self, insights: str, behavior_data: Dict) -> Dict[str, Any]:
        """Extract learning style from insights"""
        engagement_metrics = behavior_data.get("engagement_metrics", {})
        
        return {
            "preferred_formats": self._infer_learning_formats(behavior_data),
            "attention_span": self._classify_attention_span(engagement_metrics),
            "complexity_preference": self._infer_complexity_preference(behavior_data),
            "learning_goals": ["skill_development", "career_advancement"]  # Would be inferred
        }
    
    def _extract_cross_domain_insights(self, insights: str) -> Dict[str, Any]:
        """Extract cross-domain connections from insights"""
        return {
            "connections": [],  # Would be extracted from crew analysis
            "project_potential": [],  # Would be generated from connections
            "innovation_opportunities": []
        }
    
    def _determine_life_phase(self, behavior_data: Dict, learning_velocity: float) -> str:
        """Determine user's life phase based on behavior patterns"""
        engagement = behavior_data.get("engagement_metrics", {})
        
        # Handle None learning_velocity
        if learning_velocity is None:
            learning_velocity = 0.0
        
        if learning_velocity > 0.7 and engagement.get("total_actions", 0) > 50:
            return "early_career"
        elif learning_velocity > 0.5:
            return "mid_career"
        else:
            return "experienced"
    
    def _calculate_engagement_score(self, behavior_data: Dict) -> float:
        """Calculate overall engagement score"""
        metrics = behavior_data.get("engagement_metrics", {})
        
        active_days = metrics.get("active_days", 0)
        total_actions = metrics.get("total_actions", 0)
        unique_items = metrics.get("unique_items_interacted", 0)
        
        if active_days == 0:
            return 0.0
        
        # Normalize scores
        activity_score = min(1.0, active_days / 30.0)  # Max 30 days
        interaction_score = min(1.0, total_actions / 100.0)  # Max 100 actions
        diversity_score = min(1.0, unique_items / 50.0)  # Max 50 unique items
        
        return round((activity_score + interaction_score + diversity_score) / 3.0, 2)
    
    def _calculate_diversity_score(self, behavior_data: Dict) -> float:
        """Calculate content diversity score"""
        content_prefs = behavior_data.get("content_preferences", [])
        return min(1.0, len(content_prefs) / 5.0)  # Max 5 content types
    
    def _generate_recommendations(self, insights: str, behavior_data: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        engagement_insights = behavior_data.get("behavioral_insights", {}).get("engagement_insights", [])
        
        if "Power user" in str(engagement_insights):
            recommendations.append("Consider advanced features and power-user tools")
        elif "Casual user" in str(engagement_insights):
            recommendations.append("Focus on simple, intuitive interfaces")
        
        return recommendations
    
    # Helper methods for inference (simplified for demo)
    def _infer_languages_from_content(self, tech_content: List) -> List[str]:
        """Infer programming languages from content"""
        # Would use more sophisticated analysis in production
        return ["Python", "JavaScript"]  # Placeholder
    
    def _infer_skill_levels(self, behavior_data: Dict) -> Dict[str, str]:
        """Infer skill levels from behavior"""
        return {"Python": "intermediate", "JavaScript": "beginner"}  # Placeholder
    
    def _infer_technical_domains(self, content_prefs: List) -> List[str]:
        """Infer technical domains"""
        return ["Web Development", "Data Science"]  # Placeholder
    
    def _infer_preferred_tools(self, behavior_data: Dict) -> List[str]:
        """Infer preferred development tools"""
        return ["VSCode", "Git"]  # Placeholder
    
    def _infer_interests_from_behavior(self, behavior_data: Dict) -> List[str]:
        """Infer personal interests"""
        return ["technology", "learning"]  # Placeholder
    
    def _analyze_activity_timing(self, activity_patterns: List) -> Dict[str, float]:
        """Analyze activity timing preferences"""
        return {"morning": 0.3, "afternoon": 0.4, "evening": 0.3}  # Placeholder
    
    def _analyze_content_preferences(self, behavior_data: Dict) -> Dict[str, float]:
        """Analyze content format preferences"""
        return {"article": 0.6, "video": 0.4}  # Placeholder
    
    def _infer_learning_formats(self, behavior_data: Dict) -> List[str]:
        """Infer preferred learning formats"""
        return ["hands-on", "visual"]  # Placeholder
    
    def _classify_attention_span(self, engagement_metrics: Dict) -> str:
        """Classify attention span based on engagement"""
        avg_duration = engagement_metrics.get("avg_session_duration", 0)
        
        if avg_duration > 300:  # 5 minutes
            return "long"
        elif avg_duration > 120:  # 2 minutes
            return "medium"
        else:
            return "short"
    
    def _infer_complexity_preference(self, behavior_data: Dict) -> str:
        """Infer complexity preference"""
        return "moderate"  # Placeholder
    
    async def _save_persona_to_database(self, user_id: UUID, persona_data: Dict[str, Any]):
        """Save persona analysis to database"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    # Upsert persona data
                    await connection.execute("""
                        INSERT INTO user_personas (
                            user_id, technical_profile, lifestyle_profile, 
                            learning_style, life_phase, phase_confidence,
                            interests_evolution, cross_domain_insights,
                            last_analyzed_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (user_id) DO UPDATE SET
                            technical_profile = EXCLUDED.technical_profile,
                            lifestyle_profile = EXCLUDED.lifestyle_profile,
                            learning_style = EXCLUDED.learning_style,
                            life_phase = EXCLUDED.life_phase,
                            phase_confidence = EXCLUDED.phase_confidence,
                            interests_evolution = EXCLUDED.interests_evolution,
                            cross_domain_insights = EXCLUDED.cross_domain_insights,
                            last_analyzed_at = EXCLUDED.last_analyzed_at,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id,
                    json.dumps(persona_data.get("technical_profile", {})),
                    json.dumps(persona_data.get("lifestyle_profile", {})),
                    json.dumps(persona_data.get("learning_style", {})),
                    persona_data.get("life_phase"),
                    0.8,  # Default confidence
                    json.dumps(persona_data.get("interests_evolution", {})),
                    json.dumps(persona_data.get("cross_domain_insights", {})),
                    datetime.now()
                    )
                    
                    logger.info(f"Saved persona analysis for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error saving persona to database: {e}")
            raise

    async def get_user_persona(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve existing persona for a user"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    persona = await connection.fetchrow("""
                        SELECT * FROM user_personas WHERE user_id = $1
                    """, user_id)
                    
                    if persona:
                        return dict(persona)
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving persona: {e}")
            return None
    
    async def update_persona_insights(self, user_id: UUID, new_insights: Dict[str, Any]):
        """Update specific persona insights without full reanalysis"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    await connection.execute("""
                        UPDATE user_personas 
                        SET cross_domain_insights = $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $1
                    """, user_id, json.dumps(new_insights))
                    
        except Exception as e:
            logger.error(f"Error updating persona insights: {e}")
            raise