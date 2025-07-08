# PRSNL iOS App - Project Brief for Kilo Code

## Quick Start

You are building a **native iOS app** for PRSNL, a personal knowledge management system. The backend is already complete and running. Your job is to create the iOS client only.

### Critical Rules
1. **ONLY work in `/PRSNL-iOS/` directory**
2. **DO NOT modify anything in `/PRSNL/` directory**
3. **DO NOT interact with other agents' files**

### Your Resources
1. **KILO_CODE_GUIDE.md** - Complete API documentation and boundaries
2. **SWIFT_MODELS.md** - Ready-to-use Swift models matching backend exactly
3. **ARCHITECTURE.md** - Technical decisions and app structure
4. **DEVELOPMENT_PLAN.md** - Phased development approach

## Project Setup

### 1. Create Xcode Project
- Name: PRSNL
- Interface: SwiftUI
- Language: Swift
- Minimum iOS: 17.0
- Include Core Data

### 2. Project Structure
```
PRSNL-iOS/
├── PRSNL.xcodeproj
├── PRSNL/
│   ├── App/
│   │   ├── PRSNLApp.swift
│   │   └── AppDelegate.swift
│   ├── Core/
│   │   ├── API/
│   │   │   ├── APIClient.swift
│   │   │   ├── APIEndpoints.swift
│   │   │   └── APIError.swift
│   │   ├── Models/
│   │   │   ├── Models.swift (copy from SWIFT_MODELS.md)
│   │   │   └── CoreDataModels.xcdatamodeld
│   │   ├── Services/
│   │   │   ├── AuthenticationService.swift
│   │   │   ├── CacheService.swift
│   │   │   └── SyncService.swift
│   │   └── Extensions/
│   ├── Features/
│   │   ├── Timeline/
│   │   ├── Search/
│   │   ├── Capture/
│   │   ├── ItemDetail/
│   │   └── Settings/
│   └── Shared/
│       ├── Components/
│       ├── Styles/
│       └── Utils/
└── PRSNLTests/
```

## MVP Features (Phase 1 & 2)

### 1. Timeline View (First Priority)
- Infinite scroll with pagination
- Pull-to-refresh
- Display items chronologically
- Show title, summary, tags, date
- Tap to view details

### 2. Search
- Tab bar with "Keyword" and "Semantic" options
- Search bar with debouncing
- Display results with relevance scores
- Recent searches

### 3. Item Detail
- Full content display
- Tags (read-only for MVP)
- Share button
- "Find Similar" button

### 4. Basic Capture
- URL input field
- Title field (optional)
- Tags field (comma-separated)
- Save button

### 5. Settings
- API key input (secure storage)
- Server URL configuration
- About screen

## Design Guidelines

### Colors
```swift
extension Color {
    static let prsnlRed = Color(hex: "DC143C")      // Manchester United red
    static let prsnlBackground = Color(hex: "0A0A0A") // Dark background
    static let prsnlSurface = Color(hex: "1A1A1A")   // Card background
    static let prsnlText = Color(hex: "FFFFFF")      // Primary text
    static let prsnlTextSecondary = Color(hex: "A0A0A0") // Secondary text
}
```

### Typography
- Headings: SF Pro Display
- Body: SF Pro Text
- Support Dynamic Type

## API Integration

### Base Setup
```swift
class APIClient {
    static let shared = APIClient()
    private let baseURL = "http://localhost:8000/api"
    private var apiKey: String? {
        KeychainService.shared.get(.apiKey)
    }
    
    private var headers: [String: String] {
        var headers = ["Content-Type": "application/json"]
        if let apiKey = apiKey {
            headers["X-API-Key"] = apiKey
        }
        return headers
    }
}
```

### First Endpoint to Implement
```swift
// Timeline - easiest to test and visualize
func fetchTimeline(page: Int = 1) async throws -> TimelineResponse {
    let url = URL(string: "\(baseURL)/timeline?page=\(page)&limit=20")!
    var request = URLRequest(url: url)
    request.allHTTPHeaderFields = headers
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder.prsnlDecoder.decode(TimelineResponse.self, from: data)
}
```

## Development Priorities

### Week 1
1. ✅ Project setup
2. ✅ Copy models from SWIFT_MODELS.md
3. ✅ Implement APIClient
4. ✅ Create Timeline view
5. ✅ Test with real backend

### Week 2
1. Add Search functionality
2. Implement Item Detail view
3. Create Capture screen
4. Add Settings

### Week 3
1. Core Data integration
2. Offline support
3. Error handling
4. Polish UI

## Testing the Backend

1. Ensure PRSNL backend is running:
   ```bash
   cd /PRSNL/backend
   docker-compose up
   ```

2. Backend will be available at `http://localhost:8000`

3. Get an API key from the web interface or use the test key if provided

## Common Pitfalls to Avoid

1. **Date Handling**: Always use `JSONDecoder.prsnlDecoder` (not standard decoder)
2. **Tag Validation**: Sanitize tags before sending to backend
3. **Media URLs**: Prepend base URL to relative paths
4. **Rate Limits**: Implement exponential backoff for 429 errors
5. **Empty States**: Handle empty timeline/search results gracefully

## Questions for Claude02

If you need clarification on:
- Architecture decisions
- API behavior
- Security considerations
- Performance optimization

Ask Claude02 for guidance. Focus on implementation while Claude02 handles technical advisory.

## Success Criteria

The app is successful when:
1. Users can browse their knowledge timeline
2. Search works (both keyword and semantic)
3. Items can be captured from the app
4. Offline viewing works for cached content
5. The app feels native and performs well

---

**Remember**: You're building a companion iOS app, not modifying the existing system. Keep it simple, make it work, then make it beautiful.