# PRSNL Database Schema Documentation

Last Updated: 2025-08-01  
**Complete and Current Database Schema Reference**

## Overview

The PRSNL database uses PostgreSQL 16 with ARM64 architecture and includes the pgvector extension for semantic search capabilities. The system includes comprehensive authentication, user management, and an advanced **AI-powered knowledge graph system** with entity extraction, relationship analysis, semantic clustering, and gap detection capabilities.

## Core Tables

### 1. Items Table (Main Content Storage)

The primary table storing all captured content including articles, videos, code repositories, and development resources.

```sql
CREATE TABLE items (
    -- Core Identification
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url                  TEXT,
    title                TEXT NOT NULL,
    summary              TEXT,
    
    -- Content Storage
    content              TEXT,                    -- Legacy content field
    raw_content          TEXT,                    -- Original extracted content
    processed_content    TEXT,                    -- AI-processed/cleaned content
    transcription        TEXT,                    -- Video/audio transcription
    
    -- Classification & Status
    type                 VARCHAR(50) DEFAULT 'bookmark',     -- 'bookmark', 'article', 'video', 'development', etc.
    status               VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'completed', 'failed', 'bookmark'
    content_type         VARCHAR(20) DEFAULT 'auto',         -- 'auto', 'manual', 'ai_generated'
    platform             VARCHAR(255),                       -- 'youtube', 'github', 'twitter', etc.
    
    -- Development-Specific Fields (Code Cortex)
    programming_language TEXT,                               -- 'Python', 'JavaScript', 'Rust', etc.
    project_category     TEXT,                               -- 'Frontend', 'Backend', 'AI/ML', etc.
    difficulty_level     INTEGER,                            -- 1-5 scale
    is_career_related    BOOLEAN DEFAULT FALSE,              -- Career development relevance
    learning_path        TEXT,                               -- Learning track/course name
    code_snippets        JSONB,                              -- Structured code examples
    
    -- Media & Files
    thumbnail_url        TEXT,                               -- Preview image URL
    duration             INTEGER,                            -- Video duration in seconds
    video_url            TEXT,                               -- Video file URL
    file_path            TEXT,                               -- Local file path
    has_files            BOOLEAN DEFAULT FALSE,              -- Has associated files
    file_count           INTEGER DEFAULT 0,                  -- Number of attached files
    highlight            TEXT,                               -- User highlighted content
    
    -- AI & Search
    embedding            VECTOR(1536),                       -- OpenAI embedding (legacy)
    embed_vector_id      UUID,                               -- FK to embeddings table (new)
    search_vector        TSVECTOR,                           -- Full-text search index
    content_fingerprint  VARCHAR(255),                       -- Content change detection
    
    -- Configuration
    enable_summarization BOOLEAN DEFAULT FALSE,              -- Auto-summarization enabled
    metadata             JSONB DEFAULT '{}',                 -- Additional structured data
    
    -- Timestamps & Usage
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count         INTEGER DEFAULT 0
);
```

#### Item Status Values
- `pending` - Being processed/extracted
- `completed` - Successfully processed and ready
- `failed` - Processing failed
- `bookmark` - Quick save without full processing

#### Item Type Values
- `bookmark` - Simple bookmark
- `article` - Web article/blog post
- `video` - Video content
- `development` - Development/coding content
- `pdf` - PDF document
- `tweet` - Twitter/social media post

#### Development Categories (project_category)
- `Frontend` - React, Vue, Angular, UI/UX
- `Backend` - APIs, databases, server-side
- `DevOps` - CI/CD, deployment, containerization
- `Mobile` - iOS, Android, React Native
- `AI/ML` - Machine learning, data science
- `Data Science` - Analytics, visualization
- `Code Snippets` - Reusable utilities
- `Documentation` - Technical docs, tutorials
- `Tools` - Development tools, utilities
- `Security` - Security practices, implementations

### 2. Tags System

Hierarchical tagging system with many-to-many relationships.

```sql
CREATE TABLE tags (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name       VARCHAR(100) UNIQUE NOT NULL,
    parent_id  UUID REFERENCES tags(id),              -- For hierarchical tags
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE item_tags (
    item_id    UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id     UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (item_id, tag_id)
);
```

### 3. Embeddings Table (Normalized Vector Storage)

Modern approach to storing multiple embeddings per item with different models.

