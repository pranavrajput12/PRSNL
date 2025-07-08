import Foundation
import Combine

/// Service for managing live tag suggestions via WebSocket
@MainActor
class LiveTagService: ObservableObject {
    // MARK: - Published Properties
    @Published private(set) var suggestedTags: [String] = []
    @Published private(set) var isLoadingSuggestions = false
    @Published private(set) var recentTags: [String] = []
    
    // MARK: - Private Properties
    private let webSocketManager: WebSocketManager
    private var cancellables = Set<AnyCancellable>()
    private var suggestionDebouncer: Timer?
    private let debounceInterval: TimeInterval = 0.5
    
    // Cache for recent suggestions
    private var suggestionCache: [String: [String]] = [:]
    private let maxCacheSize = 50
    
    // MARK: - Initialization
    init(webSocketManager: WebSocketManager) {
        self.webSocketManager = webSocketManager
        setupWebSocketHandlers()
        loadRecentTags()
    }
    
    // MARK: - Public Methods
    
    /// Request tag suggestions for the given content
    func requestSuggestions(for content: String) {
        // Cancel any pending request
        suggestionDebouncer?.invalidate()
        
        // Don't request for very short content
        guard content.count > 3 else {
            suggestedTags = []
            return
        }
        
        // Check cache first
        if let cachedSuggestions = suggestionCache[content.lowercased()] {
            suggestedTags = cachedSuggestions
            return
        }
        
        isLoadingSuggestions = true
        
        // Debounce the request
        suggestionDebouncer = Timer.scheduledTimer(withTimeInterval: debounceInterval, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.sendSuggestionRequest(content: content)
            }
        }
    }
    
    /// Clear current suggestions
    func clearSuggestions() {
        suggestedTags = []
        isLoadingSuggestions = false
        suggestionDebouncer?.invalidate()
    }
    
    /// Add a tag to recent tags
    func addToRecentTags(_ tag: String) {
        // Remove if already exists to move to front
        recentTags.removeAll { $0 == tag }
        recentTags.insert(tag, at: 0)
        
        // Keep only last 20 tags
        if recentTags.count > 20 {
            recentTags = Array(recentTags.prefix(20))
        }
        
        // Save to UserDefaults
        UserDefaults.standard.set(recentTags, forKey: "recent_tags")
    }
    
    /// Get all available tags (combination of suggested and recent)
    func getAllAvailableTags() -> [String] {
        // Combine suggested and recent, remove duplicates
        let combined = suggestedTags + recentTags
        return Array(Set(combined)).sorted()
    }
    
    // MARK: - Private Methods
    
    private func setupWebSocketHandlers() {
        // Register handler for tag suggestions
        webSocketManager.registerHandler(for: "tag_suggestions") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleTagSuggestions(message)
            }
        }
        
        // Register handler for tag updates (when new tags are added by other users)
        webSocketManager.registerHandler(for: "tag_update") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleTagUpdate(message)
            }
        }
        
        // Monitor connection state
        webSocketManager.$connectionState
            .sink { [weak self] state in
                if state == .disconnected {
                    self?.isLoadingSuggestions = false
                }
            }
            .store(in: &cancellables)
    }
    
    private func sendSuggestionRequest(content: String) async {
        guard webSocketManager.connectionState == .connected else {
            isLoadingSuggestions = false
            return
        }
        
        await webSocketManager.send(
            type: "request_tag_suggestions",
            data: [
                "content": content,
                "limit": 10
            ]
        )
    }
    
    private func handleTagSuggestions(_ message: WebSocketManager.WebSocketMessage) {
        isLoadingSuggestions = false
        
        guard let data = message.data,
              let tags = data["tags"] as? [String] else { return }
        
        suggestedTags = tags
        
        // Cache the suggestions
        if let content = data["content"] as? String {
            updateCache(content: content, tags: tags)
        }
    }
    
    private func handleTagUpdate(_ message: WebSocketManager.WebSocketMessage) {
        guard let data = message.data,
              let newTag = data["tag"] as? String else { return }
        
        // Add to recent tags if not already present
        if !recentTags.contains(newTag) {
            addToRecentTags(newTag)
        }
        
        // Clear cache as new tags might affect suggestions
        suggestionCache.removeAll()
    }
    
    private func updateCache(content: String, tags: [String]) {
        // Limit cache size
        if suggestionCache.count >= maxCacheSize {
            // Remove oldest entries (simple FIFO for now)
            let keysToRemove = Array(suggestionCache.keys.prefix(10))
            keysToRemove.forEach { suggestionCache.removeValue(forKey: $0) }
        }
        
        suggestionCache[content.lowercased()] = tags
    }
    
    private func loadRecentTags() {
        if let saved = UserDefaults.standard.stringArray(forKey: "recent_tags") {
            recentTags = saved
        }
    }
}

// MARK: - Tag Suggestion Model
struct TagSuggestion: Identifiable, Codable {
    var id = UUID()
    let tag: String
    let score: Double
    let source: TagSource
    
    enum CodingKeys: String, CodingKey {
        case tag, score, source
    }
}
    
    enum TagSource: String, Codable {
        case ai = "ai"
        case popular = "popular"
        case recent = "recent"
        case related = "related"
    }


// MARK: - Extensions for Capture Integration
extension LiveTagService {
    /// Get smart tag suggestions based on multiple factors
    func getSmartSuggestions(for content: String, existingTags: [String] = []) -> [TagSuggestion] {
        var suggestions: [TagSuggestion] = []
        
        // 1. AI-suggested tags (highest priority)
        let aiTags = suggestedTags.filter { !existingTags.contains($0) }
        suggestions.append(contentsOf: aiTags.enumerated().map { index, tag in
            TagSuggestion(
                tag: tag,
                score: 1.0 - (Double(index) * 0.1), // Decrease score by position
                source: .ai
            )
        })
        
        // 2. Recent tags that match content
        let contentWords = content.lowercased().split(separator: " ").map(String.init)
        let matchingRecent = recentTags.filter { tag in
            !existingTags.contains(tag) &&
            contentWords.contains { word in
                tag.lowercased().contains(word) || word.contains(tag.lowercased())
            }
        }
        
        suggestions.append(contentsOf: matchingRecent.prefix(5).enumerated().map { index, tag in
            TagSuggestion(
                tag: tag,
                score: 0.7 - (Double(index) * 0.1),
                source: .recent
            )
        })
        
        // 3. Popular recent tags (not matching content directly)
        let popularRecent = recentTags.filter { tag in
            !existingTags.contains(tag) &&
            !matchingRecent.contains(tag)
        }
        
        suggestions.append(contentsOf: popularRecent.prefix(3).enumerated().map { index, tag in
            TagSuggestion(
                tag: tag,
                score: 0.4 - (Double(index) * 0.1),
                source: .popular
            )
        })
        
        // Sort by score and limit
        return Array(suggestions.sorted { $0.score > $1.score }.prefix(15))
    }
}
