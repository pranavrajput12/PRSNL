import Foundation
import Combine

enum APIError: Error {
    case invalidURL
    case requestFailed(Error)
    case invalidResponse
    case decodingFailed(Error)
    case serverError(Int, String)
    case unauthorized
    case networkUnavailable
}

class APIClient {
    static let shared = APIClient()
    private let session = URLSession.shared
    private let decoder = JSONDecoder()
    
    init() {
        // Custom date decoder to handle backend format with milliseconds
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
        formatter.timeZone = TimeZone(abbreviation: "UTC")
        
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            // Try with milliseconds first
            if let date = formatter.date(from: dateString) {
                return date
            }
            
            // Fallback to ISO8601 without milliseconds
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            if let date = formatter.date(from: dateString) {
                return date
            }
            
            // Last fallback to standard ISO8601
            let iso8601Formatter = ISO8601DateFormatter()
            if let date = iso8601Formatter.date(from: dateString) {
                return date
            }
            
            throw DecodingError.dataCorrupted(
                DecodingError.Context(
                    codingPath: decoder.codingPath,
                    debugDescription: "Invalid date format: \(dateString)"
                )
            )
        }
    }
    
    // MARK: - Helper Methods
    private func createRequest(url: URL, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        APIConfiguration.shared.headers.forEach { request.setValue($0.value, forHTTPHeaderField: $0.key) }
        return request
    }
    
    private func performRequest<T: Decodable>(_ request: URLRequest, type: T.Type) async throws -> T {
        print("🌐 Making request to: \(request.url?.absoluteString ?? "unknown")")
        print("🌐 Headers: \(request.allHTTPHeaderFields ?? [:])")
        print("🌐 HTTP Method: \(request.httpMethod ?? "GET")")
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ Invalid response type")
                throw APIError.invalidResponse
            }
            
            print("🌐 Response status: \(httpResponse.statusCode)")
            print("🌐 Response headers: \(httpResponse.allHeaderFields)")
            
            if let responseString = String(data: data, encoding: .utf8) {
                print("🌐 Response body (first 1000 chars): \(responseString.prefix(1000))")
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                do {
                    let decoded = try decoder.decode(type, from: data)
                    print("✅ Successfully decoded response of type \(type)")
                    return decoded
                } catch {
                    print("❌ Decoding failed: \(error)")
                    if let decodingError = error as? DecodingError {
                        print("❌ Detailed decoding error: \(decodingError)")
                        switch decodingError {
                        case .keyNotFound(let key, let context):
                            print("❌ Key '\(key.stringValue)' not found: \(context.debugDescription)")
                        case .typeMismatch(let type, let context):
                            print("❌ Type mismatch for \(type): \(context.debugDescription)")
                        case .valueNotFound(let type, let context):
                            print("❌ Value not found for \(type): \(context.debugDescription)")
                        case .dataCorrupted(let context):
                            print("❌ Data corrupted: \(context.debugDescription)")
                        @unknown default:
                            print("❌ Unknown decoding error")
                        }
                    }
                    throw APIError.decodingFailed(error)
                }
            case 401:
                print("❌ Unauthorized (401)")
                throw APIError.unauthorized
            default:
                let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
                print("❌ Server error \(httpResponse.statusCode): \(errorMessage)")
                throw APIError.serverError(httpResponse.statusCode, errorMessage)
            }
        } catch {
            print("❌ Network request failed: \(error)")
            if let urlError = error as? URLError {
                print("❌ URLError code: \(urlError.code.rawValue), description: \(urlError.localizedDescription)")
            }
            throw APIError.requestFailed(error)
        }
    }
    
    // MARK: - Timeline
    func fetchTimeline(page: Int = 1, limit: Int = 20) async throws -> TimelineResponse {
        let url = URL(string: "\(APIConfiguration.shared.timelineURL)?page=\(page)&limit=\(limit)")!
        let request = createRequest(url: url)
        return try await performRequest(request, type: TimelineResponse.self)
    }
    
    // MARK: - Search
    func search(query: String, limit: Int = 20) async throws -> SearchResponse {
        guard var urlComponents = URLComponents(string: APIConfiguration.shared.searchURL) else {
            throw APIError.invalidURL
        }
        
        urlComponents.queryItems = [
            URLQueryItem(name: "query", value: query),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        
        guard let searchURL = urlComponents.url else {
            throw APIError.invalidURL
        }
        
        let request = createRequest(url: searchURL)
        
        print("🔍 Searching for: \(query)")
        print("🔍 Final URL: \(searchURL.absoluteString)")
        return try await performRequest(request, type: SearchResponse.self)
    }
    
    // MARK: - Item Details
    func fetchItem(id: String) async throws -> Item {
        let url = URL(string: "\(APIConfiguration.shared.itemsURL)/\(id)")!
        let request = createRequest(url: url)
        return try await performRequest(request, type: Item.self)
    }
    
    // MARK: - Insights
    func fetchInsights() async throws -> InsightsResponse {
        let url = URL(string: APIConfiguration.shared.insightsURL)!
        let request = createRequest(url: url)
        return try await performRequest(request, type: InsightsResponse.self)
    }
    
    // MARK: - Videos
    func fetchVideos(limit: Int = 20, offset: Int = 0) async throws -> VideosResponse {
        // Backend doesn't support videos endpoint yet, return empty response
        print("⚠️ Videos endpoint not implemented in backend, returning empty response")
        
        let mockResponse = VideosResponse(
            videos: [],
            total: 0,
            limit: limit,
            offset: offset,
            hasMore: false
        )
        
        return mockResponse
    }
    
    // MARK: - Analytics
    func fetchAnalytics() async throws -> AnalyticsResponse {
        let url = URL(string: APIConfiguration.shared.analyticsURL)!
        let request = createRequest(url: url)
        return try await performRequest(request, type: AnalyticsResponse.self)
    }
    
    // MARK: - Capture
    func capture(url: String, title: String? = nil, tags: [String]? = nil) async throws -> Item {
        let captureURL = URL(string: APIConfiguration.shared.captureURL)!
        var request = createRequest(url: captureURL, method: "POST")
        
        // Generate title from URL if not provided (backend requires title)
        let finalTitle = title ?? generateTitleFromURL(url)
        
        let captureRequest = CaptureRequest(
            url: url,
            title: finalTitle,
            tags: tags
        )
        
        do {
            let jsonData = try JSONEncoder().encode(captureRequest)
            request.httpBody = jsonData
            
            print("🔗 Capturing URL: \(url) with title: \(finalTitle)")
            let response = try await performRequest(request, type: CaptureResponse.self)
            return response.item
        } catch {
            print("❌ Capture failed: \(error)")
            throw error
        }
    }
    
    private func generateTitleFromURL(_ url: String) -> String {
        guard let urlObj = URL(string: url) else {
            return "Captured Link"
        }
        
        // Extract domain name as title
        if let host = urlObj.host {
            let domain = host.replacingOccurrences(of: "www.", with: "")
            return "Content from \(domain)"
        }
        
        return "Captured Link"
    }
    
    // MARK: - Chat
    func sendChatMessage(message: String, mode: String) async throws -> ChatResponse {
        let chatURL = URL(string: APIConfiguration.shared.chatURL)!
        var request = createRequest(url: chatURL, method: "POST")
        
        let chatRequest = ChatRequest(
            message: message,
            mode: mode
        )
        
        do {
            let jsonData = try JSONEncoder().encode(chatRequest)
            request.httpBody = jsonData
            
            print("💬 Sending chat message: \(message)")
            return try await performRequest(request, type: ChatResponse.self)
        } catch {
            print("❌ Chat failed: \(error)")
            throw error
        }
    }
    
    // MARK: - Authentication
    func register(email: String, password: String, name: String) async throws -> AuthResponse {
        let registerURL = URL(string: APIConfiguration.shared.authRegisterURL)!
        var request = createRequest(url: registerURL, method: "POST")
        
        let registerRequest = RegisterRequest(
            email: email,
            password: password,
            name: name
        )
        
        do {
            let jsonData = try JSONEncoder().encode(registerRequest)
            request.httpBody = jsonData
            
            print("🔐 Registering user: \(email)")
            return try await performRequest(request, type: AuthResponse.self)
        } catch {
            print("❌ Registration failed: \(error)")
            throw error
        }
    }
    
    func login(email: String, password: String) async throws -> AuthResponse {
        let loginURL = URL(string: APIConfiguration.shared.authLoginURL)!
        var request = createRequest(url: loginURL, method: "POST")
        
        let loginRequest = LoginRequest(
            email: email,
            password: password
        )
        
        do {
            let jsonData = try JSONEncoder().encode(loginRequest)
            request.httpBody = jsonData
            
            print("🔐 Logging in user: \(email)")
            let response = try await performRequest(request, type: AuthResponse.self)
            
            // Store authentication details
            APIConfiguration.shared.login(token: response.token, userId: response.user.id)
            
            return response
        } catch {
            print("❌ Login failed: \(error)")
            throw error
        }
    }
    
    func getProfile() async throws -> User {
        let profileURL = URL(string: APIConfiguration.shared.authProfileURL)!
        let request = createRequest(url: profileURL)
        
        print("👤 Getting user profile")
        return try await performRequest(request, type: User.self)
    }
}

