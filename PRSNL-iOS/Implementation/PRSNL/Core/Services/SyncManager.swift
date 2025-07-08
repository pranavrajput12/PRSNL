import Foundation
import Combine
import Network
import CoreData

/// Responsible for synchronizing data between local Core Data storage and remote API
class SyncManager {
    static let shared = SyncManager()
    
    // MARK: - Properties
    
    /// The monitor to track network connectivity
    private let networkMonitor = NWPathMonitor()
    
    /// Whether the device is currently online
    private(set) var isOnline = false
    
    /// Whether a sync operation is currently in progress
    private(set) var isSyncing = false
    
    /// Publisher for sync status updates
    private let syncStatusSubject = PassthroughSubject<SyncOperationStatus, Never>()
    var syncStatusPublisher: AnyPublisher<SyncOperationStatus, Never> {
        syncStatusSubject.eraseToAnyPublisher()
    }
    
    /// Last sync timestamp
    private(set) var lastSyncTimestamp: Date?
    
    // MARK: - Initialization
    
    private init() {
        setupNetworkMonitoring()
    }
    
    // MARK: - Network Monitoring
    
    /// Sets up the network monitor to track connectivity changes
    private func setupNetworkMonitoring() {
        networkMonitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                let isOnline = path.status == .satisfied
                let wasOffline = !(self?.isOnline ?? false)
                self?.isOnline = isOnline
                
                // If connectivity was restored, trigger a sync
                if isOnline && wasOffline {
                    self?.triggerSync()
                }
            }
        }
        
        // Start monitoring on a background queue
        let queue = DispatchQueue(label: "NetworkMonitorQueue")
        networkMonitor.start(queue: queue)
    }
    
    // MARK: - Sync Operations
    
    /// Triggers a data sync operation if conditions are right
    func triggerSync() {
        guard isOnline && !isSyncing else { return }
        
        Task {
            await sync()
        }
    }
    
    /// Performs the actual sync operation
    func sync() async {
        guard isOnline && !isSyncing else { return }
        
        do {
            // Mark as syncing
            await MainActor.run {
                isSyncing = true
                syncStatusSubject.send(.syncing)
            }
            
            // 1. Push pending local changes to server
            try await pushLocalChanges()
            
            // 2. Pull remote changes to local database
            try await pullRemoteChanges()
            
            // Update last sync timestamp
            await MainActor.run {
                lastSyncTimestamp = Date()
                isSyncing = false
                syncStatusSubject.send(.completed)
            }
        } catch {
            await MainActor.run {
                isSyncing = false
                syncStatusSubject.send(.failed(error))
            }
        }
    }
    
    /// Pushes local changes to the server
    private func pushLocalChanges() async throws {
        // Get items that need to be pushed to server
        let itemsToSync = try fetchItemsNeedingSync()
        
        for item in itemsToSync {
            // Handle items based on sync status
            if item.syncStatus == SyncStatus.needsUpload.rawValue {
                // Convert to model and push to server
                let modelItem = CoreDataManager.shared.convertToItem(from: item)
                
                if item.id?.hasPrefix("local-") == true {
                    // This is a new item, create on server
                    let createdItem = try await APIClient.shared.createItem(
                        title: modelItem.title,
                        content: modelItem.content,
                        tags: modelItem.tags,
                        itemType: modelItem.itemType
                    )
                    
                    // Update local item with server ID and mark as synced
                    try await updateLocalItemAfterSync(localItem: item, serverItem: createdItem)
                } else {
                    // This is an existing item, update on server
                    // Note: We'd need an updateItem endpoint in the API client
                    // For now, we'll just mark it as synced
                    item.syncStatus = Int16(SyncStatus.synced.rawValue)
                    try CoreDataManager.shared.saveContext(item.managedObjectContext!)
                }
            } else if item.syncStatus == SyncStatus.needsDeletion.rawValue {
                // Delete on server
                // Note: We'd need a deleteItem endpoint in the API client
                // For now, we'll just delete locally
                if let context = item.managedObjectContext {
                    context.delete(item)
                    try CoreDataManager.shared.saveContext(context)
                }
            }
        }
    }
    
    /// Pulls remote changes from the server
    private func pullRemoteChanges() async throws {
        // Fetch timeline from server
        // We'll use a page size of 100 to get a substantial amount of data
        let response = try await APIClient.shared.fetchTimeline(page: 1, limit: 100)
        
        // Save items to Core Data
        for item in response.items {
            try CoreDataManager.shared.saveItem(item)
        }
    }
    
    /// Updates a local item with server data after sync
    private func updateLocalItemAfterSync(localItem: CDItem, serverItem: Item) async throws {
        guard let context = localItem.managedObjectContext else {
            throw NSError(
                domain: "SyncManager",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Item has no context"]
            )
        }
        
        // Update the local item with server data
        localItem.id = serverItem.id
        localItem.syncStatus = Int16(SyncStatus.synced.rawValue)
        localItem.updatedAt = serverItem.updatedAt
        
        // Save changes
        try CoreDataManager.shared.saveContext(context)
    }
    
    /// Fetches items that need to be synced
    private func fetchItemsNeedingSync() throws -> [CDItem] {
        let context = CoreDataManager.shared.viewContext
        let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
        
        // Find items that need upload or deletion
        fetchRequest.predicate = NSPredicate(format: "syncStatus != %d", SyncStatus.synced.rawValue)
        
        return try context.fetch(fetchRequest)
    }
    
    // MARK: - Local Item Management
    
    /// Creates a new item locally (offline-ready)
    func createLocalItem(title: String, content: String, tags: [String], itemType: ItemType) throws -> Item {
        let context = CoreDataManager.shared.viewContext
        
        // Create a new Core Data item
        let cdItem = CDItem(context: context)
        
        // Set basic properties
        cdItem.id = "local-\(UUID().uuidString)"
        cdItem.title = title
        cdItem.content = content
        cdItem.itemType = itemType.rawValue
        cdItem.status = ItemStatus.active.rawValue
        cdItem.createdAt = Date()
        cdItem.updatedAt = Date()
        cdItem.accessCount = 0
        cdItem.syncStatus = Int16(SyncStatus.needsUpload.rawValue)
        
        // Add tags
        CoreDataManager.shared.updateTags(for: cdItem, with: tags, in: context)
        
        // Save the context
        try CoreDataManager.shared.saveContext(context)
        
        // Convert to model
        let item = CoreDataManager.shared.convertToItem(from: cdItem)
        
        // Trigger sync if online
        triggerSync()
        
        return item
    }
    
    /// Marks a local item for deletion (will be deleted from server on next sync)
    func markItemForDeletion(id: String) throws {
        let context = CoreDataManager.shared.viewContext
        let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
        fetchRequest.predicate = NSPredicate(format: "id == %@", id)
        
        let items = try context.fetch(fetchRequest)
        
        guard let item = items.first else {
            throw NSError(
                domain: "SyncManager",
                code: 2,
                userInfo: [NSLocalizedDescriptionKey: "Item not found"]
            )
        }
        
        // If this is a local-only item, delete it immediately
        if item.id?.hasPrefix("local-") == true {
            context.delete(item)
        } else {
            // Otherwise mark for deletion on next sync
            item.syncStatus = Int16(SyncStatus.needsDeletion.rawValue)
        }
        
        try CoreDataManager.shared.saveContext(context)
        
        // Trigger sync if online
        triggerSync()
    }
}

