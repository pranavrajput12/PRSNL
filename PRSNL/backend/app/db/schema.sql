CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main items table
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    raw_content TEXT,
    processed_content TEXT,
    type VARCHAR(50) NOT NULL DEFAULT 'bookmark',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    search_vector tsvector,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    embedding vector(1536),
    transcription TEXT,
    content_type VARCHAR(50) DEFAULT 'auto',
    enable_summarization BOOLEAN DEFAULT false,
    video_url TEXT,
    platform VARCHAR(50),
    duration INTEGER,
    file_path TEXT,
    thumbnail_url TEXT,
    highlight TEXT
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Many-to-many relationship
CREATE TABLE IF NOT EXISTS item_tags (
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    PRIMARY KEY (item_id, tag_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_items_search ON items USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_accessed ON items(accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_url ON items(url);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Update trigger for search vector
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.processed_content, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS items_search_vector_update ON items;
CREATE TRIGGER items_search_vector_update
    BEFORE INSERT OR UPDATE OF title, summary, processed_content
    ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS items_updated_at ON items;
CREATE TRIGGER items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Notification function for background processing
CREATE OR REPLACE FUNCTION notify_item_created() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('item_created', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for notifications
DROP TRIGGER IF EXISTS items_notify_created ON items;
CREATE TRIGGER items_notify_created
    AFTER INSERT ON items
    FOR EACH ROW
    EXECUTE FUNCTION notify_item_created();