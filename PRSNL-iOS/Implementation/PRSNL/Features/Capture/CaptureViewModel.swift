import Foundation
import Combine
import CoreData

@MainActor
class CaptureViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var urlText = ""
    @Published var titleText = ""
    @Published var contentText = ""
    @Published var tagInput = ""
    @Published var tags: [String] = []
    @Published var recentTags: [String] = []
    
    @Published var isLoading = false
    @Published var error: Error?
    @Published var captureSuccess = false
    @Published var successMessage = ""
    
    // MARK: - Validation
    var isValid: Bool {
        // Either URL or content must be provided
        let hasURL = !urlText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let hasContent = !contentText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        return hasURL || hasContent
    }
    
    var validationMessage: String {
        if urlText.isEmpty && contentText.isEmpty {
            return "Enter a URL or write some content to capture"
        }
        return ""
    }
    
    // MARK: - Private Properties
    private let apiClient = APIClient.shared
    private let coreDataManager = CoreDataManager.shared
    private let networkMonitor = NetworkMonitor.shared
    private let syncManager = SyncManager.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    init() {
        loadRecentTags()
    }
    
    // MARK: - Public Methods
    
    /// Loads recently used tags from the API or Core Data
    func loadRecentTags() {
        Task {
            if networkMonitor.isConnected {
                do {
                    let tags = try await apiClient.fetchRecentTags()
                    self.recentTags = tags
                } catch {
                    // Fall back to offline tags
                    loadRecentTagsOffline()
                }
            } else {
                // Load from Core Data when offline
                loadRecentTagsOffline()
            }
        }
    }
    
    /// Adds a tag from the input field
    func addTag() {
        let trimmedTag = tagInput.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        
        guard !trimmedTag.isEmpty else { return }
        guard !tags.contains(trimmedTag) else {
            tagInput = ""
            return
        }
        
        tags.append(trimmedTag)
        tagInput = ""
    }
    
    /// Removes a tag at the specified index
    func removeTag(at index: Int) {
        guard index < tags.count else { return }
        tags.remove(at: index)
    }
    
    /// Adds a tag from the recent tags list
    func addRecentTag(_ tag: String) {
        guard !tags.contains(tag) else { return }
        tags.append(tag)
    }
    
    /// Captures the content
    func capture() async {
        guard isValid else { return }
        
        isLoading = true
        error = nil
        captureSuccess = false
        
        do {
            // Clean up inputs
            let url = urlText.trimmingCharacters(in: .whitespacesAndNewlines)
            let title = titleText.trimmingCharacters(in: .whitespacesAndNewlines)
            let content = contentText.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if networkMonitor.isConnected {
                // Online: Call API directly
                let response = try await apiClient.captureContent(
                    url: url.isEmpty ? nil : url,
                    content: content.isEmpty ? nil : content,
                    title: title.isEmpty ? nil : title,
                    tags: tags
                )
                
                // Handle success
                captureSuccess = true
                successMessage = response.message
                
                // Create a local copy in Core Data for offline access
                // Note: We only have the ID from the response, not the full item
                // The SyncManager will pull the full item data on next sync
            } else {
                // Offline: Save to Core Data with needsUpload status
                try await captureOffline(
                    url: url.isEmpty ? nil : url,
                    title: title.isEmpty ? nil : title,
                    content: content.isEmpty ? nil : content,
                    tags: tags
                )
                
                captureSuccess = true
                successMessage = "Saved offline. Will sync when connection is restored."
            }
            
            // Clear form after successful capture
            clearForm()
            
            // Reload recent tags to include any new ones
            loadRecentTags()
            
        } catch {
            self.error = error
        }
        
        isLoading = false
    }
    
    /// Clears the form
    func clearForm() {
        urlText = ""
        titleText = ""
        contentText = ""
        tagInput = ""
        tags = []
    }
    
    /// Validates URL format
    func validateURL() -> Bool {
        guard !urlText.isEmpty else { return true }
        
        let urlString = urlText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: urlString) else { return false }
        
        return url.scheme == "http" || url.scheme == "https"
    }
    
    // MARK: - Offline Support
    
    /// Captures content offline by saving to Core Data
    private func captureOffline(url: String?, title: String?, content: String?, tags: [String]) async throws {
        // Generate a local ID that will be replaced when synced
        let localId = "local-\(UUID().uuidString)"
        
        // Determine item type based on content
        let itemType: ItemType = url != nil ? .article : .note
        
        // Create the item in Core Data with needsUpload status
        let context = coreDataManager.viewContext
        
        let cdItem = CDItem(context: context)
        cdItem.id = localId
        cdItem.title = title ?? (url != nil ? "Captured Link" : "Quick Note")
        cdItem.content = content ?? url ?? ""
        cdItem.url = url
        cdItem.status = ItemStatus.active.rawValue
        cdItem.itemType = itemType.rawValue
        cdItem.createdAt = Date()
        cdItem.updatedAt = Date()
        cdItem.accessedAt = Date()
        cdItem.accessCount = 0
        cdItem.syncStatus = Int16(SyncStatus.needsUpload.rawValue)
        
        // Create tags
        for tagName in tags {
            let cdTag = CDTag(context: context)
            cdTag.name = tagName
            cdTag.addToItems(cdItem)
        }
        
        // Save to Core Data
        try coreDataManager.saveViewContext()
        
        // Trigger sync in background when connection is available
        Task {
            syncManager.triggerSync()
        }
    }
    
    /// Loads recent tags from Core Data when offline
    private func loadRecentTagsOffline() {
        do {
            let allTags = try coreDataManager.fetchAllTags()
            // Take the most recent 10 tags
            recentTags = Array(allTags.prefix(10))
        } catch {
            print("Failed to load tags from Core Data: \(error)")
        }
    }
}