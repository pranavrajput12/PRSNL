"""
Crawl.ai Multi-Agent System for PRSNL Second Brain

This module implements a multi-agent orchestration system using Crawl.ai
for advanced web crawling and content analysis, replacing AutoAgent.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db_pool
from app.services.crawl_ai_service import CrawlAIService, CrawlResult
from app.services.unified_ai_service import unified_ai_service
from app.services.cache import cache_service, CacheKeys
from app.services.media_agents import MEDIA_AGENTS, MediaAgentResult
from app.services.media_persistence_service import media_persistence_service
from app.services.job_persistence_service import JobPersistenceService

logger = logging.getLogger(__name__)


# Agent Response Models
class AgentResult(BaseModel):
    """Result from an individual agent"""
    agent_name: str
    status: str = "completed"
    results: Dict[str, Any]
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MultiAgentResult(BaseModel):
    """Combined results from multi-agent workflow"""
    request_id: str
    workflow: str
    agents_executed: List[str]
    results: Dict[str, Any]
    total_execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrawlAIAgent:
    """Base class for Crawl.ai agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logger
        
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute agent logic - to be overridden by subclasses"""
        raise NotImplementedError


class KnowledgeCuratorAgent(CrawlAIAgent):
    """
    Knowledge Curator Agent - Analyzes and enriches content
    Replaces AutoAgent's Knowledge Curator functionality
    """
    
    def __init__(self):
        super().__init__(
            "Knowledge Curator",
            "Analyzes new content and suggests categorization, tags, and connections"
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        start_time = datetime.utcnow()
        
        try:
            content = context.get("content", "")
            url = context.get("url")
            existing_tags = context.get("tags", [])
            
            # If URL provided, crawl it with Crawl.ai
            if url:
                async with CrawlAIService() as crawler:
                    crawl_result = await crawler.crawl_url(url, extract_content=True)
                    if crawl_result.content:
                        content = crawl_result.content
                    
                    # Use AI-analyzed metadata from crawl
                    if crawl_result.metadata:
                        context.update({
                            "ai_title": crawl_result.metadata.get("ai_title"),
                            "ai_summary": crawl_result.metadata.get("ai_summary"),
                            "ai_tags": crawl_result.metadata.get("ai_tags", []),
                            "ai_category": crawl_result.metadata.get("ai_category"),
                            "ai_entities": crawl_result.metadata.get("ai_entities", {})
                        })
            
            # Analyze content for categorization and enrichment
            analysis = await unified_ai_service.analyze_content(
                content=content[:4000],  # Limit for AI
                url=url,
                enable_key_points=True,
                enable_entities=True
            )
            
            # Find existing connections in database
            connections = await self._find_content_connections(content, existing_tags)
            
            # Generate enhancement suggestions
            suggestions = await self._generate_enhancement_suggestions(content, analysis)
            
            results = {
                "categorization": {
                    "primary_category": analysis.get("category", "uncategorized"),
                    "suggested_tags": list(set(
                        existing_tags + 
                        analysis.get("tags", []) + 
                        context.get("ai_tags", [])
                    ))[:15],
                    "confidence": 0.85
                },
                "metadata": {
                    "title": context.get("ai_title") or analysis.get("title"),
                    "summary": analysis.get("summary"),
                    "detailed_summary": analysis.get("detailed_summary"),
                    "key_points": analysis.get("key_points", []),
                    "entities": analysis.get("entities", {}),
                    "difficulty_level": analysis.get("difficulty_level"),
                    "reading_time": analysis.get("estimated_reading_time", 5)
                },
                "connections": connections,
                "enhancements": suggestions,
                "quality_score": self._calculate_quality_score(analysis)
            }
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                status="completed",
                results=results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Knowledge Curator error: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                results={"error": str(e)},
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _find_content_connections(
        self, 
        content: str, 
        tags: List[str]
    ) -> List[Dict[str, Any]]:
        """Find connections to existing content"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Find similar content by tags
                if tags:
                    query = """
                        SELECT DISTINCT i.id, i.title, i.summary,
                               COUNT(it.tag_id) as common_tags
                        FROM items i
                        JOIN item_tags it ON i.id = it.item_id
                        JOIN tags t ON it.tag_id = t.id
                        WHERE t.name = ANY($1)
                        GROUP BY i.id, i.title, i.summary
                        ORDER BY common_tags DESC
                        LIMIT 5
                    """
                    rows = await conn.fetch(query, tags)
                    
                    connections = []
                    for row in rows:
                        connections.append({
                            "item_id": str(row["id"]),
                            "title": row["title"],
                            "summary": row["summary"],
                            "connection_type": "tag_similarity",
                            "strength": row["common_tags"] / len(tags)
                        })
                    
                    return connections
                
                return []
                
        except Exception as e:
            logger.error(f"Error finding connections: {e}")
            return []
    
    async def _generate_enhancement_suggestions(
        self, 
        content: str, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate suggestions for content enhancement"""
        prompt = f"""Based on this content analysis, suggest enhancements:
        
Content: {content[:1000]}...
Current Analysis: {json.dumps(analysis, indent=2)}

Provide suggestions in JSON format:
{{
    "missing_context": ["what additional context would help"],
    "related_topics": ["topics to explore further"],
    "learning_resources": ["types of resources that would complement this"],
    "practical_applications": ["how this knowledge could be applied"],
    "follow_up_questions": ["questions to deepen understanding"]
}}"""
        
        try:
            response = await unified_ai_service.complete(
                prompt=prompt,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response)
        except:
            return {
                "missing_context": [],
                "related_topics": [],
                "learning_resources": [],
                "practical_applications": [],
                "follow_up_questions": []
            }
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate content quality score"""
        score = 0.0
        
        # Has summary
        if analysis.get("summary"):
            score += 0.2
        
        # Has key points
        if analysis.get("key_points") and len(analysis["key_points"]) >= 3:
            score += 0.2
        
        # Has entities
        entities = analysis.get("entities", {})
        if any(entities.values()):
            score += 0.2
        
        # Has proper categorization
        if analysis.get("category") and analysis["category"] != "other":
            score += 0.2
        
        # Has multiple tags
        if analysis.get("tags") and len(analysis["tags"]) >= 3:
            score += 0.2
        
        return min(score, 1.0)


class ResearchSynthesisAgent(CrawlAIAgent):
    """
    Research Synthesis Agent - Combines multiple sources into insights
    Replaces AutoAgent's Research Synthesizer functionality
    """
    
    def __init__(self):
        super().__init__(
            "Research Synthesizer",
            "Synthesizes information from multiple sources to create comprehensive insights"
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        start_time = datetime.utcnow()
        
        try:
            sources = context.get("sources", [])
            focus_area = context.get("focus", "general")
            
            # Crawl all source URLs if provided
            crawled_content = []
            if sources:
                async with CrawlAIService() as crawler:
                    for source in sources[:5]:  # Limit to 5 sources
                        if isinstance(source, str) and source.startswith("http"):
                            result = await crawler.crawl_url(source)
                            if result.content:
                                crawled_content.append({
                                    "url": source,
                                    "title": result.title,
                                    "content": result.content[:2000],
                                    "metadata": result.metadata
                                })
                        elif isinstance(source, dict):
                            crawled_content.append(source)
            
            # Synthesize the content
            synthesis = await self._synthesize_sources(crawled_content, focus_area)
            
            # Identify patterns
            patterns = await self._identify_patterns(crawled_content)
            
            # Generate insights
            insights = await self._generate_insights(synthesis, patterns)
            
            results = {
                "synthesis": synthesis,
                "patterns": patterns,
                "insights": insights,
                "source_count": len(crawled_content),
                "focus_area": focus_area
            }
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                status="completed",
                results=results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Research Synthesizer error: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                results={"error": str(e)},
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _synthesize_sources(
        self, 
        sources: List[Dict[str, Any]], 
        focus: str
    ) -> Dict[str, Any]:
        """Synthesize multiple sources into a coherent summary"""
        if not sources:
            return {"error": "No sources to synthesize"}
        
        sources_text = "\n\n".join([
            f"Source: {s.get('title', 'Unknown')}\nContent: {s.get('content', '')[:1000]}"
            for s in sources
        ])
        
        prompt = f"""Synthesize these sources with focus on '{focus}':

{sources_text}

Create a comprehensive synthesis in JSON format:
{{
    "executive_summary": "2-3 sentence overview",
    "key_findings": ["main discoveries across sources"],
    "common_themes": ["recurring themes"],
    "contradictions": ["conflicting information"],
    "knowledge_gaps": ["what's missing"],
    "synthesis": "detailed paragraph combining all sources"
}}"""
        
        try:
            response = await unified_ai_service.complete(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return {"error": "Failed to synthesize sources"}
    
    async def _identify_patterns(
        self, 
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify patterns across sources"""
        if len(sources) < 2:
            return []
        
        # Extract all entities and concepts
        all_entities = {}
        for source in sources:
            if source.get("metadata", {}).get("ai_entities"):
                for category, items in source["metadata"]["ai_entities"].items():
                    if category not in all_entities:
                        all_entities[category] = []
                    all_entities[category].extend(items)
        
        patterns = []
        
        # Find frequently mentioned entities
        for category, items in all_entities.items():
            item_counts = {}
            for item in items:
                item_counts[item] = item_counts.get(item, 0) + 1
            
            # Items mentioned in multiple sources
            frequent_items = [
                item for item, count in item_counts.items() 
                if count > 1
            ]
            
            if frequent_items:
                patterns.append({
                    "pattern_type": f"recurring_{category}",
                    "items": frequent_items,
                    "frequency": len(frequent_items) / len(set(items)),
                    "implication": f"Strong focus on these {category}"
                })
        
        return patterns
    
    async def _generate_insights(
        self, 
        synthesis: Dict[str, Any], 
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Insight from synthesis
        if synthesis.get("key_findings"):
            insights.append(
                f"Key Finding: {synthesis['key_findings'][0]}"
            )
        
        # Insight from patterns
        for pattern in patterns[:3]:
            insights.append(
                f"Pattern Detected: {pattern['implication']} - "
                f"{', '.join(pattern['items'][:3])}"
            )
        
        # Insight from gaps
        if synthesis.get("knowledge_gaps"):
            insights.append(
                f"Research Opportunity: {synthesis['knowledge_gaps'][0]}"
            )
        
        return insights


class ContentExplorerAgent(CrawlAIAgent):
    """
    Content Explorer Agent - Discovers connections and exploration paths
    Replaces AutoAgent's Content Explorer functionality
    """
    
    def __init__(self):
        super().__init__(
            "Content Explorer",
            "Discovers hidden connections and creates exploration paths"
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        start_time = datetime.utcnow()
        
        try:
            starting_point = context.get("starting_point", "")
            interests = context.get("interests", [])
            exploration_depth = context.get("depth", 2)
            
            # Build exploration map
            exploration_map = await self._build_exploration_map(
                starting_point, 
                exploration_depth
            )
            
            # Find serendipitous connections
            discoveries = await self._find_serendipitous_connections(
                starting_point,
                interests
            )
            
            # Create exploration paths
            paths = await self._create_exploration_paths(
                starting_point,
                interests,
                exploration_map
            )
            
            results = {
                "exploration_map": exploration_map,
                "discoveries": discoveries,
                "suggested_paths": paths,
                "total_connections": len(exploration_map.get("nodes", [])),
                "exploration_depth": exploration_depth
            }
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                status="completed",
                results=results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Content Explorer error: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                results={"error": str(e)},
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _build_exploration_map(
        self, 
        starting_point: str, 
        depth: int
    ) -> Dict[str, Any]:
        """Build a map of content connections"""
        # This would integrate with the database to find connections
        # For now, return a sample structure
        return {
            "center": starting_point,
            "nodes": [
                {
                    "id": "node1",
                    "title": "Related Concept 1",
                    "distance": 1,
                    "connection_type": "conceptual"
                },
                {
                    "id": "node2", 
                    "title": "Application Example",
                    "distance": 2,
                    "connection_type": "practical"
                }
            ],
            "edges": [
                {"from": starting_point, "to": "node1", "weight": 0.8},
                {"from": "node1", "to": "node2", "weight": 0.6}
            ]
        }
    
    async def _find_serendipitous_connections(
        self,
        topic: str,
        interests: List[str]
    ) -> List[Dict[str, Any]]:
        """Find unexpected, creative connections"""
        prompt = f"""Find creative, unexpected connections for:
Topic: {topic}
User Interests: {', '.join(interests)}

Suggest serendipitous connections in JSON format:
{{
    "connections": [
        {{
            "concept": "connected concept",
            "explanation": "why this connection is interesting",
            "creativity_score": 0.0-1.0,
            "learning_potential": "what can be learned"
        }}
    ]
}}"""
        
        try:
            response = await unified_ai_service.complete(
                prompt=prompt,
                temperature=0.8,  # Higher for creativity
                response_format={"type": "json_object"}
            )
            result = json.loads(response)
            return result.get("connections", [])[:5]
        except:
            return []
    
    async def _create_exploration_paths(
        self,
        start: str,
        interests: List[str],
        exploration_map: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create suggested exploration paths"""
        paths = [
            {
                "name": "Quick Overview",
                "description": "Get a broad understanding",
                "steps": ["Introduction", "Key Concepts", "Applications"],
                "estimated_time": "30 minutes",
                "difficulty": "beginner"
            },
            {
                "name": "Deep Dive",
                "description": "Comprehensive exploration",
                "steps": ["Theory", "Implementation", "Advanced Topics"],
                "estimated_time": "2-3 hours",
                "difficulty": "intermediate"
            }
        ]
        
        # Add interest-based path
        if interests:
            paths.append({
                "name": f"Focus: {interests[0]}",
                "description": f"Explore through the lens of {interests[0]}",
                "steps": ["Connection to " + interests[0], "Applications", "Case Studies"],
                "estimated_time": "1 hour",
                "difficulty": "intermediate"
            })
        
        return paths


class LearningPathAgent(CrawlAIAgent):
    """
    Learning Path Agent - Creates personalized learning journeys
    Replaces AutoAgent's Learning Pathfinder functionality
    """
    
    def __init__(self):
        super().__init__(
            "Learning Pathfinder",
            "Creates personalized learning paths and tracks progress"
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        start_time = datetime.utcnow()
        
        try:
            goal = context.get("goal", "")
            current_knowledge = context.get("current_knowledge", [])
            time_commitment = context.get("time_commitment", "moderate")
            learning_style = context.get("learning_style", "balanced")
            
            # Analyze learning goal
            goal_analysis = await self._analyze_learning_goal(goal)
            
            # Assess current knowledge level
            knowledge_assessment = await self._assess_knowledge_level(
                current_knowledge,
                goal_analysis
            )
            
            # Create learning path
            learning_path = await self._create_learning_path(
                goal,
                goal_analysis,
                knowledge_assessment,
                time_commitment,
                learning_style
            )
            
            # Generate milestones
            milestones = await self._generate_milestones(learning_path)
            
            results = {
                "learning_path": learning_path,
                "milestones": milestones,
                "goal_analysis": goal_analysis,
                "knowledge_assessment": knowledge_assessment,
                "estimated_completion": self._estimate_completion_time(
                    learning_path,
                    time_commitment
                )
            }
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                status="completed",
                results=results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Learning Path error: {e}")
            return AgentResult(
                agent_name=self.name,
                status="error",
                results={"error": str(e)},
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _analyze_learning_goal(self, goal: str) -> Dict[str, Any]:
        """Analyze the learning goal to understand requirements"""
        prompt = f"""Analyze this learning goal:
"{goal}"

Provide analysis in JSON format:
{{
    "domain": "primary knowledge domain",
    "sub_topics": ["specific topics to cover"],
    "prerequisites": ["required prior knowledge"],
    "difficulty_level": "beginner|intermediate|advanced",
    "practical_focus": true/false,
    "theoretical_depth": "shallow|moderate|deep"
}}"""
        
        try:
            response = await unified_ai_service.complete(
                prompt=prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(response)
        except:
            return {
                "domain": "general",
                "sub_topics": [],
                "prerequisites": [],
                "difficulty_level": "intermediate",
                "practical_focus": True,
                "theoretical_depth": "moderate"
            }
    
    async def _assess_knowledge_level(
        self,
        current_knowledge: List[str],
        goal_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess current knowledge level relative to goal"""
        # Check overlap with prerequisites
        prerequisites = set(goal_analysis.get("prerequisites", []))
        known = set(current_knowledge)
        
        overlap = prerequisites.intersection(known)
        missing = prerequisites - known
        
        return {
            "readiness_score": len(overlap) / len(prerequisites) if prerequisites else 0.5,
            "known_prerequisites": list(overlap),
            "missing_prerequisites": list(missing),
            "strength_areas": [k for k in known if k not in prerequisites],
            "recommended_starting_point": "beginner" if len(missing) > 2 else "intermediate"
        }
    
    async def _create_learning_path(
        self,
        goal: str,
        goal_analysis: Dict[str, Any],
        knowledge_assessment: Dict[str, Any],
        time_commitment: str,
        learning_style: str
    ) -> Dict[str, Any]:
        """Create a detailed learning path"""
        # Time allocations based on commitment
        time_allocations = {
            "minimal": {"hours_per_week": 2, "weeks": 12},
            "moderate": {"hours_per_week": 5, "weeks": 8},
            "intensive": {"hours_per_week": 10, "weeks": 4}
        }
        
        allocation = time_allocations.get(time_commitment, time_allocations["moderate"])
        
        prompt = f"""Create a learning path for:
Goal: {goal}
Domain: {goal_analysis.get('domain')}
Current Level: {knowledge_assessment.get('recommended_starting_point')}
Time: {allocation['hours_per_week']} hours/week for {allocation['weeks']} weeks
Style: {learning_style}

Structure the path in JSON format:
{{
    "phases": [
        {{
            "name": "Phase name",
            "duration": "X weeks",
            "objectives": ["what will be learned"],
            "topics": ["specific topics"],
            "resources": ["types of resources needed"],
            "exercises": ["practical exercises"],
            "assessment": "how to measure progress"
        }}
    ],
    "learning_approach": "description of approach",
    "success_metrics": ["how to measure overall success"]
}}"""
        
        try:
            response = await unified_ai_service.complete(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            return json.loads(response)
        except:
            # Fallback path
            return {
                "phases": [
                    {
                        "name": "Foundation",
                        "duration": "2 weeks",
                        "objectives": ["Understand core concepts"],
                        "topics": goal_analysis.get("sub_topics", [])[:3],
                        "resources": ["Documentation", "Tutorials"],
                        "exercises": ["Basic exercises"],
                        "assessment": "Knowledge check"
                    }
                ],
                "learning_approach": "Progressive skill building",
                "success_metrics": ["Complete all phases", "Apply knowledge"]
            }
    
    async def _generate_milestones(
        self,
        learning_path: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate checkable milestones"""
        milestones = []
        
        for i, phase in enumerate(learning_path.get("phases", [])):
            milestone = {
                "id": f"milestone_{i+1}",
                "phase": phase["name"],
                "description": f"Complete {phase['name']} phase",
                "success_criteria": phase.get("objectives", []),
                "estimated_completion": phase.get("duration", "1 week"),
                "dependencies": [f"milestone_{i}"] if i > 0 else []
            }
            milestones.append(milestone)
        
        return milestones
    
    def _estimate_completion_time(
        self,
        learning_path: Dict[str, Any],
        time_commitment: str
    ) -> str:
        """Estimate total completion time"""
        total_weeks = sum(
            int(phase.get("duration", "1 week").split()[0])
            for phase in learning_path.get("phases", [])
        )
        
        return f"{total_weeks} weeks with {time_commitment} commitment"


class CrawlAIOrchestrator:
    """
    Multi-agent orchestrator using Crawl.ai agents
    Coordinates agent execution for complex workflows
    """
    
    def __init__(self):
        self.agents = {
            "knowledge_curator": KnowledgeCuratorAgent(),
            "research_synthesizer": ResearchSynthesisAgent(),
            "content_explorer": ContentExplorerAgent(),
            "learning_pathfinder": LearningPathAgent(),
            # Media processing agents
            "image_analyzer": MEDIA_AGENTS["image_analyzer"],
            "video_processor": MEDIA_AGENTS["video_processor"],
            "audio_journal_processor": MEDIA_AGENTS["audio_journal_processor"]
        }
        self.logger = logger
        self.job_service = None  # Initialize lazily when needed
    
    async def _get_job_service(self):
        """Get job persistence service with database connection"""
        from app.db.database import get_db_connection
        async for conn in get_db_connection():
            yield JobPersistenceService(conn)
    
    async def process_content(
        self,
        content: str,
        url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        workflow: str = "full"
    ) -> MultiAgentResult:
        """
        Process content through multi-agent workflow
        
        Workflows:
        - "full": All agents
        - "curate": Just knowledge curator
        - "research": Curator + Research synthesis
        - "explore": Curator + Explorer
        """
        start_time = datetime.utcnow()
        request_id = f"crawl-{int(start_time.timestamp())}"
        
        context = {
            "content": content,
            "url": url,
            "tags": tags or []
        }
        
        results = {}
        agents_executed = []
        
        # Always run knowledge curator first
        curator_result = await self.agents["knowledge_curator"].execute(context)
        results["knowledge_curator"] = curator_result.results
        agents_executed.append("knowledge_curator")
        
        # Update context with curator results
        context.update({
            "curator_analysis": curator_result.results
        })
        
        # Execute additional agents based on workflow
        if workflow in ["full", "research"]:
            synthesizer_result = await self.agents["research_synthesizer"].execute({
                **context,
                "sources": [{"content": content, "metadata": curator_result.results}]
            })
            results["research_synthesizer"] = synthesizer_result.results
            agents_executed.append("research_synthesizer")
        
        if workflow in ["full", "explore"]:
            explorer_result = await self.agents["content_explorer"].execute({
                **context,
                "starting_point": curator_result.results.get("metadata", {}).get("title", "Content"),
                "interests": curator_result.results.get("categorization", {}).get("suggested_tags", [])
            })
            results["content_explorer"] = explorer_result.results
            agents_executed.append("content_explorer")
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        return MultiAgentResult(
            request_id=request_id,
            workflow=workflow,
            agents_executed=agents_executed,
            results=results,
            total_execution_time=total_time
        )
    
    async def create_learning_path(
        self,
        goal: str,
        current_knowledge: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> MultiAgentResult:
        """Create a personalized learning path"""
        start_time = datetime.utcnow()
        request_id = f"learn-{int(start_time.timestamp())}"
        
        context = {
            "goal": goal,
            "current_knowledge": current_knowledge or [],
            "time_commitment": preferences.get("time_commitment", "moderate") if preferences else "moderate",
            "learning_style": preferences.get("learning_style", "balanced") if preferences else "balanced"
        }
        
        # Execute learning path agent
        pathfinder_result = await self.agents["learning_pathfinder"].execute(context)
        
        # Also run content explorer to find relevant resources
        explorer_result = await self.agents["content_explorer"].execute({
            "starting_point": goal,
            "interests": current_knowledge or [],
            "depth": 3
        })
        
        results = {
            "learning_pathfinder": pathfinder_result.results,
            "content_explorer": explorer_result.results
        }
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        return MultiAgentResult(
            request_id=request_id,
            workflow="learning_path",
            agents_executed=["learning_pathfinder", "content_explorer"],
            results=results,
            total_execution_time=total_time
        )
    
    async def explore_topic(
        self,
        topic: str,
        interests: Optional[List[str]] = None,
        depth: int = 2
    ) -> MultiAgentResult:
        """Explore a topic in depth"""
        start_time = datetime.utcnow()
        request_id = f"explore-{int(start_time.timestamp())}"
        
        # First, crawl information about the topic if it's a URL
        context = {
            "starting_point": topic,
            "interests": interests or [],
            "depth": depth
        }
        
        if topic.startswith("http"):
            curator_result = await self.agents["knowledge_curator"].execute({
                "url": topic,
                "content": ""
            })
            context["curator_analysis"] = curator_result.results
            agents_executed = ["knowledge_curator", "content_explorer"]
        else:
            agents_executed = ["content_explorer"]
        
        # Explore the topic
        explorer_result = await self.agents["content_explorer"].execute(context)
        
        results = {
            "content_explorer": explorer_result.results
        }
        
        if "curator_analysis" in context:
            results["knowledge_curator"] = context["curator_analysis"]
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        return MultiAgentResult(
            request_id=request_id,
            workflow="topic_exploration",
            agents_executed=agents_executed,
            results=results,
            total_execution_time=total_time
        )
    
    async def generate_insights_report(
        self,
        time_period: str = "week",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate insights report from knowledge base"""
        # This would query the database for recent items and patterns
        # For now, return a sample structure
        return {
            "period": time_period,
            "focus_areas": focus_areas or ["all"],
            "insights": [
                "Increased interest in AI and machine learning topics",
                "Strong focus on practical implementations",
                "Growing collection of development resources"
            ],
            "recommendations": [
                "Explore more theoretical foundations",
                "Connect practical knowledge with concepts",
                "Review and synthesize older content"
            ],
            "statistics": {
                "total_items": 150,
                "new_items": 23,
                "categories_covered": 8,
                "average_quality_score": 0.82
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def process_image(
        self,
        file_path: str,
        item_id: Optional[str] = None,
        enhance_analysis: bool = True,
        job_id: Optional[str] = None
    ) -> MultiAgentResult:
        """
        Process an image through OCR and AI analysis
        
        Args:
            file_path: Path to image file
            item_id: Optional item ID for database linking
            enhance_analysis: Whether to run enhanced context analysis
            job_id: Optional job ID for tracking (auto-generated if not provided)
            
        Returns:
            MultiAgentResult with OCR text, description, objects, and tags
        """
        request_id = f"image-{int(datetime.utcnow().timestamp())}"
        start_time = time.time()
        
        # Initialize job tracking
        async for job_service in self._get_job_service():
            if not job_id:
                job_id = await job_service.generate_job_id("media_image", item_id)
            
            # Create job entry
            await job_service.create_job(
                job_type="media_image",
                input_data={
                    "file_path": file_path,
                    "item_id": item_id,
                    "enhance_analysis": enhance_analysis
                },
                item_id=item_id,
                job_id=job_id,
                metadata={"agent": "image_analyzer", "request_id": request_id}
            )
            
            try:
                # Update job to processing
                await job_service.update_job_status(
                    job_id=job_id,
                    status="processing",
                    progress_percentage=10,
                    current_stage="image_analysis",
                    stage_message="Starting image analysis and OCR processing"
                )
                
                # Execute image analysis agent
                agent = self.agents["image_analyzer"]
                result = await agent.execute({
                    "file_path": file_path,
                    "item_id": item_id,
                    "enhance_analysis": enhance_analysis
                })
                
                # Update progress
                await job_service.update_job_status(
                    job_id=job_id,
                    progress_percentage=70,
                    current_stage="database_save",
                    stage_message="Saving analysis results to database"
                )
                
                # Save results to database
                if result.status == "completed":
                    try:
                        saved_item_id = await media_persistence_service.save_image_analysis(
                            item_id=item_id,
                            file_path=file_path,
                            result=result
                        )
                        # Add database info to results
                        result.results["database"] = {
                            "item_id": saved_item_id,
                            "saved": True,
                            "save_timestamp": datetime.utcnow().isoformat()
                        }
                        self.logger.info(f"✅ Image analysis saved to database: {saved_item_id}")
                        
                        # Save job results
                        await job_service.save_job_result(
                            job_id=job_id,
                            result_data={
                                "analysis_result": result.results,
                                "database_item_id": saved_item_id,
                                "file_path": file_path,
                                "success": True
                            },
                            status="completed"
                        )
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to save image analysis to database: {e}")
                        result.results["database"] = {
                            "saved": False,
                            "error": str(e)
                        }
                        
                        # Save job with error
                        await job_service.save_job_result(
                            job_id=job_id,
                            result_data={
                                "analysis_result": result.results,
                                "database_error": str(e),
                                "file_path": file_path,
                                "success": False
                            },
                            status="failed"
                        )
                else:
                    # Agent execution failed
                    await job_service.update_job_status(
                        job_id=job_id,
                        status="failed",
                        error_message=f"Image analysis failed: {result.error_message}",
                        progress_percentage=0
                    )
                
                execution_time = time.time() - start_time
                
                # Add job information to results
                result.results["job"] = {
                    "job_id": job_id,
                    "tracking_enabled": True,
                    "status": "completed" if result.status == "completed" else "failed"
                }
                
                return MultiAgentResult(
                    request_id=request_id,
                    workflow="image_analysis",
                    agents_executed=["image_analyzer"],
                    results={"image_analyzer": result.results, "job_id": job_id},
                    total_execution_time=execution_time
                )
                
            except Exception as e:
                self.logger.error(f"Image processing failed: {e}")
                execution_time = time.time() - start_time
                
                # Update job with error
                try:
                    await job_service.update_job_status(
                        job_id=job_id,
                        status="failed",
                        error_message=str(e),
                        progress_percentage=0
                    )
                except Exception:
                    pass  # Don't fail if job update fails
                
                return MultiAgentResult(
                    request_id=request_id,
                    workflow="image_analysis",
                    agents_executed=[],
                    results={"error": str(e), "job_id": job_id},
                    total_execution_time=execution_time
                )
    
    async def process_video(
        self,
        file_path: str,
        item_id: Optional[str] = None,
        model_name: str = "base",
        language: str = "en",
        create_summary: bool = True
    ) -> MultiAgentResult:
        """
        Process a video through transcription and AI analysis
        
        Args:
            file_path: Path to video file
            item_id: Optional item ID for database linking
            model_name: Whisper model to use
            language: Language code for transcription
            create_summary: Whether to create AI summary
            
        Returns:
            MultiAgentResult with transcription, summary, and metadata
        """
        request_id = f"video-{int(datetime.utcnow().timestamp())}"
        start_time = time.time()
        
        try:
            # Execute video processing agent
            agent = self.agents["video_processor"]
            result = await agent.execute({
                "file_path": file_path,
                "item_id": item_id,
                "model_name": model_name,
                "language": language,
                "create_summary": create_summary
            })
            
            # Save results to database
            if result.status == "completed":
                try:
                    saved_item_id = await media_persistence_service.save_video_transcription(
                        item_id=item_id,
                        file_path=file_path,
                        result=result
                    )
                    # Add database info to results
                    result.results["database"] = {
                        "item_id": saved_item_id,
                        "saved": True,
                        "save_timestamp": datetime.utcnow().isoformat()
                    }
                    self.logger.info(f"✅ Video transcription saved to database: {saved_item_id}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to save video transcription to database: {e}")
                    result.results["database"] = {
                        "saved": False,
                        "error": str(e)
                    }
            
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="video_processing",
                agents_executed=["video_processor"],
                results={"video_processor": result.results},
                total_execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Video processing failed: {e}")
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="video_processing",
                agents_executed=[],
                results={"error": str(e)},
                total_execution_time=execution_time
            )
    
    async def process_audio_journal(
        self,
        file_path: str,
        item_id: Optional[str] = None,
        journal_id: Optional[str] = None,
        model_name: str = "base",
        language: str = "en",
        analyze_emotions: bool = True
    ) -> MultiAgentResult:
        """
        Process an audio journal with advanced analysis
        
        Args:
            file_path: Path to audio file
            item_id: Optional item ID for database linking
            journal_id: Optional audio journal ID
            model_name: Whisper model to use
            language: Language code for transcription
            analyze_emotions: Whether to perform emotion analysis
            
        Returns:
            MultiAgentResult with transcription, analysis, and journal metadata
        """
        request_id = f"journal-{int(datetime.utcnow().timestamp())}"
        start_time = time.time()
        
        try:
            # Execute audio journal processing agent
            agent = self.agents["audio_journal_processor"]
            result = await agent.execute({
                "file_path": file_path,
                "item_id": item_id,
                "journal_id": journal_id,
                "model_name": model_name,
                "language": language,
                "analyze_emotions": analyze_emotions
            })
            
            # Save results to database
            if result.status == "completed":
                try:
                    saved_item_id, saved_journal_id = await media_persistence_service.save_audio_journal(
                        item_id=item_id,
                        journal_id=journal_id,
                        file_path=file_path,
                        result=result
                    )
                    # Add database info to results
                    result.results["database"] = {
                        "item_id": saved_item_id,
                        "journal_id": saved_journal_id,
                        "saved": True,
                        "save_timestamp": datetime.utcnow().isoformat()
                    }
                    self.logger.info(f"✅ Audio journal saved to database: item={saved_item_id}, journal={saved_journal_id}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to save audio journal to database: {e}")
                    result.results["database"] = {
                        "saved": False,
                        "error": str(e)
                    }
            
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="audio_journal_processing",
                agents_executed=["audio_journal_processor"],
                results={"audio_journal_processor": result.results},
                total_execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Audio journal processing failed: {e}")
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="audio_journal_processing", 
                agents_executed=[],
                results={"error": str(e)},
                total_execution_time=execution_time
            )
    
    async def process_media_batch(
        self,
        media_files: List[Dict[str, Any]]
    ) -> MultiAgentResult:
        """
        Process multiple media files in batch
        
        Args:
            media_files: List of dicts with file_path, media_type, and options
            
        Returns:
            MultiAgentResult with results from all processed files
        """
        request_id = f"batch-{int(datetime.utcnow().timestamp())}"
        start_time = time.time()
        
        try:
            results = {}
            agents_executed = []
            
            for i, media_file in enumerate(media_files):
                file_path = media_file.get("file_path")
                media_type = media_file.get("media_type")
                options = media_file.get("options", {})
                
                if media_type == "image":
                    result = await self.process_image(file_path, **options)
                    results[f"image_{i}"] = result.results
                    agents_executed.extend(result.agents_executed)
                elif media_type == "video":
                    result = await self.process_video(file_path, **options)
                    results[f"video_{i}"] = result.results
                    agents_executed.extend(result.agents_executed)
                elif media_type == "audio_journal":
                    result = await self.process_audio_journal(file_path, **options)
                    results[f"audio_journal_{i}"] = result.results
                    agents_executed.extend(result.agents_executed)
                else:
                    results[f"unknown_{i}"] = {"error": f"Unknown media type: {media_type}"}
            
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="media_batch_processing",
                agents_executed=list(set(agents_executed)),  # Remove duplicates
                results=results,
                total_execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Batch media processing failed: {e}")
            execution_time = time.time() - start_time
            
            return MultiAgentResult(
                request_id=request_id,
                workflow="media_batch_processing",
                agents_executed=[],
                results={"error": str(e)},
                total_execution_time=execution_time
            )


# Singleton instance
crawl_ai_orchestrator = CrawlAIOrchestrator()