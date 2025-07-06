# 📚 PRSNL API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Frontend Proxy: `http://localhost:3002/api`

## Authentication
Currently no authentication required (development mode)

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
  "content": "Optional content for notes"
}
```

**Response:**
```json
{
  "message": "Item capture initiated",
  "item_id": "uuid",
  "item_type": "article|video"
}
```

**Notes:**
- Either `url` or `content` must be provided
- Videos are automatically detected and processed asynchronously
- Supported video platforms: Instagram, YouTube, Twitter, TikTok

### 🔍 Search

#### GET /api/search
Search items by query and filters

**Query Parameters:**
- `query` (string) - Search query
- `date` (string) - Date filter
- `type` (string) - Item type filter
- `tags` (string) - Tags filter

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "url": "string",
      "summary": "string",
      "tags": ["string"],
      "createdAt": "2025-07-06T10:00:00Z",
      "type": "article"
    }
  ],
  "total": 10
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
- `http://localhost:3002`
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