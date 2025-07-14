CodeCortex Feature Implementation Guide for PRSNL v3.0
🎯 Executive Summary
CodeCortex is a developer-focused knowledge management feature within PRSNL's Phase 3 AI Second Brain that creates an intelligent, personalized repository of code knowledge. It leverages PRSNL's multi-agent AI infrastructure, unified job persistence system, and existing storage architecture.
Core Value Proposition
Transform scattered technical knowledge into an AI-powered knowledge base using PRSNL's existing infrastructure:
README quality scoring via Knowledge Curator Agent
Dependency analysis via Research Synthesizer Agent
Code pattern discovery via Content Explorer Agent
Personalized learning paths via Learning Pathfinder Agent
All integrated with PRSNL's job persistence and WebSocket systems
📋 Feature Overview
What CodeCortex Does
Connects to GitHub repositories (read-only OAuth)
Analyzes content using PRSNL's AI agents
Stores everything in PRSNL's PostgreSQL (port 5433)
Tracks progress via job persistence system
Surfaces insights through PRSNL's UI
Integration with PRSNL v3.0
AI Infrastructure: Uses all 4 PRSNL AI agents
Storage: PostgreSQL with pgvector, DragonflyDB cache
Jobs: Unified job persistence system
Frontend: SvelteKit with Svelte 5 runes
API: FastAPI with Azure OpenAI integration
🏗️ Technical Architecture
System Flow Architecture (PRSNL Integrated)
┌─────────────────────────────────────────────────────────┐
│              PRSNL Frontend (Port 3004)                  │
│  • Code Cortex Hub      • Repository Selector           │
│  • AI Insights View     • Progress Tracking             │
│  • Learning Paths       • Real-time Updates             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            FastAPI Backend (Port 8000)                   │
│  • /api/codecortex/*    • Job Persistence API           │
│  • WebSocket Support    • Azure OpenAI Integration      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           PRSNL Multi-Agent AI System                    │
├─────────────────┬──────────────┬────────────────────────┤
│ Knowledge       │ Research     │ Content Explorer &      │
│ Curator         │ Synthesizer  │ Learning Pathfinder     │
└─────────────────┴──────────────┴────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│      PostgreSQL 16 (5433) + DragonflyDB (6379)         │
│  • github_repos    • code_insights    • embeddings      │
│  • processing_jobs • codecortex_items • past_solutions  │
└─────────────────────────────────────────────────────────┘
🔧 Implementation Details
1. GitHub OAuth Integration
python
# backend/app/services/github_service.py
from app.core.config import settings
from app.db import database
import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class GitHubService:
    """GitHub integration service for PRSNL"""
    
    SCOPES = ["read:user", "repo", "metadata"]
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.encryption_key = settings.ENCRYPTION_KEY.encode()
    
    async def init_oauth_flow(self, user_id: str) -> str:
        """Generate GitHub OAuth URL"""
        state = generate_secure_state(user_id)
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": f"{settings.FRONTEND_URL}/code-cortex/github-callback",
            "scope": " ".join(self.SCOPES),
            "state": state
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    def encrypt_token(self, token: str) -> bytes:
        """Encrypt token using AES-256-GCM"""
        aesgcm = AESGCM(self.encryption_key)
        nonce = os.urandom(12)
        return nonce + aesgcm.encrypt(nonce, token.encode(), None)
2. Progressive Analysis with Job Persistence
python
# backend/app/api/codecortex.py
from fastapi import APIRouter, BackgroundTasks, Depends
from app.core.auth import get_current_user
from app.services.job_persistence_service import job_persistence_service
from app.services.codecortex_service import CodeCortexService

router = APIRouter(prefix="/api/codecortex", tags=["codecortex"])

@router.post("/analyze/{repo_id}")
async def analyze_repository(
    repo_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Start progressive repository analysis using PRSNL job system"""
    
    # Create job in PRSNL's persistence system
    job_id = f"codecortex_{repo_id}_{datetime.now().timestamp()}"
    
    await job_persistence_service.create_job(
        job_id=job_id,
        job_type="crawl_ai",  # Using existing job type
        input_data={
            "repo_id": repo_id,
            "user_id": current_user.id,
            "analysis_type": "progressive",
            "phases": ["quick", "medium", "deep"]
        },
        tags=["codecortex", "repository_analysis"]
    )
    
    # Queue background analysis
    background_tasks.add_task(
        CodeCortexService().analyze_repository_progressive,
        repo_id,
        job_id,
        current_user.id
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Analysis started",
        "monitor_url": f"/api/persistence/status/{job_id}",
        "websocket_channel": f"codecortex.{job_id}"
    }
3. AI Analysis Integration with PRSNL Agents
python
# backend/app/services/codecortex_service.py
from app.services.unified_ai_service import unified_ai_service
from app.services.job_persistence_service import job_persistence_service
from app.services.ai_agents import (
    KnowledgeCuratorAgent,
    ResearchSynthesizerAgent,
    ContentExplorerAgent,
    LearningPathfinderAgent
)

class CodeCortexService:
    """Main service orchestrating CodeCortex with PRSNL AI agents"""
    
    def __init__(self):
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
        """Progressive analysis using PRSNL's infrastructure"""
        
        try:
            # Phase 1: Quick Analysis (0-30%)
            await self._quick_analysis_phase(repo_id, job_id)
            
            # Phase 2: Medium Analysis (30-70%)
            await self._medium_analysis_phase(repo_id, job_id)
            
            # Phase 3: Deep Analysis (70-100%)
            await self._deep_analysis_phase(repo_id, job_id)
            
        except Exception as e:
            await job_persistence_service.update_job(
                job_id=job_id,
                status="failed",
                error=str(e)
            )
            raise
    
    async def _quick_analysis_phase(self, repo_id: str, job_id: str):
        """Quick insights using Knowledge Curator"""
        
        await job_persistence_service.update_job(
            job_id=job_id,
            status="processing",
            progress=5,
            stage="quick_analysis",
            message="Analyzing documentation and structure"
        )
        
        # Fetch README and basic files
        readme_content = await self._fetch_readme(repo_id)
        
        if readme_content:
            # Use Knowledge Curator for documentation analysis
            analysis = await self.curator.analyze_content(
                content=readme_content,
                context={
                    "type": "documentation",
                    "source": "github_readme"
                }
            )
            
            # Store insight
            await self._store_insight(
                repo_id=repo_id,
                job_id=job_id,
                type="readme_quality",
                title="Documentation Analysis",
                detail=analysis,
                ai_agent="knowledge_curator"
            )
        
        await job_persistence_service.update_job(
            job_id=job_id,
            progress=30,
            stage="quick_complete",
            message="Quick analysis complete"
        )
4. Frontend Components (Svelte 5 with Runes)
svelte
<!-- frontend/src/routes/code-cortex/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { jobPersistenceStore } from '$lib/stores/jobPersistence';
  import RepoSelector from '$lib/components/codecortex/RepoSelector.svelte';
  import InsightsDrawer from '$lib/components/codecortex/InsightsDrawer.svelte';
  import AnalysisProgress from '$lib/components/codecortex/AnalysisProgress.svelte';
  
  // Svelte 5 runes for local state
  let selectedRepo = $state(null);
  let analysisJobId = $state(null);
  let insights = $state([]);
  let loading = $state(false);
  
  async function fetchLatest() {
    if (!selectedRepo) return;
    
    loading = true;
    try {
      // Start analysis job
      const response = await api.post(`/api/codecortex/analyze/${selectedRepo.id}`);
      analysisJobId = response.data.job_id;
      
      // Monitor job progress
      jobPersistenceStore.monitorJob(analysisJobId);
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      loading = false;
    }
  }
  
  // React to job updates
  $effect(() => {
    if (analysisJobId) {
      const job = $jobPersistenceStore.jobs.get(analysisJobId);
      if (job?.status === 'completed') {
        loadInsights();
      }
    }
  });
  
  async function loadInsights() {
    const response = await api.get('/api/codecortex/insights', {
      params: { repo_id: selectedRepo.id }
    });
    insights = response.data;
  }
</script>

<div class="codecortex-container">
  <header class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold">Code Cortex</h1>
    <button 
      on:click={fetchLatest} 
      disabled={!selectedRepo || loading}
      class="btn-primary"
    >
      {#if loading}
        <span class="spinner"></span> Analyzing...
      {:else}
        🔄 Fetch Latest
      {/if}
    </button>
  </header>
  
  <RepoSelector bind:selected={selectedRepo} />
  
  {#if analysisJobId}
    <AnalysisProgress jobId={analysisJobId} />
  {/if}
  
  {#if selectedRepo && insights.length > 0}
    <InsightsDrawer 
      repoId={selectedRepo.id} 
      {insights}
    />
  {/if}
</div>

<style>
  .codecortex-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
5. WebSocket Progress Updates
python
# backend/app/services/codecortex_websocket.py
from app.core.websocket import websocket_manager

class CodeCortexWebSocketService:
    """WebSocket integration for real-time updates"""
    
    async def send_progress_update(self, job_id: str, progress_data: dict):
        """Send progress update via PRSNL's WebSocket infrastructure"""
        
        channel = f"codecortex.{job_id}"
        message = {
            "type": "analysis_progress",
            "job_id": job_id,
            "phase": progress_data.get("current_stage"),
            "progress": progress_data.get("progress_percentage"),
            "message": progress_data.get("stage_message"),
            "insights_found": progress_data.get("insights_count", 0)
        }
        
        await websocket_manager.broadcast_to_channel(channel, message)
6. Integration with PRSNL Navigation
typescript
// Add to existing Code Cortex routes
export const codeCorteRoutes = [
  { path: '/code-cortex', label: 'Overview', icon: '🧠' },
  { path: '/code-cortex/repos', label: 'Repositories', icon: '📦' },
  { path: '/code-cortex/insights', label: 'AI Insights', icon: '💡' },
  { path: '/code-cortex/learning', label: 'Learning Paths', icon: '📚' },
  { path: '/code-cortex/solutions', label: 'Past Solutions', icon: '🔧' },
  { path: '/code-cortex/docs', label: 'Documentation', icon: '📄' }
];
📊 API Endpoints
CodeCortex Endpoints (Integrated with PRSNL)
typescript
// GitHub Integration
POST   /api/codecortex/github/connect    // Start OAuth flow
GET    /api/codecortex/github/callback   // OAuth callback
DELETE /api/codecortex/github/disconnect // Revoke access

// Repository Management
GET    /api/codecortex/repos             // List connected repos
PUT    /api/codecortex/repos/{id}        // Update repo settings
POST   /api/codecortex/analyze/{id}      // Start analysis (creates job)

// Insights & Results
GET    /api/codecortex/insights          // Get insights for repo
PUT    /api/codecortex/insights/{id}     // Update insight status
POST   /api/codecortex/insights/{id}/apply // Apply an insight

// Learning Paths
GET    /api/codecortex/learning-paths    // Get learning paths
POST   /api/codecortex/learning/progress // Update progress

// Reuse existing PRSNL endpoints
GET    /api/persistence/status/{job_id}  // Monitor analysis
WS     /ws/chat/{client_id}              // WebSocket updates
POST   /api/ai-suggest                   // Additional AI analysis
🎨 UI/UX Design (PRSNL Theme)
Visual Integration
css
/* Using PRSNL's Manchester United theme */
.codecortex-container {
  --primary: #dc143c;  /* Manchester United red */
  --surface-1: var(--prsnl-surface-1);
  --surface-2: var(--prsnl-surface-2);
  --text-primary: var(--prsnl-text-primary);
  --text-secondary: var(--prsnl-text-secondary);
}

