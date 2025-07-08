import Foundation
import CoreData
import SwiftUI
import WidgetKit

// MARK: - Widget Data Provider

class WidgetDataProvider: @unchecked Sendable {
    static let shared = WidgetDataProvider()
    
    // Direct access to Core Data persistent container
    private lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "PRSNLModel")
        
        // Configure for App Group container access
        if let storeURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: APP_GROUP_IDENTIFIER)?
            .appendingPathComponent("PRSNLModel.sqlite") {
            
            let storeDescription = NSPersistentStoreDescription(url: storeURL)
            container.persistentStoreDescriptions = [storeDescription]
        }
        
        container.loadPersistentStores { (storeDescription, error) in
            if let error = error as NSError? {
                print("[WIDGET ERROR] Failed to load persistent stores: \(error), \(error.userInfo)")
            }
        }
        
        // Configure view context for better performance in read-only widget context
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        
        return container
    }()
    
    // Background context for performing operations
    private var backgroundContext: NSManagedObjectContext {
        let context = persistentContainer.newBackgroundContext()
        context.automaticallyMergesChangesFromParent = true
        context.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        return context
    }
    
    private let cacheManager = WidgetCacheManager.shared
    private let batteryMonitor = BatteryMonitor.shared
    
    // Error tracking to limit excessive error logging
    private var lastErrorTime: [String: Date] = [:]
    private let errorCooldown: TimeInterval = 60 * 5 // 5 minutes between similar errors
    
    private init() {
        // Ensure we have proper access to the shared container
        ensureSharedContainerAccess()
        
        // Register for widget refresh notifications from main app
        setupWidgetRefreshObserver()
    }
    
    // Ensure we have proper access to the shared container
    private func ensureSharedContainerAccess() {
        // Check if we can access the shared UserDefaults as a basic test
        guard let defaults = UserDefaults(suiteName: APP_GROUP_IDENTIFIER) else {
            print("[WIDGET ERROR] Failed to access shared app group container")
            return
        }
        
        // Test read/write to verify permissions
        defaults.set(Date(), forKey: "WidgetDataProviderLastAccess")
    }
    
    // Set up to receive notifications when widget should refresh
    private func setupWidgetRefreshObserver() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleWidgetRefreshRequest),
            name: NSNotification.Name("com.prsnl.widget.refreshRequested"),
            object: nil
        )
    }
    
    // Handle widget refresh requests from main app
    @objc private func handleWidgetRefreshRequest() {
        // Clear caches so next widget reload gets fresh data
        clearWidgetCaches()
        
        #if os(iOS)
        // Request WidgetKit to reload widgets
        WidgetCenter.shared.reloadAllTimelines()
        #endif
    }
    
    // MARK: - Data Fetch Methods
    
    // Determines next refresh date based on battery state
    func nextRefreshDate() -> Date {
        let interval = batteryMonitor.getRefreshInterval()
        return Date().addingTimeInterval(interval)
    }
    
    // Fetch recent items for Timeline widget (async)
    func fetchRecentItems(limit: Int = 5) async throws -> [ItemSnapshot] {
        // Create fetch request
        let request = NSFetchRequest<NSManagedObject>(entityName: "CDItem")
        request.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: false)]
        request.fetchLimit = limit
        
        // Execute fetch on background context
        return try await backgroundContext.perform {
            let results = try request.execute()
            
            // Convert to snapshot items
            return results.map { cdItem in
                ItemSnapshot(
                    id: cdItem.value(forKey: "id") as? String ?? UUID().uuidString,
                    title: cdItem.value(forKey: "title") as? String ?? "Untitled",
                    content: cdItem.value(forKey: "content") as? String ?? "",
                    createdAt: cdItem.value(forKey: "createdAt") as? Date ?? Date(),
                    type: cdItem.value(forKey: "itemType") as? String ?? "note"
                )
            }
        }
    }
    
    // Fetch recent items with completion handler (for Widget Timeline)
    func fetchRecentItems(limit: Int = 5, completion: @escaping ([ItemSnapshot]) -> Void) {
        // Check cache first
        let cacheKey = "recentItems-\(limit)"
        if let cachedItems: [ItemSnapshot] = cacheManager.entry(for: cacheKey) {
            completion(cachedItems)
            return
        }
        
        // If not cached, fetch async and cache result
        Task {
            do {
                let items = try await fetchRecentItems(limit: limit)
                self.cacheManager.setEntry(items, for: cacheKey)
                DispatchQueue.main.async {
                    completion(items)
                }
            } catch {
                // Log error with more context
                let errorMessage = "Widget data fetch error: \(error.localizedDescription)"
                self.logWidgetError(errorMessage, error: error)
                
                // Try to recover with fallback data if possible
                DispatchQueue.main.async { [weak self] in
                    guard let self = self else { return }
                    // Try to use stale cache if available
                    if let staleItems: [ItemSnapshot] = self.getStaleCache(for: cacheKey) {
                        completion(staleItems)
                    } else {
                        // Fall back to sample data as last resort
                        completion(self.getSampleItems())
                    }
                }
            }
        }
    }
    
    // Helper method to get sample items when no data is available
    private func getSampleItems() -> [ItemSnapshot] {
        return [
            ItemSnapshot(
                id: UUID().uuidString,
                title: "Sample Item",
                content: "This is a sample item when data couldn't be loaded",
                createdAt: Date(),
                type: "note"
            )
        ]
    }
    
    // Helper method to get stale cache entries (ignoring expiration)
    private func getStaleCache<T>(for key: String) -> T? {
        // Delegate to cache manager's stale cache functionality
        return cacheManager.getStaleEntry(for: key)
    }
    
    // Helper method to log widget errors consistently with rate limiting
    private func logWidgetError(_ message: String, error: Error) {
        // Create an error identifier to group similar errors
        let nsError = error as NSError
        let errorIdentifier = "\(nsError.domain)-\(nsError.code)"
        
        // Check if we've recently logged this same error type
        if let lastTime = lastErrorTime[errorIdentifier],
           Date().timeIntervalSince(lastTime) < errorCooldown {
            // Skip detailed logging if we're in the cooldown period
            print("[WIDGET] Suppressing repeated error of type \(errorIdentifier)")
            return
        }
        
        // Update last error time for this error type
        lastErrorTime[errorIdentifier] = Date()
        
        // Log to console with detailed context
        print("---------- WIDGET ERROR ----------")
        print("🔴 \(message)")
        print("📋 Details:")
        print("  - Error: \(error)")
        print("  - Type: \(type(of: error))")
        print("  - Domain: \(nsError.domain)")
        print("  - Code: \(nsError.code)")
        print("  - Description: \(nsError.localizedDescription)")
            
        if let reason = nsError.localizedFailureReason {
            print("  - Reason: \(reason)")
        }
        
        if !nsError.userInfo.isEmpty {
            print("  - User Info:")
            for (key, value) in nsError.userInfo {
                print("    - \(key): \(value)")
            }
        }
        
        // Log stack trace for Core Data errors which are often cryptic
        if nsError.domain == NSCocoaErrorDomain {
            print("  - Stack Trace:")
            Thread.callStackSymbols.forEach { symbol in
                print("    \(symbol)")
            }
        }
        
        // Provide diagnostics about the current environment
        print("📊 Diagnostics:")
        print("  - Battery: \(batteryMonitor.getBatteryStatusDescription())")
        print("  - App Group: \(UserDefaults(suiteName: APP_GROUP_IDENTIFIER) != nil ? "Accessible" : "Inaccessible")")
        print("-----------------------------------")
    }
    
    // Fetch stats for Stats widget (async)
    func fetchStats() async throws -> StatsEntry {
        let context = backgroundContext
        
        return try await context.perform {
            // Get total items count
            let totalRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            totalRequest.resultType = .countResultType
            let totalItems = try context.count(for: totalRequest)
            
            // Get today's items count
            let todayRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            todayRequest.resultType = .countResultType
            todayRequest.predicate = NSPredicate(
                format: "createdAt >= %@",
                Calendar.current.startOfDay(for: Date()) as NSDate
            )
            let itemsToday = try context.count(for: todayRequest)
            
            // Get this week's items count
            let weekStartDate = Calendar.current.date(
                byAdding: .day,
                value: -7,
                to: Calendar.current.startOfDay(for: Date())
            )!
            let weekRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            weekRequest.resultType = .countResultType
            weekRequest.predicate = NSPredicate(
                format: "createdAt >= %@",
                weekStartDate as NSDate
            )
            let itemsThisWeek = try context.count(for: weekRequest)
            
            // Get items by type
            let typeRequest = NSFetchRequest<NSManagedObject>(entityName: "CDItem")
            let typesResults = try context.fetch(typeRequest)
            
            var itemsByType: [String: Int] = [:]
            for result in typesResults {
                if let type = result.value(forKey: "itemType") as? String {
                    itemsByType[type, default: 0] += 1
                }
            }
            
            // Get completed tasks count
            let completedRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            completedRequest.resultType = .countResultType
            completedRequest.predicate = NSPredicate(
                format: "itemType == %@ AND status == %@",
                "task", "completed"
            )
            let completedTasks = try context.count(for: completedRequest)
            
            // Get pending tasks count
            let pendingRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            pendingRequest.resultType = .countResultType
            pendingRequest.predicate = NSPredicate(
                format: "itemType == %@ AND status == %@",
                "task", "active"
            )
            let pendingTasks = try context.count(for: pendingRequest)
            
            // Create stats entry
            return StatsEntry(
                date: Date(),
                totalItems: totalItems,
                itemsToday: itemsToday,
                itemsThisWeek: itemsThisWeek,
                itemsByType: itemsByType,
                completedTasks: completedTasks,
                pendingTasks: pendingTasks
            )
        }
    }
    
    // Fetch stats with completion handler (for Widget Timeline)
    func fetchStats(completion: @escaping (StatsEntry) -> Void) {
        // Check cache first
        let cacheKey = "stats"
        if let cachedStats: StatsEntry = cacheManager.entry(for: cacheKey) {
            completion(cachedStats)
            return
        }
        
        // If not cached, fetch async and cache result
        Task {
            do {
                let stats = try await fetchStats()
                self.cacheManager.setEntry(stats, for: cacheKey)
                DispatchQueue.main.async {
                    completion(stats)
                }
            } catch {
                // Log error with more context
                let errorMessage = "Widget stats fetch error: \(error.localizedDescription)"
                self.logWidgetError(errorMessage, error: error)
                
                DispatchQueue.main.async { [weak self] in
                    guard let self = self else { return }
                    // Try to use stale cache if available
                    if let staleStats: StatsEntry = self.getStaleCache(for: cacheKey) {
                        completion(staleStats)
                    } else {
                        // Create empty stats as fallback with error indicator
                        let emptyStats = StatsEntry(
                            date: Date(),
                            totalItems: 0,
                            itemsToday: 0,
                            itemsThisWeek: 0,
                            itemsByType: ["error": 1], // Indicator that this is an error state
                            completedTasks: 0,
                            pendingTasks: 0
                        )
                        completion(emptyStats)
                    }
                }
            }
        }
    }
    
    // Clear all widget caches (call when app data changes significantly)
    func clearWidgetCaches() {
        cacheManager.clearCache()
    }
}

