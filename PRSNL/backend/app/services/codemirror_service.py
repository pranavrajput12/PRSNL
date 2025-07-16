"""
CodeMirror Service - AI-powered repository intelligence

Orchestrates repository analysis using PRSNL's multi-agent AI system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.config import settings
from app.db.database import get_db_pool, get_db_connection
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import JobPersistenceService
from app.services.embedding_manager import embedding_manager

# LangGraph integration with graceful fallback
try:
    from app.services.langgraph_workflows import create_workflow_manager
    from enum import Enum
    
    class ContentType(str, Enum):
        DOCUMENT = "document"
        VIDEO = "video"
        AUDIO = "audio"
        CODE = "code"
        IMAGE = "image"
        URL = "url"
        TEXT = "text"
    
    langgraph_workflow_service = create_workflow_manager()
    langgraph_workflow_service.enabled = True
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    langgraph_workflow_service = None
    ContentType = str  # Fallback
    
from app.services.ai_router import ai_router
from app.services.ai_router_types import AITask, TaskType
from app.services.langchain_prompts import prompt_template_manager
from app.services.codemirror_agents import (
    code_repository_analysis_agent,
    code_pattern_detection_agent,
    code_insight_generator_agent
)
from app.services.github_service import GitHubService
from app.services.websocket_manager import websocket_manager
from app.services.http_client_factory import http_client_factory, ClientType

logger = logging.getLogger(__name__)

class CodeMirrorService:
    """
    Main service for CodeMirror repository intelligence.
    Leverages PRSNL's AI infrastructure for deep code analysis.
    """
    
    def __init__(self):
        self.analysis_agent = code_repository_analysis_agent
        self.pattern_agent = code_pattern_detection_agent
        self.insight_agent = code_insight_generator_agent
        self.github = GitHubService()
        self.synthesizer = None  # Initialize if needed for synthesis
        self.use_langgraph = getattr(settings, 'CODEMIRROR_LANGGRAPH_ENABLED', True)
        self.use_enhanced_routing = getattr(settings, 'CODEMIRROR_ENHANCED_ROUTING', True)
        self.use_prompt_templates = getattr(settings, 'CODEMIRROR_PROMPT_TEMPLATES', True)
        
    async def analyze_repository(
        self,
        repo_id: str,
        job_id: str,
        user_id: str,
        analysis_depth: str = "standard"
    ):
        """
        Progressive repository analysis using PRSNL's job system.
        
        Phases:
        1. Quick (0-30%): README, structure, basic insights
        2. Standard (30-70%): Dependencies, patterns, code quality
        3. Deep (70-100%): Full analysis, learning paths, architecture
        """
        
        logger.info(f"Starting CodeMirror analysis - Job: {job_id}, Repo: {repo_id}, Depth: {analysis_depth}")
        
        try:
            # Immediate job status update to confirm method is called
            await self._update_job_progress(
                job_id=job_id,
                progress=5,
                stage="starting",
                message="CodeMirror analysis method called"
            )
            
            # Create analysis record
            analysis_id = await self._create_analysis_record(
                repo_id, job_id, analysis_depth
            )
            
            logger.info(f"Created analysis record: {analysis_id}")
            
            # Update job status
            await self._update_job_progress(
                job_id=job_id,
                progress=10,
                stage="initialization",
                message="Starting CodeMirror analysis"
            )
            
            # Phase 1: Quick Analysis
            await self._quick_analysis_phase(
                repo_id, job_id, analysis_id, user_id
            )
            
            if analysis_depth in ["standard", "deep"]:
                # Phase 2: Standard Analysis
                await self._standard_analysis_phase(
                    repo_id, job_id, analysis_id, user_id
                )
            
            if analysis_depth == "deep":
                # Phase 3: Deep Analysis
                await self._deep_analysis_phase(
                    repo_id, job_id, analysis_id, user_id
                )
            
            # Finalize analysis
            await self._finalize_analysis(analysis_id, job_id)
            
        except Exception as e:
            logger.error(f"CodeMirror analysis failed for job {job_id}: {str(e)}", exc_info=True)
            try:
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    job_service = JobPersistenceService(conn)
                    await job_service.update_job_status(
                        job_id=job_id,
                        status="failed",
                        error_message=str(e)
                    )
            except Exception as db_error:
                logger.error(f"Failed to update job status to failed: {db_error}")
            raise
    
    async def _update_job_progress(self, job_id: str, progress: int, stage: str, message: str):
        """Helper to update job progress with database connection"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.update_job_status(
                job_id=job_id,
                status="processing",
                progress_percentage=progress,
                current_stage=stage,
                stage_message=message
            )

    async def _quick_analysis_phase(
        self, repo_id: str, job_id: str, analysis_id: str, user_id: str
    ):
        """Quick analysis phase - immediate insights"""
        
        await self._update_job_progress(
            job_id,
            progress=5,
            stage="quick_analysis",
            message="Analyzing repository structure and documentation"
        )
        
        # Fetch repository metadata
        repo_data = await self._fetch_repo_data(repo_id)
        
        # Quick repository analysis
        try:
            readme_content = await self.github.fetch_file(
                repo_data['full_name'], 'README.md'
            )
        except Exception as e:
            logger.warning(f"Failed to fetch README from GitHub: {e}")
            # Return error state instead of mock data
            readme_content = None
            logger.warning(f"README analysis skipped for {repo_data.get('name', 'Repository')} due to GitHub API failure")
        
        # Prepare repo data for analysis
        analysis_data = {
            **repo_data,
            'readme_content': readme_content,
            'analysis_type': 'quick'
        }
        
        if readme_content:
            readme_analysis = await self.analysis_agent.analyze_repository(
                repo_data=analysis_data,
                analysis_depth="quick"
            )
            
            # Generate diverse insights based on analysis
            analysis_results = readme_analysis.results
            await self._generate_diverse_insights(analysis_id, analysis_results, repo_data)
        
        # Quick structure scan
        try:
            structure = await self.github.fetch_repo_structure(repo_data['full_name'])
        except Exception as e:
            logger.warning(f"Failed to fetch repo structure from GitHub: {e}")
            # Return empty structure and mark analysis as incomplete
            structure = []
            logger.error(f"Repository structure analysis failed for {repo_data['full_name']} - GitHub API unavailable")
        
        # Detect frameworks and build tools
        frameworks = self._detect_frameworks(structure)
        await self._update_analysis_metadata(analysis_id, {
            'frameworks_detected': frameworks,
            'file_count': len(structure),
            'languages_detected': self._detect_languages(structure)
        })
        
        # Send progress update
        await self._send_progress_update(job_id, 30, "quick_complete", 
                                       "Quick analysis complete")
    
    async def _standard_analysis_phase(
        self, repo_id: str, job_id: str, analysis_id: str, user_id: str
    ):
        """Standard analysis phase - patterns and dependencies"""
        
        await self._update_job_progress(
            job_id=job_id,
            progress=35,
            stage="standard_analysis",
            message="Analyzing dependencies and code patterns"
        )
        
        repo_data = await self._fetch_repo_data(repo_id)
        
        # Analyze dependencies and patterns
        package_files = await self._fetch_package_files(repo_data['full_name'])
        code_samples = await self._fetch_code_samples(repo_data['full_name'])
        
        # Standard repository analysis
        analysis_data = {
            **repo_data,
            'package_files': package_files,
            'file_samples': code_samples,
            'analysis_type': 'standard'
        }
        
        analysis_result = await self.analysis_agent.analyze_repository(
            repo_data=analysis_data,
            analysis_depth="standard"
        )
        
        # Update analysis scores
        if analysis_result.status == "completed":
            results = analysis_result.results
            await self._update_analysis_scores(
                analysis_id, 
                {
                    'security': results.get('security_score'),
                    'performance': results.get('performance_score'),
                    'quality': results.get('quality_score')
                }
            )
        
        # Detect patterns
        existing_patterns = await self._get_user_patterns(user_id)
        pattern_result = await self.pattern_agent.detect_patterns(
            repo_data=analysis_data,
            existing_patterns=existing_patterns
        )
        
        # Store detected patterns
        if pattern_result.status == "completed":
            for pattern in pattern_result.results.get('patterns', []):
                # Normalize pattern data
                pattern_type = pattern.get('pattern_type', pattern.get('type', 'other'))
                # Map pattern types to allowed values
                type_mapping = {
                    'general': 'other',
                    'architectural': 'architecture',
                    'architectural pattern': 'architecture',
                    'auth': 'authentication',
                    'auth pattern': 'authentication',
                    'error': 'error_handling',
                    'api': 'api_call',
                    'data': 'data_processing',
                    'ui': 'ui_pattern',
                    'test': 'testing',
                    'config': 'configuration'
                }
                normalized_type = type_mapping.get(pattern_type.lower(), 'other')
                
                normalized_pattern = {
                    'signature': pattern.get('pattern_signature', pattern.get('signature', 'unknown')),
                    'type': normalized_type,
                    'description': pattern.get('description', ''),
                    'code_snippet': pattern.get('code_snippet', ''),
                    'language': pattern.get('language', 'unknown'),
                    'confidence': pattern.get('confidence', 0.7),
                    'detected_by': 'code_pattern_detection_agent'
                }
                await self._store_pattern(user_id, normalized_pattern)
        
        await self._send_progress_update(job_id, 70, "standard_complete",
                                       "Pattern analysis complete")
    
    async def _deep_analysis_phase(
        self, repo_id: str, job_id: str, analysis_id: str, user_id: str
    ):
        """Deep analysis phase - architecture and learning paths"""
        
        await self._update_job_progress(
            job_id=job_id,
            progress=75,
            stage="deep_analysis",
            message="Performing deep architectural analysis"
        )
        
        # Deep comprehensive analysis
        repo_data = await self._fetch_repo_data(repo_id)
        full_codebase = await self._analyze_full_codebase(repo_data['full_name'])
        
        # Deep repository analysis
        analysis_data = {
            **repo_data,
            'full_codebase_analysis': full_codebase,
            'analysis_type': 'deep'
        }
        
        deep_analysis = await self.analysis_agent.analyze_repository(
            repo_data=analysis_data,
            analysis_depth="deep"
        )
        
        # Get existing patterns and analysis results for insight generation
        patterns = await self._get_user_patterns(user_id)
        analysis_results = deep_analysis.results if deep_analysis.status == "completed" else {}
        
        # Generate actionable insights
        insight_result = await self.insight_agent.generate_insights(
            analysis_results=analysis_results,
            patterns=patterns,
            repo_context=repo_data
        )
        
        # Store generated insights
        if insight_result.status == "completed":
            for insight in insight_result.results.get('insights', []):
                await self._create_insight(
                    analysis_id=analysis_id,
                    insight_type=insight.get('insight_type', 'general'),
                    title=insight.get('title', 'Generated Insight'),
                    description=insight.get('description', ''),
                    recommendation=insight.get('recommendation', ''),
                    severity=insight.get('severity', 'medium'),
                    generated_by="code_insight_generator_agent",
                    confidence=insight.get('confidence_score', 0.75)
                )
        
        # Update final scores
        if deep_analysis.status == "completed":
            results = deep_analysis.results
            await self._update_analysis_scores(
                analysis_id,
                {
                    'security': results.get('security_score'),
                    'performance': results.get('performance_score'),
                    'quality': results.get('quality_score')
                }
            )
        
        await self._send_progress_update(job_id, 100, "analysis_complete",
                                       "Deep analysis complete")
    
    async def synthesize_solution(
        self, user_id: str, problem_description: str, 
        file_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize a solution based on user's patterns and PRSNL knowledge.
        
        This is the "I've solved this before" feature.
        """
        
        # Search for similar patterns in user's history
        similar_patterns = await self._find_similar_patterns(
            user_id, problem_description
        )
        
        # Search across all PRSNL content
        prsnl_knowledge = await self._search_prsnl_knowledge(
            user_id, problem_description
        )
        
        # Use unified AI service to create solution
        synthesis_result = await unified_ai_service.generate_synthesis(
            prompt=f"Based on the following patterns and knowledge, synthesize a practical solution for: {problem_description}\n\nSimilar patterns: {json.dumps(similar_patterns[:3])}\n\nRelevant knowledge: {json.dumps(prsnl_knowledge[:5])}",
            context={"file_context": file_context} if file_context else {}
        )
        
        return {
            "solution": synthesis_result.get('solution'),
            "explanation": synthesis_result.get('explanation'),
            "confidence": synthesis_result.get('confidence', 0.0),
            "sources": synthesis_result.get('sources', []),
            "similar_patterns": similar_patterns[:3] if similar_patterns else []
        }
    
    async def process_cli_results(
        self, analysis_id: str, user_id: str, results: Dict[str, Any]
    ):
        """Process results from CLI tool upload"""
        
        # Extract patterns from CLI analysis
        for pattern in results.get('patterns', []):
            await self._store_pattern(user_id, {
                'signature': pattern['signature'],
                'type': pattern['type'],
                'description': pattern.get('description'),
                'code_snippet': pattern.get('code'),
                'language': pattern.get('language')
            })
        
        # Generate insights from CLI findings
        for finding in results.get('findings', []):
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type=finding['type'],
                title=finding['title'],
                description=finding['description'],
                recommendation=finding.get('recommendation', ''),
                severity=finding.get('severity', 'medium'),
                generated_by="cli_tool",
                confidence=finding.get('confidence', 0.7)
            )
    
    # Helper methods
    async def _create_analysis_record(
        self, repo_id: str, job_id: str, analysis_depth: str
    ) -> str:
        """Create initial analysis record"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            analysis_id = await db.fetchval("""
                INSERT INTO codemirror_analyses (
                    repo_id, job_id, analysis_type, analysis_depth
                ) VALUES ($1, $2, $3, $4)
                RETURNING id
            """, UUID(repo_id), job_id, 'web', analysis_depth)
            
            return str(analysis_id)
    
    async def _generate_diverse_insights(self, analysis_id: str, analysis_results: dict, repo_data: dict):
        """Generate diverse, meaningful insights based on comprehensive analysis"""
        
        # Extract enhanced metrics
        security_score = analysis_results.get('security_score', 75)
        performance_score = analysis_results.get('performance_score', 75)
        quality_score = analysis_results.get('quality_score', 75)
        test_coverage = analysis_results.get('test_coverage', 50)
        outdated_deps = analysis_results.get('outdated_dependencies', 0)
        repo_size = analysis_results.get('repository_size', repo_data.get('size', 1000))
        language = analysis_results.get('primary_language', repo_data.get('language', 'unknown'))
        
        # Security Insights (Enhanced)
        if security_score < 70:
            severity = "critical" if security_score < 50 else "high" if security_score < 60 else "medium"
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="security_vulnerability",
                title=f"Security Score: {security_score}/100 - Action Required",
                description=f"Repository '{repo_data['name']}' shows security concerns. Common issues in {language} projects include dependency vulnerabilities, weak authentication patterns, and insufficient input validation.",
                recommendation=f"• Run `npm audit` or `pip-audit` for {language} dependencies • Implement dependency scanning in CI/CD • Review authentication mechanisms • Add input sanitization • Enable security headers",
                severity=severity,
                generated_by="security_analysis_agent",
                confidence=0.92
            )
        
        # Performance Insights (Enhanced)
        if performance_score < 70:
            severity = "high" if performance_score < 50 else "medium"
            perf_issues = []
            if repo_size > 10000: perf_issues.append("large codebase optimization")
            if language in ['python', 'javascript']: perf_issues.append("runtime performance")
            if outdated_deps > 10: perf_issues.append("outdated dependencies impact")
            
            issues_text = ", ".join(perf_issues) if perf_issues else "general performance concerns"
            
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="performance_optimization",
                title=f"Performance Score: {performance_score}/100 - Optimization Needed",
                description=f"Performance analysis of '{repo_data['name']}' identifies {issues_text}. {language.title()} applications benefit from specific optimization strategies.",
                recommendation=f"• Profile {language} application performance • Optimize critical code paths • Implement caching for frequently accessed data • Review async patterns • Consider code splitting for large applications",
                severity=severity,
                generated_by="performance_analysis_agent", 
                confidence=0.87
            )
        
        # Testing & Quality Insights
        if test_coverage < 60:
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="code_quality",
                title=f"Test Coverage: {test_coverage}% - Increase Testing",
                description=f"Test coverage analysis shows '{repo_data['name']}' has insufficient test coverage. Proper testing reduces bugs and improves maintainability.",
                recommendation=f"• Add unit tests for core functions • Implement integration tests • Set up test automation • Aim for 80%+ coverage • Use {language}-specific testing frameworks",
                severity="medium" if test_coverage > 40 else "high",
                generated_by="testing_analysis_agent",
                confidence=0.9
            )
        
        # Dependency Management
        if outdated_deps > 5:
            severity = "critical" if outdated_deps > 15 else "high" if outdated_deps > 10 else "medium"
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="dependency_update",
                title=f"Dependency Health: {outdated_deps} Outdated Packages",
                description=f"Dependency analysis found {outdated_deps} outdated packages in '{repo_data['name']}'. Outdated dependencies pose security risks and limit feature access.",
                recommendation=f"• Update critical security dependencies immediately • Review breaking changes before updating • Set up automated dependency monitoring • Use dependabot or similar tools",
                severity=severity,
                generated_by="dependency_analysis_agent",
                confidence=0.95
            )
        
        # Architecture & Code Quality Insights
        if quality_score < 70:
            arch_issues = []
            if repo_size > 20000: arch_issues.append("complex architecture")
            if language in ['javascript', 'python']: arch_issues.append("dynamic typing challenges")
            
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="code_quality",
                title=f"Code Quality Score: {quality_score}/100 - Refactoring Needed",
                description=f"Code quality analysis of '{repo_data['name']}' shows areas for improvement. Common issues include high complexity, poor separation of concerns, and technical debt.",
                recommendation=f"• Refactor complex functions (>50 lines) • Implement SOLID principles • Add proper error handling • Improve code documentation • Use {language} linting tools",
                severity="high" if quality_score < 55 else "medium",
                generated_by="code_quality_agent",
                confidence=0.88
            )
        
        # Documentation & Learning Opportunities
        doc_score = analysis_results.get('documentation_completeness', 60)
        if doc_score < 70:
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="learning_opportunity",
                title=f"Documentation Score: {doc_score}% - Improve Documentation",
                description=f"Documentation analysis reveals '{repo_data['name']}' needs better developer resources. Good documentation improves team productivity and onboarding.",
                recommendation="• Create comprehensive README with setup instructions • Add inline code documentation • Include API documentation • Add contribution guidelines • Create architecture diagrams",
                severity="low" if doc_score > 50 else "medium",
                generated_by="documentation_analysis_agent",
                confidence=0.85
            )
        
        # Language-Specific Insights
        if language == 'python':
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="learning_opportunity",
                title="Python Best Practices Review",
                description=f"Python-specific analysis of '{repo_data['name']}' suggests improvements in type hints, async patterns, and package structure.",
                recommendation="• Add type hints for better IDE support • Use async/await for I/O operations • Follow PEP 8 style guide • Implement proper logging • Use virtual environments",
                severity="low",
                generated_by="python_specialist_agent",
                confidence=0.8
            )
        elif language in ['javascript', 'typescript']:
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="learning_opportunity",
                title="JavaScript/TypeScript Optimization",
                description=f"JavaScript analysis of '{repo_data['name']}' identifies opportunities for modern JS patterns and performance improvements.",
                recommendation="• Implement proper error boundaries • Use modern ES6+ features • Add TypeScript for type safety • Optimize bundle size • Implement proper state management",
                severity="low",
                generated_by="javascript_specialist_agent",
                confidence=0.8
            )
        
        # Always generate at least one insight for consistency
        if not any([security_score < 70, performance_score < 70, quality_score < 70, test_coverage < 60, outdated_deps > 5, doc_score < 70]):
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="code_quality",
                title="Repository Health Check Complete",
                description=f"Comprehensive analysis of '{repo_data['name']}' shows good overall health. Continue maintaining best practices.",
                recommendation="• Continue regular dependency updates • Maintain test coverage • Monitor security vulnerabilities • Keep documentation current",
                severity="low",
                generated_by="health_check_agent",
                confidence=0.9
            )

    async def _create_insight(self, **kwargs):
        """Create an insight record"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                INSERT INTO codemirror_insights (
                    analysis_id, insight_type, title, description,
                    severity, recommendation, generated_by_agent,
                    confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                UUID(kwargs['analysis_id']),
                kwargs['insight_type'],
                kwargs['title'],
                kwargs['description'],
                kwargs.get('severity'),
                kwargs['recommendation'],
                kwargs['generated_by'],
                kwargs['confidence']
            )
    
    async def _store_pattern(self, user_id: str, pattern: Dict[str, Any]):
        """Store or update a detected pattern"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check if pattern exists
            existing = await db.fetchrow("""
                SELECT id, occurrence_count FROM codemirror_patterns
                WHERE user_id = $1 AND pattern_signature = $2
            """, user_id, pattern['signature'])
            
            if existing:
                # Update existing pattern
                await db.execute("""
                    UPDATE codemirror_patterns
                    SET occurrence_count = occurrence_count + 1,
                        last_seen_at = NOW()
                    WHERE id = $1
                """, existing['id'])
            else:
                # Create new pattern
                await db.execute("""
                    INSERT INTO codemirror_patterns (
                        user_id, pattern_signature, pattern_type,
                        description, code_snippet, language, ai_confidence, detected_by_agent
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    user_id,
                    pattern['signature'],
                    pattern.get('type', 'other'),
                    pattern.get('description', ''),
                    pattern.get('code_snippet', ''),
                    pattern.get('language', 'unknown'),
                    pattern.get('confidence', 0.7),
                    pattern.get('detected_by', 'code_pattern_detection_agent')
                )
    
    async def _send_progress_update(
        self, job_id: str, progress: int, stage: str, message: str
    ):
        """Send progress update via WebSocket and job system"""
        
        # Update job
        await self._update_job_progress(
            job_id=job_id,
            progress=progress,
            stage=stage,
            message=message
        )
        
        # Send WebSocket update (disabled for now)
        # TODO: Fix WebSocket manager to support channel-based broadcasting
        try:
            await websocket_manager.broadcast(json.dumps({
                "type": "analysis_progress",
                "job_id": job_id,
                "progress": progress,
                "stage": stage,
                "message": message
            }))
        except Exception as ws_error:
            logger.warning(f"WebSocket broadcast failed: {ws_error}")
    
    async def _fetch_repo_data(self, repo_id: str) -> Dict[str, Any]:
        """Fetch repository data from database"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            repo = await db.fetchrow("""
                SELECT * FROM github_repos WHERE id = $1
            """, UUID(repo_id))
            
            if not repo:
                raise ValueError(f"Repository {repo_id} not found")
            
            return dict(repo)
    
    def _detect_frameworks(self, structure: List[str]) -> List[str]:
        """Detect frameworks from file structure"""
        frameworks = []
        
        framework_indicators = {
            'react': ['package.json', 'src/App.js', 'src/App.jsx', 'src/App.tsx'],
            'vue': ['vue.config.js', 'src/App.vue'],
            'angular': ['angular.json', 'src/app/app.module.ts'],
            'django': ['manage.py', 'settings.py'],
            'fastapi': ['main.py', 'app/main.py'],
            'express': ['app.js', 'server.js', 'index.js'],
            'nextjs': ['next.config.js', 'pages/_app.js'],
            'svelte': ['svelte.config.js', 'src/App.svelte']
        }
        
        for framework, indicators in framework_indicators.items():
            if any(file in structure for file in indicators):
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_languages(self, structure: List[str]) -> List[str]:
        """Detect programming languages from file extensions"""
        language_extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'csharp': ['.cs']
        }
        
        detected = set()
        for file in structure:
            for lang, exts in language_extensions.items():
                if any(file.endswith(ext) for ext in exts):
                    detected.add(lang)
        
        return list(detected)
    
    async def _finalize_analysis(self, analysis_id: str, job_id: str):
        """Finalize analysis and update completion time"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE codemirror_analyses
                SET analysis_completed_at = NOW(),
                    analysis_duration_ms = EXTRACT(EPOCH FROM (NOW() - analysis_started_at)) * 1000
                WHERE id = $1
            """, UUID(analysis_id))
            
            # Mark job as completed
            job_service = JobPersistenceService(db)
            await job_service.update_job_status(
                job_id=job_id,
                status="completed",
                progress_percentage=100
            )
            await job_service.save_job_result(
                job_id=job_id,
                result_data={"analysis_id": analysis_id}
            )
    
    async def _fetch_package_files(self, repo_full_name: str) -> Dict[str, Any]:
        """Fetch package management files from repository"""
        package_files = {}
        
        # Try to fetch various package files
        package_file_names = [
            'package.json', 'requirements.txt', 'Pipfile', 'poetry.lock',
            'Gemfile', 'go.mod', 'Cargo.toml', 'pom.xml', 'build.gradle'
        ]
        
        try:
            for file_name in package_file_names:
                content = await self.github.fetch_file(repo_full_name, file_name)
                if content:
                    package_files[file_name] = content
        except Exception as e:
            logger.warning(f"Failed to fetch package files from GitHub: {e}")
            # Return empty package files and log the failure
            package_files = {}
            logger.error(f"Package analysis failed for {repo_full_name} - GitHub API unavailable")
        
        return package_files
    
    async def _get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get existing patterns for a user"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    pattern_signature,
                    pattern_type,
                    description,
                    occurrence_count,
                    ai_confidence,
                    last_seen_at
                FROM codemirror_patterns 
                WHERE user_id = $1
                ORDER BY occurrence_count DESC, last_seen_at DESC
                LIMIT 20
            """
            
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]
    
    async def _fetch_code_samples(self, repo_full_name: str) -> List[Dict[str, Any]]:
        """Fetch representative code samples from repository"""
        code_samples = []
        
        try:
            # Get repository structure
            structure = await self.github.fetch_repo_structure(repo_full_name)
            
            # Filter for code files (limit to reasonable amount)
            code_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.cs']
            code_files = [f for f in structure if any(f.endswith(ext) for ext in code_extensions)][:20]
            
            # Fetch sample from each file
            for file_path in code_files:
                content = await self.github.fetch_file(repo_full_name, file_path)
                if content:
                    # Get first 100 lines as sample
                    lines = content.split('\n')[:100]
                    code_samples.append({
                        'file': file_path,
                        'language': self._detect_language_from_file(file_path),
                        'content': '\n'.join(lines)
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch code samples from GitHub: {e}")
            # Return empty code samples and log the failure
            code_samples = []
            logger.error(f"Code analysis failed for {repo_full_name} - GitHub API unavailable")
        
        return code_samples
    
    async def _analyze_full_codebase(self, repo_full_name: str) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis"""
        analysis = {
            'structure': {},
            'patterns': [],
            'improvement_areas': [],
            'architecture': {}
        }
        
        # Get full repository structure
        structure = await self.github.fetch_repo_structure(repo_full_name)
        
        # Analyze directory structure
        analysis['structure'] = self._analyze_directory_structure(structure)
        
        # Detect architectural patterns
        analysis['architecture'] = self._detect_architecture_patterns(structure)
        
        # Identify improvement areas based on structure
        if not any('test' in f.lower() for f in structure):
            analysis['improvement_areas'].append({
                'area': 'testing',
                'description': 'No test files detected',
                'priority': 'high'
            })
        
        if not any(f.endswith('.md') for f in structure):
            analysis['improvement_areas'].append({
                'area': 'documentation',
                'description': 'Limited documentation found',
                'priority': 'medium'
            })
        
        return analysis
    
    async def _find_similar_patterns(self, user_id: str, description: str) -> List[Dict[str, Any]]:
        """Find similar patterns from user's history"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Use text search for similarity
            patterns = await db.fetch("""
                SELECT 
                    pattern_signature,
                    description,
                    code_examples,
                    solution_links,
                    ai_confidence
                FROM codemirror_patterns
                WHERE user_id = $1
                    AND (
                        pattern_signature ILIKE $2
                        OR description ILIKE $2
                    )
                ORDER BY occurrence_count DESC
                LIMIT 10
            """, user_id, f'%{description}%')
            
            return [dict(p) for p in patterns]
    
    async def _search_prsnl_knowledge(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search across all PRSNL content for relevant knowledge"""
        # Use unified AI service for comprehensive search
        search_results = await unified_ai_service.search_with_context(
            user_id=user_id,
            query=query,
            content_types=['code', 'documentation', 'insights'],
            limit=20
        )
        
        return search_results.get('results', [])
    
    async def _update_analysis_metadata(self, analysis_id: str, metadata: Dict[str, Any]):
        """Update analysis metadata"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE codemirror_analyses
                SET results = results || $2,
                    frameworks_detected = $3,
                    languages_detected = $4,
                    file_count = $5
                WHERE id = $1
            """, 
                UUID(analysis_id),
                json.dumps(metadata),
                json.dumps(metadata.get('frameworks_detected', [])),
                json.dumps(metadata.get('languages_detected', [])),
                metadata.get('file_count', 0)
            )
    
    async def _update_analysis_scores(self, analysis_id: str, scores: Dict[str, float]):
        """Update analysis quality scores"""
        pool = await get_db_pool()
        async with pool.acquire() as db:
            await db.execute("""
                UPDATE codemirror_analyses
                SET security_score = $2,
                    performance_score = $3,
                    quality_score = $4
                WHERE id = $1
            """, 
                UUID(analysis_id),
                scores.get('security'),
                scores.get('performance'),
                scores.get('quality')
            )
    
    def _generate_readme_recommendations(self, analysis: Dict[str, Any]) -> str:
        """Generate recommendations for README improvements"""
        recommendations = []
        
        if analysis.get('quality_score', 0) < 0.5:
            recommendations.append("Add more detailed project description")
        
        if 'installation' not in analysis.get('sections', []):
            recommendations.append("Include installation instructions")
        
        if 'usage' not in analysis.get('sections', []):
            recommendations.append("Add usage examples")
        
        if 'contributing' not in analysis.get('sections', []):
            recommendations.append("Include contribution guidelines")
        
        return " • ".join(recommendations) if recommendations else "README is well-structured"
    
    def _calculate_quality_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality scores from analysis data"""
        scores = {
            'security': 70.0,  # Base score
            'performance': 70.0,
            'quality': 70.0
        }
        
        # Adjust based on findings
        if analysis.get('structure', {}).get('has_tests'):
            scores['quality'] += 10
        
        if analysis.get('structure', {}).get('has_docs'):
            scores['quality'] += 10
        
        if 'security' in analysis.get('improvement_areas', []):
            scores['security'] -= 20
        
        # Ensure scores are within bounds
        for key in scores:
            scores[key] = max(0, min(100, scores[key]))
        
        return scores
    
    def _detect_language_from_file(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    def _analyze_directory_structure(self, files: List[str]) -> Dict[str, Any]:
        """Analyze directory structure patterns"""
        structure = {
            'has_tests': any('test' in f.lower() for f in files),
            'has_docs': any(f.endswith('.md') for f in files),
            'has_ci': any('.github/workflows' in f or '.gitlab-ci' in f for f in files),
            'depth': max(f.count('/') for f in files) if files else 0,
            'total_files': len(files)
        }
        
        return structure
    
    def _detect_architecture_patterns(self, files: List[str]) -> Dict[str, Any]:
        """Detect architectural patterns from file structure"""
        patterns = {
            'mvc': False,
            'microservices': False,
            'monorepo': False,
            'serverless': False
        }
        
        # MVC detection
        mvc_dirs = ['models', 'views', 'controllers']
        if all(any(d in f for f in files) for d in mvc_dirs):
            patterns['mvc'] = True
        
        # Microservices detection
        if any('services/' in f or 'microservices/' in f for f in files):
            patterns['microservices'] = True
        
        # Monorepo detection
        if any('packages/' in f or 'apps/' in f for f in files):
            patterns['monorepo'] = True
        
        # Serverless detection
        if any('serverless.yml' in f or 'handler.' in f for f in files):
            patterns['serverless'] = True
        
        return patterns

    async def _process_with_langgraph_workflow(
        self,
        repo_data: Dict[str, Any],
        analysis_phase: str,
        job_id: str
    ) -> Dict[str, Any]:
        """Process repository content using LangGraph workflow"""
        if not self.use_langgraph or not langgraph_workflow_service.enabled:
            logger.debug("LangGraph workflow not available, using fallback")
            return await self._fallback_analysis(repo_data, analysis_phase)
        
        try:
            # Convert repo data to content string for workflow
            content = json.dumps(repo_data, indent=2)
            
            # Update job progress
            await self._update_job_progress(
                job_id,
                progress=20,
                stage=f"langgraph_{analysis_phase}",
                message=f"Processing {analysis_phase} analysis with LangGraph workflow"
            )
            
            # Process through LangGraph workflow
            result = await langgraph_workflow_service.process_content(
                content=content,
                content_type=ContentType.CODE,
                metadata={
                    "source": "codemirror_repository",
                    "analysis_phase": analysis_phase,
                    "repository_id": repo_data.get("id"),
                    "repository_name": repo_data.get("name"),
                    "language": repo_data.get("language"),
                    "job_id": job_id
                }
            )
            
            logger.info(f"LangGraph workflow completed for {analysis_phase} analysis")
            return result
            
        except Exception as e:
            logger.error(f"LangGraph workflow failed for {analysis_phase}: {e}")
            # Fallback to standard analysis
            return await self._fallback_analysis(repo_data, analysis_phase)
    
    async def _route_analysis_task(
        self,
        content: str,
        task_type: str,
        complexity_level: int = 5,
        job_id: str = None
    ) -> Dict[str, Any]:
        """Route analysis task through enhanced AI router"""
        if not self.use_enhanced_routing:
            logger.debug("Enhanced routing disabled, using direct AI service")
            return await unified_ai_service.analyze_content(content)
        
        try:
            # Create AI task for routing
            task = AITask(
                type=TaskType.TEXT_GENERATION,
                content=content,
                priority=complexity_level,
                options={
                    "analysis_type": "code_intelligence",
                    "task_subtype": task_type,
                    "codemirror_analysis": True,
                    "job_id": job_id
                }
            )
            
            # Route through enhanced AI router
            result = await ai_router.execute_with_fallback(
                task, 
                self._execute_direct_analysis
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced routing failed for {task_type}: {e}")
            # Fallback to direct analysis
            return await self._execute_direct_analysis(content)
    
    async def _execute_direct_analysis(self, content: str, task: Optional[AITask] = None) -> Dict[str, Any]:
        """Execute direct analysis without routing"""
        # Handle both direct calls and fallback calls from router
        if isinstance(content, AITask):
            # Called as fallback from router
            actual_content = content.content
        else:
            # Direct call
            actual_content = content
        return await unified_ai_service.analyze_content(actual_content)
    
    async def _fallback_analysis(
        self,
        repo_data: Dict[str, Any],
        analysis_phase: str
    ) -> Dict[str, Any]:
        """Fallback analysis when LangGraph is not available"""
        content = json.dumps(repo_data, indent=2)
        return await unified_ai_service.analyze_content(content)
    
    async def _generate_code_insights_with_templates(
        self,
        code_content: str,
        analysis_type: str = "pattern_detection",
        language: str = "auto-detect"
    ) -> str:
        """Generate code insights using centralized prompt templates"""
        if not self.use_prompt_templates or not prompt_template_manager.enabled:
            logger.debug("Prompt templates not available, using fallback")
            return await unified_ai_service.analyze_content(code_content)
        
        try:
            # Use centralized prompt templates
            prompt = prompt_template_manager.get_prompt(
                'code_analysis',
                variables={
                    'code': code_content,
                    'analysis_type': analysis_type,
                    'language': language
                }
            )
            
            # Route through enhanced AI router if available
            if self.use_enhanced_routing:
                return await self._route_analysis_task(
                    prompt,
                    f"code_analysis_{analysis_type}",
                    complexity_level=7
                )
            else:
                return await unified_ai_service.analyze_content(prompt)
                
        except Exception as e:
            logger.error(f"Template-based analysis failed: {e}")
            # Fallback to direct analysis
            return await unified_ai_service.analyze_content(code_content)
    
    async def _enhanced_repository_analysis(
        self,
        repo_data: Dict[str, Any],
        analysis_depth: str,
        job_id: str
    ) -> Dict[str, Any]:
        """Enhanced repository analysis with all new features"""
        
        # Step 1: Use LangGraph workflow for comprehensive analysis
        workflow_result = await self._process_with_langgraph_workflow(
            repo_data, analysis_depth, job_id
        )
        
        # Step 2: Generate code insights with templates
        code_content = repo_data.get("content", "")
        insights = await self._generate_code_insights_with_templates(
            code_content,
            analysis_type="comprehensive_analysis",
            language=repo_data.get("language", "auto-detect")
        )
        
        # Step 3: Combine results
        enhanced_result = {
            "workflow_analysis": workflow_result,
            "template_insights": insights,
            "analysis_metadata": {
                "used_langgraph": self.use_langgraph,
                "used_enhanced_routing": self.use_enhanced_routing,
                "used_prompt_templates": self.use_prompt_templates,
                "analysis_depth": analysis_depth,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return enhanced_result


# Create singleton instance
codemirror_service = CodeMirrorService()