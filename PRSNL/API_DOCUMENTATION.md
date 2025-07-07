# PRSNL API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Production: `https://your-domain.com/api`

## Authentication
Currently, the API is designed for local use without authentication. Future versions will include API key authentication.

## Core Endpoints

### 1. Capture Content

#### POST `/api/capture`
Capture new content into the knowledge base.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "title": "Optional title override",
  "content": "Optional direct content instead of URL",
  "tags": ["technology", "ai"],
  "type": "page"
}
```

**Response:**
```json
{
  "message": "Item capture initiated",
  "item_id": "589d99c1-551e-4cbb-a88a-fc6bb989117f",
  "item_type": "article"
}
```

**Status Codes:**
- `201`: Capture initiated successfully
- `400`: Invalid input (missing URL or content)
- `500`: Internal server error

### 2. Search

#### GET `/api/search`
Full-text search across all captured content.

**Query Parameters:**
- `query` (required): Search query string
- `date`: Filter by date (today, week, month, year)
- `type`: Filter by type (article, video, note)
- `tags`: Comma-separated tag filter
- `limit`: Results per page (default: 20)

**Response:**
```json
{
  "results": [
    {
      "id": "item-uuid",
      "title": "Article Title",
      "snippet": "...matched content snippet...",
      "url": "https://source.url",
      "tags": ["tag1", "tag2"],
      "created_at": "2025-07-06T10:00:00Z",
      "item_type": "article"
    }
  ],
  "total": 42,
  "query": "search terms"
}
```

#### GET `/api/search/semantic` (Coming Soon)
Semantic search using embeddings.

**Additional Parameters:**
- `mode`: Search mode (semantic, hybrid)

**Response includes:**
- `similarity_score`: 0.0 to 1.0
- `match_type`: "semantic", "keyword", or "both"

### 3. Timeline

#### GET `/api/timeline`
Get items in chronological order.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `start_date`: Filter start date (ISO format)
- `end_date`: Filter end date (ISO format)

**Response:**
```json
{
  "items": [
    {
      "id": "item-uuid",
      "title": "Item Title",
      "url": "https://source.url",
      "summary": "AI-generated summary",
      "platform": "youtube",
      "item_type": "video",
      "thumbnail_url": "/media/thumbnails/uuid/medium.jpg",
      "duration": 180,
      "file_path": "/app/media/videos/2025/07/video.mp4",
      "createdAt": "2025-07-06T10:00:00Z",
      "updatedAt": "2025-07-06T10:05:00Z",
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

### 4. Items

#### GET `/api/items/{id}`
Get a single item by ID.

**Response:**
```json
{
  "id": "item-uuid",
  "title": "Item Title",
  "url": "https://source.url",
  "summary": "AI-generated summary",
  "content": "Full processed content...",
  "raw_content": "Original HTML content...",
  "item_type": "article",
  "status": "completed",
  "platform": "medium",
  "metadata": {
    "author": "John Doe",
    "published_date": "2025-07-01",
    "word_count": 1500,
    "ai_analysis": {
      "summary": "AI summary",
      "tags": ["ai", "generated", "tags"],
      "processed_at": 1720281600
    }
  },
  "tags": ["technology", "ai"],
  "created_at": "2025-07-06T10:00:00Z",
  "updated_at": "2025-07-06T10:05:00Z"
}
```

#### PATCH `/api/items/{id}`
Update an item.

**Request Body:**
```json
{
  "title": "New Title",
  "summary": "Updated summary",
  "tags": ["new", "tags"]
}
```

#### DELETE `/api/items/{id}`
Delete an item.

**Response:**
```json
{
  "message": "Item deleted successfully"
}
```

#### GET `/api/items/{id}/similar` (Coming Soon)
Get similar items based on embeddings.

**Query Parameters:**
- `limit`: Number of similar items (default: 5)

### 5. Tags

#### GET `/api/tags`
Get all tags with usage counts.

**Response:**
```json
[
  {
    "name": "technology",
    "count": 42
  },
  {
    "name": "ai",
    "count": 35
  }
]
```

#### GET `/api/tags/recent`
Get recently used tags (last 10).

**Response:**
```json
["ai", "technology", "video", "tutorial"]
```

### 6. Videos

#### GET `/api/videos/{id}/stream`
Stream a video file.

**Response:** Video file stream with appropriate headers

#### GET `/api/videos/{id}/metadata`
Get video metadata.

**Response:**
```json
{
  "id": "video-uuid",
  "title": "Video Title",
  "duration": 180,
  "platform": "youtube",
  "resolution": "1920x1080",
  "file_size": 104857600
}
```

### 7. Vision AI

#### POST `/api/vision/analyze`
Analyze an image with AI.

**Request:** Multipart form data with image file

**Response:**
```json
{
  "text": "Extracted text from image...",
  "description": "AI description of image content",
  "tags": ["screenshot", "code", "python"],
  "confidence": 0.95
}
```

### 8. Embeddings (Coming Soon)

#### POST `/api/embeddings/generate`
Generate embeddings for existing items.

**Request Body:**
```json
{
  "item_ids": ["uuid1", "uuid2"],
  "regenerate": false
}
```

#### GET `/api/embeddings/status`
Check embedding generation status.

### 9. WebSocket (Coming Soon)

#### WS `/api/ws`
WebSocket connection for real-time updates.

**Client Messages:**
```json
{
  "type": "ai_request",
  "data": {
    "task": "analyze",
    "content": "Content to analyze",
    "item_id": "optional-item-id"
  }
}
```

**Server Messages:**
```json
{
  "type": "ai_response",
  "data": {
    "content": "Streaming response text..."
  }
}
```

```json
{
  "type": "progress",
  "data": {
    "task": "transcription",
    "progress": 45,
    "item_id": "item-uuid"
  }
}
```

### 10. Admin

#### GET `/api/admin/storage/stats`
Get storage statistics.

**Response:**
```json
{
  "total_size_bytes": 1073741824,
  "video_size_bytes": 943718400,
  "thumbnail_size_bytes": 104857600,
  "temp_size_bytes": 25165824,
  "video_count": 15,
  "thumbnail_count": 45
}
```

#### POST `/api/admin/storage/cleanup`
Trigger storage cleanup.

**Response:**
```json
{
  "message": "Cleanup completed",
  "orphaned_files_removed": 5,
  "temp_files_removed": 12,
  "space_freed_bytes": 52428800
}
```

#### GET `/api/admin/debug/items`
Debug endpoint for item status.

### 11. Health & Monitoring

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "database": {
    "status": "UP",
    "details": ""
  },
  "ollama": {
    "status": "UP",
    "details": ""
  },
  "disk_space": {
    "status": "UP",
    "details": {
      "total": "500.00 GB",
      "used": "250.00 GB",
      "free": "250.00 GB",
      "percentage_free": "50.00%"
    }
  },
  "overall_status": "UP"
}
```

### 12. Analytics

#### GET `/api/analytics/trends`
Retrieves content trends over a specified timeframe.

**Query Parameters:**
- `timeframe` (optional): e.g., "7d", "30d", "90d", "1y" (default: "7d")

**Response:**
```json
{
  "trends": [
    {
      "date": "2025-07-01",
      "count": 5
    },
    {
      "date": "2025-07-02",
      "count": 8
    }
  ]
}
```

#### GET `/api/analytics/topics`
Retrieves top topics or tags based on frequency.

**Query Parameters:**
- `limit` (optional): Number of topics to return (default: 10)

**Response:**
```json
{
  "topics": [
    {
      "topic": "technology",
      "count": 42
    },
    {
      "topic": "ai",
      "count": 35
    }
  ]
}
```

#### GET `/api/analytics/usage_patterns`
Retrieves general usage patterns (e.g., total items, average items per day).

**Response:**
```json
{
  "total_items": 1234,
  "average_items_per_day_last_30_days": 15.5
}
```

#### GET `/api/analytics/ai_insights`
Retrieves AI-generated insights (placeholder for future AI analysis results).

**Query Parameters:**
- `limit` (optional): Number of insights to return (default: 5)

**Response:**
```json
{
  "insights": [
    {
      "id": 1,
      "insight": "AI suggests focusing on 'Productivity Hacks' based on recent captures."
    }
  ]
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400,
  "type": "validation_error"
}
```

Common error codes:
- `400`: Bad Request - Invalid input
- `404`: Not Found - Resource doesn't exist
- `422`: Unprocessable Entity - Validation error
- `500`: Internal Server Error

## Rate Limiting

Currently no rate limiting is implemented as this is designed for personal use. Future versions may include:
- 100 requests/minute for search
- 10 requests/minute for capture
- 1000 requests/hour overall

## Pagination

Endpoints that return lists support pagination:
- `page`: Page number (1-indexed)
- `limit` or `pageSize`: Items per page
- Response includes `total` count

## Filtering

Common filter parameters:
- `date`: today, week, month, year
- `type`: article, video, note, bookmark
- `tags`: Comma-separated list
- `platform`: youtube, twitter, instagram, tiktok

## Media Files

Static media files are served from:
- `/media/videos/{year}/{month}/{filename}`
- `/media/thumbnails/{id}/{size}.jpg`

Sizes: small (150x150), medium (300x300), large (600x600)

## Future Endpoints

### Collaboration
- `POST /api/share/item/{id}` - Share an item
- `GET /api/shared/with-me` - Items shared with user

### Export/Import
- `GET /api/export` - Export all data
- `POST /api/import` - Import data backup