// MARK: - Cache Manager for Widget Performance

// Constants
let APP_GROUP_IDENTIFIER = "group.ai.prsnl.shared"

enum CacheExpiration {
    static let short: TimeInterval = 5 * 60 // 5 minutes
    static let medium: TimeInterval = 15 * 60 // 15 minutes
    static let long: TimeInterval = 60 * 60 // 1 hour
}

public class WidgetCacheManager {
    static let shared = WidgetCacheManager()
    
    // Type-specific caches to avoid type casting issues
    private var itemsCache: [String: [ItemSnapshot]] = [:]
    private var statsCache: [String: StatsEntry] = [:]
    private var miscCache: [String: Any] = [:]
    
    // Separate stale cache for fallback
    private var staleItemsCache: [String: [ItemSnapshot]] = [:]
    private var staleStatsCache: [String: StatsEntry] = [:]
    private var staleMiscCache: [String: Any] = [:]
    
    // Track timestamps for cache entries
    private var timestamps: [String: Date] = [:]
    
    // Track errors to prevent excessive logging
    private var lastErrorTimestamps: [String: Date] = [:]
    
    // Max age for cached entries (15 minutes)
    private let maxAge: TimeInterval = CacheExpiration.medium
    
    // Max memory size (approximate)
    private let maxCacheSize = 50  // Maximum number of entries to store
    