/// Represents the current status of a sync operation
enum SyncStatus: Int, Equatable {
    case synced = 0
    case needsUpload = 1
    case needsDeletion = 2
    case syncing = 3
    case failed = 4
}

/// Represents the sync operation status
enum SyncOperationStatus {
    case idle
    case syncing
    case completed
    case failed(Error)
}

// Extension for accessing Core Data private methods
extension CoreDataManager {
    /// Updates tags for an item (accessible from SyncManager)
    func updateTags(for cdItem: CDItem, with tags: [String], in context: NSManagedObjectContext) {
        // Remove existing relationship
        let existingTags = cdItem.tags as? Set<CDTag> ?? []
        for tag in existingTags {
            cdItem.removeFromTags(tag)
        }
        
        // Add new tags
        for tagName in tags {
            // Check if tag already exists
            let fetchRequest: NSFetchRequest<CDTag> = CDTag.fetchRequest()
            fetchRequest.predicate = NSPredicate(format: "name == %@", tagName)
            
            do {
                let existingTags = try context.fetch(fetchRequest)
                let cdTag: CDTag
                
                if let existingTag = existingTags.first {
                    cdTag = existingTag
                } else {
                    cdTag = CDTag(context: context)
                    cdTag.name = tagName
                }
                
                cdItem.addToTags(cdTag)
            } catch {
                print("Error fetching tag: \(error)")
            }
        }
    }
}