-- Migration: Add CLI Integration Tables for Enhanced CodeMirror
-- Phase 1.3: Database schema extensions for GitPython, Semgrep, Comby, and Watchdog integration

-- Git analysis results table
CREATE TABLE codemirror_git_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    repository_url TEXT NOT NULL,
    
    -- Repository statistics
    total_commits INTEGER DEFAULT 0,
    total_authors INTEGER DEFAULT 0,
    repository_age_days INTEGER DEFAULT 0,
    primary_language TEXT,
    
    -- Commit patterns (stored as JSONB for flexibility)
    commits_by_hour JSONB DEFAULT '{}',
    commits_by_day JSONB DEFAULT '{}',
    commits_by_month JSONB DEFAULT '{}',
    
    -- Author analysis
    top_authors JSONB DEFAULT '[]',
    author_collaboration JSONB DEFAULT '{}',
    
    -- File patterns
    most_changed_files JSONB DEFAULT '[]',
    file_extensions JSONB DEFAULT '{}',
    hotspot_files JSONB DEFAULT '[]',
    
    -- Development patterns
    average_commit_size FLOAT DEFAULT 0,
    merge_frequency FLOAT DEFAULT 0,
    branch_patterns JSONB DEFAULT '{}',
    release_patterns JSONB DEFAULT '[]',
    
    -- Code quality indicators
    commit_message_quality JSONB DEFAULT '{}',
    refactoring_patterns JSONB DEFAULT '[]',
    technical_debt_indicators JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Security scan results table
CREATE TABLE codemirror_security_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    repository_path TEXT NOT NULL,
    
    -- Scan metadata
    scan_duration_seconds FLOAT DEFAULT 0,
    total_findings INTEGER DEFAULT 0,
    files_scanned INTEGER DEFAULT 0,
    rules_executed INTEGER DEFAULT 0,
    
    -- Security scores
    overall_security_score FLOAT CHECK (overall_security_score >= 0 AND overall_security_score <= 100),
    owasp_compliance_score FLOAT CHECK (owasp_compliance_score >= 0 AND owasp_compliance_score <= 100),
    
    -- Finding statistics
    findings_by_severity JSONB DEFAULT '{}',
    owasp_categories JSONB DEFAULT '{}',
    cwe_categories JSONB DEFAULT '{}',
    
    -- Risk assessment
    high_risk_files JSONB DEFAULT '[]',
    security_hotspots JSONB DEFAULT '[]',
    common_vulnerabilities JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Security findings table (detailed findings from Semgrep)
CREATE TABLE codemirror_security_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_scan_id UUID REFERENCES codemirror_security_scans(id) ON DELETE CASCADE,
    
    -- Finding details
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    message TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    column_number INTEGER,
    
    -- Code context
    code_snippet TEXT,
    fix_suggestion TEXT,
    
    -- Classification
    owasp_category TEXT,
    cwe_id TEXT,
    confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),
    
    -- Status tracking
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'fixed', 'false_positive')),
    status_updated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code search results table (Structural patterns from Comby)
CREATE TABLE codemirror_code_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES codemirror_analyses(id) ON DELETE CASCADE,
    repository_path TEXT NOT NULL,
    
    -- Search metadata
    search_duration_seconds FLOAT DEFAULT 0,
    total_matches INTEGER DEFAULT 0,
    languages_analyzed JSONB DEFAULT '[]',
    
    -- Pattern analysis
    matches_by_pattern JSONB DEFAULT '{}',
    identified_patterns JSONB DEFAULT '[]',
    
    -- Architecture insights
    architecture_insights JSONB DEFAULT '{}',
    consistency_violations JSONB DEFAULT '[]',
    
    -- Quality metrics
    pattern_diversity_score FLOAT CHECK (pattern_diversity_score >= 0 AND pattern_diversity_score <= 100),
    consistency_score FLOAT CHECK (consistency_score >= 0 AND consistency_score <= 100),
    maintainability_score FLOAT CHECK (maintainability_score >= 0 AND maintainability_score <= 100),
    
    -- Language-specific insights
    language_patterns JSONB DEFAULT '{}',
    framework_usage JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code matches table (Individual pattern matches)
