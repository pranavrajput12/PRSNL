-- Migration: Add CodeMirror tables for AI-powered repository intelligence
-- Simplified version without foreign key dependencies

-- CodeMirror analysis results table
CREATE TABLE IF NOT EXISTS codemirror_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID,  -- Will reference github_repos later
    job_id VARCHAR(255),  -- Will reference processing_jobs later
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
CREATE TABLE IF NOT EXISTS codemirror_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    pattern_signature TEXT NOT NULL,
    pattern_type TEXT CHECK (pattern_type IN (
        'authentication', 'api_call', 'error_handling', 'data_processing',
        'ui_pattern', 'testing', 'configuration', 'architecture', 'other'
    )),
    
    -- Pattern details
    description TEXT,
    code_snippet TEXT,
    language TEXT,
    framework TEXT,
    
    -- Tracking
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    occurrence_count INTEGER DEFAULT 1,
    repos_found_in JSONB DEFAULT '[]',
    
    -- AI generated insights
    ai_summary TEXT,
    ai_recommendations JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_codemirror_analyses_repo ON codemirror_analyses(repo_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_analyses_type ON codemirror_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_codemirror_analyses_created ON codemirror_analyses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_codemirror_patterns_user ON codemirror_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_codemirror_patterns_signature ON codemirror_patterns(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_codemirror_patterns_type ON codemirror_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_codemirror_patterns_occurrences ON codemirror_patterns(occurrence_count DESC);

-- Add update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
DROP TRIGGER IF EXISTS update_codemirror_analyses_updated_at ON codemirror_analyses;
CREATE TRIGGER update_codemirror_analyses_updated_at 
    BEFORE UPDATE ON codemirror_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_codemirror_patterns_updated_at ON codemirror_patterns;
CREATE TRIGGER update_codemirror_patterns_updated_at 
    BEFORE UPDATE ON codemirror_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE codemirror_analyses IS 'Stores AI-powered code analysis results for repositories';
COMMENT ON TABLE codemirror_patterns IS 'Stores detected code patterns and AI insights across user repositories';