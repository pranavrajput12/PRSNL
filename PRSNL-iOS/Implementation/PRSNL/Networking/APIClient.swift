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
        decoder.dateDecodingStrategy = .iso8601
    }
    
    // MARK: - Helper Methods
    private func createRequest(url: URL, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        APIConfiguration.shared.headers.forEach { request.setValue($0.value, forHTTPHeaderField: $0.key) }
        return request
    }
    
    private func performRequest<T: Decodable>(_ request: URLRequest, type: T.Type) async throws -> T {
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            do {
                return try decoder.decode(type, from: data)
            } catch {
                throw APIError.decodingFailed(error)
            }
        case 401:
            throw APIError.unauthorized
        default:
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw APIError.serverError(httpResponse.statusCode, errorMessage)
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
        var components = URLComponents(string: APIConfiguration.shared.searchURL)!
        components.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        
        guard let url = components.url else {
            throw APIError.invalidURL
        }
        
        let request = createRequest(url: url)
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
        let url = URL(string: "\(APIConfiguration.shared.videosURL)?limit=\(limit)&offset=\(offset)")!
        let request = createRequest(url: url)
        return try await performRequest(request, type: VideosResponse.self)
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
        
        let body = CaptureRequest(url: url, title: title, tags: tags)
        request.httpBody = try JSONEncoder().encode(body)
        
        return try await performRequest(request, type: Item.self)
    }
}

// MARK: - Response Models
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

struct SearchResponse: Codable {
    let results: [Item]
    let total: Int
    let query: String
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