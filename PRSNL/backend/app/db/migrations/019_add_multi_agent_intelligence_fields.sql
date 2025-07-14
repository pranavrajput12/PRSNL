-- Migration: Add Multi-Agent Intelligence Fields
-- This migration adds fields to store outputs from specialized conversation intelligence agents

-- Add specialized agent output fields to ai_conversation_imports
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS technical_content JSONB DEFAULT '{}';
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS learning_analysis JSONB DEFAULT '{}';
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS actionable_insights JSONB DEFAULT '{}';
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS knowledge_gap_analysis JSONB DEFAULT '{}';

-- Add agent processing metadata
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS agent_processing_version VARCHAR(20) DEFAULT 'v2.0';
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS agents_used TEXT[] DEFAULT ARRAY['technical', 'learning', 'insights', 'gaps'];
ALTER TABLE ai_conversation_imports ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER;

-- Update existing records to have the new agent structure
UPDATE ai_conversation_imports 
SET agent_processing_version = 'v2.0',
    agents_used = ARRAY['technical', 'learning', 'insights', 'gaps']
WHERE agent_processing_version IS NULL;

-- Add indexes for the new JSONB fields
CREATE INDEX IF NOT EXISTS idx_ai_conversations_technical_content ON ai_conversation_imports USING GIN(technical_content);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_learning_analysis ON ai_conversation_imports USING GIN(learning_analysis);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_actionable_insights ON ai_conversation_imports USING GIN(actionable_insights);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_knowledge_gaps ON ai_conversation_imports USING GIN(knowledge_gap_analysis);

-- Update the search vector function to include new agent fields
CREATE OR REPLACE FUNCTION update_ai_conversation_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.platform, '') || ' ' ||
        COALESCE(NEW.neural_category, '') || ' ' ||
        COALESCE(NEW.neural_subcategory, '') || ' ' ||
        COALESCE(NEW.summary, '') || ' ' ||
        COALESCE(array_to_string(NEW.key_topics, ' '), '') || ' ' ||
        COALESCE(array_to_string(NEW.learning_points, ' '), '') || ' ' ||
        COALESCE(NEW.technical_content->>'technologies', '') || ' ' ||
        COALESCE(NEW.actionable_insights->>'immediate_actions', '') || ' ' ||
        COALESCE(NEW.knowledge_gap_analysis->>'gaps', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON COLUMN ai_conversation_imports.technical_content IS 'Output from TechnicalContentExtractor agent: code snippets, technologies, implementation patterns';
COMMENT ON COLUMN ai_conversation_imports.learning_analysis IS 'Output from LearningJourneyAnalyzer agent: learning stages, breakthrough moments, knowledge evolution';
COMMENT ON COLUMN ai_conversation_imports.actionable_insights IS 'Output from ActionableInsightsExtractor agent: immediate actions, implementation steps, tools and resources';
COMMENT ON COLUMN ai_conversation_imports.knowledge_gap_analysis IS 'Output from KnowledgeGapIdentifier agent: knowledge gaps, learning opportunities, prerequisites';
COMMENT ON COLUMN ai_conversation_imports.agent_processing_version IS 'Version of the multi-agent system that processed this conversation';
COMMENT ON COLUMN ai_conversation_imports.agents_used IS 'List of specialized agents that analyzed this conversation';
COMMENT ON COLUMN ai_conversation_imports.processing_time_ms IS 'Total processing time in milliseconds for all agents';