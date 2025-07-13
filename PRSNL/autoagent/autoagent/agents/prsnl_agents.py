"""
PRSNL Custom Agents for Second Brain Functionality

This module defines specialized agents that work together to create
an intelligent knowledge organism from the PRSNL knowledge base.
"""

from typing import List, Dict, Any, Optional
import json
import asyncio
import os
from datetime import datetime

from autoagent import Agent
from autoagent.memory.prsnl_memory import PRSNLMemory
from autoagent.logger import MetaChainLogger

# Knowledge Curator Agent
KNOWLEDGE_CURATOR_PROMPT = """You are the Knowledge Curator Agent for PRSNL's Second Brain system.

Your responsibilities:
1. Analyze new content and suggest appropriate categorization
2. Identify knowledge gaps and learning opportunities
3. Create meaningful connections between related items
4. Enhance content with additional context and insights
5. Suggest tags and metadata for better organization

When processing content:
- Extract key concepts and themes
- Identify potential relationships with existing knowledge
- Suggest improvements or additional research areas
- Maintain consistency in categorization
- Preserve the user's personal knowledge style

Always aim to enhance understanding and discovery, not just organize."""

# Research Synthesis Agent
RESEARCH_SYNTHESIS_PROMPT = """You are the Research Synthesis Agent for PRSNL's Second Brain system.

Your responsibilities:
1. Process multiple sources to create comprehensive summaries
2. Identify patterns and trends across the knowledge base
3. Generate new insights from data relationships
4. Create synthesis reports that connect disparate information
5. Highlight contradictions or gaps in knowledge

When synthesizing information:
- Look for common themes across different sources
- Identify emerging patterns and trends
- Create structured summaries with key takeaways
- Generate actionable insights
- Suggest areas for deeper exploration

Focus on creating new understanding from existing knowledge."""

# Content Explorer Agent
CONTENT_EXPLORER_PROMPT = """You are the Content Explorer Agent for PRSNL's Second Brain system.

Your responsibilities:
1. Help users discover relevant information in their knowledge base
2. Suggest related content and unexpected connections
3. Create dynamic knowledge maps and exploration paths
4. Identify hidden relationships between concepts
5. Guide users to serendipitous discoveries

When exploring content:
- Think beyond obvious connections
- Consider interdisciplinary relationships
- Create multiple exploration paths
- Suggest both depth and breadth approaches
- Enable creative discovery

Help users see their knowledge from new perspectives."""

# Learning Path Agent
LEARNING_PATH_AGENT_PROMPT = """You are the Learning Path Agent for PRSNL's Second Brain system.

Your responsibilities:
1. Create personalized learning sequences based on user interests
2. Track knowledge progression and identify next steps
3. Suggest optimal learning paths for skill development
4. Adapt recommendations based on user behavior
5. Create milestone-based learning journeys

When creating learning paths:
- Consider the user's current knowledge level
- Build progressive difficulty curves
- Include diverse content types
- Create checkpoints for knowledge validation
- Suggest practical applications

Focus on accelerating learning and knowledge retention."""

