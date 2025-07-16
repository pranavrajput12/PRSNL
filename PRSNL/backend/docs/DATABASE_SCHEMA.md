# PRSNL Database Schema Documentation

Last Updated: 2025-07-16  
**Complete and Current Database Schema Reference**

## Overview

The PRSNL database uses PostgreSQL 16 with ARM64 architecture and includes the pgvector extension for semantic search capabilities. The system now includes comprehensive authentication and user management tables for JWT-based authentication.

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

---

**Note**: This documentation reflects the current state after the complete schema migration completed on 2025-07-12. All tables, columns, and indexes are now synchronized between development and production environments.