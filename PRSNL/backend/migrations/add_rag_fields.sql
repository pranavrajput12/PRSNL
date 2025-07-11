-- Add RAG-related fields to items table
-- Tracks which items have been indexed in the RAG system

-- Add columns to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS rag_indexed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS rag_doc_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS rag_indexed_at TIMESTAMP;

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_items_rag_indexed ON items(rag_indexed) WHERE rag_indexed = TRUE;
CREATE INDEX IF NOT EXISTS idx_items_rag_doc_id ON items(rag_doc_id);

-- Create Haystack documents table for PGVector integration
CREATE TABLE IF NOT EXISTS haystack_documents (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    meta JSONB,
    embedding vector(384),  -- all-MiniLM-L6-v2 dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient retrieval
CREATE INDEX IF NOT EXISTS idx_haystack_docs_embedding ON haystack_documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_haystack_docs_meta ON haystack_documents USING gin(meta);
CREATE INDEX IF NOT EXISTS idx_haystack_docs_created ON haystack_documents(created_at);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_haystack_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_haystack_documents_updated_at_trigger ON haystack_documents;
CREATE TRIGGER update_haystack_documents_updated_at_trigger
BEFORE UPDATE ON haystack_documents
FOR EACH ROW
EXECUTE FUNCTION update_haystack_documents_updated_at();

-- Create RAG query history table for analytics
CREATE TABLE IF NOT EXISTS rag_query_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query TEXT NOT NULL,
    answer TEXT,
    confidence FLOAT,
    documents_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for query analytics
CREATE INDEX IF NOT EXISTS idx_rag_queries_user ON rag_query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_queries_created ON rag_query_history(created_at);

-- Add comment explaining the tables
COMMENT ON TABLE haystack_documents IS 'Stores documents indexed by Haystack v2 RAG system with vector embeddings';
COMMENT ON TABLE rag_query_history IS 'Tracks RAG queries for analytics and improvement';
COMMENT ON COLUMN items.rag_indexed IS 'Whether this item has been indexed in the RAG system';
COMMENT ON COLUMN items.rag_doc_id IS 'Reference to the document ID in the RAG system';
COMMENT ON COLUMN items.rag_indexed_at IS 'When this item was indexed in the RAG system';