CREATE TABLE codemirror_code_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_search_id UUID REFERENCES codemirror_code_searches(id) ON DELETE CASCADE,
    
    -- Match details
    pattern_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    column_number INTEGER DEFAULT 0,
    
    -- Match content
    matched_text TEXT NOT NULL,
    context_before TEXT DEFAULT '',
    context_after TEXT DEFAULT '',
    
    -- Match quality
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Refactoring opportunities table
CREATE TABLE codemirror_refactoring_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_search_id UUID REFERENCES codemirror_code_searches(id) ON DELETE CASCADE,
    
    -- Opportunity details
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    
    -- Code context
    current_code TEXT NOT NULL,
    suggested_code TEXT,
    benefits JSONB DEFAULT '[]',
    
    -- Effort estimation
    effort_estimate TEXT CHECK (effort_estimate IN ('low', 'medium', 'high')),
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    
    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'rejected')),
    status_updated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- File watch events table (Real-time monitoring)
CREATE TABLE codemirror_file_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_path TEXT NOT NULL,
    
    -- Event details
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'modified', 'deleted', 'moved')),
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_extension TEXT,
    is_source_file BOOLEAN DEFAULT FALSE,
    
    -- Batching
    batch_id TEXT,
    batch_processed BOOLEAN DEFAULT FALSE,
    
    -- Timing
    event_timestamp TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis requests table (Tracking automated analysis triggers)
CREATE TABLE codemirror_analysis_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT UNIQUE NOT NULL,
    repository_path TEXT NOT NULL,
    
    -- Request details
    analysis_types JSONB DEFAULT '[]', -- ['git', 'security', 'structural']
    priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
    trigger_source TEXT CHECK (trigger_source IN ('file_watch', 'manual', 'scheduled', 'webhook')),
    
    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Results
    analysis_id UUID REFERENCES codemirror_analyses(id),
    error_message TEXT,
    
    -- Triggering events
    trigger_events JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CLI tool execution logs table
CREATE TABLE codemirror_cli_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_request_id UUID REFERENCES codemirror_analysis_requests(id) ON DELETE CASCADE,
    
    -- Tool details
    tool_name TEXT NOT NULL CHECK (tool_name IN ('git', 'semgrep', 'comby', 'watchdog')),
    tool_version TEXT,
    command_executed TEXT,
    
    -- Execution details
    exit_code INTEGER,
    execution_time_seconds FLOAT,
    stdout_output TEXT,
    stderr_output TEXT,
    
    -- Status
    status TEXT CHECK (status IN ('success', 'error', 'timeout')),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update existing codemirror_analyses table to track CLI integration
ALTER TABLE codemirror_analyses 
ADD COLUMN IF NOT EXISTS cli_tools_used JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS cli_analysis_version TEXT DEFAULT '1.0',
ADD COLUMN IF NOT EXISTS has_git_analysis BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS has_security_scan BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS has_code_search BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS file_watch_triggered BOOLEAN DEFAULT FALSE;

-- Create indexes for performance
CREATE INDEX idx_codemirror_git_analyses_analysis ON codemirror_git_analyses(analysis_id);
CREATE INDEX idx_codemirror_git_analyses_repo_url ON codemirror_git_analyses(repository_url);
CREATE INDEX idx_codemirror_git_analyses_language ON codemirror_git_analyses(primary_language);
CREATE INDEX idx_codemirror_git_analyses_created ON codemirror_git_analyses(created_at);

CREATE INDEX idx_codemirror_security_scans_analysis ON codemirror_security_scans(analysis_id);
CREATE INDEX idx_codemirror_security_scans_path ON codemirror_security_scans(repository_path);
CREATE INDEX idx_codemirror_security_scans_score ON codemirror_security_scans(overall_security_score);
CREATE INDEX idx_codemirror_security_scans_created ON codemirror_security_scans(created_at);

