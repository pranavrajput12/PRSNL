-- Knowledge Graph Extension for Cross-Feature Integration (Fixed)
-- Phase 2.1: Database Schema Enhancement
-- Date: 2025-08-02

-- Create schema_migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Unified Entity System for Cross-Feature Integration
-- =============================================

-- Create unified entities table for all content types
CREATE TABLE IF NOT EXISTS unified_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'conversation_turn', 'video_segment', 'code_function', 'code_class', 
        'code_module', 'timeline_event', 'file_attachment', 'image_entity', 
        'audio_entity', 'text_entity', 'knowledge_concept'
    )),
    source_content_id UUID REFERENCES items(id) ON DELETE CASCADE,
    parent_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    start_position INTEGER, -- For segments (video time, text position, line numbers)
    end_position INTEGER,
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_method TEXT DEFAULT 'manual', -- manual, ai_extracted, user_defined
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Conversation-Specific Entities
-- =============================================

-- Enhanced conversation turns with entity linking
CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES items(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,
    speaker_id UUID, -- For identified users
    content TEXT NOT NULL,
    turn_order INTEGER NOT NULL,
    timestamp TIMESTAMP,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'file', 'code', 'link')),
    metadata JSONB DEFAULT '{}', -- AI analysis, emotions, topics, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (conversation_id, turn_order)
);

-- Conversation topics and themes
CREATE TABLE IF NOT EXISTS conversation_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES items(id) ON DELETE CASCADE,
    topic_name TEXT NOT NULL,
    start_turn INTEGER,
    end_turn INTEGER,
    relevance_score FLOAT DEFAULT 1.0,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Video-Specific Entities
-- =============================================

-- Video segments with enhanced metadata
CREATE TABLE IF NOT EXISTS video_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES items(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    start_time INTEGER NOT NULL, -- Start time in seconds
    end_time INTEGER NOT NULL,   -- End time in seconds
    segment_type TEXT DEFAULT 'topic' CHECK (segment_type IN ('topic', 'speaker_change', 'scene_change', 'chapter')),
    title TEXT,
    transcript TEXT,
    summary TEXT,
    topics TEXT[],
    speaker TEXT,
    confidence_score FLOAT DEFAULT 1.0,
    thumbnail_url TEXT,
    metadata JSONB DEFAULT '{}', -- AI analysis, visual elements, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (end_time > start_time)
);

-- Video topics and chapters
CREATE TABLE IF NOT EXISTS video_chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES items(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    description TEXT,
    thumbnail_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (video_id, chapter_number)
);

-- =============================================
-- Code Structure Entities
-- =============================================

-- Code entities (functions, classes, modules)
CREATE TABLE IF NOT EXISTS code_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES items(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('function', 'class', 'module', 'interface', 'enum', 'variable', 'constant')),
    name TEXT NOT NULL,
    full_name TEXT, -- Fully qualified name (e.g., MyClass.myMethod)
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    language TEXT,
    visibility TEXT DEFAULT 'public' CHECK (visibility IN ('public', 'private', 'protected', 'internal')),
    parameters JSONB DEFAULT '[]', -- Function parameters
    return_type TEXT,
    documentation TEXT, -- Docstring or comments
    complexity_score INTEGER, -- Cyclomatic complexity
    dependencies TEXT[], -- Other entities this depends on
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Code dependencies and relationships
CREATE TABLE IF NOT EXISTS code_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES code_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES code_entities(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL CHECK (dependency_type IN ('calls', 'extends', 'implements', 'imports', 'uses', 'defines')),
    line_number INTEGER,
    confidence_score FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source_entity_id, target_entity_id, dependency_type)
);

-- =============================================
-- Timeline and Event Entities
-- =============================================

-- Timeline events with enhanced context
CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('content_creation', 'content_update', 'conversation', 'code_commit', 'meeting', 'learning', 'milestone')),
    title TEXT NOT NULL,
    description TEXT,
    event_timestamp TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    content_ids UUID[], -- Related content items
    participants TEXT[], -- People involved
    location TEXT,
    tags TEXT[],
    importance_score INTEGER DEFAULT 1 CHECK (importance_score >= 1 AND importance_score <= 5),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Enhanced Relationship System
-- =============================================

-- Extended relationship types for cross-feature integration
CREATE TABLE IF NOT EXISTS unified_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        -- Temporal relationships
        'precedes', 'follows', 'concurrent', 'enables', 'depends_on',
        -- Content relationships  
        'discusses', 'implements', 'references', 'explains', 'demonstrates',
        -- Structural relationships
        'contains', 'part_of', 'similar_to', 'related_to', 'opposite_of',
        -- Cross-modal relationships
        'visualizes', 'describes', 'transcribes', 'summarizes', 'extends',
        -- Learning relationships
        'prerequisite', 'builds_on', 'reinforces', 'applies', 'teaches'
    )),
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    bidirectional BOOLEAN DEFAULT false,
    context TEXT, -- Why this relationship exists
    extraction_method TEXT DEFAULT 'manual', -- manual, ai_inferred, user_defined, similarity_based
    evidence JSONB DEFAULT '{}', -- Supporting evidence for the relationship
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source_entity_id, target_entity_id, relationship_type)
);

