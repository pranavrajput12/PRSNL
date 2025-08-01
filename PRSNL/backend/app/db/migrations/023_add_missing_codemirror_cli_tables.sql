-- Migration: Add missing CodeMirror CLI integration tables
-- This adds the CLI sync and repo mappings tables that were missing

-- CodeMirror repository mappings table (for CLI integration tracking)
CREATE TABLE IF NOT EXISTS codemirror_repo_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    local_path TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    repo_id UUID REFERENCES github_repos(id),
    
    -- Integration detection
    integrations JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '{}',
    build_tools JSONB DEFAULT '[]',
    frameworks JSONB DEFAULT '[]',
    tech_stack JSONB DEFAULT '{}',
    
    -- Metadata
    last_analyzed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, local_path)
);

-- CodeMirror insights table (AI-generated insights)
CREATE TABLE IF NOT EXISTS codemirror_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    
    -- Insight details
    insight_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    recommendation TEXT,
    
    -- AI metadata
    generated_by_agent TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 0.8 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Additional data
    data JSONB DEFAULT '{}',
    
    -- Status
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'applied', 'dismissed')),
    status_updated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CodeMirror CLI sync table (for offline/online sync)
CREATE TABLE IF NOT EXISTS codemirror_cli_sync (
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
    
    -- Sync data
    local_changes JSONB DEFAULT '{}',
    remote_changes JSONB DEFAULT '{}',
    conflict_resolution TEXT,
    
    -- Timestamps
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_codemirror_repo_mappings_user ON codemirror_repo_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_repo_mappings_repo ON codemirror_repo_mappings(repo_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_repo_mappings_path ON codemirror_repo_mappings(local_path);

CREATE INDEX IF NOT EXISTS idx_codemirror_insights_analysis ON codemirror_insights(analysis_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_insights_type ON codemirror_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_codemirror_insights_severity ON codemirror_insights(severity);
CREATE INDEX IF NOT EXISTS idx_codemirror_insights_status ON codemirror_insights(status);

CREATE INDEX IF NOT EXISTS idx_codemirror_cli_sync_user ON codemirror_cli_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_cli_sync_token ON codemirror_cli_sync(sync_token);
CREATE INDEX IF NOT EXISTS idx_codemirror_cli_sync_cli_id ON codemirror_cli_sync(cli_analysis_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_cli_sync_web_id ON codemirror_cli_sync(web_analysis_id);

-- Add triggers for updated_at columns
CREATE TRIGGER update_codemirror_repo_mappings_updated_at 
    BEFORE UPDATE ON codemirror_repo_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_insights_updated_at 
    BEFORE UPDATE ON codemirror_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_cli_sync_updated_at 
    BEFORE UPDATE ON codemirror_cli_sync
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE codemirror_repo_mappings IS 'Maps local repository paths to GitHub repos for CLI integration';
COMMENT ON TABLE codemirror_insights IS 'AI-generated insights from repository analysis';
COMMENT ON TABLE codemirror_cli_sync IS 'Tracks CLI tool analysis sync with web platform';