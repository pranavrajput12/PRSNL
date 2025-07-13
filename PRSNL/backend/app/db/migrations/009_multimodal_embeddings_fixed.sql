-- Migration 009: Enhanced Multimodal Embeddings Support (Fixed)
-- Description: Extend embeddings table to support multiple modalities (text, image, video, multimodal)
-- Date: 2025-07-13

BEGIN;

-- Add new columns to embeddings table for multimodal support
ALTER TABLE embeddings 
ADD COLUMN IF NOT EXISTS embedding_type VARCHAR(50) NOT NULL DEFAULT 'text' CHECK (
    embedding_type IN ('text', 'image', 'video_frame', 'multimodal', 'audio')
),
ADD COLUMN IF NOT EXISTS modality_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS content_source VARCHAR(100), -- e.g., 'ocr_text', 'image_caption', 'video_transcript'
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64); -- SHA-256 of the source content for deduplication

-- Update the unique constraint to allow multiple embedding types per item
-- Drop the old constraint
ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS embeddings_item_id_model_name_model_version_key;

-- Add new constraint that allows multiple embedding types per item/model
ALTER TABLE embeddings 
ADD CONSTRAINT embeddings_item_model_type_unique 
UNIQUE(item_id, model_name, model_version, embedding_type);

-- Create indexes for multimodal queries
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_source ON embeddings(content_source);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_hash ON embeddings(content_hash);
CREATE INDEX IF NOT EXISTS idx_embeddings_item_type ON embeddings(item_id, embedding_type);

-- Skip specialized vector indexes for now (will create when we have data)

-- Add trigger to update content_hash automatically
CREATE OR REPLACE FUNCTION update_embedding_content_hash()
RETURNS TRIGGER AS $$
BEGIN
    -- Generate content hash from metadata if not provided
    IF NEW.content_hash IS NULL AND NEW.modality_metadata IS NOT NULL THEN
        NEW.content_hash = encode(
            digest(NEW.modality_metadata::text, 'sha256'), 
            'hex'
        );
    END IF;
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER embeddings_content_hash_trigger
    BEFORE INSERT OR UPDATE ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_content_hash();

-- Create view for multimodal search queries
CREATE OR REPLACE VIEW multimodal_embeddings AS
SELECT 
    e.id,
    e.item_id,
    e.embedding_type,
    e.model_name,
    e.vector,
    e.vector_norm,
    e.modality_metadata,
    e.content_source,
    e.created_at,
    i.title,
    i.summary,
    i.type as item_type,
    i.url,
    i.file_path,
    i.thumbnail_url
FROM embeddings e
JOIN items i ON e.item_id = i.id;

-- Add comments for documentation
COMMENT ON COLUMN embeddings.embedding_type IS 'Type of embedding: text, image, video_frame, multimodal, audio';
COMMENT ON COLUMN embeddings.modality_metadata IS 'Modal-specific metadata like image dimensions, video timestamps, etc.';
COMMENT ON COLUMN embeddings.content_source IS 'Source of the content: ocr_text, image_caption, video_transcript, etc.';
COMMENT ON COLUMN embeddings.content_hash IS 'SHA-256 hash of source content for deduplication';

COMMENT ON VIEW multimodal_embeddings IS 'Unified view for multimodal search across all embedding types';

COMMIT;