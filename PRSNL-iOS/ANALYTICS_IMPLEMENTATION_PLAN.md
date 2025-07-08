# PRSNL iOS: Analytics Implementation Plan

This document outlines a comprehensive strategy for implementing analytics in the PRSNL iOS app, enabling data-driven decision making, user behavior insights, and performance monitoring.

## 1. Analytics Architecture

### 1.1 Overview

The analytics system will collect, process, and analyze user interactions and app performance data while respecting user privacy. This implementation will enable:

- Understanding user behavior and engagement patterns
- Measuring feature adoption and effectiveness
- Identifying performance bottlenecks and crash sources
- Supporting A/B testing of new features
- Tracking conversion and retention metrics
- Informing product development decisions

### 1.2 System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│   PRSNL iOS     │────────►│  Analytics      │────────►│  Data           │
│   Application   │         │  Services       │         │  Visualization  │
│                 │◄────────┤  (Firebase)     │◄────────┤  & Analysis     │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## 2. Analytics Manager Implementation

### 2.1 AnalyticsManager Class

```swift
// IMPLEMENT: Core analytics manager
class AnalyticsManager {
    // Singleton instance
    static let shared = AnalyticsManager()
    
    // Analytics providers
    private var providers: [AnalyticsProvider] = []
    
    // User properties
    private var userProperties: [String: Any] = [:]
    
    // Queue for batching events
    private let eventQueue = DispatchQueue(label: "com.prsnl.analyticsQueue")
    
    // Batch of events waiting to be sent
    private var eventBatch: [(name: String, parameters: [String: Any])] = []
    
    // Timer for flushing events
    private var flushTimer: Timer?
    
    // Constants
    private let flushInterval: TimeInterval = 30.0
    private let maxBatchSize = 20
    
    // Tracking consent status
    private(set) var trackingEnabled = false
    
    // Debug mode flag
    private(set) var debugMode = false
    
    // Private initializer for singleton
    private init() {
        // Set up analytics providers
        setupProviders()
        
        // Start flush timer
        startFlushTimer()
        
        // Get initial tracking consent
        checkTrackingConsent()
    }
    
    // MARK: - Public Methods
    
    // Track screen view
    func trackScreen(name: String, parameters: [String: Any] = [:]) {
        guard trackingEnabled else { return }
        
        var screenParams = parameters
        screenParams["screen_name"] = name
        
        // Track screen view
        logEvent(name: "screen_view", parameters: screenParams)
        
        Logger.analytics.info("Screen tracked: \(name)")
    }
    
    // Track event
    func trackEvent(name: String, parameters: [String: Any] = [:]) {
        guard trackingEnabled else { return }
        
        // Add event to batch
        eventQueue.async { [weak self] in
            guard let self = self else { return }
            
            // Add event to batch
            self.eventBatch.append((name: name, parameters: parameters))
            
            // Flush if batch is full
            if self.eventBatch.count >= self.maxBatchSize {
                self.flushEvents()
            }
        }
        
        Logger.analytics.debug("Event tracked: \(name)")
    }
    
    // Set user ID
    func setUserId(_ userId: String?) {
        guard trackingEnabled else { return }
        
        // Set user ID in all providers
        providers.forEach { $0.setUserId(userId) }
        
        Logger.analytics.info("User ID set: \(userId ?? "nil")")
    }
    
    // Set user property
    func setUserProperty(name: String, value: Any?) {
        guard trackingEnabled else { return }
        
        // Update local cache
        if let value = value {
            userProperties[name] = value
        } else {
            userProperties.removeValue(forKey: name)
        }
        
        // Set in all providers
        providers.forEach { $0.setUserProperty(name: name, value: value) }
        
        Logger.analytics.debug("User property set: \(name) = \(String(describing: value))")
    }
    
    // Enable or disable tracking
    func setTrackingEnabled(_ enabled: Bool) {
        trackingEnabled = enabled
        
        // Store user preference
        UserDefaults.standard.set(enabled, forKey: "analytics_tracking_enabled")
        
        // Update providers
        providers.forEach { $0.setTrackingEnabled(enabled) }
        
        // If tracking was enabled, send cached events
        if enabled {
            flushEvents()
        }
        
        Logger.analytics.info("Tracking \(enabled ? "enabled" : "disabled")")
    }
    
    // Enable or disable debug mode
    func setDebugMode(_ enabled: Bool) {
        debugMode = enabled
        
        // Update providers
        providers.forEach { $0.setDebugMode(enabled) }
        
        Logger.analytics.info("Debug mode \(enabled ? "enabled" : "disabled")")
    }
    
    // Reset all analytics data
    func resetAnalyticsData() {
        // Clear user ID and properties
        setUserId(nil)
        userProperties.forEach { key, _ in
            setUserProperty(name: key, value: nil)
        }
        userProperties.removeAll()
        
        // Reset in all providers
        providers.forEach { $0.resetAnalyticsData() }
        
        Logger.analytics.info("Analytics data reset")
    }
    
    // MARK: - Private Methods
    
    // Set up analytics providers
    private func setupProviders() {
        // Firebase Analytics provider
        if let firebaseProvider = FirebaseAnalyticsProvider() {
            providers.append(firebaseProvider)
        }
        
        // Add more providers as needed
        // providers.append(MixpanelProvider())
        // providers.append(AppsFlyerProvider())
    }
    
    // Check tracking consent
    private func checkTrackingConsent() {
        // Get stored preference
        trackingEnabled = UserDefaults.standard.bool(forKey: "analytics_tracking_enabled")
        
        // Update providers
        providers.forEach { $0.setTrackingEnabled(trackingEnabled) }
    }
    
    // Start flush timer
    private func startFlushTimer() {
        flushTimer = Timer.scheduledTimer(withTimeInterval: flushInterval, repeats: true) { [weak self] _ in
            self?.flushEvents()
        }
    }
    
    // Log event directly (for screen views and immediate events)
    private func logEvent(name: String, parameters: [String: Any]) {
        // Log in all providers
        providers.forEach { $0.trackEvent(name: name, parameters: parameters) }
    }
    
    // Flush queued events
    private func flushEvents() {
        eventQueue.async { [weak self] in
            guard let self = self, !self.eventBatch.isEmpty else { return }
            
            // Get current batch
            let batch = self.eventBatch
            self.eventBatch = []
            
            // Log each event
            for event in batch {
                self.logEvent(name: event.name, parameters: event.parameters)
            }
            
            Logger.analytics.debug("Flushed \(batch.count) events")
        }
    }
    
    // Deinitialize
    deinit {
        flushTimer?.invalidate()
        flushEvents()
    }
}

// MARK: - Analytics Provider Protocol

// Protocol for analytics providers
protocol AnalyticsProvider {
    // Initialize provider
    init?()
    
    // Track event
    func trackEvent(name: String, parameters: [String: Any])
    
    // Set user ID
    func setUserId(_ userId: String?)
    
    // Set user property
    func setUserProperty(name: String, value: Any?)
    
    // Enable or disable tracking
    func setTrackingEnabled(_ enabled: Bool)
    
    // Enable or disable debug mode
    func setDebugMode(_ enabled: Bool)
    
    // Reset analytics data
    func resetAnalyticsData()
}
```