/* Progress indicators matching PRSNL style */
.analysis-progress {
  background: var(--surface-2);
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 1.5rem;
}
🚀 Implementation Phases
Phase 1: Core Integration (Week 1)
Database schema migration
GitHub OAuth implementation
Job persistence integration
Basic UI components
Phase 2: AI Analysis (Week 2)
Knowledge Curator integration
Research Synthesizer setup
Content Explorer configuration
Progressive analysis flow
Phase 3: Frontend & UX (Week 3)
Repository management UI
Insights dashboard
Progress tracking
Learning path interface
Phase 4: Polish & Optimize (Week 4)
DragonflyDB caching
Performance tuning
Mobile responsiveness
Documentation
📈 Success Metrics
Integration KPIs
Metric
Target
Measurement
Job completion rate
> 95%
Via job persistence system
AI agent utilization
All 4 agents
Agent attribution tracking
Cache hit rate
> 60%
DragonflyDB metrics
WebSocket reliability
> 99%
Connection monitoring

User Experience KPIs
Metric
Target
Measurement
First insight time
< 30s
Job progress tracking
Insight actionability
> 80%
User feedback
Learning path completion
> 40%
Progress tracking
Feature adoption
> 50%
Usage analytics

🔐 Security & Privacy
Data Protection (PRSNL Integrated)
GitHub tokens: Encrypted with AES-256-GCM
Storage: All data in PRSNL's PostgreSQL
Cache: DragonflyDB with TTL policies
No external sharing: Insights stay in PRSNL
Security Implementation
python
# Reusing PRSNL's security infrastructure
from app.core.security import encrypt_field, decrypt_field
from app.core.auth import require_user

@router.post("/repos/{repo_id}/analyze")
@require_user
async def analyze_repo(
    repo_id: str,
    current_user = Depends(get_current_user)
):
    # Verify repo ownership
    repo = await verify_repo_ownership(repo_id, current_user.id)
    # ... rest of implementation
🛠️ Technical Considerations
Rate Limiting (Azure OpenAI)
Use PRSNL's existing rate limit management
Progressive analysis spreads API calls
Cache results in DragonflyDB
Performance Optimization
Leverage pgvector for similarity search
Use PRSNL's embedding infrastructure
Background processing via job system
🤝 Integration Points
PRSNL Services Used
unified_ai_service: For all AI operations
job_persistence_service: For tracking analysis
embedding_manager: For code similarity
websocket_manager: For real-time updates
DragonflyDB: For caching
New Services to Implement
GitHubService: OAuth and API wrapper
CodeCortexService: Main orchestration
InsightManager: Insight lifecycle
LearningPathService: Path generation

