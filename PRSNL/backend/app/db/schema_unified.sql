-- PRSNL Unified Database Schema
-- This consolidates ALL migrations and fixes column name mismatches
-- Single source of truth for database structure

CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- CORE TABLES
-- ========================================

-- Main items table (consolidates all column requirements)
CREATE TABLE IF NOT EXISTS items (
    -- Core fields
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT, -- Made nullable per migration 007_make_url_nullable.sql
    title TEXT NOT NULL,
    summary TEXT,
    raw_content TEXT,
    processed_content TEXT,
    
    -- Type and status fields  
    type VARCHAR(50) NOT NULL DEFAULT 'bookmark', -- Standardized to 'type' (was type in some migrations)
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Content classification (from enable_summarization feature)
    content_type VARCHAR(50) DEFAULT 'auto',
    enable_summarization BOOLEAN DEFAULT false,
    
    -- Video/media fields (from video support migrations)
    platform VARCHAR(50),
    duration INTEGER,
    video_url TEXT,
    file_path TEXT,
    thumbnail_url TEXT,
    
    -- File support fields (from add_file_support.sql)
    has_files BOOLEAN DEFAULT FALSE,
    file_count INTEGER DEFAULT 0,
    
    -- User highlight field (from frontend)
    highlight TEXT,
    
    -- Metadata and search
    metadata JSONB DEFAULT '{}',
    search_vector tsvector,
    
    -- Embedding support (from migration 003)
    embedding vector(1536),
    
    -- Transcription support (from migration 004)
    transcription TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT items_url_or_content_check CHECK (url IS NOT NULL OR raw_content IS NOT NULL),
    CONSTRAINT chk_content_type CHECK (content_type IN ('auto', 'document', 'video', 'article', 'tutorial', 'image', 'note', 'link')),
    CONSTRAINT chk_item_type CHECK (type IN ('article', 'video', 'note', 'bookmark', 'document', 'tutorial', 'image', 'link'))
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    color VARCHAR(7), -- Hex color code
    description TEXT,
    parent_id UUID REFERENCES tags(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Many-to-many relationship between items and tags
CREATE TABLE IF NOT EXISTS item_tags (
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (item_id, tag_id)
);

-- ========================================
-- FILE SUPPORT TABLES
-- ========================================

-- Files table (from add_file_support.sql)
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    file_category VARCHAR(20) NOT NULL, -- 'document', 'image', 'pdf', 'office', 'text'
    
    -- Extracted content
    extracted_text TEXT,
    text_file_path TEXT,
    word_count INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0,
    extraction_method VARCHAR(50),
    
    -- Image-specific fields
    thumbnail_path TEXT,
    image_width INTEGER,
    image_height INTEGER,
    
    -- Processing metadata
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    processing_error TEXT,
    processed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Attachments table (consolidated from multiple migrations)
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE, -- Link to files table
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    file_size BIGINT,
    thumbnail_path TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- File processing log table
CREATE TABLE IF NOT EXISTS file_processing_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    processing_step VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'started', 'completed', 'failed'
    message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================
-- BACKGROUND PROCESSING TABLES
-- ========================================

-- Jobs table for background processing
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    payload JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ========================================
-- AUTHENTICATION & SECURITY TABLES  
-- ========================================

-- User sessions table (for future auth)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID, -- Will reference users table when created
    ip_address INET,
    user_agent TEXT,
    user_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- API keys table (for API access)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

-- Audit log table (for security)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Items table indexes
CREATE INDEX IF NOT EXISTS idx_items_search ON items USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_items_created ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_updated ON items(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_accessed ON items(accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_content_type ON items(content_type);
CREATE INDEX IF NOT EXISTS idx_items_url ON items(url) WHERE url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_platform ON items(platform) WHERE platform IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_has_files ON items(has_files) WHERE has_files = true;

-- Tags table indexes
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_parent ON tags(parent_id) WHERE parent_id IS NOT NULL;

-- Item tags indexes
CREATE INDEX IF NOT EXISTS idx_item_tags_item_id ON item_tags(item_id);
CREATE INDEX IF NOT EXISTS idx_item_tags_tag_id ON item_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_item_tags_created ON item_tags(created_at DESC);

-- Files table indexes
CREATE INDEX IF NOT EXISTS idx_files_item_id ON files(item_id);
CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash);
CREATE INDEX IF NOT EXISTS idx_files_file_category ON files(file_category);
CREATE INDEX IF NOT EXISTS idx_files_processing_status ON files(processing_status);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);

-- Attachments table indexes
CREATE INDEX IF NOT EXISTS idx_attachments_item_id ON attachments(item_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file_id ON attachments(file_id) WHERE file_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_attachments_file_type ON attachments(file_type);

-- Jobs table indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_item_id ON jobs(item_id) WHERE item_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled ON jobs(scheduled_for) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);

-- Authentication table indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ========================================
-- FUNCTIONS AND TRIGGERS
-- ========================================

-- Update search vector function
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.processed_content, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update updated_at function
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Notification function for background processing
CREATE OR REPLACE FUNCTION notify_item_created() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('item_created', NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update file count in items
CREATE OR REPLACE FUNCTION update_item_file_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE items 
        SET file_count = file_count + 1,
            has_files = TRUE
        WHERE id = NEW.item_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE items 
        SET file_count = GREATEST(file_count - 1, 0),
            has_files = (file_count - 1 > 0)
        WHERE id = OLD.item_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Auto-set item type function
CREATE OR REPLACE FUNCTION set_item_type() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type IS NULL OR NEW.type = 'bookmark' THEN
        IF NEW.url LIKE '%instagram.com%' OR 
           NEW.url LIKE '%youtube.com%' OR 
           NEW.url LIKE '%youtu.be%' OR
           NEW.url LIKE '%tiktok.com%' THEN
            NEW.type = 'video';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- TRIGGERS
-- ========================================

-- Search vector update trigger
DROP TRIGGER IF EXISTS items_search_vector_update ON items;
CREATE TRIGGER items_search_vector_update
    BEFORE INSERT OR UPDATE OF title, summary, processed_content
    ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Updated at triggers
DROP TRIGGER IF EXISTS items_updated_at ON items;
CREATE TRIGGER items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS tags_updated_at ON tags;
CREATE TRIGGER tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS files_updated_at ON files;
CREATE TRIGGER files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS jobs_updated_at ON jobs;
CREATE TRIGGER jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Notification trigger
DROP TRIGGER IF EXISTS items_notify_created ON items;
CREATE TRIGGER items_notify_created
    AFTER INSERT ON items
    FOR EACH ROW
    EXECUTE FUNCTION notify_item_created();

-- File count update trigger
DROP TRIGGER IF EXISTS trigger_update_item_file_count ON files;
CREATE TRIGGER trigger_update_item_file_count
    AFTER INSERT OR DELETE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_item_file_count();

-- Auto-set item type trigger
DROP TRIGGER IF EXISTS items_set_type ON items;
CREATE TRIGGER items_set_type
    BEFORE INSERT OR UPDATE OF url
    ON items
    FOR EACH ROW
    EXECUTE FUNCTION set_item_type();

-- ========================================
-- VIEWS FOR ANALYTICS
-- ========================================

-- Video items view
CREATE OR REPLACE VIEW video_items AS
SELECT 
    i.*,
    a.file_path as attachment_path,
    a.file_size,
    a.metadata as attachment_metadata
FROM items i
LEFT JOIN attachments a ON i.id = a.item_id AND a.file_type = 'video'
WHERE i.type = 'video';

-- File storage statistics view
CREATE OR REPLACE VIEW file_storage_stats AS
SELECT 
    file_category,
    COUNT(*) as file_count,
    SUM(file_size) as total_size_bytes,
    ROUND(SUM(file_size) / 1024.0 / 1024.0, 2) as total_size_mb,
    AVG(file_size) as avg_size_bytes,
    MIN(created_at) as first_file_date,
    MAX(created_at) as last_file_date
FROM files
GROUP BY file_category;

-- Recent files view
CREATE OR REPLACE VIEW recent_files AS
SELECT 
    f.id,
    f.item_id,
    f.original_filename,
    f.file_category,
    f.file_size,
    f.processing_status,
    f.created_at,
    i.title as item_title,
    i.url as item_url,
    CASE 
        WHEN f.word_count > 0 THEN f.word_count
        ELSE 0
    END as word_count
FROM files f
JOIN items i ON f.item_id = i.id
ORDER BY f.created_at DESC;