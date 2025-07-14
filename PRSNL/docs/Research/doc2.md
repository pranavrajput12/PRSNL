CodeCortex AI Workflow & Prompts Guide - PRSNL v3.0
🧠 AI Processing Architecture
Overview
CodeCortex leverages PRSNL's Phase 3 multi-agent AI infrastructure to analyze code repositories and generate actionable insights. This document defines all prompts, workflows, and data formats integrated with PRSNL's existing AI agents.
📊 Core AI Workflow with PRSNL Agents
mermaid
graph TD
    A[Repository Fetch] --> B{Content Router}
    B -->|README| C[Knowledge Curator Agent]
    B -->|Dependencies| D[Research Synthesizer Agent]
    B -->|Source Code| E[Content Explorer Agent]
    B -->|Learning| F[Learning Pathfinder Agent]
    
    C --> G[Unified AI Service]
    D --> G
    E --> G
    F --> G
    
    G --> H[Job Persistence System]
    H --> I[Progress Updates via WebSocket]
    H --> J[Store in PostgreSQL]
    
    J --> K[Insights Available]
🎯 Integration with PRSNL's AI Infrastructure
Leveraging Existing Services
python
# backend/app/services/codecortex_ai_orchestrator.py
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import job_persistence_service
from app.services.ai_agents import (
    KnowledgeCuratorAgent,
    ResearchSynthesizerAgent,
    ContentExplorerAgent,
    LearningPathfinderAgent
)

class CodeCortexAIOrchestrator:
    """
    Orchestrates code analysis using PRSNL's multi-agent system
    """
    
    def __init__(self):
        self.unified_ai = unified_ai_service
        self.job_service = job_persistence_service
        
        # PRSNL's existing AI agents
        self.curator = KnowledgeCuratorAgent()
        self.synthesizer = ResearchSynthesizerAgent()
        self.explorer = ContentExplorerAgent()
        self.pathfinder = LearningPathfinderAgent()
    
    async def analyze_repository_progressive(
        self, 
        repo_id: str, 
        job_id: str,
        user_id: str
    ):
        """Progressive analysis using PRSNL's job system"""
        
        # Update job status
        await self.job_service.update_job(
            job_id=job_id,
            status="processing",
            progress=0,
            stage="initialization",
            message="Starting CodeCortex analysis"
        )
        
        # Phase 1: Quick Analysis (0-30%)
        await self._quick_analysis_phase(repo_id, job_id)
        
        # Phase 2: Deep Analysis (30-70%)
        await self._deep_analysis_phase(repo_id, job_id)
        
        # Phase 3: Learning Paths (70-100%)
        await self._learning_path_phase(repo_id, job_id)
📝 Adapted Prompts for PRSNL's AI Agents
1. Knowledge Curator Agent - README Analysis
python
# Adapted for PRSNL's Knowledge Curator Agent
README_ANALYSIS_REQUEST = {
    "agent": "knowledge_curator",
    "task": "analyze_content",
    "context": {
        "content_type": "documentation",
        "source": "github_readme",
        "analysis_depth": "comprehensive"
    },
    "content": "{readme_content}",
    "metadata": {
        "language": "{language}",
        "stars": "{stars}",
        "last_updated": "{last_updated}"
    },
    "requirements": {
        "categorization": True,
        "quality_assessment": True,
        "improvement_suggestions": True,
        "tag_generation": True
    }
}

