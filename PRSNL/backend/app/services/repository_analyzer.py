"""
Repository Analyzer Service
Enhanced GitHub/GitLab repository analysis for Code Cortex with comprehensive AI-powered insights
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.config import settings
from app.services.crawl_ai_service import CrawlAIService, RepositoryMetadata
from app.services.unified_ai_service import unified_ai_service
from app.services.media_persistence_service import media_persistence_service

logger = logging.getLogger(__name__)


class CodeCortexRepositoryAnalyzer:
    """
    Enhanced repository analyzer for Code Cortex with comprehensive AI-powered analysis
    
    Features:
    - Deep code analysis and technology stack detection
    - Learning potential assessment
    - Code quality metrics
    - Integration recommendations
    - Skill development mapping
    """
    
    def __init__(self):
        self.ai_service = unified_ai_service
        self.persistence_service = media_persistence_service
    
    async def analyze_repository(self, url: str, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Comprehensive repository analysis with Code Cortex-specific insights
        
        Args:
            url: GitHub/GitLab repository URL
            save_to_db: Whether to save analysis results to database
            
        Returns:
            Dict containing comprehensive repository analysis
        """
        try:
            logger.info(f"🔍 Starting Code Cortex analysis for: {url}")
            
            # Step 1: Basic repository crawling
            async with CrawlAIService() as crawler:
                crawl_result = await crawler.crawl_url(url, extract_content=True)
                
                if crawl_result.error:
                    logger.error(f"Failed to crawl repository: {crawl_result.error}")
                    return self._create_error_result(url, crawl_result.error)
            
            # Step 2: Extract repository information
            repo_info = self._extract_repository_info(url, crawl_result)
            
            # Step 3: AI-powered code analysis
            code_analysis = await self._analyze_code_content(crawl_result.content, url)
            
            # Step 4: Technology stack detection
            tech_stack = await self._detect_technology_stack(crawl_result.content, url)
            
            # Step 5: Learning potential assessment
            learning_analysis = await self._assess_learning_potential(
                crawl_result.content, code_analysis, tech_stack
            )
            
            # Step 6: Integration recommendations
            integrations = await self._generate_integration_recommendations(
                tech_stack, code_analysis
            )
            
            # Step 7: Compile comprehensive result
            comprehensive_result = {
                "repository_info": repo_info,
                "code_analysis": code_analysis,
                "technology_stack": tech_stack,
                "learning_analysis": learning_analysis,
                "integration_recommendations": integrations,
                "analysis_metadata": {
                    "analyzed_at": "NOW()",
                    "analyzer_version": "2.0.0",
                    "analysis_depth": "comprehensive"
                }
            }
            
            # Step 8: Save to database if requested
            if save_to_db:
                await self._save_analysis_to_db(url, comprehensive_result)
            
            logger.info(f"✅ Code Cortex analysis completed for: {url}")
            return comprehensive_result
                
        except Exception as e:
            logger.error(f"Repository analysis error: {e}")
            return self._create_error_result(url, str(e))
    
    def _extract_repository_info(self, url: str, crawl_result) -> Dict[str, Any]:
        """Extract basic repository information"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        
        return {
            "name": path_parts[-1] if path_parts else "unknown",
            "full_name": "/".join(path_parts[-2:]) if len(path_parts) >= 2 else url,
            "platform": "github" if "github.com" in url else "gitlab" if "gitlab.com" in url else "other",
            "url": url,
            "description": crawl_result.metadata.get("ai_summary", "")[:500],
            "readme_content": crawl_result.content[:2000] if crawl_result.content else "",
            "basic_metadata": crawl_result.metadata or {}
        }
    
    async def _analyze_code_content(self, content: str, url: str) -> Dict[str, Any]:
        """AI-powered code content analysis"""
        try:
            analysis_prompt = f"""
            Analyze this GitHub repository content for Code Cortex learning platform:
            
            URL: {url}
            Content: {content[:3000]}
            
            Provide analysis in these areas:
            1. CODE_QUALITY: Rate 1-10 and explain (readability, structure, documentation)
            2. COMPLEXITY_LEVEL: beginner/intermediate/advanced with explanation
            3. PROJECT_TYPE: library/application/framework/tool/tutorial/other
            4. KEY_FEATURES: List 5-7 main features or capabilities
            5. ARCHITECTURE_PATTERNS: Design patterns, architectures used
            6. LEARNING_VALUE: What developers can learn from this code
            7. SKILL_REQUIREMENTS: Prerequisites needed to understand this code
            8. CODE_HIGHLIGHTS: Most interesting/educational parts
            
            Format as JSON with these exact keys: code_quality, complexity_level, project_type, key_features, architecture_patterns, learning_value, skill_requirements, code_highlights
            """
            
            result = await self.ai_service.complete(
                prompt=analysis_prompt,
                system_prompt="You are a senior software engineer analyzing code for educational value. Provide structured analysis in valid JSON.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.3
            )
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"error": "Failed to parse AI analysis", "raw_response": result}
                
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {"error": str(e)}
    
    async def _detect_technology_stack(self, content: str, url: str) -> Dict[str, Any]:
        """Detect technology stack and dependencies"""
        try:
            tech_prompt = f"""
            Analyze this repository content to identify the complete technology stack:
            
            Content: {content[:2000]}
            
            Identify:
            1. PRIMARY_LANGUAGE: Main programming language
            2. FRAMEWORKS: Web frameworks, libraries, major dependencies
            3. DATABASES: Database technologies mentioned or used
            4. INFRASTRUCTURE: Cloud services, deployment tools, containerization
            5. TESTING: Testing frameworks and tools
            6. BUILD_TOOLS: Build systems, package managers, CI/CD
            7. FRONTEND_TECH: If applicable, frontend technologies
            8. BACKEND_TECH: If applicable, backend technologies
            9. DEVELOPMENT_TOOLS: IDEs, linters, formatters mentioned
            10. DIFFICULTY_ASSESSMENT: How hard would this stack be to learn?
            
            Format as JSON with these exact keys: primary_language, frameworks, databases, infrastructure, testing, build_tools, frontend_tech, backend_tech, development_tools, difficulty_assessment
            """
            
            result = await self.ai_service.complete(
                prompt=tech_prompt,
                system_prompt="You are a technology stack expert. Analyze thoroughly and provide structured JSON response.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.2
            )
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"error": "Failed to parse tech stack analysis", "raw_response": result}
                
        except Exception as e:
            logger.error(f"Tech stack detection failed: {e}")
            return {"error": str(e)}
    
    async def _assess_learning_potential(
        self, content: str, code_analysis: Dict, tech_stack: Dict
    ) -> Dict[str, Any]:
        """Assess learning potential and educational value"""
        try:
            learning_prompt = f"""
            Assess the learning potential of this repository for developers:
            
            Code Quality: {code_analysis.get('code_quality', 'Unknown')}
            Complexity: {code_analysis.get('complexity_level', 'Unknown')}
            Tech Stack: {tech_stack.get('primary_language', 'Unknown')}
            Project Type: {code_analysis.get('project_type', 'Unknown')}
            
            Evaluate:
            1. LEARNING_SCORE: Rate 1-10 for educational value
            2. TARGET_AUDIENCE: Who should study this? (beginners/intermediate/advanced)
            3. LEARNING_OBJECTIVES: What will developers learn?
            4. TIME_INVESTMENT: How long to study/understand this codebase?
            5. PREREQUISITE_SKILLS: Required skills before studying
            6. CAREER_RELEVANCE: How relevant for career development?
            7. PRACTICAL_APPLICATIONS: Real-world use cases
            8. RECOMMENDED_STUDY_PATH: How to approach learning from this repo
            
            Format as JSON with these exact keys: learning_score, target_audience, learning_objectives, time_investment, prerequisite_skills, career_relevance, practical_applications, recommended_study_path
            """
            
            result = await self.ai_service.complete(
                prompt=learning_prompt,
                system_prompt="You are an expert coding mentor evaluating educational resources. Provide structured JSON analysis.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.3
            )
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"error": "Failed to parse learning analysis", "raw_response": result}
                
        except Exception as e:
            logger.error(f"Learning assessment failed: {e}")
            return {"error": str(e)}
    
    async def _generate_integration_recommendations(
        self, tech_stack: Dict, code_analysis: Dict
    ) -> Dict[str, Any]:
        """Generate integration and related project recommendations"""
        try:
            integration_prompt = f"""
            Based on this technology stack and code analysis, recommend integrations and related projects:
            
            Primary Language: {tech_stack.get('primary_language', 'Unknown')}
            Frameworks: {tech_stack.get('frameworks', [])}
            Project Type: {code_analysis.get('project_type', 'Unknown')}
            
            Recommend:
            1. COMPLEMENTARY_TOOLS: Tools that work well with this stack
            2. SIMILAR_PROJECTS: Other repositories to study alongside this one
            3. INTEGRATION_OPPORTUNITIES: How this could integrate with other systems
            4. DEPLOYMENT_OPTIONS: Recommended deployment platforms/strategies
            5. MONITORING_TOOLS: Appropriate monitoring and observability tools
            6. EXTENSION_IDEAS: How developers could extend this project
            7. ALTERNATIVE_IMPLEMENTATIONS: Other ways to build similar functionality
            8. LEARNING_RESOURCES: Additional resources to study this tech stack
            
            Format as JSON with these exact keys: complementary_tools, similar_projects, integration_opportunities, deployment_options, monitoring_tools, extension_ideas, alternative_implementations, learning_resources
            """
            
            result = await self.ai_service.complete(
                prompt=integration_prompt,
                system_prompt="You are a senior architect recommending integrations and complementary technologies. Provide structured JSON recommendations.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.4
            )
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"error": "Failed to parse integration recommendations", "raw_response": result}
                
        except Exception as e:
            logger.error(f"Integration recommendations failed: {e}")
            return {"error": str(e)}
    
    async def _save_analysis_to_db(self, url: str, analysis_result: Dict[str, Any]):
        """Save comprehensive analysis to database"""
        try:
            # This would integrate with the persistence service
            # For now, we'll simulate the save operation
            logger.info(f"💾 Saving repository analysis to database for: {url}")
            # await self.persistence_service.save_repository_analysis(url, analysis_result)
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}")
    
    def _create_error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create standardized error result"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        
        return {
            "repository_info": {
                "name": path_parts[-1] if path_parts else "unknown",
                "full_name": "/".join(path_parts[-2:]) if len(path_parts) >= 2 else url,
                "platform": "github" if "github.com" in url else "gitlab" if "gitlab.com" in url else "other",
                "url": url,
                "description": f"Analysis failed: {error}",
                "error": error
            },
            "analysis_status": "failed",
            "error": error
        }


# Legacy compatibility wrapper
class RepositoryAnalyzer:
    """Legacy compatibility wrapper for existing code"""
    
    def __init__(self):
        self.enhanced_analyzer = CodeCortexRepositoryAnalyzer()
    
    async def analyze_repository(self, url: str) -> RepositoryMetadata:
        """Legacy method - returns basic RepositoryMetadata"""
        try:
            enhanced_result = await self.enhanced_analyzer.analyze_repository(url, save_to_db=False)
            
            repo_info = enhanced_result.get("repository_info", {})
            code_analysis = enhanced_result.get("code_analysis", {})
            
            return RepositoryMetadata(
                name=repo_info.get("name", "unknown"),
                full_name=repo_info.get("full_name", url),
                description=repo_info.get("description", ""),
                ai_tags=code_analysis.get("key_features", []),
                ai_category=code_analysis.get("project_type", "repository")
            )
        except Exception as e:
            logger.error(f"Legacy repository analysis error: {e}")
            return RepositoryMetadata(
                name=url.split("/")[-1],
                full_name=url,
                description=f"Analysis error: {str(e)}"
            )


# Singleton instances
repository_analyzer = RepositoryAnalyzer()  # Legacy compatibility
code_cortex_analyzer = CodeCortexRepositoryAnalyzer()  # Enhanced Code Cortex analyzer