    // Cache invalidation timestamp
    private var invalidationTimestamp: TimeInterval {
        get {
            let sharedDefaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
            return sharedDefaults?.double(forKey: "WidgetCacheInvalidationTimestamp") ?? 0
        }
        set {
            let sharedDefaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
            sharedDefaults?.set(newValue, forKey: "WidgetCacheInvalidationTimestamp")
        }
    }
    
    private init() {
        // Initial cleanup
        cleanExpiredEntries()
        
        // Restore from persistent store if needed
        loadCacheFromDisk()
        
        // Set up notification observer for app termination
        #if os(iOS)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(saveCacheToDisk),
            name: UIApplication.willTerminateNotification,
            object: nil
        )
        #endif
    }
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }
    
    // Get entry from cache with type safety
    func entry<T>(for key: String) -> T? {
        // Clean expired entries first
        cleanExpiredEntries()
        
        // Check if cache is valid against global invalidation timestamp
        if isCacheInvalidated() {
            // Cache was invalidated by main app, clear it
            clearCache()
            return nil
        }
        
        // Type-specific retrieval to avoid downcasting issues
        let value: Any?
        
        switch T.self {
        case is [ItemSnapshot].Type:
            value = itemsCache[key]
        case is StatsEntry.Type:
            value = statsCache[key]
        default:
            value = miscCache[key]
        }
        
        // Verify timestamp and return if valid
        if let entry = value as? T,
           let timestamp = timestamps[key],
           Date().timeIntervalSince(timestamp) < maxAge {
            return entry
        }
        
        return nil
    }
    
    // Store entry in cache with type safety
    func setEntry<T>(_ entry: T, for key: String) {
        // Store in type-specific cache
        if let items = entry as? [ItemSnapshot] {
            itemsCache[key] = items
            staleItemsCache[key] = items
        } else if let stats = entry as? StatsEntry {
            statsCache[key] = stats
            staleStatsCache[key] = stats
        } else {
            miscCache[key] = entry
            staleMiscCache[key] = entry
        }
        
        // Update timestamp
        timestamps[key] = Date()
        
        // Clean up if cache gets too large
        enforceMemoryLimit()
    }
    
    // Get stale entry from cache (for fallback)
    func getStaleEntry<T>(for key: String) -> T? {
        // Try to get from appropriate stale cache
        let value: Any?
        
        switch T.self {
        case is [ItemSnapshot].Type:
            value = staleItemsCache[key]
        case is StatsEntry.Type:
            value = staleStatsCache[key]
        default:
            value = staleMiscCache[key]
        }
        
        return value as? T
    }
    
    // Check if cache was invalidated by the main app
    private func isCacheInvalidated() -> Bool {
        let lastCacheReset = invalidationTimestamp
        let lastEntryTimestamp = timestamps.values.max()?.timeIntervalSince1970 ?? 0
        
        return lastCacheReset > lastEntryTimestamp
    }
    
    // Invalidate cache from main app
    func invalidateCache() {
        invalidationTimestamp = Date().timeIntervalSince1970
    }
    
    // Clear expired entries
    private func cleanExpiredEntries() {
        let now = Date()
        var keysToRemove: [String] = []
        
        for (key, timestamp) in timestamps {
            if now.timeIntervalSince(timestamp) >= maxAge {
                keysToRemove.append(key)
            }
        }
        
        // Remove expired entries
        for key in keysToRemove {
            itemsCache.removeValue(forKey: key)
            statsCache.removeValue(forKey: key)
            miscCache.removeValue(forKey: key)
            timestamps.removeValue(forKey: key)
            // Note: We keep stale entries for fallback
        }
    }
    
    // Enforce memory limits
    private func enforceMemoryLimit() {
        // If we exceed our max cache size, remove oldest entries
        let totalEntries = itemsCache.count + statsCache.count + miscCache.count
        
        if totalEntries > maxCacheSize {
            // Get all keys sorted by timestamp (oldest first)
            let sortedKeys = timestamps.sorted { $0.value < $1.value }.map { $0.key }
            
            // Number of entries to remove
            let entriesToRemove = totalEntries - maxCacheSize
            
            // Remove oldest entries
            for i in 0..<min(entriesToRemove, sortedKeys.count) {
                let key = sortedKeys[i]
                itemsCache.removeValue(forKey: key)
                statsCache.removeValue(forKey: key)
                miscCache.removeValue(forKey: key)
                timestamps.removeValue(forKey: key)
                // Keep in stale cache for fallback
            }
        }
    }
    
    // Clear all entries
    func clearCache() {
        itemsCache.removeAll()
        statsCache.removeAll()
        miscCache.removeAll()
        timestamps.removeAll()
        // Keep stale cache for fallback
    }
    
    // Persist cache to disk
    @objc private func saveCacheToDisk() {
        // Save only the most important cache entries
        let defaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
        
        // Save timestamps
        defaults?.set(Date(), forKey: "WidgetCacheLastSaved")
    }
    
    // Load cache from disk
    private func loadCacheFromDisk() {
        // Load from UserDefaults if available
        let defaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
        
        // Check if we have saved cache data
        if let lastSaved = defaults?.object(forKey: "WidgetCacheLastSaved") as? Date {
            // Only restore if recently saved (within cache expiration)
            if Date().timeIntervalSince(lastSaved) < maxAge {
                // Here we would implement actual loading from persistence
            }
        }
    }
}

