​​CodeCortex Database Schema - PRSNL v3.0 Integration
🗄️ Overview
This document contains the complete database schema for CodeCortex, fully integrated with PRSNL's Phase 3 architecture. It leverages PRSNL's existing infrastructure including PostgreSQL 16 with pgvector (port 5433), the unified job persistence system, and multi-agent AI architecture.
📊 Core Tables
GitHub Integration Tables
sql
-- GitHub OAuth and Account Management
CREATE TABLE github_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    github_username TEXT,
    installation_id BIGINT,
    scopes TEXT[] NOT NULL DEFAULT '{read:user,repo,metadata}',
    access_token_enc BYTEA NOT NULL,  -- AES-256-GCM encrypted
    refresh_token_enc BYTEA,
    token_expires_at TIMESTAMPTZ,
    etag_cache JSONB DEFAULT '{}',  -- {"repo/path": "etag_value"}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id),
    INDEX idx_github_accounts_user (user_id)
);

-- GitHub Repositories
CREATE TABLE github_repos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES github_accounts(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,  -- "owner/repo"
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    item_type TEXT DEFAULT 'development',  -- For PRSNL integration
    selected BOOLEAN DEFAULT FALSE,
    default_branch TEXT DEFAULT 'main',
    last_synced_sha TEXT,
    last_fetched_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',  -- stars, language, description, topics
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(account_id, full_name),
    INDEX idx_github_repos_selected (account_id, selected),
    INDEX idx_github_repos_fetch (last_fetched_at)
);
AI-Generated Insights Tables
sql
-- AI-Generated Code Insights (integrated with PRSNL job system)
CREATE TABLE code_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),  -- PRSNL job reference
    type TEXT NOT NULL CHECK (type IN (
        'readme_quality', 'stale_dep', 'refactor', 'learning_path',
        'security_issue', 'performance', 'architecture', 'documentation'
    )),
    title TEXT NOT NULL,
    summary TEXT,
    detail JSONB NOT NULL,  -- Type-specific structured data
    fingerprint_sha TEXT UNIQUE NOT NULL,  -- SHA256 for deduplication
    severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'ignored', 'applied', 'expired')),
    ai_agent TEXT NOT NULL,  -- Which PRSNL agent generated this
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    
    INDEX idx_insights_repo_status (repo_id, status),
    INDEX idx_insights_type (type),
    INDEX idx_insights_fingerprint (fingerprint_sha),
    INDEX idx_insights_job (job_id)
);

-- Insight Priority and Actionability
CREATE TABLE insight_priorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id UUID REFERENCES code_insights(id) ON DELETE CASCADE UNIQUE,
    priority_score FLOAT NOT NULL CHECK (priority_score >= 0 AND priority_score <= 100),
    priority_category TEXT NOT NULL CHECK (priority_category IN (
        'immediate', 'this_sprint', 'backlog', 'nice_to_have'
    )),
    effort_estimate TEXT CHECK (effort_estimate IN ('minutes', 'hours', 'days', 'weeks')),
    business_impact TEXT CHECK (business_impact IN ('critical', 'high', 'medium', 'low')),
    technical_debt_cost FLOAT,
    actionability_score FLOAT CHECK (actionability_score >= 0 AND actionability_score <= 100),
    quality_factors JSONB NOT NULL DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_priorities_category (priority_category),
    INDEX idx_priorities_score (priority_score DESC)
);
Code Analysis Tables (Extending PRSNL Items)
sql
-- Code Items (extends PRSNL items table)
CREATE TABLE codecortex_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    
    -- File metadata
    file_path TEXT NOT NULL,
    file_type TEXT CHECK (file_type IN ('source', 'config', 'documentation', 'test')),
    language TEXT,
    framework TEXT,
    
    -- Code analysis
    code_type TEXT CHECK (code_type IN ('function', 'class', 'module', 'interface')),
    complexity_score FLOAT,
    documentation_score FLOAT,
    test_coverage FLOAT,
    
    -- Dependencies and relationships
    imports TEXT[],
    exports TEXT[],
    dependencies JSONB DEFAULT '{}',
    
    -- Git metadata
    commit_sha TEXT,
    line_start INTEGER,
    line_end INTEGER,
    last_modified TIMESTAMPTZ,
    
    -- Integration with PRSNL embeddings
    embed_vector_id UUID REFERENCES embeddings(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_codecortex_repo (repo_id),
    INDEX idx_codecortex_path (repo_id, file_path),
    INDEX idx_codecortex_language (language)
);

