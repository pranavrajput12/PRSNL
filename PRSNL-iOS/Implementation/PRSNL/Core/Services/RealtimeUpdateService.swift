import Foundation
import Combine
import UIKit

/// Service that handles real-time updates from WebSocket
@MainActor
class RealtimeUpdateService: ObservableObject {
    // MARK: - Published Properties
    @Published private(set) var hasUpdates = false
    @Published private(set) var lastUpdateTime: Date?
    @Published private(set) var pendingUpdates: [ItemUpdate] = []
    
    // MARK: - Types
    struct ItemUpdate {
        let id: String
        let type: UpdateType
        let timestamp: Date
        let data: [String: Any]?
        
        enum UpdateType: String {
            case created = "item_created"
            case updated = "item_updated"
            case deleted = "item_deleted"
            case tagsChanged = "tags_changed"
        }
    }
    
    // MARK: - Private Properties
    private let webSocketManager: WebSocketManager
    private let coreDataManager = CoreDataManager.shared
    private var cancellables = Set<AnyCancellable>()
    
    // Update notification publisher
    let updateNotification = PassthroughSubject<ItemUpdate, Never>()
    
    // MARK: - Initialization
    init(webSocketManager: WebSocketManager) {
        self.webSocketManager = webSocketManager
        setupWebSocketHandlers()
    }
    
    // MARK: - Public Methods
    
    /// Process pending updates
    func processPendingUpdates() async {
        guard !pendingUpdates.isEmpty else { return }
        
        let updates = pendingUpdates
        pendingUpdates.removeAll()
        hasUpdates = false
        
        for update in updates {
            await processUpdate(update)
        }
    }
    
    /// Clear all pending updates
    func clearPendingUpdates() {
        pendingUpdates.removeAll()
        hasUpdates = false
    }
    
    // MARK: - Private Methods
    
