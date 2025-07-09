ALTER TABLE items ADD COLUMN embedding VECTOR(1536);
CREATE INDEX ON items USING HNSW (embedding vector_cosine_ops);