```sql
CREATE TABLE embeddings (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id       UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name    VARCHAR(255) NOT NULL,               -- 'text-embedding-ada-002', etc.
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',   -- Model version tracking
    vector        VECTOR(1536),                        -- pgvector embedding
    vector_norm   FLOAT,                               -- Vector normalization
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_id, model_name, model_version)
);
```

### 4. Development Categories

Categories specifically for Code Cortex development content.

```sql
CREATE TABLE development_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    icon        VARCHAR(10) DEFAULT '📁',               -- Emoji icon
    color       VARCHAR(20) DEFAULT '#10b981',          -- Hex color
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 5. Chat & Conversations

AI chat functionality with conversation history.

```sql
CREATE TABLE conversations (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,              -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 6. File Management

Attachment and file tracking system.

```sql
CREATE TABLE files (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id     UUID REFERENCES items(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    file_size   BIGINT,
    mime_type   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE attachments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id     UUID REFERENCES items(id) ON DELETE CASCADE,
    file_name   TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    file_size   INTEGER,
    mime_type   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 7. Analytics & Tracking

User activity and video analysis tracking.

```sql
CREATE TABLE user_activity (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id     UUID REFERENCES items(id) ON DELETE CASCADE,
    action      VARCHAR(50) NOT NULL,                  -- 'view', 'edit', 'delete', etc.
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE video_analysis (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id     UUID REFERENCES items(id) ON DELETE CASCADE,
    analysis    JSONB NOT NULL,                        -- AI analysis results
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 8. Authentication & User Management

JWT-based authentication with email verification and session management.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(255) UNIQUE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE verification_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           VARCHAR(255) UNIQUE NOT NULL,
    token_type      VARCHAR(50) NOT NULL,           -- 'email_verification', 'magic_link'
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT verification_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for authentication tables
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_verification_tokens_user_id ON verification_tokens(user_id);
CREATE INDEX idx_verification_tokens_token ON verification_tokens(token);
CREATE INDEX idx_verification_tokens_expires_at ON verification_tokens(expires_at);
```

## 9. AI-Powered Knowledge Graph System

The knowledge graph system provides intelligent entity extraction, relationship analysis, semantic clustering, and knowledge gap detection. This advanced system was implemented in Phase 2 and includes 6 major tables with sophisticated AI algorithms.

### 9.1 Unified Entities Table

Central entity storage for cross-feature knowledge graph integration.

```sql
CREATE TABLE unified_entities (
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
```

**Key Features:**
- **Polymorphic Design**: Supports 11 different entity types
- **AI Confidence Scoring**: Machine learning confidence ratings (0-1 scale)
- **Hierarchical Structure**: Parent-child entity relationships
- **Position Tracking**: Precise location tracking for content segments
- **Extraction Method Tracking**: Distinguishes between manual, AI, and user-defined entities

### 9.2 Unified Relationships Table

Advanced relationship system with 18+ semantic relationship types and AI confidence scoring.

```sql
CREATE TABLE unified_relationships (
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
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Advanced Features:**
- **18 Semantic Relationship Types**: Covers temporal, content, structural, cross-modal, and learning relationships
- **Bidirectional Support**: Automatic reverse relationship creation
- **Evidence Tracking**: JSONB storage for relationship justification
- **Strength vs Confidence**: Separate metrics for relationship importance and AI certainty
- **Context Preservation**: Human-readable explanation of relationship reasoning

### 9.3 Conversation Analysis Tables

Enhanced conversation processing with entity linking and topic detection.

```sql
-- Enhanced conversation turns with entity linking
CREATE TABLE conversation_turns (
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
CREATE TABLE conversation_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES items(id) ON DELETE CASCADE,
    topic_name TEXT NOT NULL,
    start_turn INTEGER,
    end_turn INTEGER,
    relevance_score FLOAT DEFAULT 1.0,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.4 Video Analysis Tables

Time-based video content analysis with AI-powered segmentation.

```sql
-- Video segments with enhanced metadata
CREATE TABLE video_segments (
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

-- Video chapters and structure
CREATE TABLE video_chapters (
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
```

### 9.5 Code Structure Analysis Tables

Advanced code entity extraction with dependency tracking.

```sql
-- Code entities (functions, classes, modules)
CREATE TABLE code_entities (
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
CREATE TABLE code_dependencies (
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
```

### 9.6 Timeline and Event Analysis

Enhanced event tracking with cross-content relationships.

```sql
-- Timeline events with enhanced context
CREATE TABLE timeline_events (
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
```

### 9.7 Cross-Feature Integration Tables

Advanced linking and user interaction tracking.

```sql
-- Link content items to entities for cross-referencing
CREATE TABLE content_entity_links (
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
CREATE TABLE entity_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- From auth system when available
    entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('view', 'edit', 'like', 'bookmark', 'share', 'comment', 'rate')),
    interaction_value JSONB DEFAULT '{}', -- Rating, comment text, etc.
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id TEXT,
    metadata JSONB DEFAULT '{}',
    INDEX (user_id),
    INDEX (entity_id),
    INDEX (interaction_type),
    INDEX (timestamp)
);
```

### 9.8 Analytics and Performance Views

Materialized views for high-performance analytics.

```sql
-- Entity statistics view
CREATE MATERIALIZED VIEW entity_statistics AS
SELECT 
    entity_type,
    COUNT(*) as total_entities,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT source_content_id) as unique_sources,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM unified_entities 
GROUP BY entity_type;

-- Relationship statistics view
CREATE MATERIALIZED VIEW relationship_statistics AS
SELECT 
    relationship_type,
    COUNT(*) as total_relationships,
    AVG(confidence_score) as avg_confidence,
    AVG(strength) as avg_strength,
    COUNT(DISTINCT source_entity_id) as unique_sources,
    COUNT(DISTINCT target_entity_id) as unique_targets
FROM unified_relationships 
GROUP BY relationship_type;
```

### 9.9 Knowledge Graph Functions

Advanced PostgreSQL functions for knowledge graph operations.

```sql
-- Automatic entity creation from content
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

-- Relationship creation with validation
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

-- Refresh analytics views
CREATE OR REPLACE FUNCTION refresh_knowledge_graph_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;
END;
$$ LANGUAGE plpgsql;
```

### 9.10 Knowledge Graph Performance Indexes

Optimized indexes for high-performance graph operations.

```sql
-- Composite indexes for complex queries
CREATE INDEX idx_unified_entities_composite ON unified_entities(entity_type, source_content_id, created_at);
CREATE INDEX idx_unified_relationships_composite ON unified_relationships(relationship_type, confidence_score, created_at);

-- Full-text search indexes
CREATE INDEX idx_unified_entities_name_fts ON unified_entities USING gin(to_tsvector('english', name));
CREATE INDEX idx_unified_entities_description_fts ON unified_entities USING gin(to_tsvector('english', description));

-- Performance indexes for analytics
CREATE INDEX idx_entity_statistics_type ON entity_statistics(entity_type);
CREATE INDEX idx_relationship_statistics_type ON relationship_statistics(relationship_type);
```

## Database Indexes

### Performance Indexes
```sql
-- Items table indexes
CREATE INDEX idx_items_created ON items(created_at DESC);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_search ON items USING gin(search_vector);
CREATE INDEX idx_items_content_type ON items(content_type);
CREATE INDEX items_programming_language_idx ON items(programming_language);
CREATE INDEX items_project_category_idx ON items(project_category);
CREATE INDEX items_difficulty_level_idx ON items(difficulty_level);
CREATE INDEX items_is_career_related_idx ON items(is_career_related);
CREATE INDEX items_platform_idx ON items(platform);

-- Vector search indexes
CREATE INDEX items_embedding_idx ON items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX embeddings_vector_idx ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
```

## Database Triggers

### Auto-Update Triggers
```sql
-- Search vector auto-update
CREATE TRIGGER items_search_vector_update 
    BEFORE INSERT OR UPDATE OF title, summary, processed_content 
    ON items FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Updated timestamp auto-update
CREATE TRIGGER items_updated_at 
    BEFORE UPDATE ON items FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Item creation notifications
CREATE TRIGGER items_notify_created 
    AFTER INSERT ON items FOR EACH ROW EXECUTE FUNCTION notify_item_created();
```

## JSON Schema Examples

### Item Metadata Structure
```json
{
    "platform": "github",
    "video_metadata": {
        "platform": "youtube",
        "thumbnail": "https://img.youtube.com/...",
        "video_info": {
            "duration": 1800,
            "views": 50000
        }
    },
    "author": "username",
    "stars": 1250,
    "forks": 340,
    "language": "Python",
    "topics": ["web", "api", "python"],
    "file_path": "/media/videos/example.mp4",
    "thumbnail_url": "https://example.com/thumb.jpg"
}
```

### Code Snippets Structure
```json
[
    {
        "title": "FastAPI Basic Setup",
        "language": "python",
        "code": "from fastapi import FastAPI\napp = FastAPI()",
        "description": "Basic FastAPI application setup",
        "created_at": "2025-07-12T10:00:00Z"
    }
]
```

## API Response Transformations

### Timeline Item Response
```typescript
interface TimelineItem {
    id: string;
    title: string;
    url?: string;
    summary?: string;
    platform?: string;
    type: string;
    thumbnail_url?: string;
    duration?: number;
    file_path?: string;
    status: string;
    createdAt: string;        // Note: camelCase for frontend
    updatedAt?: string;       // Note: camelCase for frontend
    tags: string[];
}
```

### Development Item Response
```typescript
interface DevelopmentItem {
    id: string;
    title: string;
    url?: string;
    summary?: string;
    type: string;
    programming_language?: string;
    project_category?: string;
    difficulty_level?: number;
    is_career_related: boolean;
    learning_path?: string;
    code_snippets: CodeSnippet[];
    created_at: string;
    updated_at?: string;
    tags: string[];
}
```

## Common Query Patterns

### Get Timeline Items (with proper status filtering)
```sql
SELECT 
    i.id, i.title, i.url, i.summary, i.created_at,
    COALESCE(i.metadata->>'platform', i.platform) as platform,
    ARRAY_AGG(t.name) FILTER (WHERE t.name IS NOT NULL) as tags
FROM items i
LEFT JOIN item_tags it ON i.id = it.item_id
LEFT JOIN tags t ON it.tag_id = t.id
WHERE i.status IN ('completed', 'bookmark', 'pending')
GROUP BY i.id
ORDER BY i.created_at DESC
LIMIT 20;
```

### Get Development Items with Stats
```sql
SELECT 
    COUNT(*) as total_items,
    COUNT(*) FILTER (WHERE programming_language IS NOT NULL) as with_language,
    COUNT(*) FILTER (WHERE is_career_related = TRUE) as career_related
FROM items 
WHERE type = 'development' AND status = 'completed';
```

### Semantic Search (using new embeddings table)
```sql
SELECT 
    i.id, i.title, i.summary,
    1 - (e.vector <=> $1::vector) as similarity
FROM items i
JOIN embeddings e ON i.embed_vector_id = e.id
WHERE e.model_name = 'text-embedding-ada-002'
AND 1 - (e.vector <=> $1::vector) > 0.7
ORDER BY similarity DESC
LIMIT 10;
```

## Important Migration Notes

1. **Vector Storage**: Migrated from `items.embedding` to normalized `embeddings` table
2. **Development Fields**: Added comprehensive development-specific columns for Code Cortex
3. **Status Requirements**: Items must have status 'completed', 'bookmark', or 'pending' to appear in timeline
4. **Architecture**: ARM64 PostgreSQL with pgvector extension properly installed
5. **Backward Compatibility**: Legacy `embedding` column maintained for compatibility

## Maintenance Commands

### Update Development Item Categories
```sql
-- Auto-categorize based on content analysis
UPDATE items SET 
    type = 'development',
    project_category = CASE 
        WHEN title ILIKE '%react%' OR title ILIKE '%frontend%' THEN 'Frontend'
        WHEN title ILIKE '%api%' OR title ILIKE '%backend%' THEN 'Backend'
        WHEN title ILIKE '%docker%' OR title ILIKE '%devops%' THEN 'DevOps'
        WHEN title ILIKE '%ai%' OR title ILIKE '%ml%' THEN 'AI/ML'
        WHEN url ILIKE '%github.com%' THEN 'Tools'
        ELSE 'Documentation'
    END
WHERE (title ILIKE '%code%' OR url ILIKE '%github.com%' OR title ILIKE '%programming%');
```

### Rebuild Search Vectors
```sql
UPDATE items SET search_vector = to_tsvector('english', 
    title || ' ' || COALESCE(summary, '') || ' ' || COALESCE(processed_content, '')
) WHERE search_vector IS NULL;
```

## Knowledge Graph API Operations

### Advanced Query Patterns

#### Knowledge Path Discovery
```sql
-- Find learning paths between entities using graph traversal
WITH RECURSIVE path_finder AS (
    SELECT 
        source_entity_id,
        target_entity_id,
        relationship_type,
        confidence_score,
        ARRAY[source_entity_id] as path,
        1 as depth
    FROM unified_relationships
    WHERE source_entity_id = $start_entity_id
    AND confidence_score >= $min_confidence
    
    UNION ALL
    
    SELECT 
        ur.source_entity_id,
        ur.target_entity_id,
        ur.relationship_type,
        ur.confidence_score * pf.confidence_score,
        pf.path || ur.source_entity_id,
        pf.depth + 1
    FROM unified_relationships ur
    JOIN path_finder pf ON ur.source_entity_id = pf.target_entity_id
    WHERE pf.depth < $max_depth
    AND NOT ur.source_entity_id = ANY(pf.path)
)
SELECT * FROM path_finder WHERE target_entity_id = $end_entity_id;
```

#### Semantic Clustering Analysis
```sql
-- Find entities with high semantic similarity for clustering
SELECT 
    e1.id as entity1_id,
    e1.name as entity1_name,
    e2.id as entity2_id, 
    e2.name as entity2_name,
    -- Calculate similarity based on shared relationships
    COUNT(DISTINCT r1.relationship_type) as shared_relationship_types,
    AVG(r1.confidence_score + r2.confidence_score) / 2 as avg_confidence
FROM unified_entities e1
JOIN unified_relationships r1 ON e1.id = r1.source_entity_id
JOIN unified_relationships r2 ON r2.target_entity_id = r1.target_entity_id
JOIN unified_entities e2 ON e2.id = r2.source_entity_id
WHERE e1.id != e2.id
AND e1.entity_type = e2.entity_type
GROUP BY e1.id, e1.name, e2.id, e2.name
HAVING COUNT(DISTINCT r1.relationship_type) >= $min_shared_relationships
ORDER BY shared_relationship_types DESC, avg_confidence DESC;
```

#### Knowledge Gap Detection
```sql
-- Identify isolated entities (potential knowledge gaps)
SELECT 
    ue.id,
    ue.name,
    ue.entity_type,
    ue.confidence_score,
    COUNT(ur.id) as relationship_count
FROM unified_entities ue
LEFT JOIN unified_relationships ur ON (ue.id = ur.source_entity_id OR ue.id = ur.target_entity_id)
GROUP BY ue.id, ue.name, ue.entity_type, ue.confidence_score
HAVING COUNT(ur.id) <= $max_relationships
ORDER BY relationship_count ASC, ue.confidence_score DESC;
```

### API Endpoint Integration

The knowledge graph system exposes RESTful APIs at `/api/unified-knowledge-graph/*`:

- **GET /visual/full** - Complete knowledge graph for D3.js visualization
- **GET /visual/{item_id}** - Item-centered graph with configurable depth
- **GET /stats** - Comprehensive graph statistics and analytics
- **POST /relationships** - Create new entity relationships
- **DELETE /relationships/{id}** - Remove relationships
- **POST /paths/discover** - Find knowledge paths between entities
- **POST /relationships/suggest** - AI-powered relationship suggestions
- **POST /analysis/gaps** - Knowledge gap analysis and recommendations
- **POST /clustering/semantic** - Semantic clustering with multiple algorithms

### Performance Optimization

#### Graph Traversal Optimization
```sql
-- Optimized adjacency list query for large graphs
SELECT 
    source_entity_id,
    array_agg(
        json_build_object(
            'target', target_entity_id,
            'relationship', relationship_type,
            'confidence', confidence_score,
            'strength', strength
        )
    ) as adjacency_list
FROM unified_relationships
WHERE confidence_score >= $min_confidence
GROUP BY source_entity_id;
```

#### Materialized View Refresh Strategy
```sql
-- Efficient incremental refresh for large datasets
REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;

-- Conditional refresh based on data changes
CREATE OR REPLACE FUNCTION conditional_refresh_stats()
RETURNS void AS $$
BEGIN
    IF (SELECT COUNT(*) FROM pg_stat_user_tables WHERE relname = 'unified_entities' AND n_tup_ins + n_tup_upd + n_tup_del > 100) THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
    END IF;
    
    IF (SELECT COUNT(*) FROM pg_stat_user_tables WHERE relname = 'unified_relationships' AND n_tup_ins + n_tup_upd + n_tup_del > 100) THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

**Note**: This documentation reflects the current state after the knowledge graph extension migration completed on 2025-08-01. The system now includes 140+ entities and 176+ relationships with advanced AI-powered analysis capabilities. All tables, indexes, and APIs are synchronized between development and production environments.