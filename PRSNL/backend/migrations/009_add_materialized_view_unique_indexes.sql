-- Add Unique Indexes for Materialized Views Concurrent Refresh
-- Migration 009: Fix materialized view concurrent refresh issue
-- Date: 2025-08-01

-- Create schema_migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Add Unique Indexes for Materialized Views
-- =============================================

-- For entity_statistics materialized view:
-- Since entity_type groups the data, it should be unique in the result set
-- This creates a unique index that enables concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS entity_statistics_entity_type_unique_idx 
    ON entity_statistics(entity_type);

-- For relationship_statistics materialized view:
-- Since relationship_type groups the data, it should be unique in the result set
-- This creates a unique index that enables concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS relationship_statistics_relationship_type_unique_idx 
    ON relationship_statistics(relationship_type);

-- =============================================
-- Update Refresh Function to Use Concurrent Refresh
-- =============================================

-- Update the function to use concurrent refresh now that unique indexes exist
CREATE OR REPLACE FUNCTION refresh_knowledge_graph_stats()
RETURNS void AS $$
BEGIN
    -- Refresh materialized views concurrently now that unique indexes exist
    REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Comments
-- =============================================

COMMENT ON INDEX entity_statistics_entity_type_unique_idx IS 'Unique index on entity_type to enable concurrent refresh of entity_statistics materialized view';
COMMENT ON INDEX relationship_statistics_relationship_type_unique_idx IS 'Unique index on relationship_type to enable concurrent refresh of relationship_statistics materialized view';

-- =============================================
-- Migration Completion
-- =============================================

-- Log migration completion
INSERT INTO schema_migrations (version, description, applied_at) 
VALUES ('009', 'Add unique indexes for materialized views concurrent refresh', NOW())
ON CONFLICT (version) DO NOTHING;