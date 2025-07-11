-- Migration: Add AI Enhancement Fields to PRSNL
-- Version: 4.2.0
-- Date: 2025-07-11
-- Description: Adds fields for Guardrails-AI validation and whisper.cpp transcription

-- Add new AI processing fields
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS ai_processing_version TEXT DEFAULT '4.2.0',
ADD COLUMN IF NOT EXISTS detailed_summary TEXT,
ADD COLUMN IF NOT EXISTS transcription_confidence FLOAT,
ADD COLUMN IF NOT EXISTS transcription_model TEXT,
ADD COLUMN IF NOT EXISTS transcription_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS transcription_segments JSONB,
ADD COLUMN IF NOT EXISTS key_points TEXT[],
ADD COLUMN IF NOT EXISTS difficulty_level TEXT,
ADD COLUMN IF NOT EXISTS reading_time INTEGER,
ADD COLUMN IF NOT EXISTS entities JSONB;

-- Add constraints for validated fields
ALTER TABLE items 
DROP CONSTRAINT IF EXISTS chk_sentiment,
ADD CONSTRAINT chk_sentiment CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed') OR sentiment IS NULL);

ALTER TABLE items
DROP CONSTRAINT IF EXISTS chk_difficulty,
ADD CONSTRAINT chk_difficulty CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced') OR difficulty_level IS NULL);

-- Ensure category constraint includes all valid values
ALTER TABLE items
DROP CONSTRAINT IF EXISTS chk_category,
ADD CONSTRAINT chk_category CHECK (category IN ('technology', 'business', 'science', 'health', 'education', 'entertainment', 'news', 'personal', 'other') OR category IS NULL);

-- Create AI processing log table
CREATE TABLE IF NOT EXISTS ai_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    
    -- Processing details
    service_type TEXT NOT NULL CHECK (service_type IN ('analysis', 'transcription', 'summary', 'tags', 'embedding')),
    service_used TEXT NOT NULL,
    model_version TEXT,
    
    -- Performance metrics
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Validation
    validation_passed BOOLEAN DEFAULT TRUE,
    validation_errors JSONB,
    
    -- Request/Response
    request_params JSONB,
    response_data JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_log_item_id ON ai_processing_log(item_id);
CREATE INDEX IF NOT EXISTS idx_ai_log_service ON ai_processing_log(service_type, created_at);
CREATE INDEX IF NOT EXISTS idx_items_ai_processed ON items(ai_processed_at) WHERE ai_processed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_transcription ON items(id) WHERE transcription IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_difficulty ON items(difficulty_level) WHERE difficulty_level IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_key_points ON items USING gin(key_points) WHERE key_points IS NOT NULL;

-- Full-text search index on AI-generated content
CREATE INDEX IF NOT EXISTS idx_items_ai_search ON items USING gin(
    to_tsvector('english', 
        COALESCE(ai_title, '') || ' ' || 
        COALESCE(ai_summary, '') || ' ' || 
        COALESCE(detailed_summary, '') || ' ' ||
        COALESCE(transcription, '')
    )
);

-- Create content quality metrics table
CREATE TABLE IF NOT EXISTS content_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE UNIQUE,
    
    -- Quality scores
    transcription_confidence FLOAT CHECK (transcription_confidence >= 0 AND transcription_confidence <= 1),
    summary_quality_score FLOAT CHECK (summary_quality_score >= 0 AND summary_quality_score <= 1),
    tag_relevance_score FLOAT CHECK (tag_relevance_score >= 0 AND tag_relevance_score <= 1),
    overall_quality_score FLOAT CHECK (overall_quality_score >= 0 AND overall_quality_score <= 1),
    
    -- Validation metrics
    validation_failures INTEGER DEFAULT 0,
    required_repairs INTEGER DEFAULT 0,
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    
    -- Metadata
    evaluated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for quality metrics
CREATE INDEX IF NOT EXISTS idx_quality_item_id ON content_quality_metrics(item_id);
CREATE INDEX IF NOT EXISTS idx_quality_score ON content_quality_metrics(overall_quality_score);

-- Update existing NULL categories to 'other'
UPDATE items SET category = 'other' WHERE category IS NULL AND type IS NOT NULL;

-- Update function to calculate overall quality score
CREATE OR REPLACE FUNCTION update_overall_quality_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.overall_quality_score = (
        COALESCE(NEW.transcription_confidence, 0.5) * 0.3 +
        COALESCE(NEW.summary_quality_score, 0.5) * 0.4 +
        COALESCE(NEW.tag_relevance_score, 0.5) * 0.3
    );
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for quality score updates
DROP TRIGGER IF EXISTS update_quality_score_trigger ON content_quality_metrics;
CREATE TRIGGER update_quality_score_trigger
BEFORE INSERT OR UPDATE ON content_quality_metrics
FOR EACH ROW
EXECUTE FUNCTION update_overall_quality_score();

-- Add comments for documentation
COMMENT ON TABLE ai_processing_log IS 'Tracks all AI processing operations for monitoring and debugging';
COMMENT ON TABLE content_quality_metrics IS 'Stores quality metrics for AI-generated content';
COMMENT ON COLUMN items.ai_processing_version IS 'Version of AI processing pipeline used';
COMMENT ON COLUMN items.transcription_segments IS 'Word-level timestamps and segments from whisper.cpp';
COMMENT ON COLUMN items.entities IS 'Extracted entities: people, organizations, technologies, concepts';

-- Grant permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON ai_processing_log TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON content_quality_metrics TO your_app_user;