-- =============================================
-- Cross-Feature Integration Tables
-- =============================================

-- Link content items to entities for cross-referencing
CREATE TABLE IF NOT EXISTS content_entity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES items(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    link_type TEXT DEFAULT 'contains' CHECK (link_type IN ('contains', 'mentions', 'references', 'created_from', 'derived_from')),
    confidence_score FLOAT DEFAULT 1.0,
    context_snippet TEXT, -- Surrounding text where entity appears
    position_start INTEGER,
    position_end INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (content_id, entity_id, link_type)
);

-- User interaction with entities (for personalization)
CREATE TABLE IF NOT EXISTS entity_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- From auth system when available
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('view', 'edit', 'like', 'bookmark', 'share', 'comment', 'rate')),
    interaction_value JSONB DEFAULT '{}', -- Rating, comment text, etc.
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id TEXT,
    metadata JSONB DEFAULT '{}'
);

-- =============================================
-- Create All Indexes (Separate from Table Creation)
-- =============================================

-- Unified entities indexes
CREATE INDEX IF NOT EXISTS idx_unified_entities_type ON unified_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_unified_entities_source ON unified_entities(source_content_id);
CREATE INDEX IF NOT EXISTS idx_unified_entities_created ON unified_entities(created_at);
CREATE INDEX IF NOT EXISTS idx_unified_entities_confidence ON unified_entities(confidence_score);
CREATE INDEX IF NOT EXISTS idx_unified_entities_parent ON unified_entities(parent_entity_id);

