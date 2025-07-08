# PRSNL iOS Error Handling Guide

## Backend Error Response Format

All API errors follow this structure:
```json
{
    "detail": "Human-readable error message",
    "code": "ERROR_CODE" // Optional
}
```

## HTTP Status Codes & Error Types

### Custom Exception Classes
| Exception | HTTP Status | Header | Description |
|-----------|-------------|---------|-------------|
| `ItemNotFound` | 404 | `X-Error-Code: ITEM_NOT_FOUND` | Item doesn't exist |
| `InvalidInput` | 400 | `X-Error-Code: INVALID_INPUT` | Validation failed |
| `ServiceUnavailable` | 503 | `X-Error-Code: SERVICE_UNAVAILABLE` | Service temporarily down |
| `InternalServerError` | 500 | `X-Error-Code: INTERNAL_SERVER_ERROR` | Unexpected error |

### Standard HTTP Errors
| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 401 | Unauthorized | Invalid/missing API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Invalid request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server overloaded/maintenance |

## Swift Error Handling Implementation

### Custom Error Types

```swift
enum APIError: LocalizedError {
    case unauthorized
    case notFound(resource: String)
    case invalidInput(message: String)
    case serviceUnavailable(reason: String)
    case serverError(message: String)
    case rateLimitExceeded(retryAfter: Int?)
    case networkError(Error)
    case decodingError(Error)
    case unknown(statusCode: Int, message: String)
    
    var errorDescription: String? {
        switch self {
        case .unauthorized:
            return "Invalid or expired API key. Please check your settings."
        case .notFound(let resource):
            return "\(resource) not found."
        case .invalidInput(let message):
            return "Invalid input: \(message)"
        case .serviceUnavailable(let reason):
            return "Service temporarily unavailable: \(reason)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .rateLimitExceeded(let retryAfter):
            if let seconds = retryAfter {
                return "Too many requests. Try again in \(seconds) seconds."
            }
            return "Too many requests. Please try again later."
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(_):
            return "Unable to process server response."
        case .unknown(let code, let message):
            return "Error \(code): \(message)"
        }
    }
    
    var isRetryable: Bool {
        switch self {
        case .serviceUnavailable, .rateLimitExceeded, .networkError:
            return true
        default:
            return false
        }
    }
}
```

### API Client Error Handling

```swift
extension APIClient {
    func handleResponse<T: Decodable>(_ data: Data?, _ response: URLResponse?) async throws -> T {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown(statusCode: 0, message: "Invalid response")
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            // Success
            guard let data = data else {
                throw APIError.unknown(statusCode: httpResponse.statusCode, message: "No data")
            }
            
            do {
                return try JSONDecoder.prsnlDecoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
            
        case 401:
            throw APIError.unauthorized
            
        case 404:
            let errorCode = httpResponse.value(forHTTPHeaderField: "X-Error-Code")
            if errorCode == "ITEM_NOT_FOUND" {
                throw APIError.notFound(resource: "Item")
            }
            throw APIError.notFound(resource: "Resource")
            
        case 400:
            let errorMessage = try? decodeError(from: data)
            throw APIError.invalidInput(message: errorMessage ?? "Invalid request")
            
        case 429:
            let retryAfter = httpResponse.value(forHTTPHeaderField: "Retry-After")
                .flatMap { Int($0) }
            throw APIError.rateLimitExceeded(retryAfter: retryAfter)
            
        case 500:
            let errorMessage = try? decodeError(from: data)
            throw APIError.serverError(message: errorMessage ?? "Internal server error")
            
        case 503:
            let errorMessage = try? decodeError(from: data)
            throw APIError.serviceUnavailable(reason: errorMessage ?? "Service unavailable")
            
        default:
            let errorMessage = try? decodeError(from: data)
            throw APIError.unknown(
                statusCode: httpResponse.statusCode,
                message: errorMessage ?? "Unknown error"
            )
        }
    }
    
    private func decodeError(from data: Data?) -> String? {
        guard let data = data else { return nil }
        
        struct ErrorResponse: Codable {
            let detail: String
        }
        
        return try? JSONDecoder().decode(ErrorResponse.self, from: data).detail
    }
}
```

### Retry Logic with Exponential Backoff

```swift
class RetryManager {
    static func retry<T>(
        maxAttempts: Int = 3,
        delay: TimeInterval = 1.0,
        operation: @escaping () async throws -> T
    ) async throws -> T {
        var lastError: Error?
        
        for attempt in 0..<maxAttempts {
            do {
                return try await operation()
            } catch let error as APIError {
                lastError = error
                
                // Check if error is retryable
                guard error.isRetryable else {
                    throw error
                }
                
                // Special handling for rate limits
                if case .rateLimitExceeded(let retryAfter) = error {
                    let waitTime = TimeInterval(retryAfter ?? 60)
                    try await Task.sleep(nanoseconds: UInt64(waitTime * 1_000_000_000))
                    continue
                }
                
                // Exponential backoff for other retryable errors
                if attempt < maxAttempts - 1 {
                    let backoffDelay = delay * pow(2.0, Double(attempt))
                    try await Task.sleep(nanoseconds: UInt64(backoffDelay * 1_000_000_000))
                }
            } catch {
                // Non-API errors
                throw error
            }
        }
        
        throw lastError ?? APIError.unknown(statusCode: 0, message: "Max retries exceeded")
    }
}

// Usage
let items = try await RetryManager.retry {
    try await apiClient.fetchTimeline()
}
```

