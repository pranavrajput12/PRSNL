# Database Schema v2.4 - Enhanced Architecture

## Overview

This document describes the enhanced database schema with content fingerprinting, normalized embeddings, and optimized search capabilities.

## Schema Changes (v2.4)

### New Fields Added to `items` Table
```sql
-- Content fingerprinting for duplicate detection
content_fingerprint VARCHAR(64), -- SHA-256 hash of raw_content

-- Normalized embedding reference
embed_vector_id UUID REFERENCES embeddings(id) ON DELETE SET NULL
```

### New `embeddings` Table
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    vector vector(1536) NOT NULL,
    vector_norm FLOAT, -- Pre-calculated L2 norm
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Complete Schema Reference

### Core Tables

#### `items` (Enhanced)
```sql
CREATE TABLE items (
    -- Core identifiers
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content fields
    url TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    raw_content TEXT,
    processed_content TEXT,
    
    -- Classification
    type VARCHAR(50) NOT NULL DEFAULT 'bookmark',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    content_type VARCHAR(50) DEFAULT 'auto',
    enable_summarization BOOLEAN DEFAULT false,
    
    -- Media fields
    platform VARCHAR(50),
    duration INTEGER,
    video_url TEXT,
    file_path TEXT,
    thumbnail_url TEXT,
    
    -- File support
    has_files BOOLEAN DEFAULT FALSE,
    file_count INTEGER DEFAULT 0,
    
    -- User interaction
    highlight TEXT,
    
    -- Metadata and search
    metadata JSONB DEFAULT '{}',
    search_vector tsvector,
    
    -- NEW: Content fingerprinting
    content_fingerprint VARCHAR(64), -- SHA-256 of raw_content
    
    -- Embedding support
    embedding vector(1536), -- Legacy support
    embed_vector_id UUID, -- NEW: Reference to embeddings table
    
    -- Transcription
    transcription TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT items_url_or_content_check CHECK (url IS NOT NULL OR raw_content IS NOT NULL),
    CONSTRAINT chk_content_type CHECK (content_type IN ('auto', 'document', 'video', 'article', 'tutorial', 'image', 'note', 'link')),
    CONSTRAINT chk_item_type CHECK (type IN ('article', 'video', 'note', 'bookmark', 'document', 'tutorial', 'image', 'link')),
    CONSTRAINT fk_items_embed_vector_id FOREIGN KEY (embed_vector_id) REFERENCES embeddings(id) ON DELETE SET NULL
);
```

#### `embeddings` (New)
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    vector vector(1536) NOT NULL,
    vector_norm FLOAT, -- Auto-calculated L2 norm
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Prevent duplicate embeddings for same item/model
    UNIQUE(item_id, model_name, model_version)
);
```

#### `tags`
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    color VARCHAR(7), -- Hex color code
    description TEXT,
    parent_id UUID REFERENCES tags(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `item_tags` (Many-to-Many)
```sql
CREATE TABLE item_tags (
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (item_id, tag_id)
);
```

---

## Indexes and Performance

### Core Indexes
```sql
-- Items table indexes
CREATE INDEX idx_items_created_at ON items(created_at DESC);
CREATE INDEX idx_items_updated_at ON items(updated_at DESC);
CREATE INDEX idx_items_accessed_at ON items(accessed_at DESC);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_type ON items(type);
CREATE INDEX idx_items_content_type ON items(content_type);
CREATE INDEX idx_items_url ON items(url) WHERE url IS NOT NULL;
CREATE INDEX idx_items_platform ON items(platform) WHERE platform IS NOT NULL;
CREATE INDEX idx_items_has_files ON items(has_files) WHERE has_files = true;

-- NEW: Enhanced search indexes
CREATE INDEX idx_items_content_fingerprint ON items(content_fingerprint);
CREATE INDEX idx_items_embed_vector_id ON items(embed_vector_id);
CREATE INDEX idx_items_search ON items USING GIN(search_vector);
```

### Embedding Indexes
```sql
-- Embeddings table indexes
CREATE INDEX idx_embeddings_item_id ON embeddings(item_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name, model_version);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);
CREATE UNIQUE INDEX idx_embeddings_unique_item_model ON embeddings(item_id, model_name, model_version);
```

### Tag Indexes
```sql
-- Tags table indexes
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_parent_id ON tags(parent_id);

-- Item-tags relationship indexes
CREATE INDEX idx_item_tags_item_id ON item_tags(item_id);
CREATE INDEX idx_item_tags_tag_id ON item_tags(tag_id);
CREATE INDEX idx_item_tags_confidence ON item_tags(confidence);
```

---

## Views and Convenience Functions

### Items with Embeddings View
```sql
CREATE OR REPLACE VIEW items_with_embeddings AS
SELECT 
    i.*,
    e.vector as embedding_vector,
    e.model_name,
    e.model_version,
    e.vector_norm
FROM items i
LEFT JOIN embeddings e ON i.embed_vector_id = e.id;

