-- 005_add_indexes_for_performance.sql

CREATE INDEX IF NOT EXISTS idx_items_created_date ON items(created_at);
CREATE INDEX IF NOT EXISTS idx_items_ai_analysis ON items USING GIN((metadata->'ai_analysis'));
CREATE INDEX IF NOT EXISTS idx_items_embedding_exists ON items(id) WHERE embedding IS NOT NULL;
