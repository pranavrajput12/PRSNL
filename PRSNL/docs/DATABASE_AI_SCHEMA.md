# Database Schema for AI Features - PRSNL v4.2.0

## Overview

This document outlines the database schema changes and considerations for PRSNL's enhanced AI capabilities.

## Current Schema (AI-Related Fields)

### Items Table
```sql
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    
    -- Content fields
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,
    type TEXT NOT NULL,
    
    -- AI-generated fields
    ai_title TEXT,                    -- AI-generated title
    ai_summary TEXT,                  -- Brief summary (validated)
    ai_tags TEXT[],                   -- Array of lowercase tags
    category TEXT,                    -- Validated category
    sentiment TEXT,                   -- positive/neutral/negative/mixed
    
    -- Transcription
    transcription TEXT,               -- Full transcription text
    transcription_metadata JSONB,     -- Metadata (confidence, duration, etc)
    
    -- Embeddings
    embedding vector(1536),           -- OpenAI embeddings
    
    -- Analysis
    entities JSONB,                   -- Extracted entities
    key_points TEXT[],                -- Key takeaways
    difficulty_level TEXT,            -- beginner/intermediate/advanced
    reading_time INTEGER,             -- Estimated minutes
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_items_embedding (embedding),
    INDEX idx_items_ai_tags (ai_tags),
    INDEX idx_items_category (category),
    INDEX idx_items_sentiment (sentiment)
);
```

### AI Processing Log (Recommended Addition)
```sql
CREATE TABLE ai_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    
    -- Processing details
    service_type TEXT NOT NULL,       -- 'analysis', 'transcription', 'summary'
    service_used TEXT NOT NULL,       -- 'gpt-4', 'whisper.cpp', etc
    model_version TEXT,               -- Model name/version
    
    -- Performance metrics
    processing_time_ms INTEGER,       -- Time taken
    tokens_used INTEGER,              -- For LLM calls
    confidence_score FLOAT,           -- Result confidence
    
    -- Validation
    validation_passed BOOLEAN,        -- Guardrails validation result
    validation_errors JSONB,          -- Any validation issues
    
    -- Request/Response
    request_params JSONB,             -- Input parameters
    response_data JSONB,              -- Full response (for debugging)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_ai_log_item_id (item_id),
    INDEX idx_ai_log_service (service_type, created_at)
);
```

## Recommended Schema Updates

### 1. Enhanced Transcription Storage
```sql
-- Add to items table
ALTER TABLE items ADD COLUMN IF NOT EXISTS transcription_segments JSONB;
-- Stores word-level timestamps and segments

-- Example structure:
{
  "segments": [
    {
      "text": "Hello world",
      "start": 0.0,
      "end": 1.5,
      "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98},
        {"word": "world", "start": 0.7, "end": 1.5, "confidence": 0.95}
      ]
    }
  ],
  "language": "en",
  "model_used": "base"
}
```

### 2. AI Analysis Versioning
```sql
-- Track different versions of AI analysis
CREATE TABLE ai_analysis_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    
    -- Versioned fields
    title TEXT,
    summary TEXT,
    detailed_summary TEXT,
    tags TEXT[],
    category TEXT,
    sentiment TEXT,
    key_points TEXT[],
    entities JSONB,
    
    -- Metadata
    model_used TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Unique constraint
    UNIQUE(item_id, version)
);
```

### 3. Content Quality Metrics
```sql
-- Track content quality over time
CREATE TABLE content_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    
    -- Quality scores
    transcription_confidence FLOAT,
    summary_quality_score FLOAT,
    tag_relevance_score FLOAT,
    overall_quality_score FLOAT,
    
    -- Validation metrics
    validation_failures INTEGER DEFAULT 0,
    required_repairs INTEGER DEFAULT 0,
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    
    -- Metadata
    evaluated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_quality_item_id (item_id),
    INDEX idx_quality_score (overall_quality_score)
);
```

## Migration Scripts

### Add AI Enhancement Fields
```sql
-- Add new AI fields to existing items table
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS ai_processing_version TEXT DEFAULT '1.0',
ADD COLUMN IF NOT EXISTS detailed_summary TEXT,
ADD COLUMN IF NOT EXISTS transcription_confidence FLOAT,
ADD COLUMN IF NOT EXISTS transcription_model TEXT;

-- Add constraints
ALTER TABLE items 
ADD CONSTRAINT chk_sentiment CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed', NULL)),
ADD CONSTRAINT chk_difficulty CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', NULL)),
ADD CONSTRAINT chk_category CHECK (category IN ('technology', 'business', 'science', 'health', 'education', 'entertainment', 'news', 'personal', 'other', NULL));
```

