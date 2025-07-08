import Foundation
import Combine
import SwiftUI

@MainActor
class TimelineViewModel: ObservableObject {
    @Published var items: [Item] = [
        Item(
            id: "1",
            title: "Getting Started with PRSNL",
            content: "PRSNL is your personal knowledge management system. It helps you capture, organize, and retrieve information effortlessly.",
            url: "https://prsnl.ai",
            summary: "Introduction to PRSNL knowledge management",
            status: .active,
            createdAt: Date().addingTimeInterval(-86400),
            updatedAt: Date().addingTimeInterval(-86400),
            accessCount: 5,
            accessedAt: Date(),
            tags: ["tutorial", "getting-started"],
            itemType: .article,
            attachments: nil,
            keyPoints: ["Personal knowledge base", "AI-powered insights", "Cross-platform"],
            category: "Tutorial"
        ),
        Item(
            id: "2",
            title: "SwiftUI Best Practices",
            content: "SwiftUI is Apple's modern UI framework. Here are some best practices for building great apps.",
            url: nil,
            summary: "Essential SwiftUI development tips",
            status: .active,
            createdAt: Date().addingTimeInterval(-172800),
            updatedAt: Date().addingTimeInterval(-172800),
            accessCount: 10,
            accessedAt: Date(),
            tags: ["swiftui", "ios", "development"],
            itemType: .note,
            attachments: nil,
            keyPoints: ["Declarative syntax", "State management", "Performance"],
            category: "Development"
        ),
        Item(
            id: "3",
            title: "AI and Knowledge Management",
            content: "How artificial intelligence is transforming the way we manage and retrieve knowledge.",
            url: "https://example.com/ai-knowledge",
            summary: "The intersection of AI and personal knowledge",
            status: .active,
            createdAt: Date().addingTimeInterval(-259200),
            updatedAt: Date().addingTimeInterval(-259200),
            accessCount: 3,
            accessedAt: Date(),
            tags: ["ai", "knowledge-management", "future"],
            itemType: .article,
            attachments: nil,
            keyPoints: ["AI-powered search", "Automatic categorization", "Smart insights"],
            category: "Technology"
        )
    ]
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentPage = 1
    @Published var hasMorePages = true
    @Published var needsConfiguration = false
    
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        // Don't auto-load on init to prevent crashes
        // User can pull to refresh when ready
    }
    
    func loadTimeline() async {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        needsConfiguration = false
        
        do {
            let response = try await apiClient.fetchTimeline(page: 1)
            self.items = response.items
            self.currentPage = 1
            self.hasMorePages = response.page < response.totalPages
        } catch let error as APIError {
            switch error {
            case .unauthorized:
                self.errorMessage = "Please configure your API key in Settings"
                self.needsConfiguration = true
            case .networkUnavailable:
                self.errorMessage = "No internet connection"
            case .serverError(let code, let message):
                self.errorMessage = "Server error (\(code)): \(message)"
            default:
                self.errorMessage = "Failed to load timeline: \(error.localizedDescription)"
            }
            print("Timeline error: \(error)")
        } catch {
            self.errorMessage = "Failed to load timeline: \(error.localizedDescription)"
            print("Timeline error: \(error)")
        }
        
        isLoading = false
    }
    
    func loadMore() async {
        guard !isLoading && hasMorePages else { return }
        
        isLoading = true
        
        do {
            let response = try await apiClient.fetchTimeline(page: currentPage + 1)
            self.items.append(contentsOf: response.items)
            self.currentPage = response.page
            self.hasMorePages = response.page < response.totalPages
        } catch {
            self.errorMessage = "Failed to load more items: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func refresh() async {
        await loadTimeline()
    }
}