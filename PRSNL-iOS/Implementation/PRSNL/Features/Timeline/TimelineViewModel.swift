import Foundation
import Combine
import CoreData

/// View model for the Timeline feature
class TimelineViewModel: ObservableObject {
    // Published properties for UI binding
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedTags: [String] = []
    @Published var availableTags: [String] = []
    @Published var isOfflineMode = false
    @Published var syncStatus: SyncOperationStatus = .idle
    
    // Pagination state
    private var currentPage = 1
    private var totalPages = 1
    private var hasMorePages = true
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        subscribeToSyncStatus()
        updateNetworkStatus()
        Task {
            await loadAvailableTags()
        }
    }
    
    /// Subscribes to sync status updates from SyncManager
    private func subscribeToSyncStatus() {
        SyncManager.shared.syncStatusPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] status in
                self?.syncStatus = status
                
                // Refresh data when sync completes
                if case .completed = status {
                    Task {
                        await self?.loadInitialTimeline()
                    }
                }
            }
            .store(in: &cancellables)
    }
    
    /// Updates the network status indicator
    private func updateNetworkStatus() {
        isOfflineMode = !SyncManager.shared.isOnline
    }
    
    /// Loads initial timeline data
    func loadInitialTimeline() async {
        // Reset pagination
        currentPage = 1
        hasMorePages = true
        
        // Check network status
        await MainActor.run {
            updateNetworkStatus()
        }
        
        if SyncManager.shared.isOnline {
            await loadFromNetwork(isInitialLoad: true)
        } else {
            await loadFromLocalStorage()
        }
    }
    
    /// Loads the next page of timeline data
    func loadMoreItems() async {
        guard !isLoading && hasMorePages else { return }
        
        if SyncManager.shared.isOnline {
            await loadFromNetwork(isInitialLoad: false)
        } else {
            // When offline, we've already loaded all items from storage
            await MainActor.run {
                hasMorePages = false
            }
        }
    }
    
    /// Core timeline loading function for network data
    private func loadFromNetwork(isInitialLoad: Bool) async {
        // Skip if already loading
        guard !isLoading else { return }
        
        // Update loading state on main thread
        await MainActor.run {
            isLoading = true
            if isInitialLoad {
                error = nil
            }
            isOfflineMode = false
        }
        
        do {
            // Fetch timeline data from API
            let response = try await APIClient.shared.fetchTimeline(
                page: currentPage,
                limit: 20,
                tags: selectedTags.isEmpty ? nil : selectedTags
            )
            
            // Save items to Core Data for offline access
            for item in response.items {
                try CoreDataManager.shared.saveItem(item)
            }
            
            // Update state on main thread
            await MainActor.run {
                // For initial load, replace items; otherwise append
                if isInitialLoad {
                    self.items = response.items
                } else {
                    self.items.append(contentsOf: response.items)
                }
                
                // Update pagination state based on response
                self.totalPages = response.totalPages
                self.hasMorePages = currentPage < response.totalPages
                if self.hasMorePages {
                    self.currentPage += 1
                }
                
                // Update available tags from the fetched items
                self.updateAvailableTags()
                
                self.isLoading = false
                self.error = nil
            }
        } catch let apiError as APIError {
            // Handle API errors
            await MainActor.run {
                self.error = apiError.localizedDescription
                self.isLoading = false
                
                // If network error, try loading from local storage
                if case .networkUnavailable = apiError {
                    self.isOfflineMode = true
                    Task {
                        await self.loadFromLocalStorage()
                    }
                }
            }
        } catch {
            // Handle unexpected errors
            await MainActor.run {
                self.error = "An unexpected error occurred: \(error.localizedDescription)"
                self.isLoading = false
            }
        }
    }
    
    /// Loads timeline data from local Core Data storage
    private func loadFromLocalStorage() async {
        await MainActor.run {
            isLoading = true
            error = nil
        }
        
        do {
            // Fetch items from Core Data
            let predicate: NSPredicate?
            if !selectedTags.isEmpty {
                // Create predicate for tag filtering
                let tagPredicates = selectedTags.map { tag in
                    NSPredicate(format: "ANY tags.name == %@", tag)
                }
                predicate = NSCompoundPredicate(andPredicateWithSubpredicates: tagPredicates)
            } else {
                predicate = nil
            }
            
            let localItems = try CoreDataManager.shared.fetchItems(predicate: predicate)
            
            await MainActor.run {
                items = localItems
                isLoading = false
                isOfflineMode = !SyncManager.shared.isOnline
                
                // Update available tags from local items
                updateAvailableTags()
                
                // No pagination in offline mode - we've loaded everything
                hasMorePages = false
            }
        } catch {
            await MainActor.run {
                self.error = "Failed to load local data: \(error.localizedDescription)"
                isLoading = false
            }
        }
    }
    
    /// Adds or removes a tag from the filter
    func toggleTag(_ tag: String) {
        if selectedTags.contains(tag) {
            selectedTags.removeAll { $0 == tag }
        } else {
            selectedTags.append(tag)
        }
        
        // Reload timeline with new tag filter
        Task {
            await loadInitialTimeline()
        }
    }
    
    /// Updates the available tags list from the current items
    private func updateAvailableTags() {
        // First try to get tags from current items
        var tagSet = Set<String>()
        
        // Collect all unique tags from items
        for item in items {
            for tag in item.tags {
                tagSet.insert(tag)
            }
        }
        
        // If we found tags in the items, use those
        if !tagSet.isEmpty {
            availableTags = Array(tagSet).sorted()
            return
        }
        
        // Otherwise try to get from Core Data
        do {
            let tags = try CoreDataManager.shared.fetchAllTags()
            if !tags.isEmpty {
                availableTags = tags
                return
            }
        } catch {
            print("Error fetching tags from Core Data: \(error)")
        }
        
        // Fall back to default tags if nothing else worked
        availableTags = ["technology", "research", "ai", "health", "science", "news", "finance"]
    }
    
    /// Loads available tags
    private func loadAvailableTags() async {
        // First try to get from API if online
        if SyncManager.shared.isOnline {
            do {
                let tags = try await APIClient.shared.fetchRecentTags()
                await MainActor.run {
                    self.availableTags = tags
                }
                return
            } catch {
                // Fall through to Core Data
            }
        }
        
        // Try Core Data
        do {
            let tags = try CoreDataManager.shared.fetchAllTags()
            await MainActor.run {
                self.availableTags = tags.isEmpty ? ["technology", "research", "ai", "health", "science", "news", "finance"] : tags
            }
        } catch {
            await MainActor.run {
                self.availableTags = ["technology", "research", "ai", "health", "science", "news", "finance"]
            }
        }
    }
    
    /// Refreshes the timeline
    func refresh() async {
        // Reset pagination
        currentPage = 1
        hasMorePages = true
        
        // Clear existing items
        await MainActor.run {
            items = []
            updateNetworkStatus()
        }
        
        // Try to sync data if online
        if SyncManager.shared.isOnline {
            await SyncManager.shared.sync()
            await loadFromNetwork(isInitialLoad: true)
        } else {
            await loadFromLocalStorage()
        }
    }
    
    /// Retrieves the full URL for an attachment
    func getAttachmentURL(for attachment: Attachment) -> URL? {
        // Get base URL from API client through KeychainService
        let baseURL = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
        
        if let metadata = attachment.metadata, metadata.isRemote == true,
           let url = URL(string: attachment.filePath) {
            return url
        } else {
            // For local files, prepend the base URL to the relative path
            let path = attachment.filePath.hasPrefix("/") ? attachment.filePath : "/\(attachment.filePath)"
            let urlString = baseURL + path
            return URL(string: urlString)
        }
    }
    
    /// Handle real-time updates
    func handleRealtimeUpdate(_ update: RealtimeUpdateService.ItemUpdate) async {
        await MainActor.run {
            switch update.type {
            case .created:
                // Don't add to timeline immediately, wait for user refresh
                break
            case .updated:
                // Update existing item if visible
                if let index = items.firstIndex(where: { $0.id == update.id }) {
                    // Refresh just this item from Core Data
                    do {
                        if let updatedItem = try CoreDataManager.shared.fetchItem(byId: update.id) {
                            items[index] = updatedItem
                        }
                    } catch {
                        print("Error fetching updated item: \(error)")
                    }
                }
            case .deleted:
                // Remove from timeline if present
                items.removeAll { $0.id == update.id }
            case .tagsChanged:
                // Update tags if item is visible
                if let index = items.firstIndex(where: { $0.id == update.id }) {
                    // We've received new tags for this item, fetch the updated item
                    let item = items[index]
                    do {
                        if let updatedItem = try CoreDataManager.shared.fetchItem(byId: item.id) {
                            items[index] = updatedItem
                        }
                    } catch {
                        print("Error fetching item with updated tags: \(error)")
                    }
                }
            }
        }
    }
}