### Create Indexes for Performance
```sql
-- Optimize AI-related queries
CREATE INDEX IF NOT EXISTS idx_items_ai_processed ON items(ai_processed_at) WHERE ai_processed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_transcription ON items(id) WHERE transcription IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_difficulty ON items(difficulty_level) WHERE difficulty_level IS NOT NULL;

-- Full-text search on AI-generated content
CREATE INDEX IF NOT EXISTS idx_items_ai_search ON items USING gin(
    to_tsvector('english', COALESCE(ai_title, '') || ' ' || 
                          COALESCE(ai_summary, '') || ' ' || 
                          COALESCE(transcription, ''))
);
```

## Query Patterns

### Find Similar Content
```sql
-- Using embeddings for semantic search
SELECT id, title, ai_summary,
       1 - (embedding <=> $1) AS similarity
FROM items
WHERE embedding IS NOT NULL
ORDER BY embedding <=> $1
LIMIT 10;
```

### Content Quality Analysis
```sql
-- Find items that might need re-processing
SELECT i.id, i.title, i.type,
       cqm.overall_quality_score,
       apl.validation_passed,
       COUNT(apl.id) as processing_attempts
FROM items i
LEFT JOIN content_quality_metrics cqm ON i.id = cqm.item_id
LEFT JOIN ai_processing_log apl ON i.id = apl.item_id
WHERE i.ai_processed_at < NOW() - INTERVAL '30 days'
   OR cqm.overall_quality_score < 0.7
   OR apl.validation_passed = FALSE
GROUP BY i.id, i.title, i.type, cqm.overall_quality_score, apl.validation_passed
ORDER BY cqm.overall_quality_score ASC NULLS FIRST;
```

### Transcription Analytics
```sql
-- Analyze transcription usage and performance
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_transcriptions,
    AVG(CAST(transcription_metadata->>'confidence' AS FLOAT)) as avg_confidence,
    AVG(CAST(transcription_metadata->>'duration' AS FLOAT)) as avg_duration,
    STRING_AGG(DISTINCT transcription_metadata->>'model_used', ', ') as models_used
FROM items
WHERE transcription IS NOT NULL
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Best Practices

### 1. Data Integrity
- Always validate AI outputs before storing
- Use transactions for multi-table updates
- Keep original content separate from AI-generated

### 2. Performance
- Index frequently queried AI fields
- Use JSONB for flexible metadata storage
- Consider partitioning for large AI logs

### 3. Privacy
- Store transcriptions encrypted if sensitive
- Allow users to opt-out of AI processing
- Implement data retention policies

### 4. Versioning
- Track AI model versions used
- Keep history of AI analyses
- Allow rollback to previous versions

## Monitoring Queries

### AI Processing Health
```sql
-- Monitor AI processing success rate
SELECT 
    service_type,
    COUNT(*) as total_calls,
    SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) as successful,
    AVG(processing_time_ms) as avg_time_ms,
    AVG(confidence_score) as avg_confidence
FROM ai_processing_log
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY service_type;
```

### Storage Usage
```sql
-- Check AI-related storage usage
SELECT 
    pg_size_pretty(SUM(pg_column_size(transcription))) as transcription_size,
    pg_size_pretty(SUM(pg_column_size(embedding))) as embedding_size,
    pg_size_pretty(SUM(pg_column_size(ai_summary))) as summary_size,
    COUNT(*) as total_items
FROM items
WHERE ai_processed_at IS NOT NULL;
```

## Future Considerations

1. **Multi-modal Embeddings**: Store separate embeddings for text/image/audio
2. **Versioned Embeddings**: Track embedding model versions
3. **Language-specific Fields**: Support multi-language content
4. **Real-time Updates**: Stream processing results to database
5. **Federation**: Sync AI results across instances

---

This schema design ensures:
- ✅ Efficient storage of AI-generated content
- ✅ Tracking and monitoring capabilities
- ✅ Flexibility for future enhancements
- ✅ Performance optimization for AI queries