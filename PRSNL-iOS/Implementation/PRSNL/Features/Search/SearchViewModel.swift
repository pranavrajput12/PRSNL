import Foundation
import Combine
import CoreData

enum SearchState {
    case idle
    case loading
    case results(APIClient.SearchResponse)
    case error(Error)
}

// Removed duplicate SyncStatus enum - using the one from SyncManager

class SearchViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var state: SearchState = .idle
    @Published var isSearching: Bool = false
    @Published var isOfflineMode: Bool = false
    @Published var syncStatus: SyncOperationStatus = .idle
    
    private var currentPage: Int = 1
    private var canLoadMorePages = true
    private var cancellables = Set<AnyCancellable>()
    private var connectivityCancellable: AnyCancellable?
    
    // Debounced search publisher
    private var queryPublisher: AnyPublisher<String, Never> {
        $query
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .removeDuplicates()
            .eraseToAnyPublisher()
    }
    
    init() {
        setupSearchPublisher()
        monitorConnectivity()
    }
    
    private func monitorConnectivity() {
        connectivityCancellable = NetworkMonitor.shared.$isConnected
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isConnected in
                self?.isOfflineMode = !isConnected
                
                // Attempt to sync when connection is restored
                if isConnected, let status = self?.syncStatus {
                    if case .syncing = status {
                        // Already syncing, don't start another sync
                    } else {
                        Task {
                            await self?.syncSearchData()
                        }
                    }
                }
            }
    }
    
    func syncSearchData() async {
        guard !isOfflineMode else { return }
        
        syncStatus = .syncing
        
        // Remove try/catch completely since sync() doesn't throw
        await SyncManager.shared.sync()
        await MainActor.run {
            syncStatus = .completed
            
            // If we were viewing results, refresh them with the latest data
            if case .results = state, !query.isEmpty {
                resetSearch()
                performSearch(query: query)
            }
        }
    }
    
    private func setupSearchPublisher() {
        queryPublisher
            .filter { !$0.isEmpty }
            .sink { [weak self] query in
                self?.resetSearch()
                self?.performSearch(query: query)
            }
            .store(in: &cancellables)
        
        // Reset when query is cleared
        $query
            .filter { $0.isEmpty }
            .sink { [weak self] _ in
                self?.state = .idle
                self?.isSearching = false
                self?.currentPage = 1
                self?.canLoadMorePages = true
            }
            .store(in: &cancellables)
    }
    
    func resetSearch() {
        currentPage = 1
        canLoadMorePages = true
        isSearching = true
    }
    
    func performSearch(query: String) {
        guard canLoadMorePages else { return }
        
        state = currentPage == 1 ? .loading : state
        isSearching = true
        
        Task {
            do {
                let response: APIClient.SearchResponse
                
                if isOfflineMode {
                    // Perform local search using Core Data
                    let items = try await performLocalSearch(query: query, page: currentPage, limit: 20)
                    // Create a predicate for the search query
                    let titlePredicate = NSPredicate(format: "title CONTAINS[cd] %@", query)
                    let contentPredicate = NSPredicate(format: "content CONTAINS[cd] %@", query)
                    let tagPredicate = NSPredicate(format: "ANY tags.name CONTAINS[cd] %@", query)
                    let combinedPredicate = NSCompoundPredicate(orPredicateWithSubpredicates: [
                        titlePredicate,
                        contentPredicate,
                        tagPredicate
                    ])
                    
                    let totalCount = try CoreDataManager.shared.countItems(matching: combinedPredicate)
                    
                    response = APIClient.SearchResponse(
                        items: items,
                        totalResults: totalCount
                    )
                } else {
                    // Perform online search
                    response = try await APIClient.shared.searchItems(
                        query: query,
                        page: currentPage,
                        limit: 20
                    )
                }
                
                await MainActor.run {
                    if case .results(let existingResponse) = self.state, self.currentPage > 1 {
                        // Append new results to existing ones for pagination
                        var updatedItems = existingResponse.items
                        updatedItems.append(contentsOf: response.items)
                        
                        let combinedResponse = APIClient.SearchResponse(
                            items: updatedItems,
                            totalResults: response.totalResults
                        )
                        
                        self.state = .results(combinedResponse)
                    } else {
                        self.state = .results(response)
                    }
                    
                    self.isSearching = false
                    self.canLoadMorePages = !response.items.isEmpty
                    if !response.items.isEmpty {
                        self.currentPage += 1
                    }
                }
            } catch {
                await MainActor.run {
                    self.state = .error(error)
                    self.isSearching = false
                }
            }
        }
        
    }
    
    /// Attempts to refresh data by reloading from the API if online
    func refresh() async {
        if !isOfflineMode {
            await syncSearchData()
        }
        
        if !query.isEmpty {
            resetSearch()
            performSearch(query: query)
        }
    }
    
    private func performLocalSearch(query: String, page: Int, limit: Int) async throws -> [Item] {
        let offset = (page - 1) * limit
        let items = try CoreDataManager.shared.searchItems(query: query, in: CoreDataManager.shared.viewContext, limit: limit, offset: offset)
        return items
    }
    
    func loadMoreResultsIfNeeded(currentItem item: Item) {
        guard case .results(let response) = state else { return }
        
        let thresholdIndex = response.items.index(response.items.endIndex, offsetBy: -5)
        if response.items.firstIndex(where: { $0.id == item.id }) == thresholdIndex {
            performSearch(query: query)
        }
    }
    
    func hasResults() -> Bool {
        if case .results(let response) = state {
            return !response.items.isEmpty
        }
        return false
    }
    
    var resultsCountText: String {
        if case .results(let response) = state {
            return "\(response.totalResults) result\(response.totalResults == 1 ? "" : "s")"
        }
        return ""
    }
}