### 2.2 Firebase Analytics Provider

```swift
// IMPLEMENT: Firebase Analytics provider
class FirebaseAnalyticsProvider: AnalyticsProvider {
    // Firebase Analytics instance
    private let analytics: Analytics.Type = Analytics.self
    
    // Initialize provider
    required init?() {
        // Configure Firebase
        FirebaseApp.configure()
        
        // Enable analytics collection
        analytics.setAnalyticsCollectionEnabled(true)
        
        return true
    }
    
    // Track event
    func trackEvent(name: String, parameters: [String: Any]) {
        // Convert parameters to Firebase format
        let firebaseParams = parameters.compactMapValues { value in
            return convertToFirebaseValue(value)
        }
        
        // Log event
        analytics.logEvent(name, parameters: firebaseParams)
    }
    
    // Set user ID
    func setUserId(_ userId: String?) {
        analytics.setUserID(userId)
    }
    
    // Set user property
    func setUserProperty(name: String, value: Any?) {
        if let value = value {
            // Convert value to string
            let stringValue = String(describing: value)
            analytics.setUserProperty(stringValue, forName: name)
        } else {
            analytics.setUserProperty(nil, forName: name)
        }
    }
    
    // Enable or disable tracking
    func setTrackingEnabled(_ enabled: Bool) {
        analytics.setAnalyticsCollectionEnabled(enabled)
    }
    
    // Enable or disable debug mode
    func setDebugMode(_ enabled: Bool) {
        // In Firebase, this is set via command line arguments
        // or Firebase console settings
    }
    
    // Reset analytics data
    func resetAnalyticsData() {
        // Reset user ID
        analytics.setUserID(nil)
        
        // Clear all user properties
        // Firebase doesn't have a direct method to clear all properties,
        // so we would need to manually clear each known property
    }
    
    // Convert value to Firebase-compatible value
    private func convertToFirebaseValue(_ value: Any) -> Any? {
        switch value {
        case is String, is Int, is Double, is Float, is Bool, is NSNumber:
            return value
        case let date as Date:
            return date.timeIntervalSince1970
        case let array as [Any]:
            return array.map { String(describing: $0) }.joined(separator: ",")
        case let dictionary as [String: Any]:
            return dictionary.map { "\($0.key):\($0.value)" }.joined(separator: ",")
        default:
            return String(describing: value)
        }
    }
}
```

### 2.3 Analytics Extensions for SwiftUI Views

```swift
// IMPLEMENT: SwiftUI View extension for analytics tracking
extension View {
    // Track screen view
    func trackScreenView(_ name: String, parameters: [String: Any] = [:]) -> some View {
        return self.onAppear {
            AnalyticsManager.shared.trackScreen(name: name, parameters: parameters)
        }
    }
    
    // Track event on tap
    func trackOnTap(eventName: String, parameters: [String: Any] = [:]) -> some View {
        return self.simultaneousGesture(TapGesture().onEnded {
            AnalyticsManager.shared.trackEvent(name: eventName, parameters: parameters)
        })
    }
    
    // Track event on appear
    func trackOnAppear(eventName: String, parameters: [String: Any] = [:]) -> some View {
        return self.onAppear {
            AnalyticsManager.shared.trackEvent(name: eventName, parameters: parameters)
        }
    }
    
    // Track event on disappear
    func trackOnDisappear(eventName: String, parameters: [String: Any] = [:]) -> some View {
        return self.onDisappear {
            AnalyticsManager.shared.trackEvent(name: eventName, parameters: parameters)
        }
    }
}
```

## 3. Analytics Event Tracking

### 3.1 Event Naming Conventions

All events should follow a consistent naming convention:

1. Use snake_case for event names
2. Use descriptive, but concise names
3. Follow the pattern: `object_action` (e.g., `item_created`, `search_performed`)
4. Group related events with common prefixes

### 3.2 Standard Events

