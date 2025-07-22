-- Add embed_vector_id column to items table if it doesn't exist
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS embed_vector_id UUID REFERENCES embeddings(id) ON DELETE SET NULL;

-- Create the view now that the column exists
CREATE OR REPLACE VIEW items_with_embeddings AS
SELECT 
    i.*,
    e.vector as embedding_vector,
    e.model_name,
    e.model_version,
    e.vector_norm
FROM items i
LEFT JOIN embeddings e ON i.embed_vector_id = e.id;

-- Add comment
COMMENT ON VIEW items_with_embeddings IS 'Convenience view joining items with their embeddings';