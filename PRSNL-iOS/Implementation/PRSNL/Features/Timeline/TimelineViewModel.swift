import Foundation
import Combine
import SwiftUI

// MARK: - Daily Inspiration Models
struct DailyInspiration {
    let date: String
    let pun: NamePun
    let quote: InspirationalQuote
    let isViewed: Bool
    let personalizedGreeting: String
}

struct NamePun {
    let id: Int
    let text: String
    let type: String
}

struct InspirationalQuote {
    let id: Int
    let text: String
    let author: String
    let category: String
    let mood: String
    let tags: [String]
}

@MainActor
class TimelineViewModel: ObservableObject {
    @Published var items: [Item] = MockDataProvider.generateMockItems()
    @Published var dailyInspiration: DailyInspiration? = nil
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
        loadMockDailyInspiration()
    }
    
    private func loadMockDailyInspiration() {
        // Mock data for Daily Inspiration
        let mockPuns = [
            "Pran-tastic!",
            "Pran-amazing!",
            "Pran-derful!",
            "Pran-sational!",
            "Pran-believable!",
            "Pran-spiring!",
            "Pran-outstanding!"
        ]
        
        let mockQuotes = [
            InspirationalQuote(
                id: 1,
                text: "Love what you do.",
                author: "Steve Jobs",
                category: "productivity",
                mood: "motivational",
                tags: ["work", "passion", "success"]
            ),
            InspirationalQuote(
                id: 2,
                text: "Innovation distinguishes leaders.",
                author: "Steve Jobs",
                category: "innovation",
                mood: "energetic",
                tags: ["leadership", "creativity", "tech"]
            ),
            InspirationalQuote(
                id: 3,
                text: "No limits. Only imagination.",
                author: "Unknown",
                category: "motivation",
                mood: "motivational",
                tags: ["mindset", "growth", "potential"]
            ),
            InspirationalQuote(
                id: 4,
                text: "Knowledge is power.",
                author: "Kofi Annan",
                category: "learning",
                mood: "reflective",
                tags: ["knowledge", "learning", "power"]
            ),
            InspirationalQuote(
                id: 5,
                text: "Learn. Combine. Create.",
                author: "Robert Greene",
                category: "learning",
                mood: "inspirational",
                tags: ["future", "skills", "creativity"]
            )
        ]
        
        // Select random pun and quote for today
        let randomPun = mockPuns.randomElement() ?? mockPuns[0]
        let randomQuote = mockQuotes.randomElement() ?? mockQuotes[0]
        
        self.dailyInspiration = DailyInspiration(
            date: getCurrentDateString(),
            pun: NamePun(id: 1, text: randomPun, type: "greeting"),
            quote: randomQuote,
            isViewed: false,
            personalizedGreeting: getCurrentGreeting()
        )
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
    
    private func getCurrentDateString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "YYYY-MM-dd"
        return formatter.string(from: Date())
    }
    
    private func getCurrentGreeting() -> String {
        let hour = Calendar.current.component(.hour, from: Date())
        let name = "Pranav"
        
        switch hour {
        case 5..<12:
            return "Good morning, \(name)!"
        case 12..<17:
            return "Good afternoon, \(name)!"
        case 17..<21:
            return "Good evening, \(name)!"
        default:
            return "Hello, \(name)!"
        }
    }
}