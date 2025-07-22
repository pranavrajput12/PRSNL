-- Add missing columns to embeddings table for compatibility with embedding_manager

-- Add embedding_type column
ALTER TABLE embeddings 
ADD COLUMN IF NOT EXISTS embedding_type VARCHAR(50) NOT NULL DEFAULT 'text';

-- Add content_source column  
ALTER TABLE embeddings
ADD COLUMN IF NOT EXISTS content_source VARCHAR(100) DEFAULT 'direct_text';

-- Update the unique constraint to include embedding_type
DROP INDEX IF EXISTS idx_embeddings_unique_item_model;
CREATE UNIQUE INDEX idx_embeddings_unique_item_model 
ON embeddings(item_id, model_name, model_version, embedding_type);

-- Add index on embedding_type for performance
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type);

-- Update existing embeddings to have proper type
UPDATE embeddings SET embedding_type = 'text' WHERE embedding_type IS NULL;