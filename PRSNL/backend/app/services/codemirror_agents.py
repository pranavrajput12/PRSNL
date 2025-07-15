"""
CodeMirror AI Agents - Specialized agents for repository intelligence

Dedicated AI agents for CodeMirror feature that don't interfere with existing research agents.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.config import settings
from app.services.unified_ai_service import unified_ai_service
from app.services.cache import cache_service
from app.services.ai_router import ai_router
from app.services.ai_router_types import AITask, TaskType, TaskComplexity
from app.services.langchain_prompts import prompt_template_manager

logger = logging.getLogger(__name__)


class CodeMirrorAgentResult(BaseModel):
    """Result from a CodeMirror AI agent"""
    agent_name: str
    status: str = "completed"
    results: Dict[str, Any]
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CodeRepositoryAnalysisAgent:
    """
    Specialized agent for analyzing code repositories.
    
    Performs deep code analysis including:
    - Architecture patterns detection
    - Security vulnerability scanning
    - Performance bottleneck identification
    - Code quality assessment
    """
    
    def __init__(self):
        self.name = "CodeRepositoryAnalysisAgent"
        self.use_enhanced_routing = getattr(settings, 'CODEMIRROR_ENHANCED_ROUTING', True)
        self.use_prompt_templates = getattr(settings, 'CODEMIRROR_PROMPT_TEMPLATES', True)
        
    async def analyze_repository(
        self, 
        repo_data: Dict[str, Any],
        analysis_depth: str = "standard"
    ) -> CodeMirrorAgentResult:
        """
        Analyze a code repository for patterns, issues, and opportunities.
        
        Args:
            repo_data: Repository metadata and file content
            analysis_depth: Level of analysis (quick, standard, deep)
            
        Returns:
            CodeMirrorAgentResult with analysis findings
        """
        start_time = datetime.utcnow()
        
        try:
            # Build analysis prompt based on depth
            prompt = self._build_analysis_prompt(repo_data, analysis_depth)
            
            # Use enhanced routing for analysis
            response = await self._route_analysis_task(prompt, analysis_depth)
            
            # Parse AI response
            analysis_results = self._parse_analysis_response(response, repo_data)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="completed",
                results=analysis_results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    def _build_analysis_prompt(self, repo_data: Dict[str, Any], depth: str) -> str:
        """Build analysis prompt based on repository data and depth"""
        
        # Use template if available
        template_prompt = self._get_template_prompt(
            'code_analysis',
            {
                'code': repo_data.get('file_samples', ''),
                'analysis_type': f'repository_analysis_{depth}',
                'language': repo_data.get('language', 'auto-detect'),
                'repository_name': repo_data.get('name', 'Unknown'),
                'repository_description': repo_data.get('description', 'No description'),
                'repository_size': repo_data.get('size', 'Unknown'),
                'repository_stars': repo_data.get('stargazers_count', 0),
                'repository_forks': repo_data.get('forks_count', 0),
                'last_updated': repo_data.get('updated_at', 'Unknown'),
                'analysis_depth': depth,
                'default_prompt': self._get_fallback_prompt(repo_data, depth)
            }
        )
        
        return template_prompt if template_prompt else self._get_fallback_prompt(repo_data, depth)
    
    def _get_fallback_prompt(self, repo_data: Dict[str, Any], depth: str) -> str:
        """Fallback prompt when templates are not available"""
        
        prompt = f"""
        Analyze this code repository: {repo_data.get('name', 'Unknown')}
        
        Repository Information:
        - Language: {repo_data.get('language', 'Not specified')}
        - Description: {repo_data.get('description', 'No description')}
        - Size: {repo_data.get('size', 'Unknown')} KB
        - Stars: {repo_data.get('stargazers_count', 0)}
        - Forks: {repo_data.get('forks_count', 0)}
        - Last updated: {repo_data.get('updated_at', 'Unknown')}
        
        """
        
        if depth == "quick":
            prompt += """
            Perform a QUICK analysis focusing on:
            - Overall architecture assessment
            - Major security red flags
            - Critical performance issues
            """
        elif depth == "standard":
            prompt += """
            Perform a STANDARD analysis including:
            - Detailed architecture patterns review
            - Security vulnerability assessment
            - Performance optimization opportunities
            - Code quality metrics
            - Dependency analysis
            """
        else:  # deep
            prompt += """
            Perform a DEEP analysis covering:
            - Comprehensive architecture review
            - Detailed security audit
            - Performance profiling and bottlenecks
            - Code quality and maintainability assessment
            - Dependencies and technical debt analysis
            - Testing strategy evaluation
            - Documentation quality
            """
        
        # Add file samples if available
        if repo_data.get('file_samples'):
            prompt += f"""
            
            Code Samples:
            {repo_data['file_samples']}
            """
        
        return prompt
    
    def _parse_analysis_response(self, response: str, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into structured analysis results"""
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Return error state instead of fake data
        return {
            "error": "Failed to parse AI response",
            "raw_analysis": response,
            "status": "parse_error"
        }

    async def _route_analysis_task(self, content: str, complexity_level: str = "medium") -> str:
        """Route analysis task through enhanced AI router"""
        if not self.use_enhanced_routing:
            return await unified_ai_service.complete(
                prompt=content,
                system_prompt="You are a senior software architect and security expert.",
                model=settings.AZURE_OPENAI_DEPLOYMENT
            )
        
        try:
            # Map complexity levels
            complexity_map = {
                "simple": TaskComplexity.SIMPLE,
                "medium": TaskComplexity.MODERATE,
                "complex": TaskComplexity.COMPLEX,
                "deep": TaskComplexity.EXPERT
            }
            
            task = AITask(
                type=TaskType.TEXT_GENERATION,
                content=content,
                options={
                    "analysis_type": "code_repository_analysis",
                    "codemirror_agent": self.name
                }
            )
            
            # Route through enhanced AI router
            result = await ai_router.execute_with_fallback(
                task, 
                self._execute_direct_analysis
            )
            
            return result if isinstance(result, str) else str(result)
            
        except Exception as e:
            logger.error(f"Enhanced routing failed: {e}")
            return await self._execute_direct_analysis(content)
    
    async def _execute_direct_analysis(self, content: str, task: Optional[AITask] = None) -> str:
        """Execute direct analysis without routing"""
        # Handle both direct calls and fallback calls from router
        if isinstance(content, AITask):
            # Called as fallback from router
            actual_content = content.content
        else:
            # Direct call
            actual_content = content
        return await unified_ai_service.complete(
            prompt=actual_content,
            system_prompt="You are a senior software architect and security expert.",
            model=settings.AZURE_OPENAI_DEPLOYMENT
        )
    
    def _get_template_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Get prompt from template manager"""
        if not self.use_prompt_templates or not prompt_template_manager.enabled:
            return variables.get("default_prompt", "")
        
        try:
            return prompt_template_manager.get_prompt(template_name, variables)
        except Exception as e:
            logger.error(f"Template prompt generation failed: {e}")
            return variables.get("default_prompt", "")


class CodePatternDetectionAgent:
    """
    Specialized agent for detecting and cataloging code patterns.
    
    Identifies reusable patterns, anti-patterns, and solution approaches
    that can be leveraged across projects.
    """
    
    def __init__(self):
        self.name = "CodePatternDetectionAgent"
        self.use_enhanced_routing = getattr(settings, 'CODEMIRROR_ENHANCED_ROUTING', True)
        self.use_prompt_templates = getattr(settings, 'CODEMIRROR_PROMPT_TEMPLATES', True)
        
    async def detect_patterns(
        self, 
        repo_data: Dict[str, Any],
        existing_patterns: List[Dict[str, Any]] = None
    ) -> CodeMirrorAgentResult:
        """
        Detect code patterns in repository.
        
        Args:
            repo_data: Repository data and code samples
            existing_patterns: Previously detected patterns for comparison
            
        Returns:
            CodeMirrorAgentResult with detected patterns
        """
        start_time = datetime.utcnow()
        
        try:
            prompt = self._build_pattern_detection_prompt(repo_data, existing_patterns)
            
            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="""You are an expert code pattern analyst. 
                Identify recurring patterns, architectural decisions, and design approaches.
                Focus on:
                1. Design patterns (Singleton, Factory, Observer, etc.)
                2. Architectural patterns (MVC, Microservices, etc.)
                3. Security patterns (Authentication, Authorization, etc.)
                4. Performance patterns (Caching, Optimization, etc.)
                5. Anti-patterns and code smells
                
                Return patterns in JSON format with confidence scores.""",
                model=settings.AZURE_OPENAI_DEPLOYMENT
            )
            
            patterns = self._parse_pattern_response(response)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="completed",
                results={"patterns": patterns},
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    def _build_pattern_detection_prompt(
        self, 
        repo_data: Dict[str, Any], 
        existing_patterns: List[Dict[str, Any]] = None
    ) -> str:
        """Build pattern detection prompt"""
        
        prompt = f"""
        Detect code patterns in this repository: {repo_data.get('name', 'Unknown')}
        
        Repository Context:
        - Language: {repo_data.get('language', 'Not specified')}
        - Framework/Stack: {repo_data.get('topics', [])}
        """
        
        if repo_data.get('file_samples'):
            prompt += f"""
            
            Code Samples to Analyze:
            {repo_data['file_samples']}
            """
        
        if existing_patterns:
            prompt += f"""
            
            Previously Detected Patterns (for comparison):
            {json.dumps(existing_patterns[:5], indent=2)}  # Limit to first 5
            """
        
        return prompt
    
    def _parse_pattern_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse pattern detection response"""
        
        try:
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get('patterns', [])
            elif response.strip().startswith('['):
                return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Return empty list when parsing fails
        return []