// MARK: - Battery Monitor for Efficiency

// Widget-compatible battery status monitor
// Uses shared UserDefaults instead of direct UIDevice battery monitoring
class BatteryMonitor {
    static let shared = BatteryMonitor()
    
    // Constants for shared storage keys
    private struct Keys {
        static let batteryLevel = "BatteryMonitor.batteryLevel"
        static let batteryState = "BatteryMonitor.batteryState"
        static let lowPowerMode = "BatteryMonitor.lowPowerMode"
        static let lastUpdated = "BatteryMonitor.lastUpdated"
    }
    
    // Enum for battery states that can be stored in UserDefaults
    enum BatteryState: Int {
        case unknown = 0
        case unplugged = 1
        case charging = 2
        case full = 3
    }
    
    // Refresh intervals based on power conditions
    private struct RefreshIntervals {
        static let normal: TimeInterval = 15 * 60      // 15 minutes
        static let lowPower: TimeInterval = 30 * 60    // 30 minutes
        static let critical: TimeInterval = 60 * 60    // 60 minutes (1 hour)
        static let charging: TimeInterval = 10 * 60    // 10 minutes (more frequent when charging)
        static let unknown: TimeInterval = 20 * 60     // 20 minutes (conservative default)
    }
    
    // Battery level thresholds
    private struct BatteryThresholds {
        static let critical: Float = 0.2   // 20%
        static let low: Float = 0.3        // 30%
    }
    
