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
from app.db.database import get_db_connection
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import JobPersistenceService
from app.services.embedding_manager import embedding_manager
from app.services.codemirror_agents import (
    code_repository_analysis_agent,
    code_pattern_detection_agent,
    code_insight_generator_agent
)
from app.services.github_service import GitHubService
from app.services.websocket_manager import websocket_manager

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
        
        try:
            # Create analysis record
            analysis_id = await self._create_analysis_record(
                repo_id, job_id, analysis_depth
            )
            
            # Update job status
            await job_persistence_service.update_job(
                job_id=job_id,
                status="processing",
                progress=0,
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
            logger.error(f"CodeMirror analysis failed: {str(e)}")
            await job_persistence_service.update_job(
                job_id=job_id,
                status="failed",
                error=str(e)
            )
            raise
    
    async def _update_job_progress(self, job_id: str, progress: int, stage: str, message: str):
        """Helper to update job progress with database connection"""
        async with await get_db_connection() as conn:
            job_service = JobPersistenceService(conn)
            await job_service.update_job(
                job_id=job_id,
                progress=progress,
                stage=stage,
                message=message
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
        readme_content = await self.github.fetch_file(
            repo_data['full_name'], 'README.md'
        )
        
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
            
            # Generate README quality insight
            analysis_results = readme_analysis.results
            await self._create_insight(
                analysis_id=analysis_id,
                insight_type="code_quality",
                title="README Documentation Quality",
                description=analysis_results.get('summary', 'Analysis completed'),
                recommendation=self._generate_readme_recommendations(analysis_results),
                severity="medium" if analysis_results.get('quality_score', 75) < 70 else "low",
                generated_by="code_repository_analysis_agent",
                confidence=analysis_results.get('confidence_score', 0.8)
            )
        
        # Quick structure scan
        structure = await self.github.fetch_repo_structure(repo_data['full_name'])
        
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
        
        await job_persistence_service.update_job(
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
                results.get('security_score'), 
                results.get('performance_score'), 
                results.get('quality_score')
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
                await self._store_pattern(user_id, pattern)
        
        await self._send_progress_update(job_id, 70, "standard_complete",
                                       "Pattern analysis complete")
    
    async def _deep_analysis_phase(
        self, repo_id: str, job_id: str, analysis_id: str, user_id: str
    ):
        """Deep analysis phase - architecture and learning paths"""
        
        await job_persistence_service.update_job(
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
                results.get('security_score'),
                results.get('performance_score'), 
                results.get('quality_score')
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
        
        # Use Research Synthesizer to create solution
        synthesis_result = await self.synthesizer.synthesize_sources(
            sources=[
                {"type": "patterns", "content": similar_patterns},
                {"type": "prsnl_items", "content": prsnl_knowledge},
                {"type": "current_problem", "content": problem_description}
            ],
            focus="practical_solution"
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
        async with get_db_connection() as db:
            analysis_id = await db.fetchval("""
                INSERT INTO codemirror_analyses (
                    repo_id, job_id, analysis_type, analysis_depth
                ) VALUES ($1, $2, $3, $4)
                RETURNING id
            """, UUID(repo_id), job_id, 'web', analysis_depth)
            
            return str(analysis_id)
    
    async def _create_insight(self, **kwargs):
        """Create an insight record"""
        async with get_db_connection() as db:
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
        async with get_db_connection() as db:
            # Check if pattern exists
            existing = await db.fetchrow("""
                SELECT id, occurrence_count FROM codemirror_patterns
                WHERE user_id = $1 AND pattern_signature = $2
            """, UUID(user_id), pattern['signature'])
            
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
                        description, code_snippet, language,
                        ai_confidence, detected_by_agent
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    UUID(user_id),
                    pattern['signature'],
                    pattern.get('type', 'other'),
                    pattern.get('description'),
                    pattern.get('code_snippet'),
                    pattern.get('language'),
                    pattern.get('confidence', 0.7),
                    pattern.get('detected_by', 'content_explorer')
                )
    
    async def _send_progress_update(
        self, job_id: str, progress: int, stage: str, message: str
    ):
        """Send progress update via WebSocket and job system"""
        
        # Update job
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=progress,
            stage=stage,
            message=message
        )
        
        # Send WebSocket update
        channel = f"codemirror.{job_id}"
        await websocket_manager.broadcast_to_channel(channel, {
            "type": "analysis_progress",
            "job_id": job_id,
            "progress": progress,
            "stage": stage,
            "message": message
        })
    
    async def _fetch_repo_data(self, repo_id: str) -> Dict[str, Any]:
        """Fetch repository data from database"""
        async with get_db_connection() as db:
            repo = await db.fetchrow("""
                SELECT * FROM github_repos WHERE id = $1
            """, UUID(repo_id))
            
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
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE codemirror_analyses
                SET analysis_completed_at = NOW(),
                    analysis_duration_ms = EXTRACT(EPOCH FROM (NOW() - analysis_started_at)) * 1000
                WHERE id = $1
            """, UUID(analysis_id))
            
            # Mark job as completed
            await job_persistence_service.update_job(
                job_id=job_id,
                status="completed",
                progress=100,
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
        
        for file_name in package_file_names:
            content = await self.github.fetch_file(repo_full_name, file_name)
            if content:
                package_files[file_name] = content
        
        return package_files
    
    async def _get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get existing patterns for a user"""
        async with await get_db_connection() as conn:
            query = """
                SELECT 
                    pattern_signature,
                    pattern_type,
                    description,
                    occurrence_count,
                    confidence,
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
        async with get_db_connection() as db:
            # Use text search for similarity
            patterns = await db.fetch("""
                SELECT 
                    pattern_signature,
                    description,
                    code_snippet,
                    solutions,
                    ai_confidence
                FROM codemirror_patterns
                WHERE user_id = $1
                    AND (
                        pattern_signature ILIKE $2
                        OR description ILIKE $2
                    )
                ORDER BY occurrence_count DESC
                LIMIT 10
            """, UUID(user_id), f'%{description}%')
            
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
        async with get_db_connection() as db:
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
                metadata.get('frameworks_detected', []),
                metadata.get('languages_detected', []),
                metadata.get('file_count', 0)
            )
    
    async def _update_analysis_scores(self, analysis_id: str, scores: Dict[str, float]):
        """Update analysis quality scores"""
        async with get_db_connection() as db:
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


# Create singleton instance
codemirror_service = CodeMirrorService()