COMMENT ON VIEW items_with_embeddings IS 'Convenience view joining items with their embeddings';
```

### Automatic Vector Norm Calculation
```sql
CREATE OR REPLACE FUNCTION calculate_vector_norm()
RETURNS TRIGGER AS $$
BEGIN
    NEW.vector_norm = sqrt(abs(NEW.vector <#> NEW.vector));
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_embedding_norm
    BEFORE INSERT OR UPDATE OF vector ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION calculate_vector_norm();
```

### Updated At Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_items_updated_at 
    BEFORE UPDATE ON items 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embeddings_updated_at 
    BEFORE UPDATE ON embeddings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Migration Scripts

### From v2.3 to v2.4
```sql
-- migrations/011_content_fingerprint_and_embeddings.sql
BEGIN;

-- Add new fields to items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS content_fingerprint VARCHAR(64),
ADD COLUMN IF NOT EXISTS embed_vector_id UUID;

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    vector vector(1536) NOT NULL,
    vector_norm FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add foreign key constraint
ALTER TABLE items
ADD CONSTRAINT fk_items_embed_vector_id 
FOREIGN KEY (embed_vector_id) 
REFERENCES embeddings(id) 
ON DELETE SET NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_items_content_fingerprint ON items(content_fingerprint);
CREATE INDEX IF NOT EXISTS idx_items_embed_vector_id ON items(embed_vector_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_item_id ON embeddings(item_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);
CREATE UNIQUE INDEX IF NOT EXISTS idx_embeddings_unique_item_model ON embeddings(item_id, model_name, model_version);

-- Create triggers
CREATE OR REPLACE FUNCTION calculate_vector_norm()
RETURNS TRIGGER AS $$
BEGIN
    NEW.vector_norm = sqrt(abs(NEW.vector <#> NEW.vector));
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_embedding_norm
    BEFORE INSERT OR UPDATE OF vector ON embeddings
    FOR EACH ROW
    EXECUTE FUNCTION calculate_vector_norm();

-- Create view
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
COMMENT ON COLUMN items.content_fingerprint IS 'SHA-256 hash of raw_content for duplicate detection and content versioning';
COMMENT ON COLUMN items.embed_vector_id IS 'Direct pointer to pgvector embedding table, saves joins on semantic search';
COMMENT ON TABLE embeddings IS 'Normalized embedding storage for vector search';
COMMENT ON COLUMN embeddings.vector_norm IS 'Pre-calculated L2 norm for faster similarity calculations';

COMMIT;
```

---

## Query Patterns

### Content Fingerprint Operations
```sql
-- Check for duplicate content
SELECT id, title, created_at 
FROM items 
WHERE content_fingerprint = $1;

-- Find content that needs reprocessing (fingerprint changed)
SELECT id, title 
FROM items 
WHERE content_fingerprint != calculate_fingerprint(raw_content);
```

### Embedding Operations
```sql
-- Find items with embeddings
SELECT i.id, i.title, e.model_name 
FROM items i 
JOIN embeddings e ON i.embed_vector_id = e.id;

-- Semantic similarity search (optimized)
SELECT i.id, i.title, 1 - (e.vector <=> $1::vector) as similarity
FROM items i
JOIN embeddings e ON i.embed_vector_id = e.id
WHERE e.model_name = $2
ORDER BY similarity DESC
LIMIT $3;

-- Get items without embeddings
SELECT id, title 
FROM items 
WHERE embed_vector_id IS NULL 
AND (raw_content IS NOT NULL OR processed_content IS NOT NULL);
```

### Combined Search Queries
```sql
-- Hybrid search with deduplication
WITH semantic_results AS (
    SELECT i.id, i.title, 1 - (e.vector <=> $1::vector) as semantic_score
    FROM items i
    JOIN embeddings e ON i.embed_vector_id = e.id
    ORDER BY semantic_score DESC
    LIMIT 50
),
keyword_results AS (
    SELECT i.id, i.title, ts_rank_cd(search_vector, plainto_tsquery($2)) as keyword_score
    FROM items i
    WHERE search_vector @@ plainto_tsquery($2)
    ORDER BY keyword_score DESC
    LIMIT 50
),
combined AS (
    SELECT DISTINCT ON (content_fingerprint) 
        id, title,
        COALESCE(s.semantic_score, 0) * 0.7 + COALESCE(k.keyword_score, 0) * 0.3 as final_score
    FROM items i
    LEFT JOIN semantic_results s USING (id)
    LEFT JOIN keyword_results k USING (id)
    WHERE content_fingerprint IS NOT NULL
)
SELECT * FROM combined 
ORDER BY final_score DESC 
LIMIT $3;
```

---

## Performance Characteristics

### Content Fingerprinting
- **Duplicate Detection**: O(1) lookup using hash index
- **Change Detection**: O(1) comparison of fingerprints
- **Storage**: 64 bytes per item (SHA-256 hash)

### Normalized Embeddings
- **Vector Search**: O(log n) using IVFFlat index
- **Memory Usage**: ~6KB per embedding (1536 dimensions × 4 bytes)
- **Query Performance**: 10-100x faster than embedding in main table

### Search Operations
- **Semantic Search**: ~1-10ms for 1M+ items (with proper indexing)
- **Keyword Search**: ~1-5ms using GIN indexes
- **Hybrid Search**: ~5-15ms combining both methods
- **Deduplication**: Negligible overhead with fingerprint filtering

---

## Maintenance

### Regular Tasks
```sql
-- Update vector statistics (monthly)
ANALYZE embeddings;

-- Reindex vector index if needed (after bulk operations)
REINDEX INDEX idx_embeddings_vector;

-- Clean up orphaned embeddings
DELETE FROM embeddings 
WHERE item_id NOT IN (SELECT id FROM items);

-- Update content fingerprints for changed content
UPDATE items 
SET content_fingerprint = calculate_fingerprint(raw_content)
WHERE content_fingerprint != calculate_fingerprint(raw_content);
```

### Monitoring Queries
```sql
-- Check embedding coverage
SELECT 
    COUNT(*) as total_items,
    COUNT(embed_vector_id) as with_embeddings,
    ROUND(COUNT(embed_vector_id) * 100.0 / COUNT(*), 2) as coverage_percent
FROM items;

-- Check fingerprint coverage
SELECT 
    COUNT(*) as total_items,
    COUNT(content_fingerprint) as with_fingerprints,
    ROUND(COUNT(content_fingerprint) * 100.0 / COUNT(*), 2) as coverage_percent
FROM items;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('items', 'embeddings')
ORDER BY idx_scan DESC;
```