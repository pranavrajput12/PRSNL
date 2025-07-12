-- Migration 012: Add Simplified Permalink System
-- Date: 2025-07-12
-- Description: Create tables for simplified URL structure (/c/category/slug)

-- Content URLs table for new permalink system
CREATE TABLE IF NOT EXISTS content_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    slug VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    
    -- SEO essentials
    meta_title VARCHAR(160),
    meta_description VARCHAR(320),
    canonical_url VARCHAR(500),
    
    -- Performance tracking
    views INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(category, slug),
    CONSTRAINT valid_category CHECK (category IN ('dev', 'learn', 'media', 'ideas')),
    CONSTRAINT valid_slug CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$' AND length(slug) <= 60)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_urls_category_slug ON content_urls(category, slug);
CREATE INDEX IF NOT EXISTS idx_content_urls_content_id ON content_urls(content_id);
CREATE INDEX IF NOT EXISTS idx_content_urls_views ON content_urls(views DESC);
CREATE INDEX IF NOT EXISTS idx_content_urls_last_accessed ON content_urls(last_accessed DESC);

-- Simple redirects table for legacy URL mapping
CREATE TABLE IF NOT EXISTS url_redirects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    old_path VARCHAR(500) NOT NULL UNIQUE,
    new_path VARCHAR(500) NOT NULL,
    redirect_type INTEGER DEFAULT 301 CHECK (redirect_type IN (301, 302)),
    hit_count INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Index for fast redirect lookups
CREATE INDEX IF NOT EXISTS idx_url_redirects_old_path ON url_redirects(old_path) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_url_redirects_hit_count ON url_redirects(hit_count DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_content_urls_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_update_content_urls_updated_at ON content_urls;
CREATE TRIGGER trigger_update_content_urls_updated_at
    BEFORE UPDATE ON content_urls
    FOR EACH ROW
    EXECUTE FUNCTION update_content_urls_updated_at();

-- Add initial redirects for existing routes
INSERT INTO url_redirects (old_path, new_path, redirect_type) VALUES
    ('/timeline', '/p/timeline', 301),
    ('/insights', '/p/insights', 301),
    ('/chat', '/p/chat', 301),
    ('/videos', '/c/media', 301),
    ('/code-cortex', '/p/code', 301),
    ('/import', '/s/import', 301),
    ('/import/v1', '/s/import/v1', 301),
    ('/import/v2', '/s/import/v2', 301),
    ('/settings', '/s/settings', 301),
    ('/docs', '/s/docs', 301)
ON CONFLICT (old_path) DO NOTHING;

-- Add comment for documentation
COMMENT ON TABLE content_urls IS 'Simplified permalink system with /c/category/slug structure';
COMMENT ON TABLE url_redirects IS 'Legacy URL redirects for maintaining SEO and user bookmarks';
COMMENT ON COLUMN content_urls.category IS 'Content category: dev, learn, media, ideas';
COMMENT ON COLUMN content_urls.slug IS 'SEO-friendly URL slug, unique within category';
COMMENT ON COLUMN url_redirects.redirect_type IS '301 = permanent, 302 = temporary';