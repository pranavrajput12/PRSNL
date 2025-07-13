-- Migration: Rename AI Conversation tables to avoid conflict with chat conversations
-- This properly separates imported AI conversations from PRSNL's chat feature

-- Drop the old tables if they exist (from our previous attempt)
DROP TABLE IF EXISTS conversation_items CASCADE;
DROP TABLE IF EXISTS conversation_messages CASCADE; 
DROP TABLE IF EXISTS conversations CASCADE;

-- Create AI conversation imports table with better naming
CREATE TABLE IF NOT EXISTS ai_conversation_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Platform and source information
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('chatgpt', 'claude', 'perplexity', 'bard', 'gemini', 'other')),
    source_url TEXT NOT NULL,
    extension_id VARCHAR(255) NOT NULL, -- ID from the extension
    
    -- Core conversation data
    title TEXT NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    
    -- Timestamps
    conversation_date TIMESTAMPTZ NOT NULL, -- When the conversation originally happened
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Stats
    message_count INTEGER NOT NULL DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    assistant_message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- AI-powered analysis (populated by our agent)
    summary TEXT, -- AI-generated summary
    key_topics TEXT[], -- Extracted topics
    learning_points TEXT[], -- What the user learned
    user_journey TEXT, -- How user's understanding evolved
    knowledge_gaps TEXT[], -- Identified gaps in understanding
    
    -- Neural categorization
    neural_category VARCHAR(50) CHECK (neural_category IN ('learning', 'development', 'thoughts', 'reference', 'creative', 'problem-solving')),
    neural_subcategory VARCHAR(50),
    categorization_confidence FLOAT CHECK (categorization_confidence >= 0 AND categorization_confidence <= 1),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Permalinks - using simple /conversations/{platform}/{slug} format
    permalink VARCHAR(255) UNIQUE,
    
    -- Standard timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS ai_conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES ai_conversation_imports(id) ON DELETE CASCADE,
    
    -- Message identification
    original_message_id VARCHAR(255) NOT NULL, -- ID from the platform
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    sequence_number INTEGER NOT NULL, -- Order within conversation
    
    -- Content in multiple formats (from extension)
    content_text TEXT NOT NULL,
    content_html TEXT,
    content_markdown TEXT,
    
    -- AI analysis (populated by our agent)
    summary TEXT, -- One-line summary of this message
    key_points TEXT[], -- Main points from this message
    concepts_introduced TEXT[], -- New concepts in this message
    questions_asked TEXT[], -- Questions posed
    
    -- Metadata
    timestamp TIMESTAMPTZ NOT NULL,
    token_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique messages within a conversation
    CONSTRAINT unique_conversation_message UNIQUE (conversation_id, original_message_id)
);

-- Link to items table for unified search
CREATE TABLE IF NOT EXISTS ai_conversation_search_items (
    conversation_id UUID NOT NULL REFERENCES ai_conversation_imports(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    PRIMARY KEY (conversation_id, item_id)
);

-- Indexes for performance
CREATE INDEX idx_ai_conversations_platform ON ai_conversation_imports(platform);
CREATE INDEX idx_ai_conversations_slug ON ai_conversation_imports(slug);
CREATE INDEX idx_ai_conversations_neural ON ai_conversation_imports(neural_category, neural_subcategory);
CREATE INDEX idx_ai_conversations_imported_at ON ai_conversation_imports(imported_at DESC);
CREATE INDEX idx_ai_conversations_date ON ai_conversation_imports(conversation_date DESC);
CREATE INDEX idx_ai_conversations_status ON ai_conversation_imports(processing_status);
CREATE INDEX idx_ai_messages_conversation ON ai_conversation_messages(conversation_id);
CREATE INDEX idx_ai_messages_sequence ON ai_conversation_messages(conversation_id, sequence_number);
CREATE INDEX idx_ai_messages_role ON ai_conversation_messages(conversation_id, role);

-- Full text search
ALTER TABLE ai_conversation_imports ADD COLUMN search_vector tsvector;
CREATE INDEX idx_ai_conversations_search ON ai_conversation_imports USING GIN(search_vector);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION update_ai_conversation_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.platform, '') || ' ' ||
        COALESCE(NEW.neural_category, '') || ' ' ||
        COALESCE(NEW.neural_subcategory, '') || ' ' ||
        COALESCE(NEW.summary, '') || ' ' ||
        COALESCE(array_to_string(NEW.key_topics, ' '), '') || ' ' ||
        COALESCE(array_to_string(NEW.learning_points, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_conversation_search_vector_trigger
    BEFORE INSERT OR UPDATE ON ai_conversation_imports
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_conversation_search_vector();

-- Function to update conversation stats after messages are inserted
CREATE OR REPLACE FUNCTION update_ai_conversation_stats() RETURNS trigger AS $$
BEGIN
    UPDATE ai_conversation_imports 
    SET 
        message_count = (SELECT COUNT(*) FROM ai_conversation_messages WHERE conversation_id = COALESCE(NEW.conversation_id, OLD.conversation_id)),
        user_message_count = (SELECT COUNT(*) FROM ai_conversation_messages WHERE conversation_id = COALESCE(NEW.conversation_id, OLD.conversation_id) AND role = 'user'),
        assistant_message_count = (SELECT COUNT(*) FROM ai_conversation_messages WHERE conversation_id = COALESCE(NEW.conversation_id, OLD.conversation_id) AND role = 'assistant'),
        total_tokens = (SELECT COALESCE(SUM(token_count), 0) FROM ai_conversation_messages WHERE conversation_id = COALESCE(NEW.conversation_id, OLD.conversation_id)),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.conversation_id, OLD.conversation_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ai_conversation_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON ai_conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_conversation_stats();

-- Updated_at trigger
CREATE TRIGGER update_ai_conversations_updated_at
    BEFORE UPDATE ON ai_conversation_imports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE ai_conversation_imports IS 'Stores AI chat conversations imported from various platforms via Chrome extension';
COMMENT ON TABLE ai_conversation_messages IS 'Individual messages within an AI conversation';
COMMENT ON TABLE ai_conversation_search_items IS 'Links conversations to items for unified search';
COMMENT ON COLUMN ai_conversation_imports.extension_id IS 'Unique ID from the Chrome extension to prevent duplicates';
COMMENT ON COLUMN ai_conversation_imports.neural_category IS 'PRSNL neural categorization: learning, development, thoughts, reference, creative, problem-solving';
COMMENT ON COLUMN ai_conversation_imports.permalink IS 'PRSNL permalink in format: /conversations/{platform}/{slug}';
COMMENT ON COLUMN ai_conversation_imports.summary IS 'AI-generated comprehensive summary of the entire conversation';
COMMENT ON COLUMN ai_conversation_imports.user_journey IS 'AI analysis of how the user''s understanding evolved during the conversation';