```swift
// IMPLEMENT: Standard event definitions
struct AnalyticsEvents {
    // Session events
    struct Session {
        static let start = "session_start"
        static let end = "session_end"
    }
    
    // Authentication events
    struct Auth {
        static let login = "auth_login"
        static let logout = "auth_logout"
        static let signUp = "auth_sign_up"
        static let passwordReset = "auth_password_reset"
    }
    
    // Item events
    struct Item {
        static let created = "item_created"
        static let viewed = "item_viewed"
        static let updated = "item_updated"
        static let deleted = "item_deleted"
        static let shared = "item_shared"
    }
    
    // Search events
    struct Search {
        static let performed = "search_performed"
        static let resultsViewed = "search_results_viewed"
        static let filtered = "search_filtered"
    }
    
    // Timeline events
    struct Timeline {
        static let refreshed = "timeline_refreshed"
        static let itemSelected = "timeline_item_selected"
        static let scrolled = "timeline_scrolled"
    }
    
    // Settings events
    struct Settings {
        static let opened = "settings_opened"
        static let changed = "settings_changed"
    }
    
    // Error events
    struct Error {
        static let network = "error_network"
        static let api = "error_api"
        static let app = "error_app"
    }
    
    // Performance events
    struct Performance {
        static let slowOperation = "performance_slow_operation"
        static let memoryWarning = "performance_memory_warning"
    }
}

// IMPLEMENT: Standard parameter definitions
struct AnalyticsParameters {
    // Common parameters
    static let itemId = "item_id"
    static let userId = "user_id"
    static let source = "source"
    static let timestamp = "timestamp"
    static let duration = "duration"
    static let status = "status"
    static let errorCode = "error_code"
    static let errorMessage = "error_message"
    
    // Authentication parameters
    static let authMethod = "auth_method"
    
    // Item parameters
    static let itemTitle = "item_title"
    static let itemType = "item_type"
    static let itemTags = "item_tags"
    
    // Search parameters
    static let searchQuery = "search_query"
    static let searchResultCount = "search_result_count"
    static let searchFilters = "search_filters"
    
    // Performance parameters
    static let memoryUsage = "memory_usage"
    static let cpuUsage = "cpu_usage"
    static let responseTime = "response_time"
}
```

### 3.3 ViewModels Integration

```swift
// IMPLEMENT: TimelineViewModel with analytics integration
class TimelineViewModel: ObservableObject {
    // Existing properties
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var error: Error?
    
    // Dependencies
    private let apiClient: APIClient
    private let coreDataManager: CoreDataManager
    private let analyticsManager = AnalyticsManager.shared
    
    // Initialize with dependencies
    init(apiClient: APIClient = APIClient.shared, coreDataManager: CoreDataManager = CoreDataManager.shared) {
        self.apiClient = apiClient
        self.coreDataManager = coreDataManager
    }
    
    // Load timeline data
    func loadTimeline() async {
        // Track event start
        let startTime = Date()
        
        DispatchQueue.main.async {
            self.isLoading = true
            self.error = nil
        }
        
        do {
            // Fetch timeline from API
            let response = try await apiClient.fetchTimeline(page: 1, limit: 20)
            
            // Save to Core Data
            try await coreDataManager.saveItems(response.items)
            
            // Update UI
            DispatchQueue.main.async {
                self.items = response.items
                self.isLoading = false
            }
            
            // Track successful timeline load
            let duration = Date().timeIntervalSince(startTime)
            analyticsManager.trackEvent(
                name: AnalyticsEvents.Timeline.refreshed,
                parameters: [
                    AnalyticsParameters.status: "success",
                    AnalyticsParameters.duration: duration,
                    AnalyticsParameters.itemId: response.items.map { $0.id }
                ]
            )
        } catch {
            // Update UI
            DispatchQueue.main.async {
                self.error = error
                self.isLoading = false
            }
            
            // Track error
            let duration = Date().timeIntervalSince(startTime)
            analyticsManager.trackEvent(
                name: AnalyticsEvents.Error.api,
                parameters: [
                    AnalyticsParameters.status: "error",
                    AnalyticsParameters.errorMessage: error.localizedDescription,
                    AnalyticsParameters.duration: duration,
                    AnalyticsParameters.source: "TimelineViewModel.loadTimeline"
                ]
            )
        }
    }
    
    // Select item
    func selectItem(_ item: Item) {
        // Track item selection
        analyticsManager.trackEvent(
            name: AnalyticsEvents.Timeline.itemSelected,
            parameters: [
                AnalyticsParameters.itemId: item.id,
                AnalyticsParameters.itemTitle: item.title,
                AnalyticsParameters.source: "timeline"
            ]
        )
    }
}

// IMPLEMENT: ItemDetailViewModel with analytics integration
class ItemDetailViewModel: ObservableObject {
    // Existing properties
    @Published var item: Item
    @Published var isLoading = false
    @Published var error: Error?
    
    // Dependencies
    private let apiClient: APIClient
    private let coreDataManager: CoreDataManager
    private let analyticsManager = AnalyticsManager.shared
    
    // View appeared flag
    private var hasAppeared = false
    
    // Initialize with item
    init(item: Item, apiClient: APIClient = APIClient.shared, coreDataManager: CoreDataManager = CoreDataManager.shared) {
        self.item = item
        self.apiClient = apiClient
        self.coreDataManager = coreDataManager
    }
    
    // Track view appeared
    func onViewAppear() {
        // Only track first appearance
        guard !hasAppeared else { return }
        hasAppeared = true
        
        // Track item view
        analyticsManager.trackEvent(
            name: AnalyticsEvents.Item.viewed,
            parameters: [
                AnalyticsParameters.itemId: item.id,
                AnalyticsParameters.itemTitle: item.title,
                AnalyticsParameters.itemType: item.type ?? "unknown",
                AnalyticsParameters.itemTags: item.tags ?? []
            ]
        )
    }
    
    // Update item
    func updateItem(_ updatedItem: Item) {
        // Track update time
        let startTime = Date()
        
        Task {
            do {
                // Save to Core Data
                try await coreDataManager.saveItem(updatedItem)
                
                // Update local state
                DispatchQueue.main.async {
                    self.item = updatedItem
                }
                
                // Track successful update
                let duration = Date().timeIntervalSince(startTime)
                analyticsManager.trackEvent(
                    name: AnalyticsEvents.Item.updated,
                    parameters: [
                        AnalyticsParameters.itemId: updatedItem.id,
                        AnalyticsParameters.duration: duration,
                        AnalyticsParameters.status: "success"
                    ]
                )
            } catch {
                // Track error
                let duration = Date().timeIntervalSince(startTime)
                analyticsManager.trackEvent(
                    name: AnalyticsEvents.Error.app,
                    parameters: [
                        AnalyticsParameters.itemId: updatedItem.id,
                        AnalyticsParameters.errorMessage: error.localizedDescription,
                        AnalyticsParameters.duration: duration,
                        AnalyticsParameters.source: "ItemDetailViewModel.updateItem"
                    ]
                )
            }
        }
    }
    
    // Delete item
    func deleteItem() {
        // Track delete time
        let startTime = Date()
        
        Task {
            do {
                // Delete from Core Data
                try await coreDataManager.deleteItem(id: item.id)
                
                // Track successful deletion
                let duration = Date().timeIntervalSince(startTime)
                analyticsManager.trackEvent(
                    name: AnalyticsEvents.Item.deleted,
                    parameters: [
                        AnalyticsParameters.itemId: item.id,
                        AnalyticsParameters.duration: duration,
                        AnalyticsParameters.status: "success"
                    ]
                )
            } catch {
                // Track error
                let duration = Date().timeIntervalSince(startTime)
                analyticsManager.trackEvent(
                    name: AnalyticsEvents.Error.app,
                    parameters: [
                        AnalyticsParameters.itemId: item.id,
                        AnalyticsParameters.errorMessage: error.localizedDescription,
                        AnalyticsParameters.duration: duration,
                        AnalyticsParameters.source: "ItemDetailViewModel.deleteItem"
                    ]
                )
            }
        }
    }
    
    // Share item
    func shareItem() {
        // Track share event
        analyticsManager.trackEvent(
            name: AnalyticsEvents.Item.shared,
            parameters: [
                AnalyticsParameters.itemId: item.id,
                AnalyticsParameters.itemTitle: item.title
            ]
        )
    }
}
```

