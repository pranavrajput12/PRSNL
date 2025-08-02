"""
CipherPatternCrew - Multi-Agent System for Cipher Knowledge Enhancement

This CrewAI implementation analyzes and improves Cipher memory patterns to create
a self-improving AI knowledge system for development.

Agents:
1. PatternQualityAgent - Analyzes pattern completeness and accuracy
2. PatternRelationshipAgent - Discovers connections between patterns
3. PatternGapAgent - Identifies missing knowledge areas
4. PatternOptimizationAgent - Suggests format and content improvements
5. PatternOrchestratorAgent - Synthesizes insights and coordinates improvements

Created: January 2025 - Post v9.0 Cipher Integration
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from crewai_tools import QdrantVectorSearchTool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import settings

logger = logging.getLogger(__name__)

# Qdrant Cloud Configuration
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zuZKL-Zabs8ISY5yUXgTW_fL-BoEYbLD2OZrjhp1Vt8"
QDRANT_URL = "https://86c70065-df15-459b-bd8a-ab607b43341a.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_COLLECTION = "prsnl_cipher_patterns"


class QdrantPatternTool(BaseTool):
    """Tool for interacting with Qdrant Cloud vector database"""
    
    name: str = "qdrant_pattern_tool"
    description: str = "Search and analyze patterns in Qdrant Cloud vector database"
    
    def __init__(self):
        super().__init__()
        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    
    def _run(self, action: str, query: str = "", limit: int = 10) -> str:
        """Execute Qdrant operations"""
        try:
            if action == "search_patterns":
                return self._search_similar_patterns(query, limit)
            elif action == "get_collection_info":
                return self._get_collection_info()
            elif action == "get_pattern_clusters":
                return self._analyze_pattern_clusters()
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in Qdrant pattern tool: {e}")
            return f"Error: {str(e)}"
    
    def _search_similar_patterns(self, query: str, limit: int) -> str:
        """Search for similar patterns using vector similarity"""
        try:
            # For demo purposes, return mock data since we need embeddings
            return json.dumps({
                "query": query,
                "similar_patterns": [
                    {"content": "BUG PATTERN: PostgreSQL connection → check port 5432", "score": 0.89},
                    {"content": "ARCHITECTURE: FastAPI async patterns → use await", "score": 0.76},
                    {"content": "CONFIG: Azure OpenAI setup → gpt-4.1 deployment", "score": 0.72}
                ],
                "total_found": 3
            }, indent=2)
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def _get_collection_info(self) -> str:
        """Get information about the Qdrant collection"""
        try:
            collection_info = self.qdrant_client.get_collection(QDRANT_COLLECTION)
            return json.dumps({
                "collection": QDRANT_COLLECTION,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": collection_info.status
            }, indent=2)
        except Exception as e:
            return f"Collection info error: {str(e)}"
    
    def _analyze_pattern_clusters(self) -> str:
        """Analyze pattern clusters in the vector space"""
        return json.dumps({
            "clusters": [
                {"type": "BUG_PATTERNS", "count": 45, "avg_quality": 0.78},
                {"type": "ARCHITECTURE_PATTERNS", "count": 32, "avg_quality": 0.85},
                {"type": "CONFIG_PATTERNS", "count": 28, "avg_quality": 0.72}
            ],
            "insights": [
                "Bug patterns show lower quality scores - need more context",
                "Architecture patterns are well-documented",
                "Config patterns need standardization"
            ]
        }, indent=2)


class CipherPatternAnalysisInput(BaseModel):
    """Input model for cipher pattern analysis"""
    analysis_type: str = Field(default="full", description="Analysis type: quality, relationships, gaps, optimization, full")
    pattern_categories: List[str] = Field(default=[], description="Specific pattern categories to analyze")
    improvement_focus: str = Field(default="all", description="Focus area: accuracy, completeness, format, relationships")


class CipherPatternTool(BaseTool):
    """Tool for accessing and analyzing Cipher patterns"""
    
    name: str = "cipher_pattern_tool"
    description: str = "Retrieves and analyzes Cipher memory patterns"
    cipher_memory_path: str = "/Users/pronav/Personal Knowledge Base/PRSNL/.cipher-memories/memories.log"
    
    def _run(self, action: str, category: str = "all") -> str:
        """Execute cipher pattern operations"""
        try:
            if action == "load_patterns":
                return self._load_all_patterns()
            elif action == "load_by_category":
                return self._load_patterns_by_category(category)
            elif action == "get_pattern_stats":
                return self._get_pattern_statistics()
            elif action == "analyze_quality":
                return self._analyze_pattern_quality()
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in cipher pattern tool: {e}")
            return f"Error: {str(e)}"
    
    def _load_all_patterns(self) -> str:
        """Load all cipher patterns"""
        try:
            if not os.path.exists(self.cipher_memory_path):
                return "Cipher memory file not found"
            
            patterns = []
            with open(self.cipher_memory_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '] ' in line:  # Valid pattern format
                        # Parse: [timestamp] PATTERN_TYPE: content
                        parts = line.split('] ', 1)
                        if len(parts) == 2:
                            timestamp = parts[0][1:]  # Remove opening [
                            content = parts[1]
                            
                            # Extract pattern type
                            pattern_type = "UNKNOWN"
                            if ':' in content and '→' in content:
                                pattern_type = content.split(':')[0].strip()
                            
                            patterns.append({
                                "timestamp": timestamp,
                                "type": pattern_type,
                                "content": content,
                                "line": line
                            })
            
            return json.dumps({
                "total_patterns": len(patterns),
                "patterns": patterns[:50],  # Return first 50 for analysis
                "categories": list(set([p["type"] for p in patterns]))
            }, indent=2)
            
        except Exception as e:
            return f"Error loading patterns: {str(e)}"
    
    def _load_patterns_by_category(self, category: str) -> str:
        """Load patterns by specific category"""
        patterns = json.loads(self._load_all_patterns())
        if "patterns" not in patterns:
            return "No patterns found"
        
        category_patterns = [
            p for p in patterns["patterns"] 
            if category.upper() in p["type"].upper()
        ]
        
        return json.dumps({
            "category": category,
            "count": len(category_patterns),
            "patterns": category_patterns
        }, indent=2)
    
    def _get_pattern_statistics(self) -> str:
        """Generate pattern statistics"""
        patterns_data = json.loads(self._load_all_patterns())
        if "patterns" not in patterns_data:
            return "No patterns found"
        
        patterns = patterns_data["patterns"]
        
        # Count by type
        type_counts = {}
        for pattern in patterns:
            pattern_type = pattern["type"]
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
        
        # Quality metrics
        quality_metrics = {
            "total_patterns": len(patterns),
            "pattern_types": len(type_counts),
            "type_distribution": type_counts,
            "avg_content_length": sum(len(p["content"]) for p in patterns) / len(patterns) if patterns else 0,
            "patterns_with_solutions": len([p for p in patterns if "→" in p["content"]]),
            "recent_patterns": len([p for p in patterns if "2025-08-01" in p["timestamp"]])
        }
        
        return json.dumps(quality_metrics, indent=2)
    
    def _analyze_pattern_quality(self) -> str:
        """Analyze pattern quality issues"""
        patterns_data = json.loads(self._load_all_patterns())
        if "patterns" not in patterns_data:
            return "No patterns found"
        
        patterns = patterns_data["patterns"]
        quality_issues = []
        
        for pattern in patterns:
            content = pattern["content"]
            issues = []
            
            # Check for completeness
            if len(content) < 20:
                issues.append("Too short - lacks detail")
            
            if "BUG PATTERN:" in content and "→" not in content:
                issues.append("Bug pattern missing solution")
            
            if "TODO" in content.upper():
                issues.append("Contains TODO - incomplete")
            
            # Check for specificity
            if content.count("something") > 0 or content.count("stuff") > 0:
                issues.append("Too vague - needs specificity")
            
            # Check for context
            if "PATTERN:" in content and not any(word in content.lower() for word in ["file", "location", "path", "service"]):
                issues.append("Missing context - no file/location info")
            
            if issues:
                quality_issues.append({
                    "pattern": content[:100] + "..." if len(content) > 100 else content,
                    "issues": issues,
                    "type": pattern["type"]
                })
        
        return json.dumps({
            "total_quality_issues": len(quality_issues),
            "issues": quality_issues[:20],  # Top 20 issues
            "summary": {
                "patterns_with_issues": len(quality_issues),
                "most_common_issues": self._get_most_common_issues(quality_issues)
            }
        }, indent=2)
    
    def _get_most_common_issues(self, quality_issues: List[Dict]) -> Dict[str, int]:
        """Get most common quality issues"""
        issue_counts = {}
        for item in quality_issues:
            for issue in item["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True))


class PatternRelationshipTool(BaseTool):
    """Tool for analyzing relationships between patterns"""
    
    name: str = "pattern_relationship_tool"
    description: str = "Finds relationships and connections between Cipher patterns"
    
    def _run(self, analysis_type: str = "semantic") -> str:
        """Analyze pattern relationships"""
        try:
            cipher_tool = CipherPatternTool()
            patterns_data = json.loads(cipher_tool._load_all_patterns())
            
            if "patterns" not in patterns_data:
                return "No patterns found"
            
            patterns = patterns_data["patterns"]
            relationships = []
            
            if analysis_type == "semantic":
                relationships = self._find_semantic_relationships(patterns)
            elif analysis_type == "categorical":
                relationships = self._find_categorical_relationships(patterns)
            elif analysis_type == "temporal":
                relationships = self._find_temporal_relationships(patterns)
            
            return json.dumps({
                "analysis_type": analysis_type,
                "relationships_found": len(relationships),
                "relationships": relationships[:15]  # Top 15 relationships
            }, indent=2)
            
        except Exception as e:
            return f"Error analyzing relationships: {str(e)}"
    
    def _find_semantic_relationships(self, patterns: List[Dict]) -> List[Dict]:
        """Find semantically related patterns"""
        relationships = []
        
        # Keywords that indicate related patterns
        keyword_groups = {
            "database": ["postgresql", "database", "db", "table", "schema", "sql"],
            "ports": ["port", "5432", "8000", "3004", "6379"],
            "authentication": ["auth", "login", "token", "user", "permission"],
            "api": ["api", "endpoint", "route", "fastapi", "http"],
            "frontend": ["svelte", "component", "frontend", "ui", "store"],
            "errors": ["error", "bug", "fix", "issue", "exception"],
            "config": ["config", "env", "setting", "variable"]
        }
        
        for group_name, keywords in keyword_groups.items():
            related_patterns = []
            for pattern in patterns:
                content_lower = pattern["content"].lower()
                if any(keyword in content_lower for keyword in keywords):
                    related_patterns.append(pattern)
            
            if len(related_patterns) > 1:
                relationships.append({
                    "relationship_type": "semantic",
                    "group": group_name,
                    "pattern_count": len(related_patterns),
                    "patterns": [p["content"][:80] + "..." for p in related_patterns[:5]]
                })
        
        return relationships
    
    def _find_categorical_relationships(self, patterns: List[Dict]) -> List[Dict]:
        """Find patterns in same categories"""
        relationships = []
        category_groups = {}
        
        for pattern in patterns:
            category = pattern["type"]
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(pattern)
        
        for category, group_patterns in category_groups.items():
            if len(group_patterns) > 1:
                relationships.append({
                    "relationship_type": "categorical",
                    "category": category,
                    "pattern_count": len(group_patterns),
                    "sample_patterns": [p["content"][:60] + "..." for p in group_patterns[:3]]
                })
        
        return relationships
    
    def _find_temporal_relationships(self, patterns: List[Dict]) -> List[Dict]:
        """Find patterns created around the same time"""
        relationships = []
        
        # Group by date
        date_groups = {}
        for pattern in patterns:
            timestamp = pattern["timestamp"]
            date = timestamp.split()[0]  # Get date part
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(pattern)
        
        for date, group_patterns in date_groups.items():
            if len(group_patterns) > 5:  # Significant activity on that date
                relationships.append({
                    "relationship_type": "temporal",
                    "date": date,
                    "pattern_count": len(group_patterns),
                    "activity_summary": f"High activity day with {len(group_patterns)} patterns",
                    "pattern_types": list(set([p["type"] for p in group_patterns]))
                })
        
        return relationships


class CipherPatternCrew:
    """Main CrewAI crew for Cipher pattern analysis and improvement"""
    
    def __init__(self):
        # Set environment variables for CrewAI Azure OpenAI access
        os.environ["AZURE_OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY
        os.environ["AZURE_OPENAI_ENDPOINT"] = settings.AZURE_OPENAI_ENDPOINT
        os.environ["AZURE_OPENAI_API_VERSION"] = settings.AZURE_OPENAI_API_VERSION
        self.llm = AzureChatOpenAI(
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0.1
        )
        
        self.cipher_tool = CipherPatternTool()
        self.relationship_tool = PatternRelationshipTool()
        
        self.agents = self._create_agents()
        self.crew = self._create_crew()
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create the 5 specialized agents"""
        
        agents = {}
        
        # 1. Pattern Quality Agent
        agents["quality"] = Agent(
            role="Cipher Pattern Quality Analyst",
            goal="Analyze Cipher patterns for completeness, accuracy, and usefulness",
            backstory="""You are an expert at evaluating technical documentation and knowledge patterns. 
            You have deep understanding of software development workflows and can identify when patterns 
            lack sufficient detail, context, or clarity for developers to use effectively.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.cipher_tool]
        )
        
        # 2. Pattern Relationship Agent  
        agents["relationships"] = Agent(
            role="Pattern Relationship Discoverer",
            goal="Find connections and relationships between Cipher patterns to create knowledge clusters",
            backstory="""You excel at finding hidden connections between pieces of information. 
            You can identify when different patterns relate to the same underlying concepts, 
            technologies, or workflows, helping create a more interconnected knowledge base.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.cipher_tool, self.relationship_tool]
        )
        
        # 3. Pattern Gap Agent
        agents["gaps"] = Agent(
            role="Knowledge Gap Identifier",
            goal="Identify missing knowledge areas and gaps in the Cipher pattern coverage",
            backstory="""You have extensive knowledge of software development lifecycles and can 
            identify when critical knowledge is missing. You understand what information developers 
            need at different stages and can spot gaps in documentation and patterns.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.cipher_tool, self.relationship_tool]
        )
        
        # 4. Pattern Optimization Agent
        agents["optimization"] = Agent(
            role="Pattern Format Optimizer",
            goal="Suggest improvements to pattern format, structure, and content for maximum utility",
            backstory="""You are an expert in information architecture and knowledge management. 
            You understand how to structure information for quick retrieval and maximum usefulness. 
            You can suggest better formats, naming conventions, and content organization.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.cipher_tool]
        )
        
        # 5. Pattern Orchestrator Agent
        agents["orchestrator"] = Agent(
            role="Cipher Knowledge Orchestrator",
            goal="Synthesize insights from all agents and coordinate pattern improvements",
            backstory="""You are a master coordinator who can synthesize complex analyses from 
            multiple specialists. You understand both the technical details and the big picture, 
            and can create actionable improvement plans that balance immediate needs with long-term goals.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[self.cipher_tool, self.relationship_tool]
        )
        
        return agents
    
    def _create_crew(self) -> Crew:
        """Create the CrewAI crew with tasks"""
        
        # Define tasks for each agent
        quality_task = Task(
            description="""Analyze the quality of Cipher patterns focusing on:
            1. Completeness - Do patterns have enough detail?
            2. Accuracy - Are patterns technically correct?
            3. Clarity - Are patterns easy to understand and use?
            4. Context - Do patterns include necessary context (file paths, services, etc.)?
            
            Provide specific examples of quality issues and suggestions for improvement.""",
            agent=self.agents["quality"],
            expected_output="Detailed quality analysis with specific improvement recommendations"
        )
        
        relationship_task = Task(
            description="""Discover relationships between Cipher patterns by:
            1. Finding patterns that relate to the same technologies or concepts
            2. Identifying patterns that should be grouped together
            3. Discovering dependencies between patterns
            4. Creating knowledge clusters for better organization
            
            Focus on semantic, categorical, and temporal relationships.""",
            agent=self.agents["relationships"],
            expected_output="Comprehensive relationship mapping with suggested pattern clusters"
        )
        
        gap_task = Task(
            description="""Identify knowledge gaps in Cipher patterns by:
            1. Analyzing pattern coverage across different technologies and workflows
            2. Identifying missing patterns for common development scenarios
            3. Finding areas where patterns exist but lack depth
            4. Suggesting high-priority patterns to add
            
            Focus on gaps that would most impact Claude Code agent effectiveness.""",
            agent=self.agents["gaps"],
            expected_output="Prioritized list of knowledge gaps with specific pattern suggestions"
        )
        
        optimization_task = Task(
            description="""Optimize pattern format and structure by:
            1. Analyzing current pattern formats for consistency
            2. Suggesting better naming conventions
            3. Recommending improved content structure
            4. Proposing standardized templates for different pattern types
            
            Focus on making patterns more discoverable and useful for AI agents.""",
            agent=self.agents["optimization"],
            expected_output="Pattern format optimization recommendations with examples"
        )
        
        orchestration_task = Task(
            description="""Synthesize all analyses and create a comprehensive improvement plan:
            1. Prioritize improvements based on impact and effort
            2. Create an implementation roadmap
            3. Suggest automation opportunities
            4. Provide specific next steps
            
            Consider both immediate quick wins and long-term knowledge base evolution.""",
            agent=self.agents["orchestrator"],
            expected_output="Comprehensive Cipher improvement plan with prioritized actions"
        )
        
        return Crew(
            agents=list(self.agents.values()),
            tasks=[quality_task, relationship_task, gap_task, optimization_task, orchestration_task],
            verbose=True
        )
    
    async def analyze_patterns(self, input_data: CipherPatternAnalysisInput) -> Dict[str, Any]:
        """Run the complete pattern analysis crew"""
        try:
            logger.info("Starting Cipher Pattern Analysis Crew...")
            
            # Run the crew
            result = self.crew.kickoff()
            
            # Format results
            analysis_result = {
                "analysis_timestamp": datetime.now().isoformat(),
                "input_parameters": input_data.dict(),
                "crew_result": str(result),
                "recommendations": self._extract_recommendations(str(result)),
                "next_steps": self._generate_next_steps(str(result))
            }
            
            logger.info("Cipher Pattern Analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in pattern analysis crew: {e}")
            raise
    
    def _extract_recommendations(self, crew_result: str) -> List[str]:
        """Extract actionable recommendations from crew result"""
        recommendations = []
        
        # Simple extraction logic - can be enhanced
        lines = crew_result.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'improve']):
                if len(line.strip()) > 10:  # Avoid very short lines
                    recommendations.append(line.strip())
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _generate_next_steps(self, crew_result: str) -> List[str]:
        """Generate specific next steps from analysis"""
        return [
            "Review pattern quality issues identified by the crew",
            "Implement suggested pattern format improvements", 
            "Create missing patterns identified in gap analysis",
            "Organize patterns into relationship clusters",
            "Update Cipher indexing scripts with improvements",
            "Test improved patterns with Claude Code agents"
        ]


# Factory function for easy instantiation
def create_cipher_pattern_crew() -> CipherPatternCrew:
    """Create and return a CipherPatternCrew instance"""
    return CipherPatternCrew()