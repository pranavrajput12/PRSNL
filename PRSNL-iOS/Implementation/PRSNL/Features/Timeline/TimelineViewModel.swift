import Foundation
import Combine
import SwiftUI

@MainActor
class TimelineViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentPage = 1
    @Published var hasMorePages = true
    
    private let apiClient = APIClient.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        Task {
            await loadTimeline()
        }
    }
    
    func loadTimeline() async {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await apiClient.fetchTimeline(page: 1)
            self.items = response.items
            self.currentPage = 1
            self.hasMorePages = response.page < response.totalPages
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