### 3.4 SwiftUI Views Integration

```swift
// IMPLEMENT: TimelineView with analytics integration
struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    
    var body: some View {
        VStack {
            // List of items
            if viewModel.items.isEmpty && !viewModel.isLoading {
                // Empty state
                EmptyStateView()
                    .trackOnAppear(
                        eventName: "timeline_empty_state_shown"
                    )
            } else {
                // List of items
                List(viewModel.items) { item in
                    NavigationLink(destination: ItemDetailView(item: item)) {
                        ItemRowView(item: item)
                    }
                    .onTapGesture {
                        viewModel.selectItem(item)
                    }
                }
            }
        }
        .navigationTitle("Timeline")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: {
                    // Create new item
                }) {
                    Image(systemName: "plus")
                }
                .trackOnTap(
                    eventName: "timeline_create_button_tapped"
                )
            }
        }
        .refreshable {
            Task {
                await viewModel.loadTimeline()
            }
        }
        .trackScreenView(
            "Timeline",
            parameters: [
                "item_count": viewModel.items.count
            ]
        )
        .onAppear {
            Task {
                await viewModel.loadTimeline()
            }
        }
    }
}

// IMPLEMENT: ItemDetailView with analytics integration
struct ItemDetailView: View {
    @StateObject private var viewModel: ItemDetailViewModel
    
    init(item: Item) {
        self._viewModel = StateObject(wrappedValue: ItemDetailViewModel(item: item))
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Title
                Text(viewModel.item.title)
                    .font(.title)
                    .fontWeight(.bold)
                
                // Content
                Text(viewModel.item.content)
                    .font(.body)
                
                // Actions
                HStack {
                    Button(action: {
                        viewModel.shareItem()
                    }) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                    .trackOnTap(
                        eventName: AnalyticsEvents.Item.shared,
                        parameters: [
                            AnalyticsParameters.itemId: viewModel.item.id
                        ]
                    )
                    
                    Spacer()
                    
                    Button(action: {
                        // Edit item
                    }) {
                        Label("Edit", systemImage: "pencil")
                    }
                    .trackOnTap(
                        eventName: "item_edit_button_tapped",
                        parameters: [
                            AnalyticsParameters.itemId: viewModel.item.id
                        ]
                    )
                }
                .padding(.top)
            }
            .padding()
        }
        .navigationTitle("Item Details")
        .trackScreenView(
            "ItemDetail",
            parameters: [
                AnalyticsParameters.itemId: viewModel.item.id,
                AnalyticsParameters.itemTitle: viewModel.item.title
            ]
        )
        .onAppear {
            viewModel.onViewAppear()
        }
    }
}
```

## 4. Performance Tracking

### 4.1 Network Performance Monitoring