-- Code Relationships and Patterns
CREATE TABLE code_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    source_file TEXT NOT NULL,
    source_type TEXT,
    target_file TEXT NOT NULL,
    target_type TEXT,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'imports', 'extends', 'implements', 'uses', 'calls', 'references'
    )),
    relationship_metadata JSONB DEFAULT '{}',
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    discovered_by TEXT,  -- 'knowledge_curator', 'content_explorer', etc.
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_relationships_repo (repo_id),
    INDEX idx_relationships_source (repo_id, source_file),
    INDEX idx_relationships_type (relationship_type)
);
Knowledge Synthesis Tables
sql
-- Problem Detection and Tracking
CREATE TABLE detected_problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID,
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    problem_type TEXT NOT NULL CHECK (problem_type IN (
        'error', 'feature_building', 'refactoring', 'debugging', 
        'learning', 'integration', 'performance', 'security'
    )),
    problem_signature TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Context
    file_path TEXT,
    line_number INTEGER,
    error_message TEXT,
    code_context TEXT,
    
    -- Detection metadata
    detection_method TEXT,  -- 'error_console', 'code_analysis', 'user_search'
    detected_by_agent TEXT,  -- Which PRSNL agent detected this
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_time_seconds INTEGER,
    
    INDEX idx_problems_user_type (user_id, problem_type),
    INDEX idx_problems_signature (problem_signature),
    INDEX idx_problems_job (job_id)
);

-- Knowledge Search Results (uses PRSNL's search infrastructure)
CREATE TABLE knowledge_search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id UUID REFERENCES detected_problems(id) ON DELETE CASCADE,
    search_id UUID NOT NULL,
    
    -- Source information from PRSNL items
    source_type TEXT NOT NULL,  -- PRSNL item types
    source_id UUID REFERENCES items(id),
    source_reference TEXT,  -- File:line, video:timestamp, etc.
    
    -- Relevance from PRSNL search
    relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    match_type TEXT,  -- 'semantic', 'keyword', 'hybrid'
    similarity_score FLOAT,  -- From pgvector similarity
    
    -- Metadata
    excerpt TEXT,
    metadata JSONB,
    searched_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_search_results_problem (problem_id),
    INDEX idx_search_results_relevance (relevance_score DESC)
);

-- Synthesized Solutions
CREATE TABLE synthesized_solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id UUID REFERENCES detected_problems(id) ON DELETE CASCADE,
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    
    -- Solution details
    solution_code TEXT,
    explanation TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- AI agent attribution
    primary_agent TEXT NOT NULL,  -- Main PRSNL agent
    contributing_agents TEXT[],  -- Other agents involved
    
    -- References from PRSNL content
    primary_source_id UUID REFERENCES items(id),
    related_items UUID[],  -- Array of item IDs
    
    -- User interaction
    presented_at TIMESTAMPTZ DEFAULT NOW(),
    user_action TEXT CHECK (user_action IN (
        'applied', 'modified', 'rejected', 'saved', 'shared'
    )),
    action_at TIMESTAMPTZ,
    user_feedback TEXT,
    modifications_made TEXT,
    
    INDEX idx_solutions_problem (problem_id),
    INDEX idx_solutions_action (user_action)
);

-- Past Solutions Storage (integrated with PRSNL items)
CREATE TABLE past_solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    item_id UUID REFERENCES items(id),  -- Stored as PRSNL item
    
    -- Problem information
    problem_signature TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    problem_description TEXT,
    error_pattern TEXT,
    
    -- Solution effectiveness
    time_to_solve_seconds INTEGER,
    prevented_future_issues BOOLEAN DEFAULT FALSE,
    reuse_count INTEGER DEFAULT 0,
    last_reused_at TIMESTAMPTZ,
    
    -- Embeddings for similarity search
    embed_vector_id UUID REFERENCES embeddings(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_past_solutions_user (user_id),
    INDEX idx_past_solutions_signature (problem_signature),
    INDEX idx_past_solutions_reuse (reuse_count DESC)
);
Progressive Analysis Tables (Using PRSNL Job System)
sql
-- Analysis Sessions (extends PRSNL processing_jobs)
CREATE TABLE codecortex_analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id) UNIQUE,
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    
    -- Progressive phases
    phases JSONB DEFAULT '{
        "quick": {"status": "pending", "progress": 0, "insights_found": 0},
        "medium": {"status": "pending", "progress": 0, "insights_found": 0},
        "deep": {"status": "pending", "progress": 0, "insights_found": 0}
    }',
    
    -- Results summary
    insights_summary JSONB DEFAULT '{
        "critical": 0, "warnings": 0, "suggestions": 0, "total": 0
    }',
    
    -- Rate limiting (Azure OpenAI)
    rate_limit_status JSONB DEFAULT '{}',
    
    -- WebSocket session for real-time updates
    websocket_session_id TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_analysis_sessions_repo (repo_id),
    INDEX idx_analysis_sessions_job (job_id)
);