### User-Friendly Error Presentation

```swift
struct ErrorView: View {
    let error: Error
    let retry: (() -> Void)?
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: errorIcon)
                .font(.largeTitle)
                .foregroundColor(errorColor)
            
            Text(errorTitle)
                .font(.headline)
            
            Text(error.localizedDescription)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            if let retry = retry, isRetryable {
                Button("Try Again") {
                    retry()
                }
                .buttonStyle(.borderedProminent)
                .tint(.prsnlRed)
            }
        }
        .padding()
    }
    
    private var errorIcon: String {
        switch error {
        case is APIError:
            if case .networkError = error as! APIError {
                return "wifi.slash"
            } else if case .unauthorized = error as! APIError {
                return "lock.shield"
            }
            return "exclamationmark.triangle"
        default:
            return "xmark.circle"
        }
    }
    
    private var errorColor: Color {
        switch error {
        case is APIError:
            if case .rateLimitExceeded = error as! APIError {
                return .orange
            }
            return .red
        default:
            return .red
        }
    }
    
    private var errorTitle: String {
        switch error {
        case is APIError:
            if case .networkError = error as! APIError {
                return "Connection Error"
            } else if case .unauthorized = error as! APIError {
                return "Authentication Required"
            } else if case .rateLimitExceeded = error as! APIError {
                return "Slow Down"
            }
            return "Something Went Wrong"
        default:
            return "Error"
        }
    }
    
    private var isRetryable: Bool {
        if let apiError = error as? APIError {
            return apiError.isRetryable
        }
        return false
    }
}
```

### Offline Error Handling

```swift
class NetworkMonitor: ObservableObject {
    @Published var isConnected = true
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    
    init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
            }
        }
        monitor.start(queue: queue)
    }
}

// In your view
@StateObject private var networkMonitor = NetworkMonitor()

var body: some View {
    if !networkMonitor.isConnected {
        OfflineBanner()
    }
    // Rest of your view
}
```

### Logging Errors

```swift
extension APIClient {
    private func logError(_ error: Error, endpoint: String, context: [String: Any]? = nil) {
        #if DEBUG
        print("❌ API Error: \(endpoint)")
        print("   Error: \(error.localizedDescription)")
        if let context = context {
            print("   Context: \(context)")
        }
        #endif
        
        // In production, send to analytics service
        // Analytics.logError(error, metadata: ["endpoint": endpoint])
    }
}
```

## Common Error Scenarios

### 1. API Key Invalid
```swift
// In your API client
if case .unauthorized = error {
    // Clear stored credentials
    KeychainService.shared.delete(.apiKey)
    
    // Navigate to settings
    navigationManager.showSettings()
}
```

### 2. Item Not Found
```swift
// When fetching item details
do {
    let item = try await apiClient.fetchItem(id: itemId)
} catch APIError.notFound {
    // Show friendly message
    showAlert("This item has been deleted or is no longer available.")
    // Navigate back
    navigationPath.removeLast()
}
```

### 3. Network Timeout
```swift
// Configure URLSession with timeout
let configuration = URLSessionConfiguration.default
configuration.timeoutIntervalForRequest = 30
configuration.timeoutIntervalForResource = 60
```

### 4. Large File Upload
```swift
// Handle upload errors specifically
do {
    try await apiClient.uploadLargeFile(data)
} catch {
    if (error as NSError).code == NSURLErrorTimedOut {
        showAlert("Upload timed out. Try a smaller file or better connection.")
    }
}
```

## Best Practices

1. **Always provide actionable error messages** - Tell users what they can do
2. **Implement retry for transient errors** - Network issues, rate limits
3. **Log errors for debugging** - But don't expose technical details to users
4. **Handle offline gracefully** - Cache data and queue requests
5. **Validate input client-side** - Prevent unnecessary API calls
6. **Show progress indicators** - Users are more patient when they see progress
7. **Test error scenarios** - Simulate network failures, invalid responses

## Testing Error Handling

```swift
// Mock API client for testing
class MockAPIClient: APIClientProtocol {
    var shouldFail = false
    var errorToThrow: APIError = .networkError(NSError())
    
    func fetchTimeline() async throws -> TimelineResponse {
        if shouldFail {
            throw errorToThrow
        }
        
        // Return mock data
        return TimelineResponse(items: [], total: 0, page: 1, pageSize: 20)
    }
}
```