# The Knowledge Curator Agent will return structured analysis
# compatible with PRSNL's existing schema
2. Research Synthesizer Agent - Dependency Analysis
python
# Utilizing Research Synthesizer for dependency insights
DEPENDENCY_SYNTHESIS_REQUEST = {
    "agent": "research_synthesizer",
    "task": "synthesize_sources",
    "sources": [
        {
            "type": "package_manifest",
            "content": "{package_json_content}",
            "context": "dependencies"
        }
    ],
    "synthesis_focus": [
        "security_vulnerabilities",
        "outdated_packages",
        "optimization_opportunities",
        "pattern_analysis"
    ],
    "output_format": "actionable_insights"
}
3. Content Explorer Agent - Code Relationships
python
# Content Explorer for discovering code patterns
CODE_EXPLORATION_REQUEST = {
    "agent": "content_explorer",
    "task": "explore_connections",
    "content": "{code_files}",
    "exploration_params": {
        "depth": 3,
        "focus_areas": [
            "architectural_patterns",
            "code_relationships",
            "shared_concerns",
            "refactoring_opportunities"
        ],
        "existing_knowledge": "{repo_context}"
    }
}
4. Learning Pathfinder Agent - Personalized Learning
python
# Learning Pathfinder for code-based learning paths
LEARNING_PATH_REQUEST = {
    "agent": "learning_pathfinder",
    "task": "create_learning_path",
    "user_profile": {
        "current_skills": "{detected_patterns}",
        "code_samples": "{user_code_examples}",
        "identified_gaps": "{growth_areas}"
    },
    "learning_preferences": {
        "time_commitment": "30_minutes_daily",
        "learning_style": "hands_on_practice",
        "use_own_code": True
    }
}
🔄 Progressive Analysis with Job Persistence
Integration with PRSNL's Job System
python
class CodeCortexProgressiveAnalyzer:
    """Uses PRSNL's job persistence for tracking"""
    
    async def _quick_analysis_phase(self, repo_id: str, job_id: str):
        """Phase 1: Immediate insights using Knowledge Curator"""
        
        # Update job progress
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=5,
            stage="quick_analysis",
            message="Analyzing documentation and structure"
        )
        
        # Fetch and analyze README
        readme_content = await self._fetch_readme(repo_id)
        
        if readme_content:
            # Use unified AI service with Knowledge Curator
            analysis = await unified_ai_service.analyze_content(
                content=readme_content,
                enable_key_points=True,
                enable_entities=True,
                content_type="documentation"
            )
            
            # Store insight with job reference
            await self._store_insight(
                repo_id=repo_id,
                job_id=job_id,
                type="readme_quality",
                title="Documentation Analysis",
                detail=analysis,
                ai_agent="knowledge_curator",
                severity=self._calculate_severity(analysis)
            )
        
        # Update progress
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=30,
            stage="quick_complete",
            message="Quick analysis complete"
        )
WebSocket Progress Updates
python
# Integration with PRSNL's WebSocket infrastructure
async def send_progress_update(job_id: str, progress_data: dict):
    """Send real-time updates via PRSNL's WebSocket"""
    
    message = {
        "type": "job_progress",
        "job_id": job_id,
        "job_type": "crawl_ai",
        "progress": progress_data["progress_percentage"],
        "stage": progress_data["current_stage"],
        "message": progress_data["stage_message"],
        "insights_found": progress_data.get("insights_count", 0)
    }
    
    # Use PRSNL's existing WebSocket manager
    await websocket_manager.broadcast(message)