```swift
// IMPLEMENT: APIClient extension for performance tracking
extension APIClient {
    // Send request with performance tracking
    func sendRequestWithPerformanceTracking<T: Decodable>(_ request: APIRequest, responseType: T.Type) async throws -> T {
        // Start tracking time
        let startTime = Date()
        
        do {
            // Send request
            let response = try await sendRequest(request, responseType: responseType)
            
            // Calculate response time
            let responseTime = Date().timeIntervalSince(startTime) * 1000 // milliseconds
            
            // Track performance
            trackNetworkPerformance(
                endpoint: request.endpoint,
                method: request.method.rawValue,
                responseTime: responseTime,
                status: "success"
            )
            
            return response
        } catch {
            // Calculate response time
            let responseTime = Date().timeIntervalSince(startTime) * 1000 // milliseconds
            
            // Track performance
            trackNetworkPerformance(
                endpoint: request.endpoint,
                method: request.method.rawValue,
                responseTime: responseTime,
                status: "error",
                error: error
            )
            
            throw error
        }
    }
    
    // Track network performance
    private func trackNetworkPerformance(endpoint: String, method: String, responseTime: TimeInterval, status: String, error: Error? = nil) {
        var parameters: [String: Any] = [
            "endpoint": endpoint,
            "method": method,
            AnalyticsParameters.responseTime: responseTime,
            AnalyticsParameters.status: status
        ]
        
        // Add error details if available
        if let error = error {
            parameters[AnalyticsParameters.errorMessage] = error.localizedDescription
            
            if let apiError = error as? APIError {
                parameters[AnalyticsParameters.errorCode] = apiError.errorCode
            }
        }
        
        // Log slow requests (>500ms)
        if responseTime > 500 {
            AnalyticsManager.shared.trackEvent(
                name: AnalyticsEvents.Performance.slowOperation,
                parameters: parameters
            )
        }
        
        // Log all network requests (if enabled)
        if AnalyticsManager.shared.debugMode {
            AnalyticsManager.shared.trackEvent(
                name: "network_request",
                parameters: parameters
            )
        }
    }
}
```

### 4.2 App Performance Monitoring

```swift
// IMPLEMENT: Performance monitoring extension
class PerformanceMonitor {
    // Singleton instance
    static let shared = PerformanceMonitor()
    
    // Memory warning count
    private var memoryWarningCount = 0
    
    // Analytics manager
    private let analyticsManager = AnalyticsManager.shared
    
    // Initialize
    private init() {
        // Register for memory warning notifications
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleMemoryWarning),
            name: UIApplication.didReceiveMemoryWarningNotification,
            object: nil
        )
    }
    
    // MARK: - Public Methods
    
    // Track operation performance
    func trackOperation(name: String, function: () -> Void) {
        // Start tracking time
        let startTime = Date()
        
        // Execute function
        function()
        
        // Calculate duration
        let duration = Date().timeIntervalSince(startTime) * 1000 // milliseconds
        
        // Track performance
        trackOperationPerformance(name: name, duration: duration)
    }
    
    // Track async operation performance
    func trackAsyncOperation<T>(name: String, function: () async throws -> T) async rethrows -> T {
        // Start tracking time
        let startTime = Date()
        
        do {
            // Execute function
            let result = try await function()
            
            // Calculate duration
            let duration = Date().timeIntervalSince(startTime) * 1000 // milliseconds
            
            // Track performance
            trackOperationPerformance(name: name, duration: duration)
            
            return result
        } catch {
            // Calculate duration
            let duration = Date().timeIntervalSince(startTime) * 1000 // milliseconds
            
            // Track performance with error
            trackOperationPerformance(
                name: name,
                duration: duration,
                status: "error",
                error: error
            )
            
            throw error
        }
    }
    
    // MARK: - Private Methods
    
    // Track operation performance
    private func trackOperationPerformance(name: String, duration: TimeInterval, status: String = "success", error: Error? = nil) {
        var parameters: [String: Any] = [
            "operation_name": name,
            AnalyticsParameters.duration: duration,
            AnalyticsParameters.status: status
        ]
        
        // Add memory usage
        if let memoryUsage = getMemoryUsage() {
            parameters[AnalyticsParameters.memoryUsage] = memoryUsage
        }
        
        // Add CPU usage
        if let cpuUsage = getCPUUsage() {
            parameters[AnalyticsParameters.cpuUsage] = cpuUsage
        }
        
        // Add error details if available
        if let error = error {
            parameters[AnalyticsParameters.errorMessage] = error.localizedDescription
        }
        
        // Log slow operations (>100ms)
        if duration > 100 {
            analyticsManager.trackEvent(
                name: AnalyticsEvents.Performance.slowOperation,
                parameters: parameters
            )
        }
        
        // Log all operations (if debug mode)
        if analyticsManager.debugMode {
            analyticsManager.trackEvent(
                name: "performance_operation",
                parameters: parameters
            )
        }
    }
    
    // Handle memory warning
    @objc private func handleMemoryWarning() {
        memoryWarningCount += 1
        
        var parameters: [String: Any] = [
            "memory_warning_count": memoryWarningCount
        ]
        
        // Add memory usage
        if let memoryUsage = getMemoryUsage() {
            parameters[AnalyticsParameters.memoryUsage] = memoryUsage
        }
        
        // Track memory warning
        analyticsManager.trackEvent(
            name: AnalyticsEvents.Performance.memoryWarning,
            parameters: parameters
        )
    }
    
    // Get memory usage
    private func getMemoryUsage() -> Double? {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        
        let kerr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(
                    mach_task_self_,
                    task_flavor_t(MACH_TASK_BASIC_INFO),
                    $0,
                    &count
                )
            }
        }
        
        if kerr == KERN_SUCCESS {
            return Double(info.resident_size) / (1024 * 1024) // MB
        }
        
        return nil
    }
    
    // Get CPU usage
    private func getCPUUsage() -> Double? {
        var totalUsage: Double = 0
        var threadList: thread_act_array_t?
        var threadCount: mach_msg_type_number_t = 0
        
        let result = task_threads(mach_task_self_, &threadList, &threadCount)
        
        if result == KERN_SUCCESS, let threadList = threadList {
            for i in 0..<Int(threadCount) {
                var threadInfo = thread_basic_info()
                var threadInfoCount = mach_msg_type_number_t(THREAD_BASIC_INFO_COUNT)
                
                let threadResult = withUnsafeMutablePointer(to: &threadInfo) {
                    $0.withMemoryRebound(to: integer_t.self, capacity: Int(threadInfoCount)) {
                        thread_info(
                            threadList[i],
                            thread_flavor_t(THREAD_BASIC_INFO),
                            $0,
                            &threadInfoCount
                        )
                    }
                }
                
                if threadResult == KERN_SUCCESS {
                    let cpuUsage = Double(threadInfo.cpu_usage) / Double(TH_USAGE_SCALE)
                    totalUsage += cpuUsage
                }
            }
            
            // Free the thread list
            vm_deallocate(
                mach_task_self_,
                vm_address_t(UnsafePointer(threadList).pointee),
                vm_size_t(threadCount) * vm_size_t(MemoryLayout<thread_act_t>.size)
            )
        }
        
        return totalUsage * 100 // percentage
    }
}
```

