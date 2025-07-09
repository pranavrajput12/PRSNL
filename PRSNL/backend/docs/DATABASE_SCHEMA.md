# PRSNL Database Schema Documentation

## Items Table

The main table storing all captured content.

```sql
CREATE TABLE items (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url               TEXT NOT NULL,
    title             TEXT NOT NULL,
    summary           TEXT,
    raw_content       TEXT,
    processed_content TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending',
    search_vector     TSVECTOR,
    metadata          JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count      INTEGER DEFAULT 0,
    embedding         VECTOR(1536),
    transcription     TEXT
);
```

### Status Values
- `pending` - Item is being processed
- `completed` - Item successfully processed
- `failed` - Processing failed
- `bookmark` - Quick bookmark without full processing

### Metadata JSONB Fields
```json
{
    "item_type": "video|article|tweet|github|pdf",
    "platform": "youtube|twitter|github|web",
    "tags": "comma,separated,tags",
    "category": "programming|ai|productivity|etc",
    "thumbnail_url": "https://...",
    "duration": 3600,  // seconds for videos
    "file_path": "/media/videos/...",
    "author": "@username",
    "likes": 12345,
    "stars": 5000,
    "language": "JavaScript",
    "read_time": 15  // minutes for articles
}
```

## Tags System

```sql
CREATE TABLE tags (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name       VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE item_tags (
    item_id    UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id     UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (item_id, tag_id)
);
```

## API Response Formats

### Timeline Response
```typescript
{
    items: [
        {
            id: string,
            title: string,
            url: string,
            summary?: string,
            platform?: string,
            item_type: string,  // Derived from metadata or URL patterns
            thumbnail_url?: string,
            duration?: number,
            file_path?: string,
            status: string,
            createdAt: string,  // Frontend expects camelCase
            updatedAt?: string,
            tags: string[]
        }
    ],
    next_cursor?: string
}
```

### Capture Request
```typescript
{
    url: string,
    title?: string,
    tags?: string[],
    notes?: string,
    item_type?: string,
    summary?: string
}
```

### Search Response
```typescript
{
    results: [
        {
            id: string,
            title: string,
            url: string,
            snippet: string,
            tags: string[],
            created_at: string,
            type: string,
            similarity_score?: number
        }
    ]
}
```

## Important Notes

1. **Item Type**: Stored in `metadata->>'item_type'`, NOT as a separate column
2. **Tags**: Stored both in normalized tables AND in `metadata->>'tags'` as comma-separated
3. **Status**: Must be 'completed' for items to appear in timeline
4. **Frontend expects camelCase**: Transform snake_case fields in API responses
5. **Search Vector**: Auto-updated by trigger on title, summary, processed_content changes

## Common Queries

### Get Timeline Items
```sql
SELECT 
    i.*,
    ARRAY_AGG(t.name) as tags
FROM items i
LEFT JOIN item_tags it ON i.id = it.item_id
LEFT JOIN tags t ON it.tag_id = t.id
WHERE i.status IN ('completed', 'bookmark')
GROUP BY i.id
ORDER BY i.created_at DESC
LIMIT 20;
```

### Search Items
```sql
SELECT * FROM items
WHERE search_vector @@ plainto_tsquery('english', 'search terms')
ORDER BY ts_rank(search_vector, plainto_tsquery('english', 'search terms')) DESC;
```