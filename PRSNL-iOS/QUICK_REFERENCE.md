# PRSNL iOS Quick Reference for Kilo Code

## 🚀 Start Here

### Environment Setup
```bash
# Backend should be running at:
http://localhost:8000

# Test the backend:
curl http://localhost:8000/health

# API documentation available at:
http://localhost:8000/docs
```

### Test API Key
If you need a test API key, set this environment variable when running the backend:
```bash
PRSNL_API_KEY=test-api-key-for-development
```

### First API Call to Test
```swift
// Test your setup with the tags endpoint (public)
let url = URL(string: "http://localhost:8000/api/tags")!
let (data, _) = try await URLSession.shared.data(from: url)
let tags = try JSONDecoder().decode([Tag].self, from: data)
print("Found \(tags.count) tags")
```

## 🎯 MVP Priority Order

1. **Timeline View** ← Start here (easiest to test)
2. **Search** (keyword first, then semantic)
3. **Item Detail**
4. **Capture**
5. **Settings**

## 🔑 Key Information

### Manchester United Theme
```swift
extension Color {
    static let prsnlRed = Color(hex: "DC143C")
    static let prsnlBackground = Color(hex: "0A0A0A")
    static let prsnlSurface = Color(hex: "1A1A1A")
}
```

### Date Handling
```swift
// Always use the custom decoder
let timeline = try JSONDecoder.prsnlDecoder.decode(
    TimelineResponse.self, 
    from: data
)
```

### Image URLs
```swift
// Thumbnails and images need base URL prefix
let fullURL = baseURL + item.thumbnailUrl
```

### Protected Endpoints
These require `X-API-Key` header:
- POST/PATCH/DELETE `/api/items`
- POST `/api/capture`
- Admin endpoints

## 🐛 Common Issues & Solutions

### "Invalid API Key"
- Check KeychainService has stored key
- Verify header name is `X-API-Key` (not `x-api-key`)
- Try Bearer token format as fallback

### Empty Timeline
- Backend might not have data
- Create test items via web UI first
- Check if using correct endpoint

### Network Errors
- Ensure backend is running
- Check if using http (not https) for localhost
- Simulator needs host machine IP, not localhost

### Date Parsing Errors
- Use `JSONDecoder.prsnlDecoder` not standard decoder
- Backend uses ISO8601 with fractional seconds

## 📱 SwiftUI Tips

### Navigation
```swift
// Use NavigationStack (iOS 16+)
NavigationStack {
    TimelineView()
}
```

### Loading States
```swift
.overlay {
    if isLoading {
        ProgressView()
    }
}
```

### Error Display
```swift
.alert("Error", isPresented: $showError) {
    Button("OK") { }
} message: {
    Text(error?.localizedDescription ?? "Unknown error")
}
```

## 🧪 Testing Without Backend

### Mock Data
```swift
#if DEBUG
extension TimelineResponse {
    static let mock = TimelineResponse(
        items: [
            TimelineItem(
                id: UUID(),
                title: "Test Item",
                url: "https://example.com",
                summary: "Test summary",
                tags: ["test"],
                createdAt: Date(),
                itemType: "article",
                thumbnailUrl: nil,
                duration: nil,
                platform: nil,
                status: .completed
            )
        ],
        total: 1,
        page: 1,
        pageSize: 20
    )
}
#endif
```

## 📞 Quick Questions Cheatsheet

**Q: Which endpoint for X?**
→ Check KILO_CODE_GUIDE.md section "Core Endpoints You'll Need"

**Q: How to handle this error?**
→ Check ERROR_HANDLING_GUIDE.md for error types

**Q: WebSocket not connecting?**
→ Change http to ws in URL, use unique client_id

**Q: Video won't play?**
→ Check VIDEO_HANDLING_GUIDE.md for URL construction

**Q: Share extension setup?**
→ SHARE_EXTENSION_GUIDE.md has full implementation

## 🎨 UI Component Library

You might want to create these reusable components:
- `ItemCard` - For timeline/search results
- `TagChip` - Consistent tag display
- `LoadingView` - Skeleton loader
- `ErrorView` - Consistent error display
- `EmptyStateView` - For empty results

## ⚡ Performance Quick Wins

1. Use `LazyVStack` not `VStack` for lists
2. Implement pagination early
3. Cache images with `URLCache`
4. Debounce search input
5. Cancel previous requests

Remember: **Get it working first, then optimize!**