// MARK: - Response Models
struct TimelineResponse: Codable {
    let items: [Item]
    let totalResults: Int
    
    enum CodingKeys: String, CodingKey {
        case items
        case totalResults
    }
    
    // Computed properties for pagination
    var totalCount: Int { totalResults }
    var page: Int { 1 }
    var totalPages: Int { 1 }
}

struct SearchResponse: Codable {
    let items: [Item]
    let totalResults: Int
    
    enum CodingKeys: String, CodingKey {
        case items
        case totalResults
    }
    
    // Computed property for compatibility
    var results: [Item] { items }
    var query: String { "" }
}

struct InsightsResponse: Codable {
    let insights: [Insight]
    let generatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case insights
        case generatedAt = "generated_at"
    }
}

struct Insight: Codable, Identifiable {
    let id = UUID()
    let type: String
    let title: String
    let content: String
    let metadata: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case type, title, content, metadata
    }
}

// MARK: - Request Models
struct CaptureRequest: Codable {
    let url: String
    let title: String?
    let tags: [String]?
}

struct CaptureResponse: Codable {
    let success: Bool
    let message: String
    let item: Item
}

struct ChatRequest: Codable {
    let message: String
    let mode: String
}

// MARK: - Additional Response Models
struct VideosResponse: Codable {
    let videos: [VideoItem]
    let total: Int
    let limit: Int
    let offset: Int
    let hasMore: Bool
    
