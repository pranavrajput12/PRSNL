import Foundation
import CoreData
import Combine

// Import SyncStatus enum
enum SyncStatus: Int16 {
    case synced = 0
    case needsUpload = 1
    case needsUpdate = 2
    case deleted = 3
}

/// Manages all Core Data operations for the PRSNL app
class CoreDataManager {
    /// Shared instance for app-wide access
    static let shared = CoreDataManager()
    
    /// Core Data persistent container
    private lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "PRSNLModel")
        
        // Configure container to use either app groups or local storage
        ConditionalCoreDataSetup.shared.configurePersistentContainer(container)
        
        container.loadPersistentStores { (storeDescription, error) in
            if let error = error as NSError? {
                // This is a serious error - we can't load the data store
                fatalError("Failed to load persistent stores: \(error), \(error.userInfo)")
            }
        }
        
        // Enable automatic merging of changes from parent contexts
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        
        return container
    }()
    
    /// Main context for UI operations
    var viewContext: NSManagedObjectContext {
        return persistentContainer.viewContext
    }
    
    /// Private initializer to ensure singleton usage
    private init() {}
    
    /// Creates a new background context for asynchronous operations
    /// - Returns: A new NSManagedObjectContext for background work
    func createBackgroundContext() -> NSManagedObjectContext {
        let context = persistentContainer.newBackgroundContext()
        context.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        return context
    }
    
    /// Performs a task on a background context
    /// - Parameter task: The task to perform with the context
    func performBackgroundTask(_ task: @escaping (NSManagedObjectContext) -> Void) {
        let context = createBackgroundContext()
        context.perform {
            task(context)
        }
    }
    
    /// Saves changes in the specified context
    /// - Parameter context: The context to save
    /// - Throws: Core Data errors if the save fails
    func saveContext(_ context: NSManagedObjectContext) throws {
        if context.hasChanges {
            try context.save()
        }
    }
    
    /// Fetches all items from Core Data
    /// - Parameters:
    ///   - context: The context to use for fetching
    ///   - sortDescriptors: Optional sort descriptors
    /// - Returns: Array of Item objects
    /// - Throws: Core Data errors if the fetch fails
    func fetchAllItems(in context: NSManagedObjectContext, 
                      sortDescriptors: [NSSortDescriptor]? = nil) throws -> [NSManagedObject] {
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.sortDescriptors = sortDescriptors ?? [NSSortDescriptor(key: "updatedAt", ascending: false)]
        return try context.fetch(fetchRequest)
    }
    
    /// Searches for items matching the given query
    /// - Parameters:
    ///   - query: The search query
    ///   - context: The context to use for fetching
    /// - Returns: Array of matching Item objects
    /// - Throws: Core Data errors if the search fails
    func searchItems(query: String, in context: NSManagedObjectContext) throws -> [NSManagedObject] {
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        
        // Create predicates for title, content, and tags
        let titlePredicate = NSPredicate(format: "title CONTAINS[cd] %@", query)
        let contentPredicate = NSPredicate(format: "content CONTAINS[cd] %@", query)
        
        // Combine predicates with OR
        let combinedPredicate = NSCompoundPredicate(orPredicateWithSubpredicates: [
            titlePredicate,
            contentPredicate
        ])
        
        fetchRequest.predicate = combinedPredicate
        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "updatedAt", ascending: false)]
        
        return try context.fetch(fetchRequest)
    }
    
    /// Counts items matching a predicate
    /// - Parameter predicate: The predicate to match items against
    /// - Returns: The count of matching items
    /// - Throws: Core Data errors if the count fails
    func countItems(matching predicate: NSPredicate? = nil) throws -> Int {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = predicate
        return try context.count(for: fetchRequest)
    }
    
    /// Searches for items with pagination support
    /// - Parameters:
    ///   - query: The search query
    ///   - context: The context to use for fetching
    ///   - limit: Maximum number of results
    ///   - offset: Number of results to skip
    /// - Returns: Array of matching Item models
    /// - Throws: Core Data errors if the search fails
    func searchItems(query: String, in context: NSManagedObjectContext, limit: Int = 50, offset: Int = 0) throws -> [Item] {
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        
        // Create predicates for title, content, and tags
        let titlePredicate = NSPredicate(format: "title CONTAINS[cd] %@", query)
        let contentPredicate = NSPredicate(format: "content CONTAINS[cd] %@", query)
        let tagPredicate = NSPredicate(format: "ANY tags.name CONTAINS[cd] %@", query)
        
        // Combine predicates with OR
        let combinedPredicate = NSCompoundPredicate(orPredicateWithSubpredicates: [
            titlePredicate,
            contentPredicate,
            tagPredicate
        ])
        
        fetchRequest.predicate = combinedPredicate
        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "updatedAt", ascending: false)]
        fetchRequest.fetchLimit = limit
        fetchRequest.fetchOffset = offset
        
        let cdItems = try context.fetch(fetchRequest)
        return cdItems.map { convertToItem($0) }
    }
    
    /// Converts a Core Data item to a model item
    /// - Parameter cdItem: The Core Data item to convert
    /// - Returns: An Item model object
    private func convertToItem(_ cdItem: NSManagedObject) -> Item {
        let id = cdItem.value(forKey: "id") as? String ?? ""
        let title = cdItem.value(forKey: "title") as? String ?? ""
        let content = cdItem.value(forKey: "content") as? String ?? ""
        let url = cdItem.value(forKey: "url") as? String
        let summary = cdItem.value(forKey: "summary") as? String
        let itemType = cdItem.value(forKey: "itemType") as? String ?? ItemType.note.rawValue
        let status = cdItem.value(forKey: "status") as? String ?? ItemStatus.active.rawValue
        let createdAt = cdItem.value(forKey: "createdAt") as? Date ?? Date()
        let updatedAt = cdItem.value(forKey: "updatedAt") as? Date ?? Date()
        let accessedAt = cdItem.value(forKey: "accessedAt") as? Date
        let accessCount = cdItem.value(forKey: "accessCount") as? Int32 ?? 0
        
        // Get tags
        var tags: [String] = []
        if let cdTags = cdItem.value(forKeyPath: "tags") as? NSSet {
            for case let cdTag as NSManagedObject in cdTags {
                if let tagName = cdTag.value(forKey: "name") as? String {
                    tags.append(tagName)
                }
            }
        }
        
        // Convert attachments if available
        var attachments: [Attachment]? = nil
        if let cdAttachments = cdItem.value(forKeyPath: "attachments") as? NSSet, cdAttachments.count > 0 {
            attachments = []
            for case let cdAttachment as NSManagedObject in cdAttachments {
                let attachmentId = cdAttachment.value(forKey: "id") as? String ?? ""
                let fileType = cdAttachment.value(forKey: "fileType") as? String ?? ""
                let filePath = cdAttachment.value(forKey: "filePath") as? String ?? ""
                let mimeType = cdAttachment.value(forKey: "mimeType") as? String ?? ""
                
                // Create metadata if available
                var metadata: AttachmentMetadata? = nil
                if let alt = cdAttachment.value(forKey: "alt") as? String,
                   let title = cdAttachment.value(forKey: "title") as? String,
                   let isRemote = cdAttachment.value(forKey: "isRemote") as? Bool {
                    metadata = AttachmentMetadata(
                        alt: alt,
                        title: title,
                        isRemote: isRemote
                    )
                }
                
                attachments?.append(Attachment(
                    id: attachmentId,
                    fileType: fileType,
                    filePath: filePath,
                    mimeType: mimeType,
                    metadata: metadata
                ))
            }
        }
        
        return Item(
            id: id,
            title: title,
            content: content,
            url: url,
            summary: summary,
            status: ItemStatus(rawValue: status) ?? .active,
            createdAt: createdAt,
            updatedAt: updatedAt,
            accessCount: Int(accessCount),
            accessedAt: accessedAt,
            tags: tags,
            itemType: ItemType(rawValue: itemType) ?? .note,
            attachments: attachments,
            keyPoints: nil, // TODO: Add keyPoints to Core Data model
            category: nil, // TODO: Add category to Core Data model
            isFavorite: false,
            sourceUrl: nil,
            author: nil,
            publishedAt: nil,
            readingTime: nil,
            imageUrl: nil,
            source: nil
        )
    }
    
    /// Creates a new item in Core Data
    /// - Parameters:
    ///   - item: The item model to create
    ///   - context: The context to use for creation
    /// - Returns: The created Core Data item
    /// - Throws: Core Data errors if the creation fails
    @discardableResult
    func createItem(from item: Item, in context: NSManagedObjectContext) throws -> NSManagedObject {
        let entity = NSEntityDescription.entity(forEntityName: "Item", in: context)!
        let cdItem = NSManagedObject(entity: entity, insertInto: context)
        
        cdItem.setValue(item.id, forKey: "id")
        cdItem.setValue(item.title, forKey: "title")
        cdItem.setValue(item.content, forKey: "content")
        cdItem.setValue(item.url, forKey: "url")
        cdItem.setValue(item.summary, forKey: "summary")
        cdItem.setValue(item.itemType.rawValue, forKey: "itemType")
        cdItem.setValue(item.status.rawValue, forKey: "status")
        cdItem.setValue(item.createdAt, forKey: "createdAt")
        cdItem.setValue(item.updatedAt, forKey: "updatedAt")
        cdItem.setValue(item.accessedAt, forKey: "accessedAt")
        cdItem.setValue(Int32(item.accessCount), forKey: "accessCount")
        cdItem.setValue(Int16(SyncStatus.synced.rawValue), forKey: "syncStatus")
        
        // Create attachments if available
        if let attachments = item.attachments {
            for attachment in attachments {
                let attachmentEntity = NSEntityDescription.entity(forEntityName: "Attachment", in: context)!
                let cdAttachment = NSManagedObject(entity: attachmentEntity, insertInto: context)
                
                cdAttachment.setValue(attachment.id, forKey: "id")
                cdAttachment.setValue(attachment.fileType, forKey: "fileType")
                cdAttachment.setValue(attachment.filePath, forKey: "filePath")
                cdAttachment.setValue(attachment.mimeType, forKey: "mimeType")
                
                // Set metadata if available
                if let metadata = attachment.metadata {
                    cdAttachment.setValue(metadata.alt, forKey: "alt")
                    cdAttachment.setValue(metadata.title, forKey: "title")
                    cdAttachment.setValue(metadata.isRemote, forKey: "isRemote")
                }
                
                cdAttachment.setValue(cdItem, forKey: "item")
            }
        }
        
        // Update tags
        updateTags(for: cdItem, with: item.tags, in: context)
        
        try context.save()
        return cdItem
    }
    
    /// Checks if an item exists with the given ID
    /// - Parameters:
    ///   - id: The UUID of the item to check
    /// - Returns: True if the item exists, false otherwise
    func itemExists(withId id: UUID) -> Bool {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = NSPredicate(format: "id == %@", id as CVarArg)
        fetchRequest.fetchLimit = 1
        
        do {
            let count = try context.count(for: fetchRequest)
            return count > 0
        } catch {
            print("Error checking if item exists: \(error)")
            return false
        }
    }
    
    /// Updates an existing item in Core Data
    /// - Parameters:
    ///   - id: The ID of the item to update
    ///   - title: New title
    ///   - content: New content
    ///   - type: New type
    ///   - tags: New tags
    ///   - isFavorite: New favorite status
    ///   - syncStatus: New sync status
    /// - Throws: Core Data errors if the update fails
    func updateItem(id: UUID, title: String? = nil, content: String? = nil,
                   type: String? = nil, tags: [String]? = nil,
                   isFavorite: Bool? = nil, syncStatus: String? = nil) throws {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = NSPredicate(format: "id == %@", id as CVarArg)
        fetchRequest.fetchLimit = 1
        
        let items = try context.fetch(fetchRequest)
        guard let item = items.first else { return }
        
        if let title = title {
            item.setValue(title, forKey: "title")
        }
        if let content = content {
            item.setValue(content, forKey: "content")
        }
        if let type = type {
            item.setValue(type, forKey: "type")
        }
        if let isFavorite = isFavorite {
            item.setValue(isFavorite, forKey: "isFavorite")
        }
        if let syncStatus = syncStatus {
            item.setValue(syncStatus, forKey: "syncStatus")
        }
        
        item.setValue(Date(), forKey: "updatedAt")
        
        try saveContext(context)
    }
    
    /// Deletes an item with the given ID
    /// - Parameter id: The ID of the item to delete
    func deleteItem(id: UUID) {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = NSPredicate(format: "id == %@", id as CVarArg)
        
        do {
            let items = try context.fetch(fetchRequest)
            for item in items {
                context.delete(item)
            }
            try saveContext(context)
        } catch {
            print("Error deleting item: \(error)")
        }
    }
    
    /// Updates the tags for an item
    /// - Parameters:
    ///   - id: The ID of the item
    ///   - tags: The new tags array
    func updateItemTags(id: UUID, tags: [String]) {
        do {
            try updateItem(id: id, tags: tags)
        } catch {
            print("Error updating item tags: \(error)")
        }
    }
    
    /// Updates tags for a Core Data item
    /// - Parameters:
    ///   - cdItem: The Core Data item
    ///   - tagNames: Array of tag names
    ///   - context: The managed object context
    private func updateTags(for cdItem: NSManagedObject, with tagNames: [String], in context: NSManagedObjectContext) {
        // Clear existing tags
        if cdItem.value(forKey: "tags") is NSSet {
            cdItem.setValue(NSSet(), forKey: "tags")
        }
        
        // Create new tags
        let tagSet = NSMutableSet()
        for tagName in tagNames {
            let tagEntity = NSEntityDescription.entity(forEntityName: "Tag", in: context)!
            let tag = NSManagedObject(entity: tagEntity, insertInto: context)
            tag.setValue(tagName, forKey: "name")
            tag.setValue(cdItem, forKey: "item")
            tagSet.add(tag)
        }
        
        cdItem.setValue(tagSet, forKey: "tags")
    }
    
    /// Creates a new item with individual parameters
    /// - Parameters:
    ///   - id: Item ID
    ///   - title: Item title
    ///   - content: Item content
    ///   - type: Item type
    ///   - timestamp: Creation timestamp
    ///   - tags: Item tags
    ///   - isFavorite: Favorite status
    ///   - syncStatus: Sync status
    ///   - localID: Local ID
    /// - Throws: Core Data errors if creation fails
    func createItem(id: UUID, title: String, content: String, type: String,
                   timestamp: Date, tags: [String], isFavorite: Bool,
                   syncStatus: String, localID: String?) throws {
        let context = viewContext
        let entity = NSEntityDescription.entity(forEntityName: "Item", in: context)!
        let cdItem = NSManagedObject(entity: entity, insertInto: context)
        
        cdItem.setValue(id, forKey: "id")
        cdItem.setValue(title, forKey: "title")
        cdItem.setValue(content, forKey: "content")
        cdItem.setValue(type, forKey: "type")
        cdItem.setValue(timestamp, forKey: "createdAt")
        cdItem.setValue(timestamp, forKey: "updatedAt")
        cdItem.setValue(isFavorite, forKey: "isFavorite")
        cdItem.setValue(syncStatus, forKey: "syncStatus")
        if let localID = localID {
            cdItem.setValue(localID, forKey: "localID")
        }
        
        try saveContext(context)
    }
    
    /// Saves the view context
    /// - Throws: Core Data errors if the save fails
    func saveViewContext() throws {
        try saveContext(viewContext)
    }
    
    /// Fetches all tags from Core Data
    /// - Returns: Array of tag names
    /// - Throws: Core Data errors if the fetch fails
    func fetchAllTags() throws -> [String] {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Tag")
        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]
        
        let tags = try context.fetch(fetchRequest)
        return tags.compactMap { $0.value(forKey: "name") as? String }
    }
    
    /// Saves an Item model to Core Data
    /// - Parameter item: The Item to save
    /// - Throws: Core Data errors if the save fails
    func saveItem(_ item: Item) throws {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = NSPredicate(format: "id == %@", item.id)
        fetchRequest.fetchLimit = 1
        
        let existingItems = try context.fetch(fetchRequest)
        
        let cdItem: NSManagedObject
        if let existingItem = existingItems.first {
            // Update existing item
            cdItem = existingItem
        } else {
            // Create new item
            let entity = NSEntityDescription.entity(forEntityName: "Item", in: context)!
            cdItem = NSManagedObject(entity: entity, insertInto: context)
            cdItem.setValue(item.id, forKey: "id")
        }
        
        // Update properties
        cdItem.setValue(item.title, forKey: "title")
        cdItem.setValue(item.content, forKey: "content")
        cdItem.setValue(item.itemType.rawValue, forKey: "itemType")
        cdItem.setValue(item.status.rawValue, forKey: "status")
        cdItem.setValue(item.createdAt, forKey: "createdAt")
        cdItem.setValue(item.updatedAt, forKey: "updatedAt")
        cdItem.setValue(item.accessedAt, forKey: "accessedAt")
        cdItem.setValue(Int32(item.accessCount), forKey: "accessCount")
        cdItem.setValue(item.url, forKey: "url")
        cdItem.setValue(Int16(SyncStatus.synced.rawValue), forKey: "syncStatus")
        
        // Update tags
        updateTags(for: cdItem, with: item.tags, in: context)
        
        try saveContext(context)
    }
    
    /// Fetches items from Core Data
    /// - Parameters:
    ///   - predicate: Optional predicate to filter items
    ///   - sortDescriptors: Optional sort descriptors
    ///   - limit: Optional fetch limit
    /// - Returns: Array of Item models
    /// - Throws: Core Data errors if the fetch fails
    func fetchItems(predicate: NSPredicate? = nil,
                   sortDescriptors: [NSSortDescriptor]? = nil,
                   limit: Int? = nil) throws -> [Item] {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        
        fetchRequest.predicate = predicate
        fetchRequest.sortDescriptors = sortDescriptors ?? [NSSortDescriptor(key: "updatedAt", ascending: false)]
        
        if let limit = limit {
            fetchRequest.fetchLimit = limit
        }
        
        let cdItems = try context.fetch(fetchRequest)
        return cdItems.map { convertToItem($0) }
    }
    
    /// Fetches a single item by ID
    /// - Parameter id: The ID of the item to fetch
    /// - Returns: The Item if found, nil otherwise
    /// - Throws: Core Data errors if the fetch fails
    func fetchItem(byId id: String) throws -> Item? {
        let context = viewContext
        let fetchRequest = NSFetchRequest<NSManagedObject>(entityName: "Item")
        fetchRequest.predicate = NSPredicate(format: "id == %@", id)
        fetchRequest.fetchLimit = 1
        
        let cdItems = try context.fetch(fetchRequest)
        guard let cdItem = cdItems.first else { return nil }
        
        return convertToItem(cdItem)
    }
    
    /* Commented out - duplicate function with wrong types
    /// Converts a Item to an Item model
    /// - Parameter cdItem: The Core Data item
    /// - Returns: The Item model
    func convertToItem(_ cdItem: Item) -> Item {
        let tags = (cdItem.tags as? Set<CDTag>)?.compactMap { $0.name } ?? []
        
        // Convert attachments if available
        var attachments: [Attachment]? = nil
        if let cdAttachments = cdItem.attachments, cdAttachments.count > 0 {
            attachments = []
            for case let cdAttachment as NSManagedObject in cdAttachments {
                let attachmentId = cdAttachment.value(forKey: "id") as? String ?? ""
                let fileType = cdAttachment.value(forKey: "fileType") as? String ?? ""
                let filePath = cdAttachment.value(forKey: "filePath") as? String ?? ""
                let mimeType = cdAttachment.value(forKey: "mimeType") as? String ?? ""
                
                // Create metadata if available
                var metadata: AttachmentMetadata? = nil
                if let alt = cdAttachment.value(forKey: "alt") as? String,
                   let title = cdAttachment.value(forKey: "title") as? String,
                   let isRemote = cdAttachment.value(forKey: "isRemote") as? Bool {
                    metadata = AttachmentMetadata(
                        alt: alt,
                        title: title,
                        isRemote: isRemote
                    )
                }
                
                attachments?.append(Attachment(
                    id: attachmentId,
                    fileType: fileType,
                    filePath: filePath,
                    mimeType: mimeType,
                 metadata: metadata
                ))
            }
        }
        
        return Item(
            id: cdItem.id ?? "",
            title: cdItem.title ?? "",
            content: cdItem.content ?? "",
            url: cdItem.url,
            summary: cdItem.summary,
            status: ItemStatus(rawValue: cdItem.status ?? "active") ?? .active,
            createdAt: cdItem.createdAt ?? Date(),
            updatedAt: cdItem.updatedAt ?? Date(),
            accessCount: Int(cdItem.accessCount),
            accessedAt: cdItem.accessedAt,
            tags: tags,
            itemType: ItemType(rawValue: cdItem.itemType ?? "note") ?? .note,
            attachments: attachments
        )
    }
    */
    
    /// Gets the status of App Groups functionality
    /// - Returns: A string describing the current App Groups status
    func getAppGroupStatus() -> String {
        return ConditionalCoreDataSetup.shared.getStatusMessage()
    }
    
    /// Checks if App Groups are available and functioning
    /// - Returns: True if App Groups are available, false otherwise
    func isUsingAppGroups() -> Bool {
        return ConditionalCoreDataSetup.shared.isUsingAppGroups
    }
    
    // MARK: - Private Methods
}
