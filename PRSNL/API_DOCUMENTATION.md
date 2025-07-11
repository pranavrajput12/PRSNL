# 📚 PRSNL API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Frontend Proxy: `http://localhost:3003/api`
- iOS App: Configured in iOS app settings

## Client Applications
- **SvelteKit Frontend**: Web application (port 3003)
- **iOS App (PRSNL APP)**: Native iOS application - *separate codebase*
- **Chrome Extension**: Browser extension

## Navigation Structure (Neural Nest Theme)
- **Neural Nest** (`/`) - Main dashboard and knowledge hub
- **Ingest** (`/capture`) - Content capture and ingestion
- **Thought Stream** (`/timeline`) - Chronological content timeline
- **Cognitive Map** (`/insights`) - AI-powered insights and analysis
- **Mind Palace** (`/chat`) - Conversational interface with knowledge base
- **Visual Cortex** (`/videos`) - Video content management
- **Code Cortex** (`/code-cortex`) - Development content management hub
- **Knowledge Sync** (`/import`) - External data import and synchronization

## Authentication
Currently no authentication required (development mode)

**Note**: iOS app may require additional authentication mechanisms for production use.

## Endpoints

### 📊 Timeline

#### GET /api/timeline
Get paginated timeline items

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "url": "string",
      "summary": "string",
      "platform": "string",
      "item_type": "article|video|note",
      "thumbnail_url": "string",
      "duration": 120,
      "file_path": "string",
      "createdAt": "2025-07-06T10:00:00Z",
      "updatedAt": "2025-07-06T10:00:00Z",
      "tags": ["string"]
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

### 📝 Capture

#### POST /api/capture
Capture a new item (article, video, note)

**Request Body:**
```json
{
  "url": "https://example.com",
  "title": "Optional title",
  "content": "Optional content for notes",
  "content_type": "auto|document|video|article|tutorial|image|note|link",
  "enable_summarization": true,
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "message": "Item capture initiated",
  "item_id": "uuid",
  "item_type": "article|video|document|note",
  "processing_status": "pending|completed"
}
```

**Notes:**
- Either `url` or `content` must be provided
- Videos are automatically detected and processed asynchronously
- Supported video platforms: Instagram, YouTube, Twitter, TikTok
- AI summarization can be enabled/disabled per content type
- All content types supported: auto, document, video, article, tutorial, image, note, link

### 📁 File Upload

#### POST /api/file/upload
Upload and process files (documents, PDFs, images, etc.)

**Request Body:** `multipart/form-data`
- `files`: File(s) to upload (max 50MB each)
- `url`: Optional URL associated with files
- `title`: Optional title for the item
- `highlight`: Optional highlight text
- `content_type`: Content type classification (auto|document|video|article|tutorial|image|note|link)
- `enable_summarization`: Whether to enable AI summarization (boolean)
- `tags`: JSON string of tags array

**Response:**
```json
{
  "file_id": "uuid",
  "item_id": "uuid", 
  "original_filename": "document.pdf",
  "file_size": 1024000,
  "file_category": "document",
  "processing_status": "completed|processing",
  "message": "File uploaded and processed successfully"
}
```

#### GET /api/file/status/{file_id}
Get file processing status

**Response:**
```json
{
  "file_id": "uuid",
  "status": "completed|processing|failed|ai_failed",
  "progress": 100.0,
  "message": "File processed successfully",
  "extracted_text_length": 5000,
  "word_count": 850,
  "ai_analysis_complete": true
}
```

#### GET /api/file/content/{file_id}
Get file content and metadata

**Response:**
```json
{
  "file_id": "uuid",
  "item_id": "uuid",
  "original_filename": "document.pdf",
  "file_category": "document",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "extracted_text": "Full extracted text content...",
  "word_count": 850,
  "page_count": 5,
  "processing_status": "completed",
  "thumbnail_path": "/path/to/thumbnail.jpg",
  "title": "Document Title",
  "summary": "AI-generated summary",
  "tags": ["tag1", "tag2"],
  "created_at": "2025-07-09T10:00:00Z",
  "processed_at": "2025-07-09T10:01:00Z"
}
```

#### DELETE /api/file/{file_id}
Delete a file and its associated item

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

#### GET /api/file/stats
Get file storage and processing statistics

**Response:**
```json
{
  "storage_stats": [
    {
      "file_category": "document",
      "total_files": 25,
      "total_size_mb": 150.5
    }
  ],
  "processing_stats": [
    {
      "status": "completed",
      "count": 20
    }
  ],
  "recent_files": [
    {
      "file_id": "uuid",
      "filename": "document.pdf",
      "created_at": "2025-07-09T10:00:00Z"
    }
  ]
}
```

### 🔍 Enhanced Search

#### POST /api/search/
Advanced multi-modal search with semantic, keyword, and hybrid modes

**Request Body:**
```json
{
  "query": "machine learning",
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

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "string",
      "url": "string",
      "snippet": "string",
      "tags": ["string"],
      "created_at": "2025-07-06T10:00:00Z",
      "similarity": 0.89,
      "search_metadata": {
        "has_embedding": true,
        "search_timestamp": "2025-07-06T10:00:00Z"
      },
      "search_type": "hybrid",
      "component_scores": {
        "semantic": 0.85,
        "keyword": 0.92
      }
    }
  ],
  "total": 15,
  "query": "machine learning",
  "search_type": "hybrid",
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  },
  "timestamp": "2025-07-06T10:00:00Z",
  "deduplication": {
    "original_count": 18,
    "deduplicated_count": 15,
    "removed_duplicates": 3
  }
}
```

### 🏷️ Tags

#### GET /api/tags
Get all tags with usage count

**Response:**
```json
[
  {
    "name": "string",
    "count": 10
  }
]
```