    enum CodingKeys: String, CodingKey {
        case videos, total, limit, offset
        case hasMore = "has_more"
    }
}

struct VideoItem: Codable, Identifiable {
    let id: String
    let title: String
    let url: String
    let platform: String?
    let thumbnail: String?
    let duration: String?
    let summary: String?
    let hasTranscript: Bool
    let keyTopics: [String]
    let createdAt: String
    let category: String?
    
    enum CodingKeys: String, CodingKey {
        case id, title, url, platform, thumbnail, duration, summary, category
        case hasTranscript = "has_transcript"
        case keyTopics = "key_topics"
        case createdAt = "created_at"
    }
}

struct AnalyticsResponse: Codable {
    let totalItems: Int
    let todayItems: Int
    let weekItems: Int
    let topTags: [TagCount]
    let itemsByType: [TypeCount]
    
    enum CodingKeys: String, CodingKey {
        case totalItems = "total_items"
        case todayItems = "today_items"
        case weekItems = "week_items"
        case topTags = "top_tags"
        case itemsByType = "items_by_type"
    }
}

struct TagCount: Codable {
    let tag: String
    let count: Int
}

struct TypeCount: Codable {
    let type: String
    let count: Int
}

struct ChatResponse: Codable {
    let success: Bool
    let response: String
    let messageId: String
    let timestamp: Date?
    let context: String?
    
    enum CodingKeys: String, CodingKey {
        case success, response, timestamp, context
        case messageId = "messageId"
    }
}

// MARK: - Authentication Models
struct RegisterRequest: Codable {
    let email: String
    let password: String
    let name: String
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct AuthResponse: Codable {
    let success: Bool
    let token: String
    let user: User
}

struct User: Codable {
    let id: String
    let email: String
    let name: String
    let createdAt: Date?
    
    enum CodingKeys: String, CodingKey {
        case id, email, name
        case createdAt = "created_at"
    }
}