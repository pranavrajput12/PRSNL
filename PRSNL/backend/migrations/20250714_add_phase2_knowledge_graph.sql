-- Phase 2: Knowledge Graph Background Processing Migration
-- Date: 2025-07-14
-- Purpose: Add tables for distributed knowledge graph operations with Celery

-- Knowledge Graphs table for storing assembled graphs
CREATE TABLE IF NOT EXISTS knowledge_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    graph_name TEXT NOT NULL,
    graph_structure JSONB NOT NULL DEFAULT '{}',
    entities_count INTEGER DEFAULT 0,
    relationships_count INTEGER DEFAULT 0,
    enhancement_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Relationships table for individual graph edges
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES knowledge_graphs(id) ON DELETE CASCADE,
    source_entity TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence_score FLOAT DEFAULT 0.8,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Content Entity Links table for linking content to entities
CREATE TABLE IF NOT EXISTS content_entity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    entity_id UUID NOT NULL,
    link_type TEXT DEFAULT 'mention',
    confidence_score FLOAT DEFAULT 0.8,
    context_text TEXT,
    position_start INTEGER DEFAULT 0,
    position_end INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Entities table (if not exists from previous migrations)
CREATE TABLE IF NOT EXISTS knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT DEFAULT 'general',
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization

-- Knowledge Graphs indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_user_id ON knowledge_graphs(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_created_at ON knowledge_graphs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_entities_count ON knowledge_graphs(entities_count DESC);

-- Knowledge Relationships indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_graph_id ON knowledge_relationships(graph_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_source ON knowledge_relationships(source_entity);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_target ON knowledge_relationships(target_entity);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_confidence ON knowledge_relationships(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_type ON knowledge_relationships(relation_type);

-- Content Entity Links indexes
CREATE INDEX IF NOT EXISTS idx_content_entity_links_content_id ON content_entity_links(content_id);
CREATE INDEX IF NOT EXISTS idx_content_entity_links_entity_id ON content_entity_links(entity_id);
CREATE INDEX IF NOT EXISTS idx_content_entity_links_confidence ON content_entity_links(confidence_score DESC);

-- Knowledge Entities indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_user_id ON knowledge_entities(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_type ON knowledge_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_name ON knowledge_entities(name);

-- Views for common queries

-- Entity Connections View
CREATE OR REPLACE VIEW entity_connections_view AS
SELECT 
    r.id as relationship_id,
    r.source_entity,
    r.target_entity,
    r.relation_type,
    r.confidence_score,
    r.metadata as relationship_metadata,
    kg.id as graph_id,
    kg.graph_name,
    kg.user_id,
    e1.name as source_name,
    e1.entity_type as source_type,
    e2.name as target_name,
    e2.entity_type as target_type
FROM knowledge_relationships r
JOIN knowledge_graphs kg ON r.graph_id = kg.id
LEFT JOIN knowledge_entities e1 ON r.source_entity = e1.id::text
LEFT JOIN knowledge_entities e2 ON r.target_entity = e2.id::text;

-- Content Links Summary View
CREATE OR REPLACE VIEW content_links_summary AS
SELECT 
    cel.content_id,
    COUNT(*) as total_entity_links,
    AVG(cel.confidence_score) as avg_confidence,
    ARRAY_AGG(DISTINCT ke.entity_type) as linked_entity_types,
    ARRAY_AGG(DISTINCT ke.name) as linked_entity_names
FROM content_entity_links cel
JOIN knowledge_entities ke ON cel.entity_id = ke.id
GROUP BY cel.content_id;

-- Knowledge Graph Statistics View
CREATE OR REPLACE VIEW knowledge_graph_stats AS
SELECT 
    kg.id,
    kg.graph_name,
    kg.user_id,
    kg.entities_count,
    kg.relationships_count,
    COUNT(DISTINCT r.relation_type) as relation_types_count,
    AVG(r.confidence_score) as avg_relationship_confidence,
    MAX(r.confidence_score) as max_relationship_confidence,
    MIN(r.confidence_score) as min_relationship_confidence,
    kg.created_at
FROM knowledge_graphs kg
LEFT JOIN knowledge_relationships r ON kg.id = r.graph_id
GROUP BY kg.id, kg.graph_name, kg.user_id, kg.entities_count, kg.relationships_count, kg.created_at;

-- Performance monitoring functions

-- Function to get entity relationship count
CREATE OR REPLACE FUNCTION get_entity_relationship_count(entity_uuid TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM knowledge_relationships
        WHERE source_entity = entity_uuid OR target_entity = entity_uuid
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get graph connectivity metrics
CREATE OR REPLACE FUNCTION get_graph_connectivity_metrics(graph_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    total_entities INTEGER;
    total_relationships INTEGER;
    avg_connections FLOAT;
    connectivity_metrics JSONB;
BEGIN
    SELECT entities_count, relationships_count
    INTO total_entities, total_relationships
    FROM knowledge_graphs
    WHERE id = graph_uuid;
    
    IF total_entities > 0 THEN
        avg_connections := (total_relationships * 2.0) / total_entities;
    ELSE
        avg_connections := 0;
    END IF;
    
    connectivity_metrics := jsonb_build_object(
        'total_entities', total_entities,
        'total_relationships', total_relationships,
        'average_connections_per_entity', avg_connections,
        'density', CASE 
            WHEN total_entities > 1 THEN 
                total_relationships::FLOAT / (total_entities * (total_entities - 1) / 2.0)
            ELSE 0 
        END
    );
    
    RETURN connectivity_metrics;
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining updated_at timestamps

-- Knowledge Graphs trigger
CREATE OR REPLACE FUNCTION update_knowledge_graphs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_knowledge_graphs_updated_at
    BEFORE UPDATE ON knowledge_graphs
    FOR EACH ROW
    EXECUTE FUNCTION update_knowledge_graphs_updated_at();

-- Knowledge Entities trigger
CREATE OR REPLACE FUNCTION update_knowledge_entities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_knowledge_entities_updated_at
    BEFORE UPDATE ON knowledge_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_knowledge_entities_updated_at();

-- Comments for documentation
COMMENT ON TABLE knowledge_graphs IS 'Stores assembled knowledge graphs with metadata and structure';
COMMENT ON TABLE knowledge_relationships IS 'Individual relationships/edges in knowledge graphs';
COMMENT ON TABLE content_entity_links IS 'Links between content and knowledge entities';
COMMENT ON TABLE knowledge_entities IS 'Knowledge entities extracted from content';

COMMENT ON VIEW entity_connections_view IS 'Comprehensive view of entity relationships with names and metadata';
COMMENT ON VIEW content_links_summary IS 'Summary statistics for content-entity links';
COMMENT ON VIEW knowledge_graph_stats IS 'Statistical overview of knowledge graph characteristics';

COMMENT ON FUNCTION get_entity_relationship_count IS 'Count total relationships for a specific entity';
COMMENT ON FUNCTION get_graph_connectivity_metrics IS 'Calculate connectivity metrics for a knowledge graph';

-- Grant necessary permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;