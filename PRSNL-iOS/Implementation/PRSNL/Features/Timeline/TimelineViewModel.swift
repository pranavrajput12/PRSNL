import Foundation
import Combine
import SwiftUI

@MainActor
class TimelineViewModel: ObservableObject {
    @Published var items: [Item] = MockDataProvider.generateMockItems()
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