## 5. Crash Reporting

### 5.1 Firebase Crashlytics Integration

```swift
// IMPLEMENT: Crashlytics integration
class CrashReporter {
    // Singleton instance
    static let shared = CrashReporter()
    
    // Enable crash reporting
    private var isEnabled = true
    
    // Initialize
    private init() {
        // Set up crash reporting
        setupCrashlytics()
    }
    
    // MARK: - Public Methods
    
    // Record non-fatal error
    func recordError(_ error: Error, context: [String: Any]? = nil) {
        guard isEnabled else { return }
        
        // Record in Crashlytics
        Crashlytics.crashlytics().record(error: error, userInfo: context)
        
        // Log in analytics
        AnalyticsManager.shared.trackEvent(
            name: AnalyticsEvents.Error.app,
            parameters: [
                AnalyticsParameters.errorMessage: error.localizedDescription,
                AnalyticsParameters.context: context ?? [:]
            ]
        )
    }
    
    // Set user identifier
    func setUserIdentifier(_ identifier: String?) {
        guard isEnabled else { return }
        
        Crashlytics.crashlytics().setUserID(identifier ?? "")
    }
    
    // Set custom key
    func setCustomKey(_ key: String, value: Any?) {
        guard isEnabled else { return }
        
        if let value = value {
            if let stringValue = value as? String {
                Crashlytics.crashlytics().setCustomValue(stringValue, forKey: key)
            } else if let intValue = value as? Int {
                Crashlytics.crashlytics().setCustomValue(intValue, forKey: key)
            } else if let boolValue = value as? Bool {
                Crashlytics.crashlytics().setCustomValue(boolValue, forKey: key)
            } else if let doubleValue = value as? Double {
                Crashlytics.crashlytics().setCustomValue(doubleValue, forKey: key)
            } else if let floatValue = value as? Float {
                Crashlytics.crashlytics().setCustomValue(floatValue, forKey: key)
            } else {
                Crashlytics.crashlytics().setCustomValue(String(describing: value), forKey: key)
            }
        }
    }
    
    // Set crash reporting enabled
    func setCrashReportingEnabled(_ enabled: Bool) {
        isEnabled = enabled
        Crashlytics.crashlytics().setCrashlyticsCollectionEnabled(enabled)
    }
    
    // Log a message to the crash report
    func log(_ message: String) {
        guard isEnabled else { return }
        
        Crashlytics.crashlytics().log(message)
    }
    
    // MARK: - Private Methods
    
    // Set up Crashlytics
    private func setupCrashlytics() {
        // Enable Crashlytics
        Crashlytics.crashlytics().setCrashlyticsCollectionEnabled(true)
        
        // Set app version
        if let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String,
           let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String {
            setCustomKey("app_version", value: "\(version) (\(build))")
        }
    }
}
```

### 5.2 Error Handling Integration

