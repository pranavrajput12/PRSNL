# Enhanced Search API Documentation

## Overview

The Enhanced Search API provides advanced multi-modal search capabilities with content fingerprint-based deduplication and normalized embedding architecture. This API supports semantic, keyword, and hybrid search modes with automatic performance optimization.

## Base URL
```
http://localhost:8000/api/search
```

## Authentication
All endpoints support optional authentication. Include user context when available for personalized results.

---

## Endpoints

### 1. Enhanced Search (Main Endpoint)

**POST** `/search/`

Perform multi-modal search with automatic deduplication and advanced filtering.

#### Request Body
```json
{
  "query": "machine learning healthcare",
  "search_type": "hybrid",
  "limit": 20,
  "threshold": 0.3,
  "include_duplicates": false,
  "filters": {
    "type": "article",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

#### Parameters
- `query` (string, required): Search query text
- `search_type` (string): "semantic", "keyword", or "hybrid" (default: "hybrid")
- `limit` (integer): Maximum results (1-100, default: 20)
- `threshold` (float): Minimum similarity threshold (0.0-1.0, default: 0.3)
- `include_duplicates` (boolean): Whether to include duplicate content (default: false)
- `filters` (object, optional): Additional filtering criteria

#### Response
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "Article title",
      "url": "https://example.com",
      "summary": "Article summary",
      "created_at": "2024-01-01T00:00:00Z",
      "similarity": 0.89,
      "search_metadata": {
        "has_embedding": true,
        "search_timestamp": "2024-01-01T00:00:00Z"
      },
      "search_type": "hybrid",
      "component_scores": {
        "semantic": 0.85,
        "keyword": 0.92
      }
    }
  ],
  "total": 15,
  "query": "machine learning healthcare",
  "search_type": "hybrid",
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "deduplication": {
    "original_count": 18,
    "deduplicated_count": 15,
    "removed_duplicates": 3
  },
  "user_id": "anonymous",
  "request_params": {
    "search_type": "hybrid",
    "limit": 20,
    "threshold": 0.3,
    "include_duplicates": false
  }
}
```

---

### 2. Semantic Search (GET Convenience)

**GET** `/search/semantic`

Direct semantic search using embeddings.

#### Query Parameters
- `q` (string, required): Search query
- `limit` (integer): Maximum results (default: 20)
- `threshold` (float): Minimum similarity threshold (default: 0.3)

#### Example
```bash
curl "http://localhost:8000/api/search/semantic?q=machine%20learning&limit=10&threshold=0.5"
```

---

### 3. Keyword Search (GET Convenience)

**GET** `/search/keyword`

Full-text search using PostgreSQL search vectors.

#### Query Parameters
- `q` (string, required): Search query
- `limit` (integer): Maximum results (default: 20)

#### Example
```bash
curl "http://localhost:8000/api/search/keyword?q=machine%20learning&limit=10"
```

---

### 4. Duplicate Detection

**POST** `/search/duplicates`

Find exact content duplicates using SHA-256 fingerprints.

#### Request Body
```json
{
  "content": "Content to check for duplicates",
  "exclude_id": "uuid-to-exclude"
}
```

#### Response
```json
{
  "duplicates": [
    {
      "id": "uuid",
      "title": "Duplicate item title",
      "url": "https://example.com",
      "summary": "Summary",
      "created_at": "2024-01-01T00:00:00Z",
      "content_fingerprint": "sha256-hash",
      "match_type": "exact_fingerprint"
    }
  ],
  "total": 1,
  "content_fingerprint": "sha256-hash-of-input",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 5. Similar Items

**POST** `/search/similar`

Find items similar to a specific item using embedding similarity.

#### Request Body
```json
{
  "item_id": "uuid",
  "limit": 10,
  "threshold": 0.5
}
```

#### Response
```json
{
  "similar_items": [
    {
      "id": "uuid",
      "title": "Similar item",
      "similarity": 0.85,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "reference_item_id": "original-uuid",
  "threshold": 0.5,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 6. Search Statistics

**GET** `/search/stats`

Get system statistics about search capabilities.

#### Response
```json
{
  "items": {
    "total": 1000,
    "with_fingerprint": 950,
    "with_embedding": 800,
    "with_legacy_embedding": 200
  },
  "embeddings": {
    "total": 800,
    "unique_models": 1,
    "items_covered": 800
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 7. Migrate Legacy Embeddings

**POST** `/search/migrate-embeddings`

Migrate embeddings from items.embedding to normalized embeddings table.

#### Response
```json
{
  "migration_result": {
    "migrated": 200,
    "skipped": 0,
    "failed": 0
  },
  "message": "Migrated 200 embeddings, 0 failed",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 8. Update All Embeddings

**POST** `/search/update-embeddings`

Update embeddings for all items using content fingerprint change detection.

#### Query Parameters
- `model_name` (string, optional): Embedding model to use

#### Response
```json
{
  "update_result": {
    "updated": 50,
    "unchanged": 750,
    "failed": 0
  },
  "message": "Updated 50 embeddings, 750 unchanged, 0 failed",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `500`: Internal server error

---

## Usage Examples

### JavaScript/TypeScript
```typescript
// Using fetch API
const searchResults = await fetch('/api/search/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'machine learning',
    search_type: 'hybrid',
    limit: 10
  })
}).then(res => res.json());

// Using Svelte-Query (recommended)
import { createQuery } from '@tanstack/svelte-query';

const searchQuery = createQuery({
  queryKey: ['search', query, searchType],
  queryFn: () => enhancedSearchService.search(query, searchType),
  enabled: !!query
});
```

### Python
```python
import httpx

async def search_items(query: str, search_type: str = "hybrid"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/search/",
            json={
                "query": query,
                "search_type": search_type,
                "limit": 20
            }
        )
        return response.json()
```

### cURL
```bash
# Hybrid search
curl -X POST "http://localhost:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "search_type": "hybrid",
    "limit": 10
  }'

# Check for duplicates
curl -X POST "http://localhost:8000/api/search/duplicates" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Content to check for duplicates"
  }'
```

---

## Performance Notes

1. **Semantic Search**: Uses pre-computed embeddings for fast similarity calculation
2. **Keyword Search**: Leverages PostgreSQL full-text search with GIN indexes
3. **Hybrid Search**: Combines both methods with configurable weights
4. **Deduplication**: O(1) lookup using SHA-256 content fingerprints
5. **Caching**: Automatic query result caching via Svelte-Query (frontend)

---

## Content Fingerprinting

The system uses SHA-256 hashing of normalized content for:
- **Instant duplicate detection** (O(1) lookup)
- **Change tracking** (detect when content needs reprocessing)
- **Storage optimization** (avoid processing identical content)

Fingerprints are automatically generated during content capture and updated when content changes.

---

## Embedding Architecture

### Normalized Storage
- Embeddings stored in separate `embeddings` table
- `embed_vector_id` foreign key for O(1) vector lookups
- Support for multiple embedding models and versions
- Pre-calculated vector norms for faster similarity computation

### Benefits
- **Query Performance**: No joins on large vector data during searches
- **Memory Efficiency**: Load vectors only when needed
- **Model Versioning**: Support multiple embedding models simultaneously
- **Migration Support**: Seamless transition from legacy embedding storage