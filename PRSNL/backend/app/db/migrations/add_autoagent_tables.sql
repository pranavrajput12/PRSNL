-- AutoAgent Integration Tables for PRSNL Second Brain
-- ===================================================

-- Agent Memory Storage
CREATE TABLE IF NOT EXISTS agent_memory (
    agent_id VARCHAR(255) PRIMARY KEY,
    memory_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Graph Nodes
CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    node_type VARCHAR(50) NOT NULL DEFAULT 'concept',
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Graph Edges (Relationships)
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    relationship VARCHAR(100) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relationship)
);

-- Learning Paths
CREATE TABLE IF NOT EXISTS learning_paths (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    path_name VARCHAR(255) NOT NULL,
    goal TEXT,
    current_milestone INTEGER DEFAULT 0,
    total_milestones INTEGER DEFAULT 0,
    progress FLOAT DEFAULT 0.0,
    path_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Agent Insights
CREATE TABLE IF NOT EXISTS agent_insights (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    insight_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    related_items INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    confidence FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Explorations
CREATE TABLE IF NOT EXISTS content_explorations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    starting_item_id INTEGER REFERENCES items(id),
    exploration_path JSONB NOT NULL,
    discoveries INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_memory_updated ON agent_memory(updated_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_item ON knowledge_graph_nodes(item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_relationship ON knowledge_graph_edges(relationship);
CREATE INDEX IF NOT EXISTS idx_learning_paths_user ON learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_insights_type ON agent_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_agent_insights_created ON agent_insights(created_at);

-- Functions for knowledge graph operations
CREATE OR REPLACE FUNCTION get_node_connections(node_id INTEGER, max_depth INTEGER DEFAULT 2)
RETURNS TABLE(
    node_id INTEGER,
    depth INTEGER,
    path INTEGER[]
) AS $$
WITH RECURSIVE connections AS (
    -- Base case: start node
    SELECT 
        n.id as node_id,
        0 as depth,
        ARRAY[n.id] as path
    FROM knowledge_graph_nodes n
    WHERE n.id = $1
    
    UNION ALL
    
    -- Recursive case: follow edges
    SELECT 
        CASE 
            WHEN e.source_id = c.node_id THEN e.target_id
            ELSE e.source_id
        END as node_id,
        c.depth + 1,
        c.path || CASE 
            WHEN e.source_id = c.node_id THEN e.target_id
            ELSE e.source_id
        END
    FROM connections c
    JOIN knowledge_graph_edges e ON (e.source_id = c.node_id OR e.target_id = c.node_id)
    WHERE c.depth < $2
    AND NOT (CASE 
        WHEN e.source_id = c.node_id THEN e.target_id
        ELSE e.source_id
    END = ANY(c.path))
)
SELECT DISTINCT node_id, depth, path FROM connections;
$$ LANGUAGE SQL;

-- Update trigger for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_memory_updated
    BEFORE UPDATE ON agent_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_nodes_updated
    BEFORE UPDATE ON knowledge_graph_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated
    BEFORE UPDATE ON learning_paths
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();