import Foundation

/// Networking errors that can occur when interacting with the PRSNL API
enum APIError: Error {
    case invalidURL
    case requestFailed(Error)
    case invalidResponse
    case decodingFailed(Error)
    case serverError(Int, String)
    case unauthorized
    case networkUnavailable
    
    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .requestFailed(let error):
            return "Request failed: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid server response"
        case .decodingFailed(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message)"
        case .unauthorized:
            return "Authentication required"
        case .networkUnavailable:
            return "Network connection unavailable"
        }
    }
}

/// Provides methods for interacting with the PRSNL API
class APIClient {
    static let shared = APIClient()
    
    /// Base URL from Keychain, defaulting to localhost if not set
    var baseURL: String {
        let stored = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
        return stored + "/api"
    }
    
    /// Base server URL without /api for attachment paths
    var serverURL: String {
        return KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
    }
    
    /// API key stored in Keychain
    private var apiKey: String? {
        return KeychainService.shared.get(.apiKey)
    }
    
    private init() {
        // Set default API key for development if none exists
        if apiKey == nil {
            KeychainService.shared.set("test-api-key-for-development", for: .apiKey)
        }
    }
    
    /// Sets the API key for authentication
    func setAPIKey(_ key: String) {
        KeychainService.shared.set(key, for: .apiKey)
    }
    
    /// Clears the API key
    func clearAPIKey() {
        KeychainService.shared.delete(.apiKey)
    }
    
    /// Sets a custom server URL
    func setServerURL(_ url: String) {
        KeychainService.shared.set(url, for: .serverURL)
    }
    
    /// Makes an API request
    /// - Parameters:
    ///   - endpoint: The API endpoint (path component after baseURL)
    ///   - method: HTTP method (GET, POST, etc.)
    ///   - params: Optional query parameters
    ///   - body: Optional request body data
    ///   - requiresAuth: Whether this request requires authentication
    /// - Returns: Data from the API response
    private func request(
        endpoint: String,
        method: String = "GET",
        params: [String: String]? = nil,
        body: Data? = nil,
        requiresAuth: Bool = true
    ) async throws -> Data {
        // Construct URL with query parameters
        guard var components = URLComponents(string: "\(baseURL)/\(endpoint)") else {
            throw APIError.invalidURL
        }
        
        if let params = params {
            components.queryItems = params.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        
        guard let url = components.url else {
            throw APIError.invalidURL
        }
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add auth API key if required
        if requiresAuth {
            guard let key = apiKey else {
                throw APIError.unauthorized
            }
            request.addValue(key, forHTTPHeaderField: "X-API-Key")
        }
        
        // Add body if provided
        if let body = body {
            request.httpBody = body
        }
        
        // Execute request
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            // Check response status
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200..<300:
                return data
            case 401:
                throw APIError.unauthorized
            default:
                // Try to extract error message from response
                let errorMessage = try? JSONDecoder().decode([String: String].self, from: data)["message"] ?? "Unknown error"
                throw APIError.serverError(httpResponse.statusCode, errorMessage ?? "Unknown error")
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.requestFailed(error)
        }
    }
    
    // MARK: - Timeline API
    
