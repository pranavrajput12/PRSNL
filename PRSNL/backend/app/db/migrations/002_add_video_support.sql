-- Migration to add video support to PRSNL database
-- This adds type, video-specific fields, and attachments table

-- Add type column to distinguish between different content types
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS type VARCHAR(20) NOT NULL DEFAULT 'article';

-- Add video-specific columns
ALTER TABLE items
ADD COLUMN IF NOT EXISTS file_path TEXT,
ADD COLUMN IF NOT EXISTS duration INTEGER, -- in seconds
ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;

-- Update existing rows to have correct type
UPDATE items SET type = 'article' WHERE type IS NULL;

-- Create attachments table for multiple files per item
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- e.g., 'video', 'image', 'document'
    mime_type VARCHAR(100),
    file_size BIGINT, -- in bytes
    metadata JSONB DEFAULT '{}', -- for video: width, height, bitrate, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for attachments
CREATE INDEX IF NOT EXISTS idx_attachments_item_id ON attachments(item_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file_type ON attachments(file_type);

-- Add index for type
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);

-- Add platform column for videos (instagram, youtube, etc.)
ALTER TABLE items
ADD COLUMN IF NOT EXISTS platform VARCHAR(50);

-- Update metadata structure to include video-specific data
-- This will be handled in the application layer, but we can update the column comment
COMMENT ON COLUMN items.metadata IS 'JSON metadata including video data like resolution, view_count, like_count, etc.';

-- Create a view for video items
CREATE OR REPLACE VIEW video_items AS
SELECT 
    i.*,
    a.file_path as attachment_path,
    a.file_size,
    a.metadata as attachment_metadata
FROM items i
LEFT JOIN attachments a ON i.id = a.item_id AND a.file_type = 'video'
WHERE i.type = 'video';

-- Add constraints
ALTER TABLE items
ADD CONSTRAINT chk_item_type CHECK (type IN ('article', 'video', 'note', 'bookmark'));

-- Function to automatically set type based on URL
CREATE OR REPLACE FUNCTION set_item_type() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type IS NULL OR NEW.type = 'article' THEN
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

-- Create trigger to auto-set item type
DROP TRIGGER IF EXISTS items_set_type ON items;
CREATE TRIGGER items_set_type
    BEFORE INSERT OR UPDATE OF url
    ON items
    FOR EACH ROW
    EXECUTE FUNCTION set_item_type();