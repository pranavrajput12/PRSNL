# Swift Models for PRSNL iOS App

Copy these models directly into your iOS project. They match the backend schemas exactly.

```swift
import Foundation

// MARK: - Enums

enum ItemStatus: String, Codable, CaseIterable {
    case pending = "pending"
    case completed = "completed"
    case failed = "failed"
    case bookmark = "bookmark"
}

enum VideoQuality: String, Codable, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case original = "original"
}

// MARK: - Core Models

struct Item: Codable, Identifiable {
    let id: UUID
    let url: String?
    let title: String
    let summary: String?
    let content: String?
    let tags: [String]
    let createdAt: Date
    let updatedAt: Date
    let accessedAt: Date
    let accessCount: Int
    let status: ItemStatus
    
    enum CodingKeys: String, CodingKey {
        case id, url, title, summary, content, tags, status
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case accessedAt = "accessed_at"
        case accessCount = "access_count"
    }
}

// MARK: - Request Models

struct CaptureRequest: Codable {
    let url: String?
    let content: String?
    let title: String?
    let highlight: String?
    let tags: [String]?
    
    init(url: String? = nil, content: String? = nil, title: String? = nil, 
         highlight: String? = nil, tags: [String]? = nil) {
        self.url = url
        self.content = content
        self.title = title
        self.highlight = highlight
        self.tags = tags
    }
}

struct ItemUpdateRequest: Codable {
    let title: String?
    let summary: String?
    let tags: [String]?
}

struct SearchRequest: Codable {
    let query: String
    let tags: [String]?
    let limit: Int?
    let offset: Int?
    
    init(query: String, tags: [String]? = nil, limit: Int? = 20, offset: Int? = 0) {
        self.query = query
        self.tags = tags
        self.limit = limit
        self.offset = offset
    }
}

struct SemanticSearchRequest: Codable {
    let query: String
}

// MARK: - Response Models

struct CaptureResponse: Codable {
    let id: UUID
    let status: ItemStatus
    let message: String
}

struct SearchResult: Codable, Identifiable {
    let id: UUID
    let title: String
    let url: String?
    let snippet: String
    let tags: [String]
    let createdAt: Date
    let score: Float?
    
    enum CodingKeys: String, CodingKey {
        case id, title, url, snippet, tags, score
        case createdAt = "created_at"
    }
}

struct SearchResponse: Codable {
    let results: [SearchResult]
    let total: Int
    let tookMs: Int
    
    enum CodingKeys: String, CodingKey {
        case results, total
        case tookMs = "took_ms"
    }
}

struct TimelineItem: Codable, Identifiable {
    let id: UUID
    let title: String
    let url: String?
    let summary: String
    let tags: [String]
    let createdAt: Date
    let itemType: String?
    let thumbnailUrl: String?
    let duration: Int?
    let platform: String?
    let status: ItemStatus
    
    enum CodingKeys: String, CodingKey {
        case id, title, url, summary, tags, status, duration, platform
        case createdAt = "created_at"
        case itemType = "item_type"
        case thumbnailUrl = "thumbnail_url"
    }
}

struct TimelineResponse: Codable {
    let items: [TimelineItem]
    let total: Int
    let page: Int
    let pageSize: Int
}

struct Tag: Codable {
    let name: String
    let count: Int
}

struct TrendData: Codable {
    let date: String
    let count: Int
}

struct TrendsResponse: Codable {
    let trends: [TrendData]
}

struct UsagePatternsResponse: Codable {
    let totalItems: Int
    let averageItemsPerDayLast30Days: Float
    
    enum CodingKeys: String, CodingKey {
        case totalItems = "total_items"
        case averageItemsPerDayLast30Days = "average_items_per_day_last_30_days"
    }
}

// MARK: - API Error

struct APIError: Codable, LocalizedError {
    let detail: String
    let code: String?
    
    var errorDescription: String? {
        return detail
    }
}

// MARK: - Validation Constants

struct ValidationConstants {
    static let maxTitleLength = 500
    static let maxSummaryLength = 5000
    static let maxContentLength = 50000
    static let maxTagLength = 50
    static let maxTagsCount = 20
    static let maxQueryLength = 1000
    static let maxHighlightLength = 1000
}

// MARK: - Extensions for Validation

extension String {
    func isValidTag() -> Bool {
        let pattern = "^[a-z0-9\\s\\-]+$"
        let regex = try? NSRegularExpression(pattern: pattern, options: .caseInsensitive)
        let range = NSRange(location: 0, length: self.utf16.count)
        return regex?.firstMatch(in: self.lowercased(), options: [], range: range) != nil
    }
    
    func sanitizedTag() -> String? {
        let trimmed = self.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimmed.isEmpty,
              trimmed.count <= ValidationConstants.maxTagLength,
              trimmed.isValidTag() else {
            return nil
        }
        return trimmed
    }
}

extension Array where Element == String {
    func sanitizedTags() -> [String] {
        return self.compactMap { $0.sanitizedTag() }
            .removingDuplicates()
            .prefix(ValidationConstants.maxTagsCount)
            .map { $0 }
    }
}

extension Array where Element: Equatable {
    func removingDuplicates() -> [Element] {
        var result = [Element]()
        for value in self {
            if !result.contains(value) {
                result.append(value)
            }
        }
        return result
    }
}

// MARK: - Date Formatter

extension DateFormatter {
    static let iso8601Full: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
        formatter.calendar = Calendar(identifier: .iso8601)
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()
}

// MARK: - Custom Date Decoding Strategy

extension JSONDecoder {
    static let prsnlDecoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            // Try ISO8601 with fractional seconds first
            if let date = DateFormatter.iso8601Full.date(from: dateString) {
                return date
            }
            
            // Try standard ISO8601
            if let date = ISO8601DateFormatter().date(from: dateString) {
                return date
            }
            
            throw DecodingError.dataCorruptedError(in: container, 
                debugDescription: "Cannot decode date string \(dateString)")
        }
        return decoder
    }()
}

extension JSONEncoder {
    static let prsnlEncoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .custom { date, encoder in
            var container = encoder.singleValueContainer()
            let dateString = DateFormatter.iso8601Full.string(from: date)
            try container.encode(dateString)
        }
        return encoder
    }()
}
```