CREATE INDEX idx_codemirror_security_findings_scan ON codemirror_security_findings(security_scan_id);
CREATE INDEX idx_codemirror_security_findings_severity ON codemirror_security_findings(severity);
CREATE INDEX idx_codemirror_security_findings_file ON codemirror_security_findings(file_path);
CREATE INDEX idx_codemirror_security_findings_status ON codemirror_security_findings(status);
CREATE INDEX idx_codemirror_security_findings_rule ON codemirror_security_findings(rule_id);

CREATE INDEX idx_codemirror_code_searches_analysis ON codemirror_code_searches(analysis_id);
CREATE INDEX idx_codemirror_code_searches_path ON codemirror_code_searches(repository_path);
CREATE INDEX idx_codemirror_code_searches_maintainability ON codemirror_code_searches(maintainability_score);
CREATE INDEX idx_codemirror_code_searches_created ON codemirror_code_searches(created_at);

CREATE INDEX idx_codemirror_code_matches_search ON codemirror_code_matches(code_search_id);
CREATE INDEX idx_codemirror_code_matches_pattern ON codemirror_code_matches(pattern_name);
CREATE INDEX idx_codemirror_code_matches_file ON codemirror_code_matches(file_path);
CREATE INDEX idx_codemirror_code_matches_confidence ON codemirror_code_matches(confidence_score);

CREATE INDEX idx_codemirror_refactoring_search ON codemirror_refactoring_opportunities(code_search_id);
CREATE INDEX idx_codemirror_refactoring_effort ON codemirror_refactoring_opportunities(effort_estimate);
CREATE INDEX idx_codemirror_refactoring_risk ON codemirror_refactoring_opportunities(risk_level);
CREATE INDEX idx_codemirror_refactoring_status ON codemirror_refactoring_opportunities(status);
CREATE INDEX idx_codemirror_refactoring_file ON codemirror_refactoring_opportunities(file_path);

