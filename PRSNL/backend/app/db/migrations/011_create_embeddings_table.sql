-- Migration: Create separate embeddings table for normalized vector storage
-- Date: 2025-07-11
-- Description: Creates embeddings table to support embed_vector_id foreign key

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    vector vector(1536) NOT NULL,
    vector_norm FLOAT, -- Pre-calculated norm for faster similarity
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_embeddings_item_id ON embeddings(item_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);

-- Add unique constraint to prevent duplicate embeddings for same item/model
CREATE UNIQUE INDEX IF NOT EXISTS idx_embeddings_unique_item_model 
ON embeddings(item_id, model_name, model_version);

-- Create function to calculate and store vector norm
CREATE OR REPLACE FUNCTION calculate_vector_norm()
RETURNS TRIGGER AS $$
BEGIN
    NEW.vector_norm = sqrt(abs(NEW.vector <#> NEW.vector));
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-calculate norm
CREATE TRIGGER calculate_embedding_norm
    BEFORE INSERT OR UPDATE OF vector ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION calculate_vector_norm();

-- Add foreign key constraint from items to embeddings
ALTER TABLE items
ADD CONSTRAINT fk_items_embed_vector_id 
FOREIGN KEY (embed_vector_id) 
REFERENCES embeddings(id) 
ON DELETE SET NULL;

-- Create view for easy embedding lookups
CREATE OR REPLACE VIEW items_with_embeddings AS
SELECT 
    i.*,
    e.vector as embedding_vector,
    e.model_name,
    e.model_version,
    e.vector_norm
FROM items i
LEFT JOIN embeddings e ON i.embed_vector_id = e.id;

-- Add comments
COMMENT ON TABLE embeddings IS 'Normalized embedding storage for vector search';
COMMENT ON COLUMN embeddings.vector_norm IS 'Pre-calculated L2 norm for faster similarity calculations';
COMMENT ON VIEW items_with_embeddings IS 'Convenience view joining items with their embeddings';