```swift
// IMPLEMENT: Global error handler
class ErrorHandler {
    // Singleton instance
    static let shared = ErrorHandler()
    
    // Crash reporter
    private let crashReporter = CrashReporter.shared
    
    // Analytics manager
    private let analyticsManager = AnalyticsManager.shared
    
    // Initialize
    private init() {
        // Set up global error handler
        setupGlobalErrorHandler()
    }
    
    // MARK: - Public Methods
    
    // Handle error
    func handleError(_ error: Error, source: String, context: [String: Any]? = nil) {
        // Create error context
        var errorContext: [String: Any] = [
            "source": source
        ]
        
        // Add additional context if provided
        if let context = context {
            for (key, value) in context {
                errorContext[key] = value
            }
        }
        
        // Record error in crash reporter
        crashReporter.recordError(error, context: errorContext)
        
        // Track error in analytics
        trackError(error, source: source, context: errorContext)
        
        // Log error
        Logger.error.error("\(source): \(error.localizedDescription)")
    }
    
    // MARK: - Private Methods
    
    // Set up global error handler
    private func setupGlobalErrorHandler() {
        // Set uncaught exception handler
        NSSetUncaughtExceptionHandler { exception in
            let error = NSError(
                domain: "UncaughtException",
                code: 0,
                userInfo: [
                    NSLocalizedDescriptionKey: exception.reason ?? "Unknown exception",
                    "ExceptionName": exception.name.rawValue,
                    "ExceptionCallStack": exception.callStackSymbols
                ]
            )
            
            self.crashReporter.recordError(error, context: ["fatal": true])
        }
    }
    
    // Track error in analytics
    private func trackError(_ error: Error, source: String, context: [String: Any]) {
        // Determine error type
        let errorType: String
        if let _ = error as? URLError {
            errorType = AnalyticsEvents.Error.network
        } else if let _ = error as? APIError {
            errorType = AnalyticsEvents.Error.api
        } else {
            errorType = AnalyticsEvents.Error.app
        }
        
        // Create parameters
        var parameters: [String: Any] = [
            AnalyticsParameters.errorMessage: error.localizedDescription,
            AnalyticsParameters.source: source
        ]
        
        // Add context
        for (key, value) in context {
            parameters[key] = value
        }
        
        // Track error event
        analyticsManager.trackEvent(
            name: errorType,
            parameters: parameters
        )
    }
}
```

## 6. User Opt-In and Privacy

### 6.1 Analytics Consent View

```swift
// IMPLEMENT: Analytics consent view
struct AnalyticsConsentView: View {
    @AppStorage("analytics_tracking_enabled") private var trackingEnabled = false
    @State private var isShowingDetails = false
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 60))
                .foregroundColor(.blue)
                .padding(.bottom, 10)
            
            Text("Help Us Improve")
                .font(.title)
                .bold()
            
            Text("We collect anonymous usage data to improve your experience with the app. This helps us understand how you use the app and identify areas for improvement.")
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            // Consent toggle
            VStack(alignment: .leading) {
                Toggle("Enable Analytics", isOn: $trackingEnabled)
                    .onChange(of: trackingEnabled) { oldValue, newValue in
                        AnalyticsManager.shared.setTrackingEnabled(newValue)
                    }
                
                Text("You can change this setting later in the app preferences.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color.secondary.opacity(0.1))
            .cornerRadius(10)
            
            // Privacy details button
            Button("What data do we collect?") {
                isShowingDetails = true
            }
            .padding(.top, 10)
        }
        .padding()
        .frame(maxWidth: 400)
        .sheet(isPresented: $isShowingDetails) {
            AnalyticsDetailsView()
        }
        .onAppear {
            // Set initial tracking state
            AnalyticsManager.shared.setTrackingEnabled(trackingEnabled)
        }
    }
}

// IMPLEMENT: Analytics details view
struct AnalyticsDetailsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Data collection section
                    Section {
                        Text("We collect the following anonymous data:")
                            .font(.headline)
                            .padding(.bottom, 5)
                        
                        BulletPoint(text: "App usage information, such as screens viewed and buttons tapped")
                        BulletPoint(text: "Performance metrics, such as app speed and crashes")
                        BulletPoint(text: "Device information, such as model and iOS version")
                        BulletPoint(text: "Feature usage, such as which features you use most")
                    }
                    .padding(.bottom, 10)
                    
                    // What we don't collect section
                    Section {
                        Text("We do NOT collect:")
                            .font(.headline)
                            .padding(.bottom, 5)
                        
                        BulletPoint(text: "Personal identifiable information")
                        BulletPoint(text: "The content of your items or notes")
                        BulletPoint(text: "Your contact information")
                        BulletPoint(text: "Your location")
                    }
                    .padding(.bottom, 10)
                    
                    // How we use data section
                    Section {
                        Text("How we use this data:")
                            .font(.headline)
                            .padding(.bottom, 5)
                        
                        BulletPoint(text: "Improve app performance and stability")
                        BulletPoint(text: "Identify and fix bugs faster")
                        BulletPoint(text: "Understand which features are most valuable")
                        BulletPoint(text: "Make informed decisions about future updates")
                    }
                    
                    // Data storage
                    Section {
                        Text("Data Storage:")
                            .font(.headline)
                            .padding(.bottom, 5)
                        
                        Text("We use Firebase Analytics to process and store this data. The data is stored securely and in accordance with Google's privacy policy.")
                    }
                    .padding(.top, 10)
                }
                .padding()
            }
            .navigationTitle("Analytics Information")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// Helper view for bullet points
struct BulletPoint: View {
    let text: String
    
    var body: some View {
        HStack(alignment: .top) {
            Text("•")
                .padding(.trailing, 5)
            Text(text)
            Spacer()
        }
    }
}
```

### 6.2 Privacy Settings in the App

