import Foundation
import CoreData
import Combine
import UIKit

// Simplified CoreDataManager for ShareExtension
class CoreDataManager {
    static let shared = CoreDataManager()
    
    // Core Data persistent container
    private lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "PRSNLModel")
        
        // Configure container to use app groups
        if let url = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: "group.ai.prsnl.shared") {
            let storeURL = url.appendingPathComponent("PRSNLModel.sqlite")
            let description = NSPersistentStoreDescription(url: storeURL)
            container.persistentStoreDescriptions = [description]
        }
        
        container.loadPersistentStores { (storeDescription, error) in
            if let error = error as NSError? {
                print("Failed to load persistent stores: \(error), \(error.userInfo)")
            }
        }
        
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        
        return container
    }()
    
    // Main context for UI operations
    var viewContext: NSManagedObjectContext {
        return persistentContainer.viewContext
    }
    
    // Save context
    func saveViewContext() throws {
        if viewContext.hasChanges {
            try viewContext.save()
        }
    }
    
    // Simple method to fetch recent tags
    func fetchRecentTags(limit: Int) async throws -> [String] {
        let context = viewContext
        let fetchRequest: NSFetchRequest<CDTag> = CDTag.fetchRequest()
        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]
        fetchRequest.fetchLimit = limit
        
        let tags = try context.fetch(fetchRequest)
        return tags.compactMap { $0.name }
    }
}

// Simplified NetworkMonitor for ShareExtension
class NetworkMonitor {
    static let shared = NetworkMonitor()
    
    // We'll just default to connected for simplicity in the extension
    let isConnected = true
}

// KeychainService for accessing shared keychain items
class KeychainService {
    static let shared = KeychainService()
    
    enum KeychainKey: String {
        case apiKey = "apiKey"
    }
    
    func get(_ key: KeychainKey) -> String? {
        return UserDefaults(suiteName: "group.ai.prsnl.shared")?.string(forKey: key.rawValue)
    }
}

// Core Data model classes
@objc(CDItem)
public class CDItem: NSManagedObject {
    @NSManaged public var id: String?
    @NSManaged public var title: String?
    @NSManaged public var content: String?
    @NSManaged public var url: String?
    @NSManaged public var summary: String?
    @NSManaged public var status: String?
    @NSManaged public var syncStatus: Int16
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var accessedAt: Date?
    @NSManaged public var accessCount: Int32
    @NSManaged public var itemType: String?
    @NSManaged public var tags: NSSet?
    
    public func addToTags(_ tag: CDTag) {
        let tags = self.tags ?? NSSet()
        self.tags = tags.addingObjects(from: [tag]) as NSSet
    }
}

@objc(CDTag)
public class CDTag: NSManagedObject {
    @NSManaged public var name: String?
    @NSManaged public var items: NSSet?
    
    public func addToItems(_ item: CDItem) {
        let items = self.items ?? NSSet()
        self.items = items.addingObjects(from: [item]) as NSSet
    }
}

extension CDTag {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<CDTag> {
        return NSFetchRequest<CDTag>(entityName: "Tag")
    }
}

extension CDItem {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<CDItem> {
        return NSFetchRequest<CDItem>(entityName: "Item")
    }
}

// SyncStatus enum
enum SyncStatus: Int16 {
    case synced = 0
    case needsUpload = 1
    case needsUpdate = 2
    case deleted = 3
}