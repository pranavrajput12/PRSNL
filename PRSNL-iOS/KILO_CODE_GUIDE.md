# PRSNL iOS App Development Guide for Kilo Code

## ⚠️ CRITICAL BOUNDARIES ⚠️

### Working Directory
- **ONLY WORK IN**: `/PRSNL-iOS/` directory
- **DO NOT MODIFY**: Any files in `/PRSNL/` directory
- **DO NOT ACCESS**: Other agent task files (GEMINI_TASKS.md, WINDSURF_TASKS.md)

### Your Role
You are the lead orchestrator for the iOS app development, working alongside Claude02 (technical advisor). The iOS app is a **separate project** from the main PRSNL web application.

## Project Overview

You'll be building a native iOS app that connects to the existing PRSNL backend API. The backend is already complete and running - your job is to create the iOS client only.

### Technology Stack
- **Framework**: SwiftUI (iOS 17.0+)
- **Language**: Swift 5.9+
- **Architecture**: MVVM with Combine
- **Networking**: URLSession with async/await
- **Local Storage**: Core Data

### Design Requirements
- **Theme**: Manchester United red (#DC143C) as accent color
- **Dark Mode**: Full support
- **Typography**: SF Pro Display (headings), SF Pro Text (body)

## Backend API Reference

### Connection Details
- **Base URL**: `http://localhost:8000/api` (development)
- **Authentication**: API Key in header: `X-API-Key: {api_key}`
- **Content-Type**: `application/json`

### Core Endpoints You'll Need

#### 1. Authentication Check
```swift
// Test API key validity
GET /api/items
Headers: X-API-Key: {api_key}
```

#### 2. Capture Content
```swift
POST /api/capture
Headers: X-API-Key: {api_key}
Body: {
    "url": "https://example.com",     // Optional
    "content": "Direct text content", // Optional (url or content required)
    "title": "Optional title",
    "tags": ["tag1", "tag2"]
}
Response: {
    "id": "uuid",
    "status": "pending",
    "message": "Item capture initiated"
}
```

#### 3. Search Items
```swift
// Keyword search
GET /api/search?query={query}&limit=20&offset=0
Response: {
    "items": [{
        "id": "uuid",
        "title": "Item Title",
        "url": "https://...",
        "summary": "Summary text",
        "tags": ["tag1", "tag2"],
        "createdAt": "2025-01-07T12:00:00Z",
        "type": "article"
    }],
    "total": 50
}

// Semantic search
POST /api/search/semantic?limit=20
Body: { "query": "natural language query" }
Response: Same format as keyword search

// Find similar
GET /api/search/similar/{item_id}?limit=10
Response: Same format as keyword search
```

#### 4. Timeline
```swift
GET /api/timeline?page=1&limit=20
Response: {
    "items": [{
        "id": "uuid",
        "title": "Title",
        "summary": "Summary",
        "thumbnail_url": "/media/thumbnails/...", // For videos
        "duration": 300,                          // For videos (seconds)
        "createdAt": "2025-01-07T12:00:00Z",
        "tags": ["tag1"]
    }],
    "total": 100,
    "page": 1,
    "pageSize": 20
}
```

#### 5. Item Details
```swift
GET /api/items/{item_id}
Response: {
    "id": "uuid",
    "title": "Title",
    "url": "https://...",
    "content": "Full content text",
    "summary": "Summary",
    "created_at": "2025-01-07T12:00:00Z",
    "tags": ["tag1", "tag2"],
    "status": "completed"
}

// Update item
PATCH /api/items/{item_id}
Headers: X-API-Key: {api_key}
Body: {
    "title": "New Title",
    "summary": "New Summary",
    "tags": ["new-tag1", "new-tag2"]
}

// Delete item
DELETE /api/items/{item_id}
Headers: X-API-Key: {api_key}
```

#### 6. Tags
```swift
// All tags with counts
GET /api/tags
Response: [
    {"name": "productivity", "count": 25},
    {"name": "technology", "count": 18}
]

// Recent tags
GET /api/tags/recent
Response: ["tag1", "tag2", "tag3", ...]
```

#### 7. Analytics
```swift
// Content trends
GET /api/analytics/trends?timeframe=30d
Response: {
    "trends": [
        {"date": "2025-01-01", "count": 5}
    ]
}

// Usage patterns
GET /api/analytics/usage_patterns
Response: {
    "total_items": 500,
    "average_items_per_day_last_30_days": 16.7
}
```

#### 8. Media (for videos)
```swift
// Stream video
GET /api/videos/{video_id}/stream
Response: Video file (video/mp4)

// Note: Construct thumbnail URLs as:
// {baseURL}/media/thumbnails/{filename}
```

## Data Models to Implement

### Core Models
```swift
struct Item: Codable {
    let id: String
    let title: String
    let url: String?
    let content: String?
    let summary: String
    let tags: [String]
    let createdAt: Date
    let updatedAt: Date?
    let type: ItemType
    let status: ItemStatus
}

enum ItemType: String, Codable {
    case article = "article"
    case video = "video"
}

enum ItemStatus: String, Codable {
    case pending = "pending"
    case completed = "completed"
    case failed = "failed"
}

struct Tag: Codable {
    let name: String
    let count: Int
}

struct SearchResponse: Codable {
    let items: [Item]
    let total: Int
}

struct TimelineResponse: Codable {
    let items: [TimelineItem]
    let total: Int
    let page: Int
    let pageSize: Int
}

struct CaptureRequest: Codable {
    let url: String?
    let content: String?
    let title: String?
    let tags: [String]?
}

struct CaptureResponse: Codable {
    let id: String
    let status: String
    let message: String
}
```

## Development Phases

### Phase 1: Foundation ✅ (Planned)
- Create Xcode project
- Set up Core Data models
- Implement API client with async/await
- Create authentication service
- Design navigation structure

### Phase 2: Core Features
- Timeline view with infinite scroll
- Search implementation (keyword + semantic)
- Item detail view
- Basic capture functionality

### Phase 3: Advanced Features
- Share extension for system-wide capture
- Offline support with sync
- Tag management
- Analytics dashboard

### Phase 4: Polish
- Animations and transitions
- Error handling
- Performance optimization
- App Store preparation

## Implementation Guidelines

### API Client Pattern
```swift
class PRSNLAPIClient {
    static let shared = PRSNLAPIClient()
    private let baseURL = "http://localhost:8000/api"
    
    func request<T: Decodable>(_ endpoint: String, 
                               method: String = "GET",
                               body: Encodable? = nil) async throws -> T {
        // Implementation here
    }
}
```

### Error Handling
- Handle network errors gracefully
- Show offline state when appropriate
- Implement retry logic for failed requests
- Cache responses for offline access

### UI/UX Guidelines
- Follow iOS Human Interface Guidelines
- Use Manchester United red (#DC143C) sparingly as accent
- Implement pull-to-refresh where appropriate
- Show loading states for all async operations
- Support Dynamic Type for accessibility

## Testing Requirements
- Unit tests for all API client methods
- UI tests for critical user flows
- Test offline mode functionality
- Test with various network conditions

## Important Notes

1. **Do Not Modify Backend**: The backend is complete and managed by other agents. Only consume the API.
2. **Separate Project**: This iOS app is independent from the main web application.
3. **API Key Storage**: Use iOS Keychain for secure storage.
4. **Rate Limits**: Respect the API rate limits mentioned in the endpoints.
5. **Media URLs**: Prefix relative URLs with base server URL.

## Coordination with Claude02

- **Claude02**: Reviews architecture, provides guidance, handles documentation
- **Kilo Code**: Implements features, writes code, manages project
- **Communication**: Update progress in your responses

## Next Steps

1. Create the Xcode project with SwiftUI template
2. Set up the project structure as outlined
3. Implement the API client
4. Create Core Data models
5. Build the first view (Timeline)

Remember: Focus only on the iOS app. Do not access or modify any files outside of `/PRSNL-iOS/` directory.