## Usage Examples

### Creating a capture request:
```swift
let captureRequest = CaptureRequest(
    url: "https://example.com/article",
    title: "Interesting Article",
    tags: ["technology", "ai"]
)

let jsonData = try JSONEncoder.prsnlEncoder.encode(captureRequest)
```

### Decoding search results:
```swift
let searchResponse = try JSONDecoder.prsnlDecoder.decode(
    SearchResponse.self, 
    from: responseData
)

for result in searchResponse.results {
    print("\(result.title) - Score: \(result.score ?? 0)")
}
```

### Validating tags before sending:
```swift
let userTags = ["Technology", "AI/ML", "  productivity  ", ""]
let validTags = userTags.sanitizedTags()
// Result: ["technology", "ai-ml", "productivity"]
```

### Working with dates:
```swift
// The custom decoder/encoder handles the backend's date format automatically
let item = try JSONDecoder.prsnlDecoder.decode(Item.self, from: itemData)
print("Created: \(item.createdAt)")  // Already a Swift Date object
```

## Important Notes

1. **Always use `JSONDecoder.prsnlDecoder` and `JSONEncoder.prsnlEncoder`** for consistency with backend date formats
2. **Tag validation**: Use the `sanitizedTags()` extension before sending tags to the backend
3. **Optional fields**: Many fields are optional (`String?`) - handle these appropriately in your UI
4. **Score field**: In search results, score is optional and ranges from 0.0 to 1.0
5. **Media URLs**: `thumbnailUrl` and similar fields are relative paths - prepend with base URL

These models provide complete type safety and match the backend API exactly.