### 📄 Items

#### GET /api/items/{id}
Get a single item by ID

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "url": "string",
  "content": "string",
  "summary": "string",
  "platform": "string",
  "item_type": "string",
  "thumbnail_url": "string",
  "duration": 120,
  "file_path": "string",
  "createdAt": "2025-07-06T10:00:00Z",
  "updatedAt": "2025-07-06T10:00:00Z",
  "tags": ["string"],
  "attachments": []
}
```

#### PATCH /api/items/{id}
Update an item

**Request Body:**
```json
{
  "title": "New title",
  "summary": "Updated summary",
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "message": "Item updated successfully",
  "id": "uuid"
}
```

#### DELETE /api/items/{id}
Delete an item

**Response:**
```json
{
  "message": "Item deleted successfully",
  "id": "uuid"
}
```

### 🎥 Videos

#### GET /api/videos/{item_id}/stream
Stream a video file

**Response:** Video file stream

#### GET /api/videos/{item_id}/metadata
Get video metadata

**Response:**
```json
{
  "id": "uuid",
  "url": "string",
  "title": "string",
  "description": "string",
  "author": "string",
  "duration": 120,
  "video_path": "string",
  "thumbnail_path": "string",
  "platform": "instagram",
  "metadata": {},
  "downloaded_at": "2025-07-06T10:00:00Z",
  "status": "completed"
}
```

#### POST /api/videos/{item_id}/transcode
Request video transcoding

**Request Body:**
```json
{
  "quality": "high|standard"
}
```

#### DELETE /api/videos/{item_id}
Delete a video and associated files

### 💬 Telegram

#### POST /api/telegram/webhook
Webhook endpoint for Telegram bot updates

#### POST /api/telegram/setup-webhook
Manually setup Telegram webhook

### 💻 Development Content

#### GET /api/development/stats
Get development content statistics and analytics

**Response:**
```json
{
  "total_items": 4,
  "by_language": {
    "python": 2,
    "javascript": 1,
    "dockerfile": 1
  },
  "by_category": {
    "Backend": 1,
    "Frontend": 1,
    "DevOps": 1
  },
  "by_difficulty": {
    "2": 2,
    "3": 1,
    "4": 1
  },
  "career_related_count": 1,
  "recent_activity": [
    {
      "id": "uuid",
      "title": "GitHub - fastapi/fastapi: FastAPI framework",
      "programming_language": "python",
      "project_category": "Backend",
      "created_at": "2025-07-11T04:22:42Z"
    }
  ]
}
```

#### GET /api/development/docs
Get development documents with filtering

**Query Parameters:**
- `limit` (integer, default: 20) - Items per page
- `offset` (integer, default: 0) - Pagination offset
- `category` (string) - Filter by project category
- `language` (string) - Filter by programming language
- `difficulty` (integer, 1-5) - Filter by difficulty level
- `career_related` (boolean) - Filter career-related content
- `search` (string) - Full-text search query

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "GitHub - fastapi/fastapi: FastAPI framework",
    "url": "https://github.com/fastapi/fastapi",
    "summary": "High performance web framework for Python",
    "type": "development",
    "programming_language": "python",
    "project_category": "Backend",
    "difficulty_level": 2,
    "is_career_related": false,
    "learning_path": null,
    "code_snippets": [],
    "created_at": "2025-07-11T04:22:42Z",
    "updated_at": "2025-07-11T04:22:43Z",
    "tags": ["python", "api", "framework"]
  }
]
```

#### GET /api/development/categories
Get all development categories with item counts

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Frontend",
    "description": "Frontend development resources",
    "icon": "🎨",
    "color": "#3b82f6",
    "created_at": "2025-07-11T00:00:00Z",
    "item_count": 2
  }
]
```

#### GET /api/development/languages
Get all programming languages found in development content

**Response:**
```json
{
  "languages": [
    {
      "name": "python",
      "count": 2
    },
    {
      "name": "javascript", 
      "count": 1
    }
  ]
}
```

**Example Usage:**
```bash
# Get development statistics
curl "http://localhost:8000/api/development/stats"

# Search Python backend content
curl "http://localhost:8000/api/development/docs?language=python&category=Backend"

# Get all development categories
curl "http://localhost:8000/api/development/categories"
```

### 📊 Admin

#### GET /api/storage/metrics
Get storage usage metrics

**Response:**
```json
{
  "total_size_bytes": 1000000,
  "video_count": 10,
  "thumbnail_count": 30,
  "temp_files_count": 5
}
```

### 🏥 Health

#### GET /health
Check system health

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
      "total": "100.00 GB",
      "used": "50.00 GB",
      "free": "50.00 GB",
      "percentage_free": "50.00%"
    }
  },
  "overall_status": "UP"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message",
  "status": 400
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## Data Formats

### Timestamps
All timestamps are in ISO 8601 format with UTC timezone:
`2025-07-06T10:00:00Z`

### IDs
All IDs are UUIDs in standard format:
`123e4567-e89b-12d3-a456-426614174000`

## Frontend Integration Notes

### Field Name Conventions
The backend now returns camelCase fields directly for frontend compatibility:
- `createdAt` (instead of `created_at`)
- `updatedAt` (instead of `updated_at`)

Note: Some fields still use snake_case:
- `item_type`
- `thumbnail_url`
- `file_path`

### CORS Configuration
Allowed origins:
- `http://localhost:3000`
- `http://localhost:3003`
- `http://localhost:5173`

## Rate Limiting
Currently no rate limiting in development mode

## Future Enhancements
- [ ] Authentication & Authorization
- [ ] WebSocket support for real-time updates
- [ ] Batch operations
- [ ] GraphQL endpoint
- [ ] API versioning
- [ ] Rate limiting
- [ ] Pagination cursors