-- Smart Sampling Metadata
CREATE TABLE analysis_sampling (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES codecortex_analysis_sessions(id) ON DELETE CASCADE,
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    sampling_strategy TEXT NOT NULL CHECK (sampling_strategy IN (
        'full_docs_sample_code', 'smart_sampling', 'progressive_sampling', 'docs_only'
    )),
    total_files INTEGER NOT NULL,
    files_sampled TEXT[] NOT NULL,
    files_skipped TEXT[],
    sampling_metadata JSONB DEFAULT '{}',
    token_usage INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_sampling_session (session_id)
);
Learning & Success Tracking Tables
sql
-- Learning Paths (generated by Learning Pathfinder Agent)
CREATE TABLE codecortex_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    repo_id UUID REFERENCES github_repos(id),
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    
    -- Path details
    title TEXT NOT NULL,
    duration_weeks INTEGER DEFAULT 4,
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    
    -- Generated by Learning Pathfinder
    modules JSONB NOT NULL,  -- Weekly modules with lessons
    user_code_references JSONB,  -- Links to user's actual code
    
    -- Progress tracking
    progress JSONB DEFAULT '{"completed_lessons": [], "current_week": 1}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    INDEX idx_learning_paths_user (user_id)
);

-- Success Metrics (integrated with PRSNL metrics)
CREATE TABLE codecortex_success_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE,
    
    -- Time efficiency
    total_problems_solved INTEGER DEFAULT 0,
    total_time_saved_seconds BIGINT DEFAULT 0,
    average_resolution_time_seconds INTEGER,
    
    -- Code quality
    insights_applied INTEGER DEFAULT 0,
    bugs_prevented INTEGER DEFAULT 0,
    refactorings_completed INTEGER DEFAULT 0,
    
    -- Knowledge metrics
    solutions_captured INTEGER DEFAULT 0,
    solutions_reused INTEGER DEFAULT 0,
    patterns_discovered INTEGER DEFAULT 0,
    
    -- Learning progress
    learning_paths_completed INTEGER DEFAULT 0,
    skills_improved TEXT[],
    
    -- Calculated metrics
    roi_multiplier FLOAT,
    trust_score FLOAT DEFAULT 0.5,
    
    last_calculated TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_codecortex_metrics_user (user_id)
);

-- Achievement Tracking
CREATE TABLE codecortex_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    achievement_type TEXT NOT NULL CHECK (achievement_type IN (
        'first_repo', 'pattern_hunter', 'insight_master', 'speed_demon',
        'quality_guardian', 'knowledge_sharer', 'learning_champion'
    )),
    achievement_data JSONB NOT NULL,
    achieved_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, achievement_type),
    INDEX idx_achievements_user (user_id)
);
Cache & Performance Tables
sql
-- DragonflyDB Cache Inventory (integrated with PRSNL)
CREATE TABLE codecortex_cache_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_type TEXT CHECK (cache_type IN (
        'analysis_result', 'insight', 'pattern', 'learning_path',
        'synthesis_result', 'problem_detection'
    )),
    
    -- References
    user_id UUID REFERENCES users(id),
    repo_id UUID REFERENCES github_repos(id),
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    
    -- Cache metadata
    size_bytes INTEGER,
    ttl_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_accessed TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    
    INDEX idx_cache_user (user_id),
    INDEX idx_cache_expires (expires_at)
);

-- AI Analysis Cache (for expensive operations)
CREATE TABLE codecortex_ai_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key TEXT UNIQUE NOT NULL,  -- SHA256(content + agent + version)
    ai_agent TEXT NOT NULL,  -- Which PRSNL agent
    agent_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output JSONB NOT NULL,
    token_count INTEGER,
    processing_time_ms INTEGER,
    model_used TEXT,  -- 'prsnl-gpt-4' or 'gpt-4.1-mini'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    INDEX idx_ai_cache_key (cache_key),
    INDEX idx_ai_cache_expires (expires_at)
);
Integration Tables
sql
-- WebSocket Sessions (for real-time updates)
CREATE TABLE codecortex_websocket_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    
    -- Connection details
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    last_ping_at TIMESTAMPTZ DEFAULT NOW(),
    disconnected_at TIMESTAMPTZ,
    
    -- Subscriptions
    subscribed_repos UUID[],  -- Array of repo IDs
    subscribed_jobs VARCHAR(255)[],  -- Array of job IDs
    
    INDEX idx_ws_user (user_id),
    INDEX idx_ws_active (disconnected_at) WHERE disconnected_at IS NULL
);

