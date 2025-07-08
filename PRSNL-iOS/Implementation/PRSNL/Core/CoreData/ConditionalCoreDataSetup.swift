import Foundation
import CoreData

/// A utility class that helps set up Core Data with or without App Groups
/// This allows testing on devices without a paid developer account
class ConditionalCoreDataSetup {
    /// Shared instance for app-wide access
    static let shared = ConditionalCoreDataSetup()
    
    /// Flag indicating if App Groups are available and properly configured
    private(set) var isUsingAppGroups: Bool = false
    
    /// The app group identifier used for shared container access
    let appGroupIdentifier = "group.ai.prsnl.shared"
    
    /// Creates a persistent store description that works with or without App Groups
    /// - Returns: A configured NSPersistentStoreDescription
    func createPersistentStoreDescription() -> NSPersistentStoreDescription {
        // First try to use the App Group container
        if let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier) {
            let storeURL = containerURL.appendingPathComponent("PRSNLModel.sqlite")
            isUsingAppGroups = true
            print("Using App Group container at \(storeURL.path)")
            return NSPersistentStoreDescription(url: storeURL)
        }
        
        // Fallback to the local Documents directory if App Groups aren't available
        // This allows testing without a paid developer account
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let storeURL = documentsDirectory.appendingPathComponent("PRSNLModel.sqlite")
        isUsingAppGroups = false
        print("Using local container at \(storeURL.path) (App Groups not available)")
        return NSPersistentStoreDescription(url: storeURL)
    }
    
    /// Configures a persistent container with the appropriate store description
    /// - Parameter container: The NSPersistentContainer to configure
    func configurePersistentContainer(_ container: NSPersistentContainer) {
        let storeDescription = createPersistentStoreDescription()
        container.persistentStoreDescriptions = [storeDescription]
    }
    
    /// Returns the shared container URL if available, or local Documents directory otherwise
    /// - Returns: URL for shared data storage
    func getSharedContainerURL() -> URL {
        if let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier) {
            isUsingAppGroups = true
            return containerURL
        }
        
        // Fallback to Documents directory
        isUsingAppGroups = false
        return FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
    }
    
    /// Gets a UserDefaults instance that works with or without App Groups
    /// - Returns: A UserDefaults instance for settings storage
    func getSharedUserDefaults() -> UserDefaults {
        // Try to use app group user defaults
        if let sharedDefaults = UserDefaults(suiteName: appGroupIdentifier) {
            isUsingAppGroups = true
            return sharedDefaults
        }
        
        // Fallback to standard user defaults
        isUsingAppGroups = false
        return UserDefaults.standard
    }
    
    /// Shows the current state of App Groups functionality
    /// - Returns: A string describing the current setup
    func getStatusMessage() -> String {
        if isUsingAppGroups {
            return "Using App Groups for data sharing (full functionality available)"
        } else {
            return "Using local storage (App Groups not available - extensions may have limited functionality)"
        }
    }
}