class PRSNLAgentFactory:
    """Factory for creating PRSNL-specific agents."""
    
    @staticmethod
    def create_knowledge_curator(memory: PRSNLMemory, logger: Optional[MetaChainLogger] = None) -> Agent:
        """Create a Knowledge Curator agent."""
        
        async def analyze_content(content: str, existing_tags: List[str] = None) -> Dict[str, Any]:
            """Analyze content and suggest categorization."""
            # This would integrate with the AI service to analyze content
            return {
                "suggested_tags": ["example", "tag"],
                "category": "development",
                "key_concepts": ["concept1", "concept2"],
                "quality_score": 0.85,
                "improvement_suggestions": []
            }
        
        async def find_connections(item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
            """Find connections to other items in the knowledge base."""
            return await memory.get_related_items(item_id, limit)
        
        async def suggest_enhancements(content: str) -> Dict[str, Any]:
            """Suggest enhancements for the content."""
            return {
                "additional_context": "Consider adding...",
                "related_topics": ["topic1", "topic2"],
                "research_suggestions": ["Look into..."],
                "metadata_suggestions": {}
            }
        
        # Check if function calling is disabled
        use_functions = os.getenv("FN_CALL", "True").lower() != "false"
        
        agent = Agent(
            name="Knowledge Curator",
            model="azure/prsnl-gpt-4",
            instructions=KNOWLEDGE_CURATOR_PROMPT,
            functions=[analyze_content, find_connections, suggest_enhancements] if use_functions else [],
            parallel_tool_calls=use_functions
        )
        
        return agent
    
    @staticmethod
    def create_research_synthesizer(memory: PRSNLMemory, logger: Optional[MetaChainLogger] = None) -> Agent:
        """Create a Research Synthesis agent."""
        
        async def synthesize_sources(item_ids: List[str], focus: Optional[str] = None) -> Dict[str, Any]:
            """Synthesize information from multiple sources."""
            # Retrieve content from memory
            synthesis = {
                "summary": "Comprehensive synthesis...",
                "key_findings": [],
                "patterns": [],
                "contradictions": [],
                "gaps": [],
                "insights": []
            }
            return synthesis
        
        async def identify_patterns(query: str, time_range: Optional[str] = None) -> List[Dict[str, Any]]:
            """Identify patterns across the knowledge base."""
            return [
                {
                    "pattern": "Increasing interest in...",
                    "evidence": ["item1", "item2"],
                    "strength": 0.8,
                    "implications": []
                }
            ]
        
        async def generate_insights(context: str) -> List[str]:
            """Generate new insights from existing knowledge."""
            return [
                "Insight 1: Connection between X and Y suggests...",
                "Insight 2: The pattern indicates..."
            ]
        
        # Check if function calling is disabled
        use_functions = os.getenv("FN_CALL", "True").lower() != "false"
        
        agent = Agent(
            name="Research Synthesizer",
            model="azure/prsnl-gpt-4",
            instructions=RESEARCH_SYNTHESIS_PROMPT,
            functions=[synthesize_sources, identify_patterns, generate_insights] if use_functions else [],
            parallel_tool_calls=use_functions
        )
        
        return agent
    
    @staticmethod
    def create_content_explorer(memory: PRSNLMemory, logger: Optional[MetaChainLogger] = None) -> Agent:
        """Create a Content Explorer agent."""
        
        async def explore_connections(starting_point: str, depth: int = 2) -> Dict[str, Any]:
            """Explore connections from a starting point."""
            exploration_map = {
                "start": starting_point,
                "paths": [],
                "discoveries": [],
                "unexpected_connections": []
            }
            return exploration_map
        
        async def suggest_exploration_paths(interests: List[str]) -> List[Dict[str, Any]]:
            """Suggest exploration paths based on interests."""
            return [
                {
                    "path_name": "Technical Deep Dive",
                    "steps": ["concept1", "concept2", "concept3"],
                    "estimated_time": "2 hours",
                    "difficulty": "intermediate"
                }
            ]
        
        async def find_serendipitous_connections(item_id: str) -> List[Dict[str, Any]]:
            """Find unexpected, serendipitous connections."""
            return [
                {
                    "item_id": "123",
                    "connection_type": "metaphorical",
                    "explanation": "Both concepts share...",
                    "creativity_score": 0.9
                }
            ]
        
        # Check if function calling is disabled
        use_functions = os.getenv("FN_CALL", "True").lower() != "false"
        
        agent = Agent(
            name="Content Explorer",
            model="azure/prsnl-gpt-4",
            instructions=CONTENT_EXPLORER_PROMPT,
            functions=[explore_connections, suggest_exploration_paths, find_serendipitous_connections] if use_functions else [],
            parallel_tool_calls=use_functions
        )
        
        return agent
    
    @staticmethod
    def create_learning_pathfinder(memory: PRSNLMemory, logger: Optional[MetaChainLogger] = None) -> Agent:
        """Create a Learning Path agent."""
        
        async def create_learning_path(goal: str, current_knowledge: List[str]) -> Dict[str, Any]:
            """Create a personalized learning path."""
            return {
                "goal": goal,
                "duration": "4 weeks",
                "milestones": [
                    {
                        "week": 1,
                        "objectives": ["Learn basics of..."],
                        "resources": ["item1", "item2"],
                        "exercises": []
                    }
                ],
                "prerequisites": [],
                "success_metrics": []
            }
        
        async def track_progress(user_id: str, path_id: str) -> Dict[str, Any]:
            """Track user progress on a learning path."""
            return {
                "completion": 0.35,
                "current_milestone": 2,
                "strengths": ["Good grasp of..."],
                "areas_for_improvement": ["Need more practice with..."],
                "next_steps": ["Complete exercise..."]
            }
        
        async def adapt_path(path_id: str, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
            """Adapt learning path based on user progress and feedback."""
            return {
                "adjustments": [
                    "Added more examples for concept X",
                    "Reduced pace for section Y"
                ],
                "new_resources": ["item3", "item4"],
                "revised_duration": "5 weeks"
            }
        
        # Check if function calling is disabled
        use_functions = os.getenv("FN_CALL", "True").lower() != "false"
        
        agent = Agent(
            name="Learning Pathfinder",
            model="azure/prsnl-gpt-4",
            instructions=LEARNING_PATH_AGENT_PROMPT,
            functions=[create_learning_path, track_progress, adapt_path] if use_functions else [],
            parallel_tool_calls=use_functions
        )
        
        return agent

class PRSNLMultiAgentOrchestrator:
    """Orchestrator for PRSNL multi-agent workflows."""
    
    def __init__(self, memory: PRSNLMemory, logger: Optional[MetaChainLogger] = None):
        self.memory = memory
        self.logger = logger
        
        # Initialize MetaChain for running agents
        from autoagent import MetaChain
        self.metachain = MetaChain(log_path=logger)
        
        # Initialize agents
        self.knowledge_curator = PRSNLAgentFactory.create_knowledge_curator(memory, logger)
        self.research_synthesizer = PRSNLAgentFactory.create_research_synthesizer(memory, logger)
        self.content_explorer = PRSNLAgentFactory.create_content_explorer(memory, logger)
        self.learning_pathfinder = PRSNLAgentFactory.create_learning_pathfinder(memory, logger)
        
        self.agents = {
            "knowledge_curator": self.knowledge_curator,
            "research_synthesizer": self.research_synthesizer,
            "content_explorer": self.content_explorer,
            "learning_pathfinder": self.learning_pathfinder
        }
    
    async def process_new_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process new content through the multi-agent workflow.
        
        Args:
            content: New content to process
            
        Returns:
            Processing results from all agents
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_id": content.get("id"),
            "agent_outputs": {},
            "processing_result": {}
        }
        
        # Prepare content for agent processing
        content_text = content.get("content", "")
        title = content.get("title", "Untitled")
        tags = content.get("tags", [])
        
        # Step 1: Knowledge Curator analyzes and categorizes
        curator_messages = [
            {"role": "system", "content": "You are the Knowledge Curator Agent. Analyze the provided content and suggest categorization, tags, and improvements."},
            {"role": "user", "content": f"Please analyze this content:\n\nTitle: {title}\nTags: {', '.join(tags)}\n\nContent:\n{content_text}\n\nProvide categorization suggestions, additional tags, key concepts, and improvement recommendations."}
        ]
        
        # Use await since MetaChain.run is async
        curator_response = await self.metachain.run_async(
            agent=self.knowledge_curator,
            messages=curator_messages,
            context_variables={"content": content}
        )
        
        curator_output = curator_response.messages[-1]["content"] if curator_response.messages else ""
        results["agent_outputs"]["knowledge_curator"] = curator_output
        
        # Step 2: Research Synthesizer analyzes patterns and generates insights
        synthesis_messages = [
            {"role": "system", "content": "You are the Research Synthesis Agent. Analyze content for patterns and generate insights."},
            {"role": "user", "content": f"Based on this content and analysis:\n\nContent: {content_text}\n\nCurator Analysis: {curator_output}\n\nIdentify patterns, generate insights, and suggest research directions."}
        ]
        
        synthesis_response = await self.metachain.run_async(
            agent=self.research_synthesizer,
            messages=synthesis_messages,
            context_variables={"content": content, "curator_analysis": curator_output}
        )
        
        synthesis_output = synthesis_response.messages[-1]["content"] if synthesis_response.messages else ""
        results["agent_outputs"]["research_synthesizer"] = synthesis_output
        
        # Compile final processing result
        results["processing_result"] = {
            "enrichments": {
                "categories": self._extract_categories(curator_output),
                "tags": tags + self._extract_tags(curator_output),
                "key_concepts": self._extract_concepts(curator_output),
                "summary": self._extract_summary(synthesis_output),
                "insights": self._extract_insights(synthesis_output)
            }
        }
        
        return results
    
    async def explore_topic(self, topic: str, user_interests: List[str]) -> Dict[str, Any]:
        """
        Explore a topic using multiple agents.
        
        Args:
            topic: Topic to explore
            user_interests: User's stated interests
            
        Returns:
            Exploration results
        """
        results = {
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "explorations": {}
        }
        
        # Content Explorer creates exploration paths
        explorer_messages = [
            {"role": "system", "content": "You are the Content Explorer Agent. Help discover relevant information and create exploration paths."},
            {"role": "user", "content": f"Create exploration paths for the topic '{topic}' considering these interests: {', '.join(user_interests)}. Suggest multiple learning approaches and discovery paths."}
        ]
        
        explorer_response = await self.metachain.run_async(
            agent=self.content_explorer,
            messages=explorer_messages,
            context_variables={"topic": topic, "interests": user_interests}
        )
        
        explorer_output = explorer_response.messages[-1]["content"] if explorer_response.messages else ""
        results["explorations"]["content_explorer"] = explorer_output
        
        # Create learning path
        pathfinder_messages = [
            {"role": "system", "content": "You are the Learning Pathfinder Agent. Create personalized learning sequences."},
            {"role": "user", "content": f"Create a comprehensive learning path to master '{topic}'. Consider the user's current knowledge in: {', '.join(user_interests)}. Include milestones, resources, and time estimates."}
        ]
        
        pathfinder_response = await self.metachain.run_async(
            agent=self.learning_pathfinder,
            messages=pathfinder_messages,
            context_variables={"topic": topic, "current_knowledge": user_interests}
        )
        
        pathfinder_output = pathfinder_response.messages[-1]["content"] if pathfinder_response.messages else ""
        results["explorations"]["learning_pathfinder"] = pathfinder_output
        
        return results
    
    async def generate_insights_report(self, time_period: str = "week") -> Dict[str, Any]:
        """
        Generate an insights report across the knowledge base.
        
        Args:
            time_period: Time period for the report
            
        Returns:
            Comprehensive insights report
        """
        report = {
            "period": time_period,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {}
        }
        
        # Get recent items from knowledge base for context
        recent_items = await self.memory.get_recent_items(limit=10)
        kb_context = "Recent knowledge base items:\n" + "\n".join(
            [f"- {item.get('title', 'Untitled')}: {item.get('content', '')[:100]}..." 
             for item in recent_items]
        ) if recent_items else "No recent items found."
        
        # Use Research Synthesizer to identify patterns and generate insights
        synthesizer_messages = [
            {"role": "system", "content": "You are the Research Synthesis Agent. Analyze the knowledge base and generate insights."},
            {"role": "user", "content": f"Generate an insights report for the past {time_period}.\n\n{kb_context}\n\nIdentify patterns, trends, knowledge gaps, and provide actionable insights."}
        ]
        
        synthesizer_response = await self.metachain.run_async(
            agent=self.research_synthesizer,
            messages=synthesizer_messages,
            context_variables={"time_period": time_period, "recent_items": recent_items}
        )
        
        synthesizer_output = synthesizer_response.messages[-1]["content"] if synthesizer_response.messages else ""
        report["sections"]["synthesis"] = synthesizer_output
        
        # Use Content Explorer for exploration suggestions
        explorer_messages = [
            {"role": "system", "content": "You are the Content Explorer Agent. Suggest exploration areas based on insights."},
            {"role": "user", "content": f"Based on this insights report:\n\n{synthesizer_output}\n\nSuggest exploration areas, emerging patterns to investigate, and knowledge gaps to fill."}
        ]
        
        explorer_response = await self.metachain.run_async(
            agent=self.content_explorer,
            messages=explorer_messages,
            context_variables={"insights": synthesizer_output}
        )
        
        explorer_output = explorer_response.messages[-1]["content"] if explorer_response.messages else ""
        report["sections"]["exploration_suggestions"] = explorer_output
        
        return report
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract categories from curator output."""
        # Simple extraction - in production, use NLP or regex
        categories = []
        if "category" in text.lower():
            # Extract categories mentioned in the text
            lines = text.split('\n')
            for line in lines:
                if "category" in line.lower() or "categories" in line.lower():
                    # Simple heuristic: extract words after "category:" or similar
                    categories.append("development")  # Default for now
                    break
        return categories
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract additional tags from curator output."""
        tags = []
        if "tag" in text.lower():
            # Extract tags mentioned in the text
            lines = text.split('\n')
            for line in lines:
                if "tag" in line.lower():
                    # Simple extraction
                    tags.extend(["ai", "knowledge-management"])  # Default for now
                    break
        return tags
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from curator output."""
        concepts = []
        if "concept" in text.lower() or "key" in text.lower():
            # Extract concepts
            concepts = ["knowledge curation", "ai agents", "second brain"]  # Default for now
        return concepts
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from synthesis output."""
        # Take first paragraph or first 200 chars as summary
        paragraphs = text.split('\n\n')
        if paragraphs:
            return paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
        return text[:200] + "..." if len(text) > 200 else text
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract insights from synthesis output."""
        insights = []
        lines = text.split('\n')
        for line in lines:
            if "insight" in line.lower() or line.strip().startswith('-'):
                insights.append(line.strip().lstrip('-').strip())
        return insights[:5]  # Limit to 5 insights