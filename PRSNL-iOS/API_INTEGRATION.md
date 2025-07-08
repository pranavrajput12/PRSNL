# PRSNL iOS API Integration Guide

## Backend Connection Setup

### Base Configuration
```swift
struct APIConfig {
    static let baseURL = ProcessInfo.processInfo.environment["API_URL"] ?? "http://localhost:8000"
    static let apiVersion = "/api"
    static let timeout: TimeInterval = 30.0
}
```

### Authentication
```swift
// Store in Keychain
let token = "Bearer <user_token>"
KeychainService.shared.save(token, for: .apiToken)
```

## Core API Endpoints

### 1. Capture Content
```swift
POST /api/capture
Body: {
    "url": "https://example.com",
    "title": "Optional title",
    "tags": ["tag1", "tag2"],
    "notes": "Optional notes"
}
Response: {
    "id": "uuid",
    "status": "processing",
    "message": "Content captured successfully"
}
```

### 2. Search
```swift
// Keyword Search
GET /api/search?q=query&limit=20&offset=0

// Semantic Search
GET /api/semantic-search?q=natural+language+query&limit=10

Response: {
    "items": [...],
    "total": 100,
    "has_more": true
}
```

### 3. Timeline
```swift
GET /api/timeline?limit=20&offset=0&start_date=2024-01-01&end_date=2024-12-31

Response: {
    "items": [...],
    "total": 500,
    "has_more": true
}
```

### 4. Item Details
```swift
GET /api/items/{id}

Response: {
    "id": "uuid",
    "url": "https://...",
    "title": "...",
    "content": "...",
    "summary": "AI generated summary",
    "tags": [...],
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 5. Tags
```swift
GET /api/tags

Response: {
    "tags": [
        {"name": "tag1", "count": 45},
        {"name": "tag2", "count": 23}
    ]
}
```

### 6. Analytics (New)
```swift
// Content Trends
GET /api/analytics/trends?days=30

// Knowledge Graph
GET /api/analytics/knowledge_graph

// Semantic Clusters
GET /api/analytics/semantic_clusters

// Usage Patterns
GET /api/analytics/usage_patterns
```

### 7. WebSocket Streaming
```swift
// For real-time AI tag suggestions
ws://localhost:8000/ws/ai-tag-stream/{client_id}
```

## Swift Implementation Examples

### API Client Setup
```swift
class PRSNLAPIClient {
    static let shared = PRSNLAPIClient()
    private let session = URLSession.shared
    
    private var baseURL: URL {
        URL(string: APIConfig.baseURL + APIConfig.apiVersion)!
    }
    
    private var headers: [String: String] {
        [
            "Authorization": KeychainService.shared.get(.apiToken) ?? "",
            "Content-Type": "application/json"
        ]
    }
}
```

### Async/Await Request Example
```swift
func searchItems(query: String) async throws -> SearchResponse {
    var components = URLComponents(url: baseURL.appendingPathComponent("search"), resolvingAgainstBaseURL: false)!
    components.queryItems = [URLQueryItem(name: "q", value: query)]
    
    var request = URLRequest(url: components.url!)
    request.allHTTPHeaderFields = headers
    
    let (data, response) = try await session.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse,
          (200...299).contains(httpResponse.statusCode) else {
        throw APIError.invalidResponse
    }
    
    return try JSONDecoder().decode(SearchResponse.self, from: data)
}
```

### Error Handling
```swift
enum APIError: Error {
    case invalidResponse
    case unauthorized
    case serverError(String)
    case networkError(Error)
    case decodingError(Error)
}
```

### Offline Support Strategy
1. Cache all GET responses in Core Data
2. Queue POST/PUT/DELETE operations when offline
3. Sync when connection restored
4. Show offline indicator in UI

## Testing Against Local Backend

### 1. Simulator Testing
```bash
# Backend should be accessible at host machine's IP
# Find your IP: ifconfig | grep inet
# Update API_URL to http://YOUR_IP:8000
```

### 2. Device Testing
- Ensure device and backend are on same network
- Update API_URL to backend machine's IP
- May need to disable App Transport Security for HTTP

### 3. Mock Server Option
```swift
#if DEBUG
class MockAPIClient: APIClientProtocol {
    // Return mock data for testing
}
#endif
```

## Rate Limiting
Backend implements rate limiting:
- 100 requests per minute per IP
- Handle 429 responses with exponential backoff

## Important Notes
1. All timestamps are ISO 8601 format
2. IDs are UUIDs
3. Pagination uses limit/offset
4. Search supports fuzzy matching
5. Tags are case-insensitive