-- Conversation indexes
CREATE INDEX IF NOT EXISTS idx_conversation_turns_conv_order ON conversation_turns(conversation_id, turn_order);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_speaker ON conversation_turns(speaker);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_timestamp ON conversation_turns(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_entity ON conversation_turns(entity_id);
CREATE INDEX IF NOT EXISTS idx_conversation_topics_conv ON conversation_topics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_topics_name ON conversation_topics(topic_name);

-- Video indexes
CREATE INDEX IF NOT EXISTS idx_video_segments_video ON video_segments(video_id);
CREATE INDEX IF NOT EXISTS idx_video_segments_start ON video_segments(start_time);
CREATE INDEX IF NOT EXISTS idx_video_segments_type ON video_segments(segment_type);
CREATE INDEX IF NOT EXISTS idx_video_segments_entity ON video_segments(entity_id);
CREATE INDEX IF NOT EXISTS idx_video_chapters_video_num ON video_chapters(video_id, chapter_number);

-- Code indexes
CREATE INDEX IF NOT EXISTS idx_code_entities_repo ON code_entities(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_entities_type ON code_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_code_entities_file ON code_entities(file_path);
CREATE INDEX IF NOT EXISTS idx_code_entities_name ON code_entities(name);
CREATE INDEX IF NOT EXISTS idx_code_entities_entity ON code_entities(entity_id);
CREATE INDEX IF NOT EXISTS idx_code_deps_source ON code_dependencies(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_code_deps_target ON code_dependencies(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_code_deps_type ON code_dependencies(dependency_type);

-- Timeline indexes
CREATE INDEX IF NOT EXISTS idx_timeline_events_type ON timeline_events(event_type);
CREATE INDEX IF NOT EXISTS idx_timeline_events_timestamp ON timeline_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_timeline_events_importance ON timeline_events(importance_score);
CREATE INDEX IF NOT EXISTS idx_timeline_events_entity ON timeline_events(entity_id);

-- Relationship indexes
CREATE INDEX IF NOT EXISTS idx_relationships_source ON unified_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON unified_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON unified_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_confidence ON unified_relationships(confidence_score);
CREATE INDEX IF NOT EXISTS idx_relationships_created ON unified_relationships(created_at);

-- Content entity links indexes
CREATE INDEX IF NOT EXISTS idx_content_links_content ON content_entity_links(content_id);
CREATE INDEX IF NOT EXISTS idx_content_links_entity ON content_entity_links(entity_id);
CREATE INDEX IF NOT EXISTS idx_content_links_type ON content_entity_links(link_type);

-- Entity interactions indexes
CREATE INDEX IF NOT EXISTS idx_entity_interactions_user ON entity_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_entity_interactions_entity ON entity_interactions(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_interactions_type ON entity_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_entity_interactions_timestamp ON entity_interactions(timestamp);

-- Composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_unified_entities_composite ON unified_entities(entity_type, source_content_id, created_at);
CREATE INDEX IF NOT EXISTS idx_unified_relationships_composite ON unified_relationships(relationship_type, confidence_score, created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_composite ON conversation_turns(conversation_id, turn_order, timestamp);
CREATE INDEX IF NOT EXISTS idx_video_segments_time_range ON video_segments(video_id, start_time, end_time);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_unified_entities_name_fts ON unified_entities USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_unified_entities_description_fts ON unified_entities USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_conversation_turns_content_fts ON conversation_turns USING gin(to_tsvector('english', content));

-- =============================================
-- Performance and Analytics Views
-- =============================================

-- Materialized view for entity statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS entity_statistics AS
SELECT 
    entity_type,
    COUNT(*) as total_entities,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT source_content_id) as unique_sources,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM unified_entities 
GROUP BY entity_type;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_entity_statistics_type ON entity_statistics(entity_type);

-- Materialized view for relationship statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS relationship_statistics AS
SELECT 
    relationship_type,
    COUNT(*) as total_relationships,
    AVG(confidence_score) as avg_confidence,
    AVG(strength) as avg_strength,
    COUNT(DISTINCT source_entity_id) as unique_sources,
    COUNT(DISTINCT target_entity_id) as unique_targets
FROM unified_relationships 
GROUP BY relationship_type;

-- Create index on relationship statistics
CREATE INDEX IF NOT EXISTS idx_relationship_statistics_type ON relationship_statistics(relationship_type);

-- =============================================
-- Knowledge Graph Integration Functions
-- =============================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_knowledge_graph_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;
END;
$$ LANGUAGE plpgsql;

-- Function to create entity from content automatically
CREATE OR REPLACE FUNCTION create_entity_from_content(
    p_entity_type text,
    p_source_content_id uuid,
    p_name text,
    p_description text DEFAULT NULL,
    p_metadata jsonb DEFAULT '{}'
) RETURNS uuid AS $$
DECLARE
    new_entity_id uuid;
BEGIN
    INSERT INTO unified_entities (entity_type, source_content_id, name, description, metadata, extraction_method)
    VALUES (p_entity_type, p_source_content_id, p_name, p_description, p_metadata, 'ai_extracted')
    RETURNING id INTO new_entity_id;
    
    RETURN new_entity_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create relationship with validation
CREATE OR REPLACE FUNCTION create_relationship(
    p_source_entity_id uuid,
    p_target_entity_id uuid,
    p_relationship_type text,
    p_confidence_score float DEFAULT 1.0,
    p_context text DEFAULT NULL,
    p_bidirectional boolean DEFAULT false
) RETURNS uuid AS $$
DECLARE
    new_relationship_id uuid;
BEGIN
    -- Prevent self-relationships
    IF p_source_entity_id = p_target_entity_id THEN
        RAISE EXCEPTION 'Cannot create relationship between entity and itself';
    END IF;
    
    -- Create the relationship
    INSERT INTO unified_relationships (
        source_entity_id, target_entity_id, relationship_type, 
        confidence_score, context, bidirectional, extraction_method
    )
    VALUES (
        p_source_entity_id, p_target_entity_id, p_relationship_type,
        p_confidence_score, p_context, p_bidirectional, 'ai_inferred'
    )
    RETURNING id INTO new_relationship_id;
    
    -- Create reverse relationship if bidirectional
    IF p_bidirectional THEN
        INSERT INTO unified_relationships (
            source_entity_id, target_entity_id, relationship_type,
            confidence_score, context, bidirectional, extraction_method
        )
        VALUES (
            p_target_entity_id, p_source_entity_id, p_relationship_type,
            p_confidence_score, p_context, false, 'ai_inferred'
        );
    END IF;
    
    RETURN new_relationship_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Triggers for Automatic Maintenance
-- =============================================

-- Update timestamps on entity changes
CREATE OR REPLACE FUNCTION update_entity_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_unified_entities_timestamp
    BEFORE UPDATE ON unified_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_timestamp();

CREATE TRIGGER update_unified_relationships_timestamp
    BEFORE UPDATE ON unified_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_timestamp();

-- =============================================
-- Comments and Documentation
-- =============================================

COMMENT ON TABLE unified_entities IS 'Central entity table for cross-feature knowledge graph integration';
COMMENT ON TABLE conversation_turns IS 'Individual turns in conversations with entity linking';
COMMENT ON TABLE video_segments IS 'Time-based video segments with AI analysis';
COMMENT ON TABLE code_entities IS 'Code structure entities (functions, classes, modules)';
COMMENT ON TABLE timeline_events IS 'Timeline events with enhanced context and relationships';
COMMENT ON TABLE unified_relationships IS 'Cross-feature relationships with confidence scoring';
COMMENT ON TABLE content_entity_links IS 'Links between content items and extracted entities';

COMMENT ON COLUMN unified_entities.entity_type IS 'Type of entity for polymorphic behavior';
COMMENT ON COLUMN unified_entities.extraction_method IS 'How this entity was created (manual, ai_extracted, user_defined)';
COMMENT ON COLUMN unified_relationships.relationship_type IS 'Semantic relationship type between entities';
COMMENT ON COLUMN unified_relationships.bidirectional IS 'Whether this relationship implies a reverse relationship';

-- =============================================
-- Migration Completion
-- =============================================

-- Log migration completion
INSERT INTO schema_migrations (version, description, applied_at) 
VALUES ('008', 'Knowledge Graph Extension for Cross-Feature Integration', NOW())
ON CONFLICT (version) DO NOTHING;