    /// Fetches the user's knowledge timeline
    /// - Parameters:
    ///   - page: Page number for pagination (starts at 1)
    ///   - limit: Number of items per page
    ///   - tags: Optional array of tags to filter by
    /// - Returns: Array of timeline items and pagination info
    func fetchTimeline(page: Int = 1, limit: Int = 20, tags: [String]? = nil) async throws -> TimelineResponse {
        var params: [String: String] = [
            "page": "\(page)",
            "limit": "\(limit)"
        ]
        
        // Add tags filter if provided
        if let tags = tags, !tags.isEmpty {
            params["tags"] = tags.joined(separator: ",")
        }
        
        let data = try await request(endpoint: "timeline", params: params)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            let response = try decoder.decode(TimelineResponse.self, from: data)
            return response
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Response structure for timeline API
    struct TimelineResponse: Codable {
        let items: [Item]
        let totalCount: Int
        let page: Int
        let totalPages: Int
        
        enum CodingKeys: String, CodingKey {
            case items
            case totalCount = "total_count"
            case page
            case totalPages = "total_pages"
        }
    }
    
    // MARK: - Item API
    
    /// Fetches a specific item by ID
    /// - Parameter id: The item's unique identifier
    /// - Returns: The requested item
    func fetchItem(id: String) async throws -> Item {
        let data = try await request(endpoint: "items/\(id)")
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            return try decoder.decode(Item.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Creates a new item
    /// - Parameters:
    ///   - title: Item title
    ///   - content: Item content text
    ///   - tags: Array of tags
    ///   - itemType: Type of item (default: .note)
    /// - Returns: The newly created item
    func createItem(title: String, content: String, tags: [String], itemType: ItemType = .note) async throws -> Item {
        let itemData = CreateItemRequest(
            title: title,
            content: content,
            tags: tags,
            itemType: itemType
        )
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let body = try encoder.encode(itemData)
        
        let data = try await request(endpoint: "items", method: "POST", body: body)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            return try decoder.decode(Item.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Request structure for creating items
    private struct CreateItemRequest: Codable {
        let title: String
        let content: String
        let tags: [String]
        let itemType: ItemType
        
        enum CodingKeys: String, CodingKey {
            case title
            case content
            case tags
            case itemType = "item_type"
        }
    }
    
    // MARK: - Search API
    
    /// Searches for items matching the query
    /// - Parameters:
    ///   - query: Search query text
    ///   - page: Page number for pagination
    ///   - limit: Items per page
    /// - Returns: Search results
    func searchItems(query: String, page: Int = 1, limit: Int = 20) async throws -> SearchResponse {
        let params: [String: String] = [
            "q": query,
            "page": "\(page)",
            "limit": "\(limit)"
        ]
        
        let data = try await request(endpoint: "search", params: params)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            let response = try decoder.decode(SearchResponse.self, from: data)
            return response
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Response structure for search API
    struct SearchResponse: Codable {
        let items: [Item]
        let totalResults: Int
        
        enum CodingKeys: String, CodingKey {
            case items
            case totalResults = "total_results"
        }
    }
    
    /// Performs a semantic search using the content of an existing item
    /// - Parameters:
    ///   - itemId: The ID of the item to find similar content for
    ///   - limit: Maximum number of results to return
    /// - Returns: List of similar items
    func findSimilarItems(to itemId: String, limit: Int = 10) async throws -> [Item] {
        let params: [String: String] = [
            "limit": "\(limit)"
        ]
        
        let data = try await request(endpoint: "search/similar/\(itemId)", params: params)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            return try decoder.decode([Item].self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    // MARK: - Capture API
    
    /// Captures content from a URL or direct text
    /// - Parameters:
    ///   - url: Optional URL to capture content from
    ///   - content: Optional direct content text
    ///   - title: Optional title for the item
    ///   - highlight: Optional highlighted text
    ///   - tags: Array of tags to assign
    /// - Returns: Capture response with status
    func captureContent(
        url: String? = nil,
        content: String? = nil,
        title: String? = nil,
        highlight: String? = nil,
        tags: [String] = []
    ) async throws -> CaptureResponse {
        // Validate that either URL or content is provided
        guard url != nil || content != nil else {
            throw APIError.invalidInput("Either URL or content must be provided")
        }
        
        let captureRequest = CaptureRequest(
            url: url,
            content: content,
            title: title,
            highlight: highlight,
            tags: tags
        )
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        let body = try encoder.encode(captureRequest)
        
        let data = try await request(endpoint: "capture", method: "POST", body: body)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            return try decoder.decode(CaptureResponse.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Request structure for capture API
    struct CaptureRequest: Codable {
        let url: String?
        let content: String?
        let title: String?
        let highlight: String?
        let tags: [String]
    }
    
    /// Response structure for capture API
    struct CaptureResponse: Codable {
        let id: String
        let status: String
        let message: String
    }
    
    // MARK: - Tags API
    
    /// Fetches all tags with their usage counts
    /// - Returns: Array of tags with counts
    func fetchTags() async throws -> [TagCount] {
        let data = try await request(endpoint: "tags")
        
        let decoder = JSONDecoder()
        
        do {
            return try decoder.decode([TagCount].self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Fetches recently used tags
    /// - Returns: Array of tag names
    func fetchRecentTags() async throws -> [String] {
        let data = try await request(endpoint: "tags/recent")
        
        let decoder = JSONDecoder()
        
        do {
            return try decoder.decode([String].self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
    
    /// Tag with usage count
    struct TagCount: Codable {
        let name: String
        let count: Int
    }
}

// Extension to add custom error case
extension APIError {
    static func invalidInput(_ message: String) -> APIError {
        return .serverError(400, message)
    }
}