    // UserDefaults for shared storage
    private let sharedDefaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
    
    private init() {
        // No battery monitoring setup needed - we'll read from shared UserDefaults
        // Low power mode can still be detected in the widget
        updateLowPowerModeStatus()
    }
    
    // Read the current battery level from shared UserDefaults
    var batteryLevel: Float {
        return sharedDefaults?.float(forKey: Keys.batteryLevel) ?? 0.5 // Default 50%
    }
    
    // Read the current battery state from shared UserDefaults
    var batteryState: BatteryState {
        let stateValue = sharedDefaults?.integer(forKey: Keys.batteryState) ?? 0
        return BatteryState(rawValue: stateValue) ?? .unknown
    }
    
    // Low power mode can be detected in extensions
    var isLowPowerModeEnabled: Bool {
        if #available(iOS 9.0, *) {
            return ProcessInfo.processInfo.isLowPowerModeEnabled
        }
        return false
    }
    
    // Check if we have recent battery data
    var hasFreshBatteryData: Bool {
        guard let lastUpdated = sharedDefaults?.object(forKey: Keys.lastUpdated) as? Date else {
            return false
        }
        // Consider data fresh if updated within the last hour
        return Date().timeIntervalSince(lastUpdated) < 3600 // 1 hour
    }
    
    // Update low power mode status (this CAN work in extensions)
    private func updateLowPowerModeStatus() {
        if #available(iOS 9.0, *) {
            let isLowPower = ProcessInfo.processInfo.isLowPowerModeEnabled
            sharedDefaults?.set(isLowPower, forKey: Keys.lowPowerMode)
        }
    }
    
    // Get the appropriate refresh interval based on available data
    func getRefreshInterval() -> TimeInterval {
        // Update low power mode status (this works in extensions)
        updateLowPowerModeStatus()
        
        // If we don't have fresh battery data, use a conservative approach
        if !hasFreshBatteryData {
            return RefreshIntervals.unknown
        }
        
        // Use the battery data from shared UserDefaults
        let level = batteryLevel
        let state = batteryState
        let isLowPower = isLowPowerModeEnabled
        
        // Determine refresh interval based on battery state
        switch state {
        case .charging, .full:
            return RefreshIntervals.charging
            
        case .unplugged:
            if level < BatteryThresholds.critical {
                return RefreshIntervals.critical
            } else if isLowPower {
                return RefreshIntervals.lowPower
            } else {
                return RefreshIntervals.normal
            }
            
        case .unknown:
            return RefreshIntervals.unknown
        }
    }
    
    // For debugging - get a description of current battery status
    func getBatteryStatusDescription() -> String {
        let stateString: String
        switch batteryState {
        case .charging: stateString = "charging"
        case .full: stateString = "full"
        case .unplugged: stateString = "unplugged"
        case .unknown: stateString = "unknown"
        }
        
        // Compose status string
        var status = "Battery: \(Int(batteryLevel * 100))%, State: \(stateString), " +
                    "Low Power Mode: \(isLowPowerModeEnabled ? "On" : "Off")"
        
        // Add freshness indicator
        if let lastUpdated = sharedDefaults?.object(forKey: Keys.lastUpdated) as? Date {
            let minutes = Int(Date().timeIntervalSince(lastUpdated) / 60)
            status += ", Last Updated: \(minutes) min ago"
        } else {
            status += ", No battery data available"
        }
        
        return status
    }
}

