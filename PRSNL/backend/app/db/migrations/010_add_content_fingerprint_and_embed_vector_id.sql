-- Migration: Add content fingerprinting and embedding vector ID fields
-- Date: 2025-07-11
-- Description: Adds content_fingerprint for deduplication and embed_vector_id for direct pgvector pointer

-- Add content_fingerprint field for SHA-256 hash of raw_content
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS content_fingerprint VARCHAR(64);

-- Add embed_vector_id for direct pointer to pgvector table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS embed_vector_id UUID;

-- Create index on content_fingerprint for fast duplicate detection
CREATE INDEX IF NOT EXISTS idx_items_content_fingerprint ON items(content_fingerprint);

-- Create index on embed_vector_id for fast embedding lookups
CREATE INDEX IF NOT EXISTS idx_items_embed_vector_id ON items(embed_vector_id);

-- Add comments for documentation
COMMENT ON COLUMN items.content_fingerprint IS 'SHA-256 hash of raw_content for duplicate detection and content versioning';
COMMENT ON COLUMN items.embed_vector_id IS 'Direct pointer to pgvector embedding table, saves joins on semantic search';

-- Update the updated_at trigger to include new fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Ensure trigger exists for items table
DROP TRIGGER IF EXISTS update_items_updated_at ON items;
CREATE TRIGGER update_items_updated_at 
    BEFORE UPDATE ON items 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();