-- Mobile Sync Queue (for PRSNL mobile app)
CREATE TABLE codecortex_mobile_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action_type TEXT NOT NULL CHECK (action_type IN (
        'view_insight', 'apply_insight', 'dismiss_insight',
        'start_learning', 'complete_lesson'
    )),
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    synced_at TIMESTAMPTZ,
    device_id TEXT,
    
    INDEX idx_mobile_sync_pending (user_id, synced_at) WHERE synced_at IS NULL
);
🚀 Migration Scripts
sql
-- Enable required extensions (if not already enabled by PRSNL)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_github_accounts_updated_at 
    BEFORE UPDATE ON github_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_github_repos_updated_at 
    BEFORE UPDATE ON github_repos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codecortex_items_updated_at 
    BEFORE UPDATE ON codecortex_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for text search
CREATE INDEX idx_codecortex_items_search 
    ON codecortex_items 
    USING gin(to_tsvector('english', 
        file_path || ' ' || 
        COALESCE(language, '') || ' ' || 
        COALESCE(framework, '')
    ));

-- Create materialized view for quick dashboard stats
CREATE MATERIALIZED VIEW codecortex_dashboard_stats AS
SELECT 
    u.id as user_id,
    COUNT(DISTINCT gr.id) as repos_count,
    COUNT(DISTINCT ci.id) as insights_count,
    COUNT(DISTINCT ci.id) FILTER (WHERE ci.severity = 'critical') as critical_count,
    COUNT(DISTINCT ci.id) FILTER (WHERE ci.status = 'applied') as applied_count,
    AVG(csm.trust_score) as avg_trust_score
FROM users u
LEFT JOIN github_accounts ga ON u.id = ga.user_id
LEFT JOIN github_repos gr ON ga.id = gr.account_id AND gr.selected = true
LEFT JOIN code_insights ci ON gr.id = ci.repo_id
LEFT JOIN codecortex_success_metrics csm ON u.id = csm.user_id
GROUP BY u.id;

CREATE INDEX idx_dashboard_stats_user ON codecortex_dashboard_stats(user_id);
📊 Common Queries
sql
-- Get user's active problems with solutions
SELECT 
    dp.*,
    ss.solution_code,
    ss.confidence_score,
    ss.primary_agent
FROM detected_problems dp
LEFT JOIN synthesized_solutions ss ON dp.id = ss.problem_id
WHERE dp.user_id = $1 
    AND dp.resolved_at IS NULL
ORDER BY dp.detected_at DESC;

-- Get insights with priority for dashboard
SELECT 
    ci.*,
    ip.priority_category,
    ip.priority_score,
    gr.full_name as repo_name
FROM code_insights ci
JOIN insight_priorities ip ON ci.id = ip.insight_id
JOIN github_repos gr ON ci.repo_id = gr.id
JOIN github_accounts ga ON gr.account_id = ga.id
WHERE ga.user_id = $1 
    AND gr.selected = true 
    AND ci.status = 'open'
ORDER BY ip.priority_score DESC
LIMIT 20;

-- Get learning progress
SELECT 
    clp.*,
    COUNT(DISTINCT lpe.lesson_id) as completed_lessons,
    MAX(lpe.completed_at) as last_activity
FROM codecortex_learning_paths clp
LEFT JOIN learning_progress_entries lpe ON clp.id = lpe.learning_path_id
WHERE clp.user_id = $1
GROUP BY clp.id
ORDER BY clp.created_at DESC;
🔑 Key Integration Points
Job System: All long-running tasks use PRSNL's processing_jobs table
Embeddings: Code similarity uses PRSNL's embeddings table with pgvector
Items: Solutions and code files stored as PRSNL items with type 'development'
Search: Leverages PRSNL's enhanced search infrastructure
WebSocket: Uses PRSNL's existing WebSocket infrastructure
Cache: DragonflyDB integration follows PRSNL patterns
This unified schema provides CodeCortex with a robust foundation while fully leveraging PRSNL's Phase 3 infrastructure.

