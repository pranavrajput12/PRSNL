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
    
    // MARK: - Timeline
    func fetchTimeline(page: Int = 1, limit: Int = 20) async throws -> TimelineResponse {
        let url = URL(string: "\(APIConfiguration.shared.timelineURL)?page=\(page)&limit=\(limit)")!
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode, "Failed to fetch timeline")
        }
        
        do {
            return try decoder.decode(TimelineResponse.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
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
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode, "Search failed")
        }
        
        return try decoder.decode(SearchResponse.self, from: data)
    }
    
    // MARK: - Item Details
    func fetchItem(id: String) async throws -> Item {
        let url = URL(string: "\(APIConfiguration.shared.itemsURL)/\(id)")!
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode, "Failed to fetch item")
        }
        
        return try decoder.decode(Item.self, from: data)
    }
    
    // MARK: - Insights
    func fetchInsights() async throws -> InsightsResponse {
        let url = URL(string: APIConfiguration.shared.insightsURL)!
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode, "Failed to fetch insights")
        }
        
        return try decoder.decode(InsightsResponse.self, from: data)
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