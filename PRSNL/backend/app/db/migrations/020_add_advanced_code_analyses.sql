-- Migration: Add advanced code analyses table for Phase 5
-- Purpose: Store AI-powered code analysis results with quality scores and recommendations
-- Date: 2025-07-23

-- 1. Advanced code analyses table
CREATE TABLE IF NOT EXISTS advanced_code_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES github_repos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL DEFAULT 'comprehensive', -- comprehensive, security, performance, quality, architecture
    analysis_depth VARCHAR(20) NOT NULL DEFAULT 'standard', -- quick, standard, deep
    
    -- Analysis results
    results JSONB NOT NULL DEFAULT '{}',
    quality_scores JSONB NOT NULL DEFAULT '{}',
    ai_insights JSONB NOT NULL DEFAULT '{}',
    recommendations JSONB NOT NULL DEFAULT '[]',
    
    -- Processing metadata
    processing_stats JSONB NOT NULL DEFAULT '{}',
    analysis_config JSONB NOT NULL DEFAULT '{}',
    
    -- Status and timestamps
    status VARCHAR(20) NOT NULL DEFAULT 'completed', -- pending, processing, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_analysis_type CHECK (analysis_type IN ('comprehensive', 'security', 'performance', 'quality', 'architecture')),
    CONSTRAINT valid_analysis_depth CHECK (analysis_depth IN ('quick', 'standard', 'deep')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 2. Multi-modal analysis sessions table
CREATE TABLE IF NOT EXISTS multimodal_analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Content data
    content_data JSONB NOT NULL DEFAULT '{}',
    modalities_processed TEXT[] NOT NULL DEFAULT '{}',
    analysis_depth VARCHAR(20) NOT NULL DEFAULT 'standard',
    
    -- Results
    cross_modal_insights JSONB NOT NULL DEFAULT '{}',
    unified_understanding JSONB NOT NULL DEFAULT '{}',
    recommendations JSONB NOT NULL DEFAULT '[]',
    
    -- Processing metadata
    processing_stats JSONB NOT NULL DEFAULT '{}',
    
    -- Status and timestamps
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_multimodal_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_multimodal_depth CHECK (analysis_depth IN ('quick', 'standard', 'comprehensive'))
);

-- 3. Natural language command logs table
CREATE TABLE IF NOT EXISTS natural_language_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Command data
    original_command TEXT NOT NULL,
    parsed_command JSONB NOT NULL DEFAULT '{}',
    user_context JSONB NOT NULL DEFAULT '{}',
    multimodal_context JSONB NOT NULL DEFAULT '{}',
    
    -- Execution results
    execution_result JSONB NOT NULL DEFAULT '{}',
    natural_response JSONB NOT NULL DEFAULT '{}',
    
    -- Processing metadata
    processing_stats JSONB NOT NULL DEFAULT '{}',
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    
    -- Status and timestamps
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_nl_status CHECK (status IN ('success', 'failed', 'needs_clarification')),
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_advanced_code_analyses_repo_id ON advanced_code_analyses(repo_id);
CREATE INDEX IF NOT EXISTS idx_advanced_code_analyses_user_id ON advanced_code_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_advanced_code_analyses_type ON advanced_code_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_advanced_code_analyses_created_at ON advanced_code_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_advanced_code_analyses_status ON advanced_code_analyses(status);

CREATE INDEX IF NOT EXISTS idx_multimodal_sessions_user_id ON multimodal_analysis_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_multimodal_sessions_session_id ON multimodal_analysis_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_multimodal_sessions_created_at ON multimodal_analysis_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_multimodal_sessions_modalities ON multimodal_analysis_sessions USING GIN(modalities_processed);

CREATE INDEX IF NOT EXISTS idx_nl_commands_user_id ON natural_language_commands(user_id);
CREATE INDEX IF NOT EXISTS idx_nl_commands_command_id ON natural_language_commands(command_id);
CREATE INDEX IF NOT EXISTS idx_nl_commands_created_at ON natural_language_commands(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nl_commands_confidence ON natural_language_commands(confidence_score DESC);

-- 5. Add updated_at trigger for advanced_code_analyses
CREATE TRIGGER update_advanced_code_analyses_updated_at 
    BEFORE UPDATE ON advanced_code_analyses
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_multimodal_sessions_updated_at 
    BEFORE UPDATE ON multimodal_analysis_sessions
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 6. Add some sample data for testing (optional)
-- This can be removed in production
INSERT INTO advanced_code_analyses (
    repo_id, analysis_type, results, quality_scores, processing_stats, status
) 
SELECT 
    gr.id,
    'comprehensive',
    '{"ai_insights": {"architecture": {"score": 0.85}}, "code_metrics": {"complexity": 8.5}}',
    '{"overall": 0.78, "security": 0.82, "performance": 0.75, "quality": 0.80}',
    '{"duration_ms": 15000, "files_analyzed": 150, "lines_of_code": 12500}',
    'completed'
FROM github_repos gr
LIMIT 3
ON CONFLICT DO NOTHING;

-- Migration tracking
INSERT INTO migrations (version, name, applied_at)
VALUES (20, 'add_advanced_code_analyses', NOW())
ON CONFLICT (version) DO NOTHING;