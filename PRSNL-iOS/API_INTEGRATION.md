# API Integration Guide

Complete API reference for PRSNL iOS backend integration.

## 🔧 Configuration

### Base URLs
```swift
// Development
http://localhost:8000

// Production  
https://api.prsnl.ai

// Configure in Settings or via:
APIClient.shared.setBaseURL("http://localhost:8000")
```

### Authentication
```swift
// Set API token
APIClient.shared.setAPIToken("your-token-here")

// Headers sent with each request
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

## 📡 REST API Endpoints

### Items Management

#### List Items (Paginated)
```http
GET /api/items?page=1&pageSize=20&sort=created_at&order=desc
```

**Response:**
```json
{
  "items": [{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "My note content",
    "type": "note",
    "createdAt": "2025-07-09T10:00:00Z",
    "modifiedAt": "2025-07-09T10:00:00Z",
    "tags": [
      {"name": "swift", "color": "#FF6B6B"},
      {"name": "ios", "color": "#4ECDC4"}
    ],
    "attachments": [],
    "embedding": null
  }],
  "total": 156,
  "page": 1,
  "pageSize": 20
}
```

#### Get Single Item
```http
GET /api/items/{id}
```

#### Create Item
```http
POST /api/items
Content-Type: application/json

{
  "content": "New note content",
  "type": "note",
  "tags": ["swift", "ios"]
}
```

#### Update Item
```http
PUT /api/items/{id}
Content-Type: application/json

{
  "content": "Updated content",
  "tags": ["swift", "ios", "updated"]
}
```

#### Delete Item
```http
DELETE /api/items/{id}
```

### Search

#### Search Items
```http
GET /api/items/search?q=swift&type=note,article&tags=ios,development&from=2025-01-01&to=2025-12-31
```

**Parameters:**
- `q` - Search query (required)
- `type` - Comma-separated item types
- `tags` - Comma-separated tag names
- `from` - Start date (ISO 8601)
- `to` - End date (ISO 8601)
- `page` - Page number (default: 1)
- `pageSize` - Items per page (default: 20)

#### Semantic Search
```http
POST /api/items/search/semantic
Content-Type: application/json

{
  "query": "How to implement dark mode in SwiftUI",
  "limit": 10,
  "threshold": 0.7
}
```

### Tags

#### List All Tags
```http
GET /api/tags
```

**Response:**
```json
{
  "tags": [
    {"name": "swift", "color": "#FF6B6B", "count": 42},
    {"name": "ios", "color": "#4ECDC4", "count": 38}
  ]
}
```

#### Popular Tags
```http
GET /api/tags/popular?limit=10
```

#### Create Tag
```http
POST /api/tags
Content-Type: application/json

{
  "name": "swiftui",
  "color": "#9B59B6"
}
```

### Videos

#### List Videos
```http
GET /api/videos?category=tutorial&page=1&pageSize=20
```

**Categories:** all, tutorial, lecture, podcast, documentary

#### Get Video Details
```http
GET /api/videos/{id}
```

**Response:**
```json
{
  "id": "video-123",
  "title": "SwiftUI Tutorial",
  "description": "Learn SwiftUI basics",
  "duration": 1800,
  "thumbnailUrl": "https://...",
  "videoUrl": "https://...",
  "category": "tutorial",
  "views": 1523,
  "createdAt": "2025-07-09T10:00:00Z"
}
```

#### Get Video Transcript
```http
GET /api/videos/{id}/transcript
```

### Import/Export

#### Import Data
```http
POST /api/import
Content-Type: multipart/form-data

file: [file data]
format: json|csv|markdown
```

#### Export Data
```http
GET /api/export?format=json&from=2025-01-01&to=2025-12-31
```

## 🔌 WebSocket API

### Chat Connection
```javascript
// Connect
ws://localhost:8000/ws/chat/{client_id}

// Send message
{
  "type": "message",
  "content": "What is SwiftUI?",
  "timestamp": "2025-07-09T10:00:00Z"
}

// Receive message
{
  "type": "response",
  "content": "SwiftUI is Apple's declarative UI framework...",
  "timestamp": "2025-07-09T10:00:01Z",
  "metadata": {
    "tokens": 150,
    "model": "gpt-4"
  }
}
```

### Message Types
- `message` - User message
- `response` - AI response
- `error` - Error message
- `typing` - Typing indicator
- `connected` - Connection established
- `disconnected` - Connection closed

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "content",
      "reason": "Content cannot be empty"
    }
  },
  "timestamp": "2025-07-09T10:00:00Z"
}
```

### Common Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

## 🔄 Rate Limiting

- **Default**: 100 requests per minute
- **Search**: 30 requests per minute
- **Import**: 10 requests per hour

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1720521600
```

## 🧪 Testing

### Test Endpoints
```http
# Health check
GET /api/health

# Test authentication
GET /api/auth/test
```

### Mock API Token
For development: `test-api-key-for-development`

## 📝 Swift Integration Examples

### Using APIClient
```swift
// Get items
let items = try await APIClient.shared.getItems(page: 1, pageSize: 20)

// Search
let results = try await APIClient.shared.searchItems(
    query: "SwiftUI",
    filters: SearchFilters(
        types: [.note, .article],
        tags: ["ios"],
        dateRange: DateRange(from: startDate, to: endDate)
    )
)

// Create item
let newItem = Item(
    content: "My note",
    type: .note,
    tags: [Tag(name: "swift")]
)
let created = try await APIClient.shared.createItem(newItem)
```

### WebSocket Chat
```swift
// Connect
webSocketManager.connect(clientId: UUID().uuidString)

// Send message
webSocketManager.sendMessage("Hello, AI!")

// Receive messages
webSocketManager.onMessage = { message in
    print("Received: \(message)")
}
```

## 🔐 Implementation Details

### Current APIClient Status
- ✅ Base structure implemented
- ✅ Async/await support
- ✅ Error handling
- ✅ Token management
- ❌ Not connected to ViewModels (using mock data)

### Switching from Mock to Real Data
1. In `TimelineViewModel`:
```swift
// Current (mock):
items = MockDataProvider.shared.getTimelineItems()

// Change to:
items = try await APIClient.shared.getItems(page: currentPage)
```

2. In `SearchViewModel`:
```swift
// Current (mock):
results = MockDataProvider.shared.searchItems(query)

// Change to:
results = try await APIClient.shared.searchItems(query: query)
```

3. In `VideosViewModel`:
```swift
// Current (mock):
videos = MockDataProvider.shared.getVideos()

// Change to:
videos = try await APIClient.shared.getVideos()
```

### Network Configuration
For simulator testing with local backend:
```swift
// Use host machine's IP
let baseURL = "http://192.168.1.100:8000"  // Replace with your IP
```

For device testing:
1. Ensure device and backend on same network
2. May need to add to Info.plist for HTTP:
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```