🎛️ Configuration for Azure OpenAI
Model Configuration (Using PRSNL's Setup)
python
CODECORTEX_AI_CONFIG = {
    # Leverage PRSNL's dual-model strategy
    "models": {
        "complex_analysis": "prsnl-gpt-4",      # For deep code analysis
        "quick_insights": "gpt-4.1-mini",       # For fast responses
    },
    
    # Agent-specific settings
    "agent_settings": {
        "knowledge_curator": {
            "model": "prsnl-gpt-4",
            "temperature": 0.3,
            "max_tokens": 2000
        },
        "research_synthesizer": {
            "model": "prsnl-gpt-4",
            "temperature": 0.5,
            "max_tokens": 2500
        },
        "content_explorer": {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "max_tokens": 1500
        },
        "learning_pathfinder": {
            "model": "prsnl-gpt-4",
            "temperature": 0.8,
            "max_tokens": 3000
        }
    },
    
    # Use PRSNL's rate limits
    "rate_limits": {
        "max_concurrent": 5,
        "tokens_per_minute": 150000,
        "requests_per_minute": 60
    }
}
📊 Database Integration
Storing Insights in PRSNL's Schema
python
async def store_codecortex_insight(
    repo_id: str,
    job_id: str,
    insight_data: dict
) -> str:
    """Store insight using PRSNL's database schema"""
    
    # Create insight record
    insight = {
        "id": str(uuid.uuid4()),
        "repo_id": repo_id,
        "job_id": job_id,
        "type": insight_data["type"],
        "title": insight_data["title"],
        "summary": insight_data["summary"],
        "detail": json.dumps(insight_data["detail"]),
        "severity": insight_data.get("severity", "info"),
        "status": "open",
        "ai_agent": insight_data["ai_agent"],
        "created_at": datetime.utcnow()
    }
    
    # Use PRSNL's database connection
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO code_insights 
            (id, repo_id, job_id, type, title, summary, detail, 
             severity, status, ai_agent, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            *insight.values()
        )
    
    return insight["id"]
🔄 Smart Sampling with Embeddings
Leveraging PRSNL's Embedding Infrastructure
python
class CodeCortexEmbeddingService:
    """Uses PRSNL's embedding service for code similarity"""
    
    async def create_code_embeddings(self, code_files: List[dict]):
        """Generate embeddings for code files"""
        
        embeddings = []
        for file in code_files:
            # Prepare content for embedding
            content = f"{file['path']}\n{file['content']}"
            
            # Use PRSNL's embedding service
            embedding_result = await embedding_manager.create_embedding(
                item_id=file['item_id'],
                content=content,
                update_item=True
            )
            
            embeddings.append({
                "file_path": file['path'],
                "embedding_id": embedding_result['id'],
                "vector": embedding_result['vector']
            })
        
        return embeddings
    
    async def find_similar_code(self, query_code: str, limit: int = 10):
        """Find similar code patterns using vector search"""
        
        # Generate query embedding
        query_vector = await embedding_manager.generate_embedding(query_code)
        
        # Search using pgvector
        similar = await embedding_manager.search_similar(
            query_embedding=query_vector,
            limit=limit,
            threshold=0.7,
            filter_type="development"
        )
        
        return similar
🎯 Git History Analysis with PRSNL
Integrated Git Analysis
python
class GitHistoryAnalyzer:
    """Git analysis integrated with PRSNL's AI agents"""
    
    async def analyze_git_history(self, repo_id: str, job_id: str):
        """Analyze git history using PRSNL's infrastructure"""
        
        # Extract git history
        commits = await self.extract_commit_history(repo_id)
        
        # Use Research Synthesizer for pattern analysis
        git_insights = await self.synthesizer.synthesize_sources(
            sources=[{
                "type": "git_history",
                "commits": commits,
                "focus": "problem_solution_patterns"
            }],
            identify_patterns=True,
            generate_insights=True
        )
        
        # Store insights
        for insight in git_insights:
            await store_codecortex_insight(
                repo_id=repo_id,
                job_id=job_id,
                insight_data={
                    "type": "git_pattern",
                    "title": insight["title"],
                    "summary": insight["summary"],
                    "detail": insight,
                    "ai_agent": "research_synthesizer"
                }
            )
📱 Frontend Integration Patterns
Using TanStack Query v5
typescript
// frontend/src/lib/api/codecortex.ts
import { createQuery } from '@tanstack/svelte-query';
import { api } from '$lib/api';

export const useCodeAnalysis = (repoId: string) => {
    return createQuery({
        queryKey: ['codecortex', 'analysis', repoId],
        queryFn: async () => {
            const response = await api.get(`/api/codecortex/insights`, {
                params: { repo_id: repoId }
            });
            return response.data;
        },
        gcTime: 5 * 60 * 1000, // 5 minutes (was cacheTime)
        staleTime: 30 * 1000, // 30 seconds
        refetchOnWindowFocus: true
    });
};

export const useAnalysisProgress = (jobId: string) => {
    return createQuery({
        queryKey: ['persistence', 'job', jobId],
        queryFn: async () => {
            const response = await api.get(`/api/persistence/status/${jobId}`);
            return response.data;
        },
        refetchInterval: (data) => {
            // Poll while processing
            return data?.status === 'processing' ? 1000 : false;
        }
    });
};
🚀 Implementation Checklist
Phase 1: Core Integration
Set up database tables for CodeCortex
Integrate with PRSNL's AI agents
Connect to job persistence system
Implement progress tracking
Phase 2: Analysis Pipeline
Quick analysis with Knowledge Curator
Deep analysis with Research Synthesizer
Pattern discovery with Content Explorer
Learning paths with Learning Pathfinder
Phase 3: Frontend UI
Repository management interface
Progress tracking components
Insights dashboard
Learning path viewer
Phase 4: Optimization
Smart code sampling
Embedding-based similarity
Git history analysis
Cache optimization with DragonflyDB
🔑 Key Integration Points
AI Service: All AI calls go through unified_ai_service
Jobs: All long-running tasks use job_persistence_service
Storage: PostgreSQL with pgvector on port 5433
Cache: DragonflyDB for performance
WebSocket: Real-time updates via existing infrastructure
Frontend: Svelte 5 with runes and TanStack Query v5
This implementation fully leverages PRSNL's Phase 3 AI infrastructure while adding CodeCortex-specific functionality for code analysis and learning path generation.

