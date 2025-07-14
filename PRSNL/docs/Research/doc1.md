CodeCortex Feature Implementation Guide for PRSNL v3.0
🎯 Executive Summary
CodeCortex is an AI-powered system that integrates with PRSNL's Phase 3 AI Second Brain architecture to analyze developer code and provide personalized insights. It leverages PRSNL's existing multi-agent AI infrastructure and unified job persistence system.
🏗️ Architecture Overview
Integration with PRSNL Phase 3 Architecture
┌─────────────────────────────────────────────────────────┐
│                    PRSNL Frontend (Port 3004)            │
│  • Neural Nest Integration  • Code Cortex Hub           │
│  • Progress Tracking        • Real-time Updates         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (Port 8000)             │
│  • /api/codecortex/*        • WebSocket Support         │
│  • Job Persistence API      • Azure OpenAI Integration  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              PRSNL AI Agent Infrastructure               │
├─────────────────┬──────────────┬───────────────────────┤
│ Knowledge       │ Research     │  Content Explorer &    │
│ Curator Agent   │ Synthesizer  │  Learning Pathfinder   │
│ (Code Analysis) │ (Insights)   │  (Learning Paths)      │
└─────────────────┴──────────────┴───────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Unified Job Persistence System              │
│  • processing_jobs table    • /api/persistence/*        │
│  • Job lifecycle tracking   • Progress monitoring       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│         PostgreSQL 16 (Port 5433) + DragonflyDB         │
│  • github_repos table       • codecortex_items         │
│  • insights table           • embeddings (pgvector)    │
└─────────────────────────────────────────────────────────┘
🚀 Implementation Phases
Phase 1: Core Integration (Days 1-2)
Database Schema Updates
sql
-- Add to existing PRSNL database at port 5433
-- GitHub Integration Tables
CREATE TABLE github_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    github_username TEXT,
    access_token_enc BYTEA,  -- Encrypted
    etag_cache JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE github_repos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES github_accounts(id),
    full_name TEXT NOT NULL,  -- "owner/repo"
    item_type TEXT DEFAULT 'development',
    selected BOOLEAN DEFAULT FALSE,
    default_branch TEXT,
    last_synced_sha TEXT,
    last_fetched_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extend existing items table for code content
CREATE TABLE codecortex_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    repo_id UUID REFERENCES github_repos(id),
    file_path TEXT,
    language TEXT,
    framework TEXT,
    code_type TEXT,
    complexity_score FLOAT,
    documentation_score FLOAT,
    commit_sha TEXT,
    line_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code insights integrated with job system
CREATE TABLE code_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id),
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    detail JSONB,
    severity TEXT DEFAULT 'info',
    status TEXT DEFAULT 'open',
    ai_agent TEXT,  -- Which PRSNL agent generated this
    created_at TIMESTAMPTZ DEFAULT NOW()
);
Phase 2: API Integration (Days 3-4)
FastAPI Endpoints
python
# backend/app/api/codecortex.py
from fastapi import APIRouter, BackgroundTasks, Depends
from app.core.auth import get_current_user
from app.services.codecortex_service import CodeCortexService
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import job_persistence_service

router = APIRouter(prefix="/api/codecortex", tags=["codecortex"])

@router.post("/analyze/{repo_id}")
async def analyze_repository(
    repo_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Start progressive repository analysis using PRSNL job system"""
    
    # Create job in persistence system
    job_id = f"codecortex_{repo_id}_{datetime.now().timestamp()}"
    
    await job_persistence_service.create_job(
        job_id=job_id,
        job_type="crawl_ai",  # Using existing job type
        input_data={
            "repo_id": repo_id,
            "user_id": current_user.id,
            "analysis_type": "progressive"
        },
        tags=["codecortex", "repository_analysis"]
    )
    
    # Queue background task
    background_tasks.add_task(
        analyze_repo_progressive,
        repo_id,
        job_id,
        current_user.id
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Analysis started",
        "monitor_url": f"/api/persistence/status/{job_id}"
    }

@router.get("/repos")
async def get_repositories(
    current_user = Depends(get_current_user)
):
    """Get user's connected repositories"""
    return await CodeCortexService().get_user_repos(current_user.id)

@router.ws("/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket for real-time analysis progress"""
    await websocket.accept()
    # Integrate with PRSNL's existing WebSocket infrastructure
Phase 3: AI Agent Integration (Days 5-6)
Leveraging PRSNL's AI Agents
python
# backend/app/services/codecortex_ai_service.py
from app.services.ai_agents import (
    KnowledgeCuratorAgent,
    ResearchSynthesizerAgent,
    ContentExplorerAgent,
    LearningPathfinderAgent
)

class CodeCortexAIService:
    """Orchestrates PRSNL AI agents for code analysis"""
    
    def __init__(self):
        self.curator = KnowledgeCuratorAgent()
        self.synthesizer = ResearchSynthesizerAgent()
        self.explorer = ContentExplorerAgent()
        self.pathfinder = LearningPathfinderAgent()
    
    async def analyze_code_with_agents(self, code_content: str, context: dict):
        """Use multi-agent system for comprehensive analysis"""
        
        # Phase 1: Knowledge Curator analyzes structure
        structure_analysis = await self.curator.analyze_content(
            content=code_content,
            context={
                "type": "source_code",
                "language": context.get("language"),
                "file_path": context.get("file_path")
            }
        )
        
        # Phase 2: Research Synthesizer finds patterns
        patterns = await self.synthesizer.synthesize_sources(
            sources=[code_content],
            focus="code_patterns_and_issues"
        )
        
        # Phase 3: Content Explorer finds relationships
        relationships = await self.explorer.explore_connections(
            content=code_content,
            existing_knowledge=context.get("repo_context", {})
        )
        
        # Phase 4: Learning Pathfinder creates improvement plan
        learning_path = await self.pathfinder.create_learning_path(
            current_state=structure_analysis,
            target_improvements=patterns.get("suggested_improvements", [])
        )
        
        return {
            "structure": structure_analysis,
            "patterns": patterns,
            "relationships": relationships,
            "learning_path": learning_path,
            "processing_time": context.get("processing_time")
        }
Phase 4: Frontend Integration (Days 7-8)
SvelteKit Components (Svelte 5 with Runes)
svelte
<!-- frontend/src/routes/code-cortex/repos/+page.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { jobPersistenceStore } from '$lib/stores/jobPersistence';
    import RepoCard from '$lib/components/codecortex/RepoCard.svelte';
    import AnalysisProgress from '$lib/components/codecortex/AnalysisProgress.svelte';
    
    // Svelte 5 runes for local state
    let repos = $state([]);
    let activeJobs = $state(new Map());
    let loading = $state(true);
    
    onMount(async () => {
        await loadRepos();
        // Subscribe to job updates
        jobPersistenceStore.subscribeToJobType('crawl_ai');
    });
    
    async function loadRepos() {
        try {
            const response = await api.get('/api/codecortex/repos');
            repos = response.data;
        } finally {
            loading = false;
        }
    }
    
    async function analyzeRepo(repoId: string) {
        const response = await api.post(`/api/codecortex/analyze/${repoId}`);
        activeJobs.set(repoId, response.job_id);
        
        // Monitor job progress
        jobPersistenceStore.monitorJob(response.job_id);
    }
    
    // Reactive job status
    $effect(() => {
        activeJobs.forEach((jobId, repoId) => {
            const status = $jobPersistenceStore.jobs.get(jobId);
            if (status?.status === 'completed') {
                // Refresh repo insights
                loadRepoInsights(repoId);
            }
        });
    });
</script>

<div class="codecortex-repos">
    <header class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Code Repositories</h1>
        <a href="/code-cortex" class="btn-secondary">
            ← Back to Code Cortex
        </a>
    </header>
    
    {#if loading}
        <div class="loading-spinner">Loading repositories...</div>
    {:else if repos.length === 0}
        <div class="empty-state">
            <p>No repositories connected yet.</p>
            <button class="btn-primary" on:click={connectGitHub}>
                Connect GitHub
            </button>
        </div>
    {:else}
        <div class="repo-grid">
            {#each repos as repo (repo.id)}
                {@const jobId = activeJobs.get(repo.id)}
                {@const jobStatus = jobId ? $jobPersistenceStore.jobs.get(jobId) : null}
                
                <RepoCard 
                    {repo} 
                    isAnalyzing={jobStatus?.status === 'processing'}
                    on:analyze={() => analyzeRepo(repo.id)}
                />
                
                {#if jobStatus?.status === 'processing'}
                    <AnalysisProgress 
                        job={jobStatus}
                        compact={true}
                    />
                {/if}
            {/each}
        </div>
    {/if}
</div>

<style>
    .codecortex-repos {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .repo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
    }
    
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: var(--surface-2);
        border-radius: 8px;
    }
</style>
Progress Monitoring Component
svelte
<!-- frontend/src/lib/components/codecortex/AnalysisProgress.svelte -->
<script lang="ts">
    import type { ProcessingJob } from '$lib/types';
    
    interface Props {
        job: ProcessingJob;
        compact?: boolean;
    }
    
    let { job, compact = false }: Props = $props();
    
    // Calculate phase from progress
    let currentPhase = $derived(() => {
        if (job.progress_percentage < 30) return 'quick';
        if (job.progress_percentage < 60) return 'medium';
        return 'deep';
    });
</script>

<div class="analysis-progress" class:compact>
    <div class="progress-header">
        <span class="status-icon">
            {#if job.status === 'processing'}
                <span class="spinner">⟳</span>
            {:else if job.status === 'completed'}
                ✅
            {:else if job.status === 'failed'}
                ❌
            {/if}
        </span>
        
        <span class="phase-label">
            {#if currentPhase === 'quick'}
                Quick Analysis
            {:else if currentPhase === 'medium'}
                Detailed Scan
            {:else}
                Deep Analysis
            {/if}
        </span>
        
        <span class="percentage">{job.progress_percentage}%</span>
    </div>
    
    <div class="progress-bar">
        <div 
            class="progress-fill"
            style="width: {job.progress_percentage}%"
        ></div>
    </div>
    
    {#if job.current_stage && !compact}
        <p class="stage-message">{job.stage_message}</p>
    {/if}
</div>

<style>
    .analysis-progress {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
    }
    
    .analysis-progress.compact {
        padding: 0.75rem;
        font-size: 0.9em;
    }
    
    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .spinner {
        display: inline-block;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .progress-bar {
        height: 6px;
        background: var(--surface-3);
        border-radius: 3px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: var(--primary);
        transition: width 0.3s ease;
    }
    
    .stage-message {
        margin-top: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.9em;
    }
</style>
Phase 5: Service Implementation (Days 9-10)
Progressive Analysis Service
python
# backend/app/services/codecortex_service.py
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import job_persistence_service
from app.core.config import settings
import asyncio

class CodeCortexService:
    """Main service orchestrating CodeCortex functionality with PRSNL integration"""
    
    async def analyze_repo_progressive(self, repo_id: str, job_id: str, user_id: str):
        """Progressive analysis using PRSNL's job system"""
        
        try:
            # Update job status
            await job_persistence_service.update_job(
                job_id=job_id,
                status="processing",
                progress=0,
                stage="initialization",
                message="Starting repository analysis"
            )
            
            # Phase 1: Quick Analysis (0-30%)
            await self._quick_analysis_phase(repo_id, job_id)
            
            # Phase 2: Medium Analysis (30-60%)
            await self._medium_analysis_phase(repo_id, job_id)
            
            # Phase 3: Deep Analysis (60-100%)
            await self._deep_analysis_phase(repo_id, job_id)
            
            # Mark complete
            await job_persistence_service.update_job(
                job_id=job_id,
                status="completed",
                progress=100,
                stage="completed",
                message="Analysis complete"
            )
            
        except Exception as e:
            await job_persistence_service.update_job(
                job_id=job_id,
                status="failed",
                error=str(e)
            )
            raise
    
    async def _quick_analysis_phase(self, repo_id: str, job_id: str):
        """Quick insights - README, basic structure"""
        
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=5,
            stage="quick_analysis",
            message="Analyzing README and structure"
        )
        
        # Fetch README
        readme_content = await self._fetch_readme(repo_id)
        
        if readme_content:
            # Use PRSNL's unified AI service
            analysis = await unified_ai_service.analyze_content(
                content=readme_content,
                enable_key_points=True,
                content_type="documentation"
            )
            
            # Store insight
            await self._store_insight(
                repo_id=repo_id,
                job_id=job_id,
                type="readme_quality",
                title="README Analysis",
                detail=analysis,
                ai_agent="knowledge_curator"
            )
        
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=30,
            stage="quick_complete",
            message="Quick analysis complete"
        )
🔄 Integration with Existing PRSNL Features
Leveraging Current Infrastructure
AI Agents: Use existing Knowledge Curator, Research Synthesizer for code analysis
Job System: All analysis tracked through /api/persistence/* endpoints
Search: Code integrated with PRSNL's semantic search
Chat: Code knowledge available in Mind Palace chat
Storage: Uses existing PostgreSQL + pgvector setup
Navigation Integration
typescript
// Add to existing Code Cortex navigation
const codeCorteRoutes = [
    { path: '/code-cortex', label: 'Overview' },
    { path: '/code-cortex/repos', label: 'Repositories' },
    { path: '/code-cortex/insights', label: 'AI Insights' },
    { path: '/code-cortex/learning', label: 'Learning Paths' },
    { path: '/code-cortex/docs', label: 'Documentation' },
    { path: '/code-cortex/synapses', label: 'Code Connections' }
];
📊 API Endpoints Summary
typescript
// CodeCortex specific endpoints
POST   /api/codecortex/analyze/{repo_id}    // Start analysis (creates job)
GET    /api/codecortex/repos                // List repositories
POST   /api/codecortex/repos/connect        // Connect GitHub
GET    /api/codecortex/insights             // Get code insights
GET    /api/codecortex/insights/{id}        // Get specific insight
PUT    /api/codecortex/insights/{id}/apply  // Apply insight

// Reuse existing PRSNL endpoints
GET    /api/persistence/status/{job_id}     // Monitor analysis progress
GET    /api/persistence/jobs?job_type=crawl_ai  // List code analysis jobs
POST   /api/ai-suggest                      // Get AI suggestions for code
WS     /ws/chat/{client_id}                 // Chat about code knowledge
🎨 UI Theme Integration
Using PRSNL's Manchester United theme (#dc143c):
css
/* CodeCortex specific styles */
.codecortex-container {
    --cc-primary: #dc143c;  /* Manchester United red */
    --cc-bg-primary: var(--surface-1);
    --cc-bg-secondary: var(--surface-2);
    --cc-text-primary: var(--text-primary);
    --cc-success: #10b981;
    --cc-warning: #f59e0b;
    --cc-error: #ef4444;
}
🚀 Implementation Timeline
Week 1: Foundation
Database schema setup
GitHub OAuth integration
Basic API endpoints
Job system integration
Week 2: AI Integration
Connect to PRSNL AI agents
Progressive analysis implementation
Insight generation and storage
WebSocket progress updates
Week 3: Frontend
Repository management UI
Progress tracking components
Insights dashboard
Learning path interface
Week 4: Polish
Performance optimization
Error handling
Documentation
Testing and refinement
🔑 Key Changes from Original
Port Updates: Frontend on 3004, Backend on 8000, PostgreSQL on 5433
AI Integration: Uses PRSNL's multi-agent system instead of direct AI calls
Job System: Leverages unified job persistence instead of custom implementation
Storage: Uses existing PostgreSQL with pgvector, no separate storage
Cache: DragonflyDB instead of Redis
Auth: Integrates with PRSNL's existing auth system
Frontend: Svelte 5 with runes, TanStack Query v5 for state management
This implementation fully integrates CodeCortex into PRSNL's Phase 3 architecture while maintaining the core value proposition of AI-powered code intelligence.

