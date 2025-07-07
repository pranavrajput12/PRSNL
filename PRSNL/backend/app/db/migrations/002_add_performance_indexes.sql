-- Migration: Add performance indexes for PRSNL
-- This migration adds additional indexes to improve query performance

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_items_status_created 
    ON items(status, created_at DESC) 
    WHERE status IN ('completed', 'pending', 'failed');

-- Index for filtering by item_type (stored in metadata)
CREATE INDEX IF NOT EXISTS idx_items_item_type 
    ON items((metadata->>'item_type'));

-- Index for platform filtering (for video items)
CREATE INDEX IF NOT EXISTS idx_items_platform 
    ON items((metadata->>'platform')) 
    WHERE metadata->>'platform' IS NOT NULL;

-- Composite index for tag queries
CREATE INDEX IF NOT EXISTS idx_item_tags_tag_item 
    ON item_tags(tag_id, item_id);

-- Index for high confidence tags
CREATE INDEX IF NOT EXISTS idx_item_tags_confidence 
    ON item_tags(confidence DESC) 
    WHERE confidence > 0.8;

-- Index for URL prefix searches (for domain filtering)
CREATE INDEX IF NOT EXISTS idx_items_url_prefix 
    ON items(url text_pattern_ops);

-- Index for title searches
CREATE INDEX IF NOT EXISTS idx_items_title_trgm 
    ON items USING gin(title gin_trgm_ops);

-- Partial index for bookmarks
CREATE INDEX IF NOT EXISTS idx_items_bookmarks 
    ON items(created_at DESC) 
    WHERE status = 'bookmark';

-- Index for access patterns (frequently accessed items)
CREATE INDEX IF NOT EXISTS idx_items_popular 
    ON items(access_count DESC, accessed_at DESC) 
    WHERE access_count > 0;

-- Index for embedding similarity searches
CREATE INDEX IF NOT EXISTS idx_items_embedding 
    ON items USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100)
    WHERE embedding IS NOT NULL;

-- Index for recent items with specific tags (via JOIN)
CREATE INDEX IF NOT EXISTS idx_items_recent_tagged 
    ON items(created_at DESC) 
    WHERE id IN (SELECT DISTINCT item_id FROM item_tags);

-- Partial index for video items
CREATE INDEX IF NOT EXISTS idx_items_videos 
    ON items(created_at DESC) 
    WHERE metadata->>'item_type' = 'video';

-- Index for full-text search with specific languages
CREATE INDEX IF NOT EXISTS idx_items_search_english 
    ON items USING GIN(to_tsvector('english', title || ' ' || COALESCE(summary, '')));

-- Analyze tables to update statistics
ANALYZE items;
ANALYZE tags;
ANALYZE item_tags;