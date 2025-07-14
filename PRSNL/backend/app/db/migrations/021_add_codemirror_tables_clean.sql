-- Migration: Add CodeMirror tables for AI-powered repository intelligence
-- This feature adds deep code analysis and pattern recognition to Code Cortex

-- CodeMirror analysis results table
CREATE TABLE codemirror_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    job_id VARCHAR(255) REFERENCES processing_jobs(job_id),
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('web', 'cli')),
    analysis_depth TEXT NOT NULL CHECK (analysis_depth IN ('quick', 'standard', 'deep')),
    
    -- Analysis results
    results JSONB NOT NULL DEFAULT '{}',
    file_count INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    languages_detected JSONB DEFAULT '[]',
    frameworks_detected JSONB DEFAULT '[]',
    
    -- Metrics
    security_score FLOAT CHECK (security_score >= 0 AND security_score <= 100),
    performance_score FLOAT CHECK (performance_score >= 0 AND performance_score <= 100),
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 100),
    
    -- Timing
    analysis_started_at TIMESTAMPTZ DEFAULT NOW(),
    analysis_completed_at TIMESTAMPTZ,
    analysis_duration_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CodeMirror detected patterns table
CREATE TABLE codemirror_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    pattern_signature TEXT NOT NULL,
    pattern_type TEXT CHECK (pattern_type IN (
        'authentication', 'api_call', 'error_handling', 'data_processing',
        'ui_pattern', 'testing', 'configuration', 'architecture', 'other'
    )),
    
    -- Pattern details
    description TEXT,
    code_examples JSONB DEFAULT '[]',
    solution_links JSONB DEFAULT '[]',
    
    -- Pattern frequency and quality
    occurrence_count INTEGER DEFAULT 1,
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Pattern relationships
    related_patterns JSONB DEFAULT '[]',
    source_repos JSONB DEFAULT '[]',
    
    -- AI analysis
    ai_confidence FLOAT CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    detected_by_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CodeMirror repository mappings table (for CLI integration tracking)
CREATE TABLE codemirror_repo_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    local_path TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    repo_id UUID REFERENCES github_repos(id),
    
    -- Integration detection
    integrations JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '{}',
    build_tools JSONB DEFAULT '[]',
    
    -- Mapping metadata
    last_synced_at TIMESTAMPTZ,
    cli_version TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, local_path)
);

-- CodeMirror insights table (actionable recommendations)
CREATE TABLE codemirror_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    pattern_id UUID REFERENCES codemirror_patterns(id),
    
    -- Insight content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    insight_type TEXT CHECK (insight_type IN (
        'security_vulnerability', 'performance_optimization', 'code_quality',
        'dependency_update', 'pattern_improvement', 'learning_opportunity'
    )),
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    recommendation TEXT NOT NULL,
    
    -- Insight status
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'applied', 'dismissed')),
    acknowledged_at TIMESTAMPTZ,
    applied_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    
    -- AI metadata
    generated_by_agent TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CodeMirror CLI sync table (for offline/online sync)
CREATE TABLE codemirror_cli_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    sync_token TEXT UNIQUE NOT NULL,
    
    -- Sync details
    cli_analysis_id TEXT NOT NULL, -- ID from CLI tool
    web_analysis_id UUID REFERENCES codemirror_analyses(id),
    
    -- Sync metadata
    cli_version TEXT NOT NULL,
    machine_id TEXT,
    sync_status TEXT DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'conflict', 'error')),
    
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_codemirror_analyses_repo ON codemirror_analyses(repo_id);
CREATE INDEX idx_codemirror_analyses_type ON codemirror_analyses(analysis_type);
CREATE INDEX idx_codemirror_analyses_created ON codemirror_analyses(created_at);

CREATE INDEX idx_codemirror_patterns_user ON codemirror_patterns(user_id);
CREATE INDEX idx_codemirror_patterns_signature ON codemirror_patterns(pattern_signature);
CREATE INDEX idx_codemirror_patterns_type ON codemirror_patterns(pattern_type);
CREATE INDEX idx_codemirror_patterns_occurrences ON codemirror_patterns(occurrence_count);

CREATE INDEX idx_codemirror_mappings_user ON codemirror_repo_mappings(user_id);

CREATE INDEX idx_codemirror_insights_analysis ON codemirror_insights(analysis_id);
CREATE INDEX idx_codemirror_insights_status ON codemirror_insights(status);
CREATE INDEX idx_codemirror_insights_type ON codemirror_insights(insight_type);

CREATE INDEX idx_codemirror_sync_user ON codemirror_cli_sync(user_id);
CREATE INDEX idx_codemirror_sync_token ON codemirror_cli_sync(sync_token);

-- Add triggers for updated_at
CREATE TRIGGER update_codemirror_analyses_updated_at 
    BEFORE UPDATE ON codemirror_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_patterns_updated_at 
    BEFORE UPDATE ON codemirror_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_mappings_updated_at 
    BEFORE UPDATE ON codemirror_repo_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE codemirror_analyses IS 'AI-powered repository analysis results';
COMMENT ON TABLE codemirror_patterns IS 'Detected code patterns and solutions';
COMMENT ON TABLE codemirror_repo_mappings IS 'CLI-to-web repository mappings';
COMMENT ON TABLE codemirror_insights IS 'Actionable insights and recommendations';
COMMENT ON TABLE codemirror_cli_sync IS 'CLI sync coordination table';