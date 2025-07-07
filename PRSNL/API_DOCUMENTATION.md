# PRSNL API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Production: `https://your-domain.com/api`

## Authentication
Currently, the API is designed for local use without authentication. Future versions will include API key authentication.

## Core Endpoints

### AI Enhancement Endpoints

#### POST `/api/ai/suggest`
Get AI-powered suggestions for title, summary, and tags based on URL content.

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "title": "How to Build a React Application",
  "summary": "A comprehensive guide to building modern React applications with hooks and best practices.",
  "tags": ["react", "javascript", "frontend", "tutorial"],
  "category": "tutorial"
}
```

### Vision AI Endpoints

#### POST `/api/vision/analyze`
Analyze uploaded images with OCR and AI.

**Request:** Multipart form data with image file

**Response:**
```json
{
  "text": "Extracted text from image",
  "description": "AI-generated description",
  "objects": ["laptop", "coffee", "notebook"],
  "tags": ["workspace", "productivity"]
}
```

#### POST `/api/vision/screenshot`
Process screenshots with enhanced analysis.

**Request:** Multipart form data with screenshot

**Response:** Similar to `/api/vision/analyze` with additional UI element detection

#### GET `/api/vision/status`
Check vision AI provider availability.

**Response:**
```json
{
  "azure_available": true,
  "tesseract_available": true,
  "active_provider": "azure"
}
```

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

#### GET `/api/search/similar/{item_id}`
Find items similar to a given item using embeddings.

**Path Parameters:**
- `item_id`: UUID of the item to find similar items for

**Query Parameters:**
- `limit`: Number of results (default: 10)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Similar Article",
      "similarity_score": 0.92,
      "summary": "Article summary"
    }
  ]
}
```

#### POST `/api/search/semantic`
Semantic search using natural language queries.

**Request Body:**
```json
{
  "query": "How do I optimize React performance?",
  "limit": 20
}
```

**Response:** Similar to regular search but with relevance scores

**Response:**
```json
{
  "results": [
    {
      "id": "589d99c1-551e-4cbb-a88a-fc6bb989117f",
      "title": "Advanced React Patterns",
      "summary": "Learn advanced React patterns...",
      "tags": ["react", "javascript"],
      "created_at": "2025-07-01T10:30:00Z",
      "url": "https://example.com/react-patterns",
      "item_type": "article"
    }
  ],
  "total": 42
}
```

### 3. Timeline

#### GET `/api/timeline`
Get paginated timeline of captured items.

**Query Parameters:**
- `page` (default: 1): Page number
- `per_page` (default: 20): Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "589d99c1-551e-4cbb-a88a-fc6bb989117f",
      "title": "Article Title",
      "summary": "Brief summary...",
      "created_at": "2025-07-01T10:30:00Z",
      "tags": ["technology"],
      "item_type": "article"
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

### 4. Items

#### GET `/api/items/{id}`
Get a specific item by ID.

**Response:**
```json
{
  "id": "589d99c1-551e-4cbb-a88a-fc6bb989117f",
  "title": "Article Title",
  "content": "Full content...",
  "summary": "Brief summary...",
  "url": "https://example.com/article",
  "tags": ["technology", "ai"],
  "created_at": "2025-07-01T10:30:00Z",
  "updated_at": "2025-07-01T10:30:00Z",
  "item_type": "article",
  "metadata": {
    "author": "John Doe",
    "ai_analysis": {
      "key_points": ["point1", "point2"],
      "sentiment": "positive",
      "reading_time": 5
    }
  }
}
```

#### PATCH `/api/items/{id}`
Update an existing item.

**Request Body:**
```json
{
  "title": "Updated Title",
  "summary": "Updated summary",
  "tags": ["new-tag"]
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

### 5. Tags

#### GET `/api/tags`
Get all tags with usage counts.

**Response:**
```json
{
  "tags": [
    {
      "name": "technology",
      "count": 42
    },
    {
      "name": "ai",
      "count": 35
    }
  ]
}
```

### 6. Analytics

#### GET `/api/analytics/trends`
Get content trends over time.

**Query Parameters:**
- `timeframe`: day, week, month, year (default: week)

**Response:**
```json
{
  "trends": [
    {
      "date": "2025-07-01",
      "articles": 5,
      "videos": 2,
      "notes": 3,
      "bookmarks": 1
    }
  ]
}
```

#### GET `/api/analytics/topics`
Get top topics/tags.

**Query Parameters:**
- `limit`: Number of topics (default: 10)

**Response:**
```json
{
  "topics": [
    {
      "tag": "technology",
      "count": 42,
      "percentage": 15.5
    }
  ]
}
```

#### GET `/api/analytics/usage_patterns`
Get usage statistics.

**Response:**
```json
{
  "total_items": 500,
  "average_per_day": 12.5,
  "most_active_day": "Monday",
  "most_active_hour": 14
}
```

#### GET `/api/analytics/ai_insights`
Get AI-generated insights about your knowledge base.

**Response:**
```json
{
  "insights": [
    {
      "type": "trend",
      "title": "Increased interest in AI",
      "description": "You've captured 40% more AI-related content this week"
    }
  ]
}
```

## WebSocket Endpoints

### WS `/ws/ai-stream/{client_id}`
Stream AI responses in real-time.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ai-stream/unique-client-id');
```

**Send Message:**
```json
{
  "type": "process",
  "content": "Content to process",
  "url": "https://example.com"
}
```

**Receive Streaming Response:**
```json
{
  "type": "chunk",
  "content": "Partial response..."
}
```

### WS `/ws/ai-tag-stream/{client_id}`
Stream AI-generated tag suggestions.

**Send Message:**
```json
{
  "type": "suggest",
  "content": "Content to analyze for tags"
}
```

## Video Endpoints

### GET `/api/videos/{id}/stream`
Stream video content.

**Response:** Video stream with proper Range header support

### GET `/api/videos/{id}/download`
Download video file.

**Response:** Video file with appropriate Content-Disposition header

## Health Check

### GET `/api/health`
Check API and service health.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ollama": "available",
    "azure_openai": "available",
    "disk_space": "adequate",
    "embeddings": "ready"
  },
  "timestamp": "2025-07-07T10:30:00Z"
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input provided",
    "details": {
      "field": "url",
      "issue": "Invalid URL format"
    }
  }
}
```

### Common Error Codes:
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server error
- `RATE_LIMITED`: Too many requests
- `INSUFFICIENT_STORAGE`: Storage capacity exceeded

## Rate Limiting

- Default: 100 requests per minute per IP
- Capture endpoints: 20 requests per minute
- AI endpoints: 10 requests per minute

## Pagination

All list endpoints support pagination:

```
GET /api/timeline?page=2&per_page=50
```

Maximum `per_page`: 100

## Response Headers

- `X-Total-Count`: Total number of items (for paginated responses)
- `X-Page`: Current page number
- `X-Per-Page`: Items per page
- `X-Processing-Time`: Request processing time in ms