CREATE INDEX idx_codemirror_file_events_repo ON codemirror_file_events(repository_path);
CREATE INDEX idx_codemirror_file_events_type ON codemirror_file_events(event_type);
CREATE INDEX idx_codemirror_file_events_timestamp ON codemirror_file_events(event_timestamp);
CREATE INDEX idx_codemirror_file_events_batch ON codemirror_file_events(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX idx_codemirror_file_events_processed ON codemirror_file_events(batch_processed);
CREATE INDEX idx_codemirror_file_events_source ON codemirror_file_events(is_source_file) WHERE is_source_file = TRUE;

CREATE INDEX idx_codemirror_analysis_requests_repo ON codemirror_analysis_requests(repository_path);
CREATE INDEX idx_codemirror_analysis_requests_status ON codemirror_analysis_requests(status);
CREATE INDEX idx_codemirror_analysis_requests_priority ON codemirror_analysis_requests(priority);
CREATE INDEX idx_codemirror_analysis_requests_trigger ON codemirror_analysis_requests(trigger_source);
CREATE INDEX idx_codemirror_analysis_requests_created ON codemirror_analysis_requests(created_at);

CREATE INDEX idx_codemirror_cli_executions_request ON codemirror_cli_executions(analysis_request_id);
CREATE INDEX idx_codemirror_cli_executions_tool ON codemirror_cli_executions(tool_name);
CREATE INDEX idx_codemirror_cli_executions_status ON codemirror_cli_executions(status);
CREATE INDEX idx_codemirror_cli_executions_created ON codemirror_cli_executions(created_at);

-- Add triggers for updated_at columns
CREATE TRIGGER update_codemirror_git_analyses_updated_at 
    BEFORE UPDATE ON codemirror_git_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_security_scans_updated_at 
    BEFORE UPDATE ON codemirror_security_scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codemirror_code_searches_updated_at 
    BEFORE UPDATE ON codemirror_code_searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add table comments for documentation
COMMENT ON TABLE codemirror_git_analyses IS 'Git repository analysis results using GitPython';
COMMENT ON TABLE codemirror_security_scans IS 'Security scan results using Semgrep';
COMMENT ON TABLE codemirror_security_findings IS 'Individual security vulnerabilities found by Semgrep';
COMMENT ON TABLE codemirror_code_searches IS 'Structural code search results using Comby';
COMMENT ON TABLE codemirror_code_matches IS 'Individual pattern matches found by Comby';
COMMENT ON TABLE codemirror_refactoring_opportunities IS 'Refactoring opportunities identified from code analysis';
COMMENT ON TABLE codemirror_file_events IS 'File system events from Watchdog monitoring';
COMMENT ON TABLE codemirror_analysis_requests IS 'Automated analysis requests triggered by file changes';
COMMENT ON TABLE codemirror_cli_executions IS 'CLI tool execution logs and results';

-- Add column comments for key fields
COMMENT ON COLUMN codemirror_git_analyses.commits_by_hour IS 'Histogram of commits by hour of day (0-23)';
COMMENT ON COLUMN codemirror_git_analyses.author_collaboration IS 'Network of authors who collaborate on same files';
COMMENT ON COLUMN codemirror_git_analyses.hotspot_files IS 'Files with high change frequency and size';
COMMENT ON COLUMN codemirror_git_analyses.technical_debt_indicators IS 'Commits indicating technical debt';

COMMENT ON COLUMN codemirror_security_scans.overall_security_score IS 'Overall security score (0-100, higher is better)';
COMMENT ON COLUMN codemirror_security_scans.owasp_compliance_score IS 'OWASP Top 10 compliance score (0-100)';
COMMENT ON COLUMN codemirror_security_scans.security_hotspots IS 'Files with multiple vulnerability types';

COMMENT ON COLUMN codemirror_code_searches.pattern_diversity_score IS 'Diversity of patterns found (0-100)';
COMMENT ON COLUMN codemirror_code_searches.consistency_score IS 'Code consistency score (0-100)';
COMMENT ON COLUMN codemirror_code_searches.maintainability_score IS 'Overall maintainability score (0-100)';

COMMENT ON COLUMN codemirror_file_events.batch_id IS 'Groups related file events for batch processing';
COMMENT ON COLUMN codemirror_file_events.is_source_file IS 'Whether file is a source code file';

COMMENT ON COLUMN codemirror_analysis_requests.analysis_types IS 'JSON array of analysis types to run';
COMMENT ON COLUMN codemirror_analysis_requests.trigger_events IS 'File events that triggered this analysis';

-- Create a view for comprehensive analysis overview
CREATE VIEW codemirror_analysis_overview AS
SELECT 
    a.id,
    a.repo_id,
    a.analysis_type,
    a.analysis_depth,
    a.security_score,
    a.performance_score,
    a.quality_score,
    a.analysis_completed_at,
    
    -- Git analysis summary
    g.total_commits,
    g.total_authors,
    g.primary_language,
    g.average_commit_size,
    
    -- Security scan summary
    s.overall_security_score,
    s.owasp_compliance_score,
    s.total_findings,
    
    -- Code search summary
    cs.pattern_diversity_score,
    cs.consistency_score,
    cs.maintainability_score,
    cs.total_matches,
    
    -- CLI integration status
    a.cli_tools_used,
    a.has_git_analysis,
    a.has_security_scan,
    a.has_code_search,
    a.file_watch_triggered,
    
    a.created_at,
    a.updated_at
    
FROM codemirror_analyses a
LEFT JOIN codemirror_git_analyses g ON a.id = g.analysis_id
LEFT JOIN codemirror_security_scans s ON a.id = s.analysis_id
LEFT JOIN codemirror_code_searches cs ON a.id = cs.analysis_id;

COMMENT ON VIEW codemirror_analysis_overview IS 'Comprehensive view of all analysis results with CLI integration status';