// MARK: - WidgetCacheManager Diagnostics Extension
extension WidgetCacheManager {
    
    // Get a diagnostic overview of cache status
    func getCacheStatus() -> String {
        let totalItems = itemsCache.count + statsCache.count + miscCache.count
        let totalStaleItems = staleItemsCache.count + staleStatsCache.count + staleMiscCache.count
        let oldestEntry = timestamps.values.min()
        let newestEntry = timestamps.values.max()
        
        var ageDescription = "No entries"
        if let oldest = oldestEntry, let newest = newestEntry {
            let oldestAge = Date().timeIntervalSince(oldest)
            let newestAge = Date().timeIntervalSince(newest)
            ageDescription = "Oldest: \(Int(oldestAge))s, Newest: \(Int(newestAge))s"
        }
        
        let invalidated = isCacheInvalidated() ? "Yes" : "No"
        
        return "Cache entries: \(totalItems), Stale entries: \(totalStaleItems), \(ageDescription), Invalidated: \(invalidated)"
    }
    
    // Get detailed cache info for debugging
    func getDetailedCacheInfo() -> String {
        var info = "--- Cache Diagnostic Info ---\n"
        
        // Cache sizes
        info += "Item cache: \(itemsCache.count) entries\n"
        info += "Stats cache: \(statsCache.count) entries\n"
        info += "Misc cache: \(miscCache.count) entries\n"
        info += "Stale caches: \(staleItemsCache.count + staleStatsCache.count + staleMiscCache.count) entries\n"
        
        // Cache keys
        let allKeys = Set(itemsCache.keys)
            .union(statsCache.keys)
            .union(miscCache.keys)
        
        info += "\nCache keys (\(allKeys.count)):\n"
        for key in allKeys.sorted() {
            let timestamp = timestamps[key]
            let age = timestamp != nil ? Date().timeIntervalSince(timestamp!) : 0
            info += "- \(key): \(timestamp != nil ? "\(Int(age))s old" : "no timestamp")\n"
        }
        
        // Invalidation status
        info += "\nInvalidation status:\n"
        info += "- Last reset: \(Date(timeIntervalSince1970: invalidationTimestamp))\n"
        info += "- Is invalidated: \(isCacheInvalidated() ? "Yes" : "No")\n"
        
        return info
    }
}