class CodeInsightGeneratorAgent:
    """
    Specialized agent for generating actionable insights and recommendations.
    
    Synthesizes analysis results into practical, prioritized insights
    that developers can act upon.
    """
    
    def __init__(self):
        self.name = "CodeInsightGeneratorAgent"
        
    async def generate_insights(
        self, 
        analysis_results: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        repo_context: Dict[str, Any]
    ) -> CodeMirrorAgentResult:
        """
        Generate actionable insights from analysis and patterns.
        
        Args:
            analysis_results: Repository analysis results
            patterns: Detected patterns
            repo_context: Repository metadata
            
        Returns:
            CodeMirrorAgentResult with generated insights
        """
        start_time = datetime.utcnow()
        
        try:
            prompt = self._build_insight_prompt(analysis_results, patterns, repo_context)
            
            response = await unified_ai_service.complete(
                prompt=prompt,
                system_prompt="""You are a senior technical advisor specializing in code optimization.
                Generate prioritized, actionable insights based on the analysis and patterns.
                
                For each insight, provide:
                1. Clear title and description
                2. Severity level (low, medium, high, critical)
                3. Specific recommendation with steps
                4. Estimated effort and impact
                5. Relevant code examples if applicable
                
                Focus on insights that provide the highest value with reasonable effort.""",
                model=settings.AZURE_OPENAI_DEPLOYMENT
            )
            
            insights = self._parse_insights_response(response)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="completed",
                results={"insights": insights},
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeMirrorAgentResult(
                agent_name=self.name,
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    def _build_insight_prompt(
        self, 
        analysis_results: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        repo_context: Dict[str, Any]
    ) -> str:
        """Build insight generation prompt"""
        
        return f"""
        Generate actionable insights for repository: {repo_context.get('name', 'Unknown')}
        
        Analysis Results:
        {json.dumps(analysis_results, indent=2)}
        
        Detected Patterns:
        {json.dumps(patterns[:10], indent=2)}  # Limit to first 10
        
        Repository Context:
        - Language: {repo_context.get('language', 'Not specified')}
        - Team Size: {repo_context.get('contributors_count', 'Unknown')}
        - Activity Level: {repo_context.get('updated_at', 'Unknown')}
        - Visibility: {'Public' if not repo_context.get('private') else 'Private'}
        """
    
    def _parse_insights_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse insight generation response"""
        
        try:
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get('insights', [])
            elif response.strip().startswith('['):
                return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Fallback: create single insight from response
        return [{
            "title": "Repository Analysis Complete",
            "description": response[:500],
            "insight_type": "general",
            "severity": "medium",
            "recommendation": "Review the analysis results and consider the suggested improvements",
            "confidence_score": 0.7,
            "estimated_effort": "medium",
            "expected_impact": "medium"
        }]


# Singleton instances for CodeMirror agents
code_repository_analysis_agent = CodeRepositoryAnalysisAgent()
code_pattern_detection_agent = CodePatternDetectionAgent()
code_insight_generator_agent = CodeInsightGeneratorAgent()