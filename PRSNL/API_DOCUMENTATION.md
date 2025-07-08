# PRSNL API Documentation
*Last Updated: 2025-01-08*

## Base URL
- Development: `http://localhost:8000/api`
- Production: `http://localhost:8001/api` (through NGINX)

**NOTE**: The API prefix is `/api` NOT `/api/v1`

## Authentication
Currently, the API is designed for local use without authentication. Future versions will include API key authentication.

## Core Endpoints

### 📥 Capture

#### POST `/api/capture`
Capture new content with AI processing.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "title": "Optional title override",
  "tags": ["optional", "tags"],
  "notes": "Optional notes",
  "item_type": "article",  // Optional: video, article, tweet, etc.
  "summary": "Optional summary"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "pending",  // or "completed"
  "message": "Item capture initiated"
}
```

### 📋 Timeline

#### GET `/api/timeline`
Get items in reverse chronological order.

**Query Parameters:**
- `limit` (int): Number of items (default: 20, max: 100)
- `cursor` (string): Pagination cursor

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Item Title",
      "url": "https://...",
      "summary": "Item summary",
      "platform": "youtube",  // for videos
      "item_type": "video",
      "thumbnail_url": "https://...",
      "duration": 3600,  // seconds for videos
      "status": "completed",
      "createdAt": "2025-01-08T12:00:00Z",
      "tags": ["tag1", "tag2"]
    }
  ],
  "next_cursor": "2025-01-08T12:00:00Z"
}
```

### 🔍 Search

#### GET `/api/search`
Keyword-based search.

**Query Parameters:**
- `query` (string): Search terms
- `limit` (int): Max results (default: 10)
- `type` (string): Filter by item type
- `tags` (string): Comma-separated tags

#### POST `/api/search/semantic`
Semantic search using embeddings.

**Request Body:**
```json
{
  "query": "machine learning tutorials",
  "limit": 10,
  "full_text_query": "optional keyword filter"
}
```

#### GET `/api/search/similar/{id}`
Find items similar to a specific item.

### 📄 Items

#### GET `/api/items/{id}`
Get single item details.

#### PATCH `/api/items/{id}`
Update item metadata.

#### DELETE `/api/items/{id}`
Delete an item.

### 🏷️ Tags

#### GET `/api/tags`
Get all tags with usage counts.

**Response:**
```json
[
  {
    "name": "javascript",
    "count": 42
  }
]
```

### 🤖 AI Features

#### POST `/api/suggest`
Get AI suggestions for URL content.

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "title": "Suggested Title",
  "summary": "AI-generated summary",
  "tags": ["suggested", "tags"],
  "category": "tutorial"
}
```

#### POST `/api/vision/analyze`
Analyze images with AI.

**Request:** Multipart form with `file` field

**Response:**
```json
{
  "text": "Extracted text",
  "description": "AI description",
  "objects": ["detected", "objects"],
  "tags": ["suggested", "tags"]
}
```

### 📊 AI Analytics & Processing

#### POST `/api/categorize`
Categorize a single item.

**Request Body:**
```json
{
  "item_id": "uuid"
}
```

#### POST `/api/categorize/bulk`
Categorize multiple uncategorized items.

**Request Body:**
```json
{
  "limit": 100
}
```

#### GET `/api/categories/stats`
Get category statistics.

#### POST `/api/duplicates/check`
Check if content is duplicate.

**Request Body:**
```json
{
  "url": "https://...",
  "title": "Title",
  "content": "Optional content"
}
```

#### GET `/api/duplicates/find-all`
Find all duplicate groups.

#### POST `/api/duplicates/merge`
Merge duplicate items.

**Request Body:**
```json
{
  "keep_id": "uuid",
  "duplicate_ids": ["uuid1", "uuid2"]
}
```

#### POST `/api/summarization/item`
Summarize a single item.

**Request Body:**
```json
{
  "item_id": "uuid",
  "summary_type": "brief"  // or "detailed", "key_points"
}
```

#### POST `/api/summarization/digest`
Generate periodic digest.

**Request Body:**
```json
{
  "period": "daily",  // or "weekly", "monthly"
  "summary_type": "brief"
}
```

#### POST `/api/summarization/topic`
Summarize by topic.

**Request Body:**
```json
{
  "topic": "machine learning",
  "limit": 20
}
```

### 📹 Video Features

#### GET `/api/videos/{id}/stream`
Stream video file (for downloaded videos).

#### GET `/api/videos/{id}/metadata`
Get video metadata.

#### POST `/api/video-streaming/analyze/{id}`
Analyze video content with AI.

#### GET `/api/video-streaming/mini-course`
Get generated mini-courses from videos.

### 📈 Analytics

#### GET `/api/analytics/trends`
Content trends over time.

#### GET `/api/analytics/topics`  
Topic clusters in knowledge base.

#### GET `/api/analytics/usage_patterns`
Usage statistics and patterns.

#### GET `/api/analytics/ai_insights`
AI-generated insights about your knowledge.

### 💬 WebSocket

#### WS `/ws/chat/{client_id}`
RAG-based chat with knowledge base.

**Message Format:**
```json
{
  "message": "User question",
  "history": [],
  "chat_mode": "general"
}
```

**Response Types:**
- `connection`: Connection established
- `status`: Processing status
- `chunk`: Streaming response chunk
- `complete`: Response complete with citations
- `error`: Error message

### 🔧 Utility

#### GET `/api/health`
Health check endpoint.

#### GET `/api/debug/session`
Debug session information.

#### GET `/api/metrics`
Prometheus metrics endpoint.

## Rate Limiting

- Default: 10 requests per minute per IP
- Capture endpoint: 10 per minute
- Search endpoints: 30 per minute
- Analytics: 20 per minute

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

Common status codes:
- 400: Bad Request
- 404: Not Found
- 429: Rate Limited
- 500: Internal Server Error

## Notes

1. All timestamps are in ISO 8601 format with UTC timezone
2. Frontend expects camelCase fields (createdAt, updatedAt, etc.)
3. Item types: video, article, tweet, github, pdf, note
4. Status values: pending, completed, failed, bookmark
5. Platform values: youtube, twitter, github, web