    private func setupWebSocketHandlers() {
        // Item updates
        webSocketManager.registerHandler(for: "item_created") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleItemUpdate(message, type: .created)
            }
        }
        
        webSocketManager.registerHandler(for: "item_updated") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleItemUpdate(message, type: .updated)
            }
        }
        
        webSocketManager.registerHandler(for: "item_deleted") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleItemUpdate(message, type: .deleted)
            }
        }
        
        webSocketManager.registerHandler(for: "tags_changed") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleItemUpdate(message, type: .tagsChanged)
            }
        }
        
        // Batch updates
        webSocketManager.registerHandler(for: "batch_update") { [weak self] message in
            Task { @MainActor [weak self] in
                self?.handleBatchUpdate(message)
            }
        }
        
        // Connection state monitoring
        webSocketManager.$connectionState
            .sink { [weak self] state in
                if state == .connected {
                    // Request any missed updates when reconnecting
                    Task {
                        await self?.requestMissedUpdates()
                    }
                }
            }
            .store(in: &cancellables)
    }
    
    private func handleItemUpdate(_ message: WebSocketManager.WebSocketMessage, type: ItemUpdate.UpdateType) {
        guard let data = message.data,
              let itemId = data["id"] as? String else { return }
        
        let update = ItemUpdate(
            id: itemId,
            type: type,
            timestamp: message.timestamp,
            data: data
        )
        
        // Add to pending updates
        pendingUpdates.append(update)
        hasUpdates = true
        lastUpdateTime = Date()
        
        // Notify subscribers
        updateNotification.send(update)
        
        // Auto-process if in foreground
        if UIApplication.shared.applicationState == .active {
            Task {
                try? await Task.sleep(nanoseconds: 500_000_000) // 0.5s delay
                await processSingleUpdate(update)
            }
        }
    }
    
    private func handleBatchUpdate(_ message: WebSocketManager.WebSocketMessage) {
        guard let data = message.data,
              let updates = data["updates"] as? [[String: Any]] else { return }
        
        for updateData in updates {
            if let typeString = updateData["type"] as? String,
               let type = ItemUpdate.UpdateType(rawValue: typeString),
               let itemId = updateData["id"] as? String {
                
                let update = ItemUpdate(
                    id: itemId,
                    type: type,
                    timestamp: message.timestamp,
                    data: updateData
                )
                
                pendingUpdates.append(update)
            }
        }
        
        hasUpdates = !pendingUpdates.isEmpty
        lastUpdateTime = Date()
    }
    
    private func processSingleUpdate(_ update: ItemUpdate) async {
        // Remove from pending if still there
        pendingUpdates.removeAll { $0.id == update.id && $0.type == update.type }
        
        await processUpdate(update)
        
        // Update state
        hasUpdates = !pendingUpdates.isEmpty
    }
    
    private func processUpdate(_ update: ItemUpdate) async {
        switch update.type {
        case .created:
            await handleItemCreated(update)
        case .updated:
            await handleItemUpdated(update)
        case .deleted:
            await handleItemDeleted(update)
        case .tagsChanged:
            await handleTagsChanged(update)
        }
    }
    
    private func handleItemCreated(_ update: ItemUpdate) async {
        guard let data = update.data else { return }
        
        // Check if item already exists
        guard let itemId = UUID(uuidString: update.id) else { return }
        if coreDataManager.itemExists(withId: itemId) {
            return
        }
        
        // Create item from WebSocket data
        if data["url"] as? String != nil,
           let content = data["content"] as? String {
            
            let title = data["title"] as? String
            let tags = data["tags"] as? [String] ?? []
            // Not using summary for now
            let capturedAt = data["captured_at"] as? String
            
            let dateFormatter = ISO8601DateFormatter()
            let date = capturedAt.flatMap { dateFormatter.date(from: $0) } ?? Date()
            
            do {
                try coreDataManager.createItem(
                    id: itemId,
                    title: title ?? "Untitled",
                    content: content,
                    type: "article",
                    timestamp: date,
                    tags: tags,
                    isFavorite: false,
                    syncStatus: String(SyncStatus.synced.rawValue),
                    localID: nil
                )
            } catch {
                print("Error creating item from WebSocket: \(error)")
            }
        }
    }
    
    private func handleItemUpdated(_ update: ItemUpdate) async {
        guard let data = update.data else { return }
        
        // Update existing item
        if data["url"] != nil {
            let title = data["title"] as? String
            let content = data["content"] as? String ?? ""
            let tags = data["tags"] as? [String] ?? []
            // Not using summary for now
            
            guard let itemId = UUID(uuidString: update.id) else { return }
            do {
                try coreDataManager.updateItem(
                    id: itemId,
                    title: title,
                    content: content,
                    type: "article",
                    tags: tags
                )
            } catch {
                print("Error updating item from WebSocket: \(error)")
            }
        }
    }
    
    private func handleItemDeleted(_ update: ItemUpdate) async {
        guard let itemId = UUID(uuidString: update.id) else { return }
        coreDataManager.deleteItem(id: itemId)
    }
    
    private func handleTagsChanged(_ update: ItemUpdate) async {
        guard let data = update.data,
              let tags = data["tags"] as? [String] else { return }
        
        guard let itemId = UUID(uuidString: update.id) else { return }
        coreDataManager.updateItemTags(id: itemId, tags: tags)
    }
    
    private func requestMissedUpdates() async {
        // Get the timestamp of the last received update
        let lastSync = UserDefaults.standard.object(forKey: "last_sync_timestamp") as? Date ?? Date().addingTimeInterval(-3600)
        
        await webSocketManager.send(
            type: "request_updates",
            data: [
                "since": ISO8601DateFormatter().string(from: lastSync),
                "client_id": UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
            ]
        )
        
        // Update last sync timestamp
        UserDefaults.standard.set(Date(), forKey: "last_sync_timestamp")
    }
}

// MARK: - Timeline Integration
extension RealtimeUpdateService {
    /// Check if a specific item has pending updates
    func hasPendingUpdate(for itemId: String) -> Bool {
        pendingUpdates.contains { $0.id == itemId }
    }
    
    /// Get update type for a specific item
    func updateType(for itemId: String) -> ItemUpdate.UpdateType? {
        pendingUpdates.first { $0.id == itemId }?.type
    }
}