```swift
// IMPLEMENT: Privacy settings view
struct PrivacySettingsView: View {
    @AppStorage("analytics_tracking_enabled") private var trackingEnabled = false
    @AppStorage("crash_reporting_enabled") private var crashReportingEnabled = true
    
    var body: some View {
        List {
            Section(header: Text("Data Collection")) {
                // Analytics toggle
                Toggle("Analytics", isOn: $trackingEnabled)
                    .onChange(of: trackingEnabled) { oldValue, newValue in
                        AnalyticsManager.shared.setTrackingEnabled(newValue)
                    }
                
                // Description
                Text("Collect anonymous usage data to help us improve the app")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Section(header: Text("Crash Reporting")) {
                // Crash reporting toggle
                Toggle("Crash Reporting", isOn: $crashReportingEnabled)
                    .onChange(of: crashReportingEnabled) { oldValue, newValue in
                        CrashReporter.shared.setCrashReportingEnabled(newValue)
                    }
                
                // Description
                Text("Send anonymous crash reports to help us identify and fix bugs")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Section(header: Text("Your Data")) {
                // Reset analytics data button
                Button("Reset Analytics Data") {
                    resetAnalyticsData()
                }
                .foregroundColor(.red)
                
                // Privacy policy button
                NavigationLink(destination: PrivacyPolicyView()) {
                    Text("Privacy Policy")
                }
            }
        }
        .navigationTitle("Privacy")
        .onAppear {
            // Ensure settings are in sync with manager
            AnalyticsManager.shared.setTrackingEnabled(trackingEnabled)
            CrashReporter.shared.setCrashReportingEnabled(crashReportingEnabled)
        }
    }
    
    // Reset analytics data
    private func resetAnalyticsData() {
        AnalyticsManager.shared.resetAnalyticsData()
        
        // Show confirmation
        // (Would use an alert or toast in the actual implementation)
    }
}

// IMPLEMENT: Privacy policy view
struct PrivacyPolicyView: View {
    var body: some View {
        ScrollView {
            Text(privacyPolicyText)
                .padding()
        }
        .navigationTitle("Privacy Policy")
    }
    
    // Privacy policy text
    private var privacyPolicyText: String {
        """
        # Privacy Policy
        
        ## Introduction
        
        This privacy policy explains how we collect, use, and protect your data when you use the PRSNL app.
        
        ## Data We Collect
        
        We collect the following types of data:
        
        - **Usage Data**: Information about how you use the app, such as screens viewed and features used.
        - **Performance Data**: Technical information about app performance and crashes.
        - **Device Information**: Technical details about your device, such as model and iOS version.
        
        ## How We Use Your Data
        
        We use this data to:
        
        - Improve the app's performance and stability
        - Identify and fix bugs
        - Understand which features are most valuable
        - Make informed decisions about future updates
        
        ## Data Storage
        
        We use Firebase Analytics and Crashlytics to process and store this data. The data is stored securely and in accordance with Google's privacy policy.
        
        ## Your Rights
        
        You have the right to:
        
        - Opt out of data collection through the app settings
        - Request the deletion of your data
        - Access your data
        
        ## Changes to This Policy
        
        We may update this privacy policy from time to time. We will notify you of any changes by posting the new policy in the app.
        
        ## Contact Us
        
        If you have any questions about this privacy policy, please contact us at:
        
        privacy@prsnl.com
        """
    }
}
```

## 7. Analytics Dashboard and Reporting

### 7.1 Key Metrics and KPIs

1. **User Engagement**
   - Daily/Monthly Active Users (DAU/MAU)
   - Session duration and frequency
   - Retention rates (1-day, 7-day, 30-day)
   - Feature usage rates

2. **Performance Metrics**
   - App crash rate
   - API response times
   - App load time
   - Memory usage

3. **Conversion Metrics**
   - Registration completion rate
   - Onboarding completion rate
   - Premium feature adoption rate

4. **Content Metrics**
   - Item creation rate
   - Content engagement (views, edits, shares)
   - Search usage and effectiveness

### 7.2 Firebase Analytics Dashboard Setup

The Firebase Analytics dashboard should be configured with the following:

1. **Custom Dashboards**
   - User Engagement Dashboard
   - Performance Monitoring Dashboard
   - Conversion Funnel Dashboard
   - Content Usage Dashboard

2. **Custom Dimensions**
   - User Type (free, premium)
   - Subscription Status
   - App Version
   - Device Type
   - Connection Type

3. **Retention Cohorts**
   - New User Cohort
   - Feature Adoption Cohort
   - Subscription Cohort

4. **Conversion Funnels**
   - Registration Funnel
   - Onboarding Funnel
   - Feature Discovery Funnel
   - Premium Conversion Funnel

### 7.3 Data Export and Integration

For advanced analytics and integration with other systems, we will:

1. **Set up BigQuery Export**
   - Enable daily export of Firebase Analytics data to BigQuery
   - Create custom queries for detailed analysis

2. **Create Data Studio Reports**
   - Executive Summary Dashboard
   - Weekly Performance Report
   - User Behavior Analysis
   - Feature Adoption Report

3. **API Integrations**
   - Connect with customer support systems
   - Integrate with marketing automation tools
   - Feed data to product analytics platforms

## 8. Implementation Checklist

### 8.1 Initial Setup

- [ ] Add Firebase dependencies to the project
- [ ] Configure Firebase in AppDelegate
- [ ] Implement AnalyticsManager class
- [ ] Set up FirebaseAnalyticsProvider

### 8.2 Core Implementation

- [ ] Implement standard events and parameters
- [ ] Add analytics tracking to view models
- [ ] Add screen tracking to main views
- [ ] Implement SwiftUI tracking extensions

### 8.3 Advanced Features

- [ ] Set up crash reporting
- [ ] Implement performance monitoring
- [ ] Create user consent flow
- [ ] Add privacy settings to the app

### 8.4 Testing and Validation

- [ ] Verify events are firing correctly in debug mode
- [ ] Test opt-in/opt-out functionality
- [ ] Validate performance tracking
- [ ] Test crash reporting

### 8.5 Dashboard and Reporting

- [ ] Configure Firebase Analytics dashboard
- [ ] Set up custom dashboards
- [ ] Create custom reports
- [ ] Set up data export to BigQuery (if needed)

## 9. Future Enhancements

- A/B testing implementation using Firebase Remote Config
- User segmentation for targeted analytics
- Advanced funnel analysis
- Machine learning-based user behavior prediction
- Real-time analytics dashboards
- Custom analytics events for business-specific metrics