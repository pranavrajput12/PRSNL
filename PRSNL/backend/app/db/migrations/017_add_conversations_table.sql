-- Migration: Add AI Chat Conversations Support for Neural Echo
-- This migration creates tables to store imported AI chat conversations from ChatGPT, Claude, Perplexity, etc.

-- Main conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('chatgpt', 'claude', 'perplexity', 'bard', 'other')),
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    timestamp TIMESTAMPTZ NOT NULL, -- When the conversation originally happened
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message_count INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER DEFAULT 0, -- Total tokens in conversation
    metadata JSONB DEFAULT '{}', -- Platform-specific metadata
    
    -- Neural categorization
    neural_category VARCHAR(50) CHECK (neural_category IN ('learning', 'development', 'thoughts', 'reference', 'creative')),
    neural_subcategory VARCHAR(50),
    categorization_confidence FLOAT CHECK (categorization_confidence >= 0 AND categorization_confidence <= 1),
    
    -- Permalinks
    permalink VARCHAR(255) UNIQUE,
    
    -- Standard timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique conversations per platform
    CONSTRAINT unique_platform_url UNIQUE (platform, source_url)
);

-- Conversation messages table
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id VARCHAR(255) NOT NULL, -- Original message ID from platform
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content_text TEXT NOT NULL,
    content_html TEXT, -- Original HTML if available
    content_markdown TEXT, -- Converted markdown
    timestamp TIMESTAMPTZ NOT NULL,
    sequence_number INTEGER NOT NULL, -- Order within conversation
    token_count INTEGER DEFAULT 0, -- Approximate token count
    metadata JSONB DEFAULT '{}', -- Message-specific metadata (e.g., model used)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure unique messages within a conversation
    CONSTRAINT unique_conversation_message UNIQUE (conversation_id, message_id)
);

-- Link conversations to items table for unified search
CREATE TABLE IF NOT EXISTS conversation_items (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    PRIMARY KEY (conversation_id, item_id)
);

-- Create indexes for performance
CREATE INDEX idx_conversations_platform ON conversations(platform);
CREATE INDEX idx_conversations_slug ON conversations(slug);
CREATE INDEX idx_conversations_neural ON conversations(neural_category, neural_subcategory);
CREATE INDEX idx_conversations_imported_at ON conversations(imported_at DESC);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);
CREATE INDEX idx_conversation_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_conversation_messages_sequence ON conversation_messages(conversation_id, sequence_number);

-- Full text search on conversations
ALTER TABLE conversations ADD COLUMN search_vector tsvector;
CREATE INDEX idx_conversations_search ON conversations USING GIN(search_vector);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION update_conversation_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.platform, '') || ' ' ||
        COALESCE(NEW.neural_category, '') || ' ' ||
        COALESCE(NEW.neural_subcategory, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversation_search_vector_trigger
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_search_vector();

-- Function to update conversation metadata after messages are inserted
CREATE OR REPLACE FUNCTION update_conversation_stats() RETURNS trigger AS $$
BEGIN
    UPDATE conversations 
    SET 
        message_count = (SELECT COUNT(*) FROM conversation_messages WHERE conversation_id = NEW.conversation_id),
        total_tokens = (SELECT COALESCE(SUM(token_count), 0) FROM conversation_messages WHERE conversation_id = NEW.conversation_id),
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_stats();

-- Add updated_at trigger
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Stores imported AI chat conversations from various platforms';
COMMENT ON TABLE conversation_messages IS 'Individual messages within a conversation';
COMMENT ON TABLE conversation_items IS 'Links conversations to items for unified search';
COMMENT ON COLUMN conversations.neural_category IS 'PRSNL neural categorization: learning, development, thoughts, reference, creative';
COMMENT ON COLUMN conversations.permalink IS 'PRSNL permalink in format: /neural-echo/{platform}/{slug}';