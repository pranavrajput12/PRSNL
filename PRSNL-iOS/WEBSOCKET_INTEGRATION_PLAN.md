# PRSNL iOS: WebSocket Integration Plan

This document outlines a comprehensive strategy for implementing WebSocket-based real-time communication in the PRSNL iOS app, enabling immediate data synchronization, notifications, and collaborative features.

## 1. WebSocket Architecture

### 1.1 Overview

The WebSocket integration will establish persistent, bidirectional communication between the PRSNL iOS app and the backend server, allowing for real-time updates without polling. This will enable:

- Immediate synchronization of changes
- Real-time notifications of remote updates
- Potential collaborative editing features
- Status indicators showing online presence

### 1.2 System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│   PRSNL iOS     │◄────────┤  WebSocket      │◄────────┤  PRSNL Backend  │
│   Application   │         │  Server         │         │  Services       │
│                 │────────►│                 │────────►│                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    ▲
                                    │
                                    ▼
                            ┌─────────────────┐
                            │                 │
                            │  Other Client   │
                            │  Applications   │
                            │                 │
                            └─────────────────┘
```

## 2. WebSocket Client Implementation

### 2.1 WebSocket Manager Class

```swift
// IMPLEMENT: Core WebSocket manager
class WebSocketManager: ObservableObject {
    // Published properties to expose connection state
    @Published private(set) var connectionState: ConnectionState = .disconnected
    @Published private(set) var lastError: Error?
    
    // Connection states
    enum ConnectionState {
        case connecting
        case connected
        case disconnected
        case reconnecting
        
        var description: String {
            switch self {
            case .connecting: return "Connecting"
            case .connected: return "Connected"
            case .disconnected: return "Disconnected"
            case .reconnecting: return "Reconnecting"
            }
        }
    }
    
    // WebSocket instance
    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession!
    
    // Configuration
    private let serverURL: URL
    private var authToken: String?
    private var messageHandlers: [String: (WebSocketMessage) -> Void] = [:]
    
    // Reconnection settings
    private var reconnectTimer: Timer?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    private let reconnectDelay: TimeInterval = 3.0
    
    // Background task ID for iOS background mode
    private var backgroundTaskID: UIBackgroundTaskIdentifier = .invalid
    
    // Heartbeat timer to keep connection alive
    private var heartbeatTimer: Timer?
    private let heartbeatInterval: TimeInterval = 30.0
    
    // Initialize with server URL
    init(serverURL: URL) {
        self.serverURL = serverURL
        
        // Configure URLSession
        let configuration = URLSessionConfiguration.default
        session = URLSession(configuration: configuration, delegate: self, delegateQueue: OperationQueue())
        
        // Setup notification observers
        setupNotificationObservers()
    }
    
    // Connect to WebSocket server
    func connect(with token: String? = nil) {
        guard connectionState != .connected && connectionState != .connecting else {
            return
        }
        
        // Update auth token if provided
        if let token = token {
            self.authToken = token
        }
        
        // Update connection state
        connectionState = .connecting
        
        // Create WebSocket URL with auth token if available
        var urlComponents = URLComponents(url: serverURL, resolvingAgainstBaseURL: true)
        if let authToken = authToken {
            let queryItem = URLQueryItem(name: "token", value: authToken)
            urlComponents?.queryItems = [queryItem]
        }
        
        guard let url = urlComponents?.url else {
            handleError(WebSocketError.invalidURL)
            return
        }
        
        // Create WebSocket task
        var request = URLRequest(url: url)
        request.timeoutInterval = 30
        
        // Add any required headers
        if let authToken = authToken {
            request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        webSocket = session.webSocketTask(with: request)
        
        // Start receiving messages
        receiveMessage()
        
        // Connect
        webSocket?.resume()
        
        // Start heartbeat timer
        startHeartbeatTimer()
        
        Logger.network.info("WebSocket connecting to \(url.absoluteString)")
    }
    
    // Disconnect from WebSocket server
    func disconnect(closeCode: URLSessionWebSocketTask.CloseCode = .normalClosure) {
        stopHeartbeatTimer()
        stopReconnectTimer()
        
        webSocket?.cancel(with: closeCode, reason: nil)
        webSocket = nil
        connectionState = .disconnected
        
        Logger.network.info("WebSocket disconnected")
    }
    
    // Send a message to the server
    func send<T: Encodable>(type: String, payload: T) {
        guard connectionState == .connected, let webSocket = webSocket else {
            Logger.network.error("Cannot send message - WebSocket not connected")
            return
        }
        
        do {
            // Create message object
            let message = WebSocketMessage(type: type, payload: payload)
            
            // Encode to JSON
            let encoder = JSONEncoder()
            let data = try encoder.encode(message)
            
            // Send as string
            let jsonString = String(data: data, encoding: .utf8)!
            webSocket.send(.string(jsonString)) { [weak self] error in
                if let error = error {
                    self?.handleError(error)
                }
            }
            
            Logger.network.debug("WebSocket sent message of type: \(type)")
        } catch {
            handleError(error)
        }
    }
    
    // Register a handler for a specific message type
    func registerHandler(for messageType: String, handler: @escaping (WebSocketMessage) -> Void) {
        messageHandlers[messageType] = handler
    }
    
    // Unregister a handler for a specific message type
    func unregisterHandler(for messageType: String) {
        messageHandlers.removeValue(forKey: messageType)
    }
    
    // MARK: - Private Methods
    
    // Start receiving messages
    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .success(let message):
                self.handleMessage(message)
                
                // Continue receiving messages
                self.receiveMessage()
                
            case .failure(let error):
                self.handleError(error)
                
                // Attempt reconnection
                if self.connectionState == .connected {
                    self.attemptReconnect()
                }
            }
        }
    }
    
    // Handle incoming message
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            // Decode JSON message
            guard let data = text.data(using: .utf8) else {
                Logger.network.error("Could not convert WebSocket message to data")
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let webSocketMessage = try decoder.decode(WebSocketMessage.self, from: data)
                
                // Dispatch to appropriate handler
                DispatchQueue.main.async {
                    // Handle system messages
                    if webSocketMessage.type == "ping" {
                        self.handlePing()
                        return
                    }
                    
                    // Find handler for this message type
                    if let handler = self.messageHandlers[webSocketMessage.type] {
                        handler(webSocketMessage)
                    } else {
                        Logger.network.warning("No handler registered for WebSocket message type: \(webSocketMessage.type)")
                    }
                }
                
                Logger.network.debug("WebSocket received message of type: \(webSocketMessage.type)")
            } catch {
                Logger.network.error("Failed to decode WebSocket message: \(error.localizedDescription)")
            }
            
        case .data(let data):
            // Our protocol uses string messages, but handle binary data just in case
            Logger.network.warning("Received binary WebSocket message - not supported")
            
        @unknown default:
            Logger.network.error("Unknown WebSocket message type received")
        }
    }
    
    // Handle errors
    private func handleError(_ error: Error) {
        lastError = error
        Logger.network.error("WebSocket error: \(error.localizedDescription)")
        
        // Post notification about error
        NotificationCenter.default.post(name: .webSocketError, object: error)
    }
    
    // Attempt to reconnect
    private func attemptReconnect() {
        guard reconnectAttempts < maxReconnectAttempts else {
            Logger.network.error("Maximum WebSocket reconnection attempts reached")
            connectionState = .disconnected
            return
        }
        
        reconnectAttempts += 1
        connectionState = .reconnecting
        
        // Stop previous timer if any
        stopReconnectTimer()
        
        // Calculate delay with exponential backoff
        let delay = reconnectDelay * pow(1.5, Double(reconnectAttempts - 1))
        
        Logger.network.info("Attempting WebSocket reconnection in \(delay) seconds (attempt \(reconnectAttempts)/\(maxReconnectAttempts))")
        
        // Schedule reconnection
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            guard let self = self else { return }
            self.connect()
        }
    }
    
    // Setup notification observers for app state changes
    private func setupNotificationObservers() {
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(handleAppDidEnterBackground), 
                                               name: UIApplication.didEnterBackgroundNotification, 
                                               object: nil)
        
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(handleAppWillEnterForeground), 
                                               name: UIApplication.willEnterForegroundNotification, 
                                               object: nil)
        
        NotificationCenter.default.addObserver(self, 
                                               selector: #selector(handleAppWillTerminate), 
                                               name: UIApplication.willTerminateNotification, 
                                               object: nil)
    }
    
    // Handle app entering background
    @objc private func handleAppDidEnterBackground() {
        // Start background task to keep socket alive briefly
        backgroundTaskID = UIApplication.shared.beginBackgroundTask { [weak self] in
            self?.endBackgroundTask()
        }
        
        // Option 1: Keep connection in background (drains battery)
        // Do nothing - connection will be maintained
        
        // Option 2: Disconnect to save resources (recommended for most apps)
        // disconnect()
    }
    
    // Handle app entering foreground
    @objc private func handleAppWillEnterForeground() {
        endBackgroundTask()
        
        // Reconnect if disconnected
        if connectionState == .disconnected {
            connect()
        }
    }
    
    // Handle app termination
    @objc private func handleAppWillTerminate() {
        disconnect(closeCode: .normalClosure)
    }
    
    // End background task
    private func endBackgroundTask() {
        if backgroundTaskID != .invalid {
            UIApplication.shared.endBackgroundTask(backgroundTaskID)
            backgroundTaskID = .invalid
        }
    }
    
    // Start heartbeat timer to keep connection alive
    private func startHeartbeatTimer() {
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: heartbeatInterval, repeats: true) { [weak self] _ in
            self?.sendHeartbeat()
        }
    }
    
    // Stop heartbeat timer
    private func stopHeartbeatTimer() {
        heartbeatTimer?.invalidate()
        heartbeatTimer = nil
    }
    
    // Send heartbeat ping
    private func sendHeartbeat() {
        let pingMessage = WebSocketMessage(type: "ping", payload: ["timestamp": Date().timeIntervalSince1970])
        
        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(pingMessage)
            let jsonString = String(data: data, encoding: .utf8)!
            
            webSocket?.send(.string(jsonString)) { [weak self] error in
                if let error = error {
                    self?.handleError(error)
                }
            }
        } catch {
            handleError(error)
        }
    }
    
    // Handle ping response
    private func handlePing() {
        // Respond with pong
        let pongMessage = WebSocketMessage(type: "pong", payload: ["timestamp": Date().timeIntervalSince1970])
        
        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(pongMessage)
            let jsonString = String(data: data, encoding: .utf8)!
            
            webSocket?.send(.string(jsonString)) { [weak self] error in
                if let error = error {
                    self?.handleError(error)
                }
            }
        } catch {
            handleError(error)
        }
    }
    
    // Stop reconnect timer
    private func stopReconnectTimer() {
        reconnectTimer?.invalidate()
        reconnectTimer = nil
    }
}

// MARK: - URLSessionWebSocketDelegate

extension WebSocketManager: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        // Reset reconnection attempts
        reconnectAttempts = 0
        
        // Update connection state
        DispatchQueue.main.async {
            self.connectionState = .connected
            
            // Post notification about connection
            NotificationCenter.default.post(name: .webSocketConnected, object: nil)
            
            Logger.network.info("WebSocket connected")
        }
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        // Handle close
        DispatchQueue.main.async {
            self.connectionState = .disconnected
            
            // Post notification about disconnection
            NotificationCenter.default.post(name: .webSocketDisconnected, object: nil)
            
            if let reason = reason, let reasonString = String(data: reason, encoding: .utf8) {
                Logger.network.info("WebSocket closed with code \(closeCode.rawValue): \(reasonString)")
            } else {
                Logger.network.info("WebSocket closed with code \(closeCode.rawValue)")
            }
            
            // Attempt reconnect if not a normal closure
            if closeCode != .normalClosure {
                self.attemptReconnect()
            }
        }
    }
}

// MARK: - WebSocket Message Types

// WebSocket message structure
struct WebSocketMessage: Codable {
    let type: String
    let payload: AnyCodable
    
    // Convenience initializer with generic payload
    init<T: Encodable>(type: String, payload: T) {
        self.type = type
        self.payload = AnyCodable(payload)
    }
}

// Helper for encoding/decoding arbitrary JSON
struct AnyCodable: Codable {
    private let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init<T: Encodable>(_ value: T) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if container.decodeNil() {
            self.value = NSNull()
        } else if let bool = try? container.decode(Bool.self) {
            self.value = bool
        } else if let int = try? container.decode(Int.self) {
            self.value = int
        } else if let double = try? container.decode(Double.self) {
            self.value = double
        } else if let string = try? container.decode(String.self) {
            self.value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            self.value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            self.value = dictionary.mapValues { $0.value }
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "AnyCodable value cannot be decoded")
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case is NSNull:
            try container.encodeNil()
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            let context = EncodingError.Context(codingPath: container.codingPath, debugDescription: "AnyCodable value cannot be encoded")
            throw EncodingError.invalidValue(value, context)
        }
    }
}

// Custom WebSocket errors
enum WebSocketError: Error, LocalizedError {
    case invalidURL
    case connectionFailed
    case disconnected
    case messageEncodingFailed
    case messageDecodingFailed
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid WebSocket URL"
        case .connectionFailed:
            return "Failed to connect to WebSocket server"
        case .disconnected:
            return "WebSocket is disconnected"
        case .messageEncodingFailed:
            return "Failed to encode WebSocket message"
        case .messageDecodingFailed:
            return "Failed to decode WebSocket message"
        }
    }
}

// Notification names
extension Notification.Name {
    static let webSocketConnected = Notification.Name("WebSocketConnected")
    static let webSocketDisconnected = Notification.Name("WebSocketDisconnected")
    static let webSocketError = Notification.Name("WebSocketError")
}
```

### 2.2 SyncManager Integration with WebSocket

```swift
// IMPLEMENT: Enhanced SyncManager with WebSocket support
class SyncManager {
    // Existing properties
    private let apiClient: APIClient
    private let coreDataManager: CoreDataManager
    private let networkMonitor: NetworkMonitor
    
    // WebSocket manager
    private let webSocketManager: WebSocketManager
    
    // Sync queue for operations
    private let syncQueue = DispatchQueue(label: "com.prsnl.syncQueue", qos: .utility)
    
    // Published state
    @Published private(set) var syncState: SyncState = .idle
    @Published private(set) var lastSyncDate: Date?
    @Published private(set) var isSyncing = false
    
    // Sync state enum
    enum SyncState {
        case idle
        case syncing
        case failed(Error)
        case completed
    }
    
    // Initialize with dependencies
    init(apiClient: APIClient, coreDataManager: CoreDataManager, networkMonitor: NetworkMonitor) {
        self.apiClient = apiClient
        self.coreDataManager = coreDataManager
        self.networkMonitor = networkMonitor
        
        // Initialize WebSocket manager with server URL
        let wsURL = URL(string: "wss://api.prsnl.com/ws")!
        self.webSocketManager = WebSocketManager(serverURL: wsURL)
        
        // Setup observers
        setupObservers()
        
        // Register WebSocket message handlers
        registerWebSocketHandlers()
    }
    
    // MARK: - Public Methods
    
    // Start the sync manager
    func start() {
        // Start network monitoring
        networkMonitor.startMonitoring()
        
        // Connect to WebSocket if online
        if networkMonitor.isConnected {
            connectWebSocket()
        }
        
        // Initial sync if needed
        if networkMonitor.isConnected && needsInitialSync() {
            syncItemsFromAPI()
        }
    }
    
    // Stop the sync manager
    func stop() {
        // Disconnect WebSocket
        webSocketManager.disconnect()
        
        // Stop network monitoring
        networkMonitor.stopMonitoring()
    }
    
    // Connect to WebSocket
    func connectWebSocket() {
        // Get auth token
        if let token = try? KeychainService().retrieve(key: KeychainKeys.authToken) {
            webSocketManager.connect(with: token)
        } else {
            Logger.sync.warning("Cannot connect to WebSocket: No auth token available")
        }
    }
    
    // Manually trigger a sync from API
    func syncItemsFromAPI() {
        guard networkMonitor.isConnected else {
            Logger.sync.warning("Cannot sync: Device is offline")
            return
        }
        
        guard !isSyncing else {
            Logger.sync.info("Sync already in progress")
            return
        }
        
        syncQueue.async {
            self.performSync()
        }
    }
    
    // Sync local changes to API
    func syncLocalChangesToAPI() {
        guard networkMonitor.isConnected else {
            Logger.sync.warning("Cannot sync local changes: Device is offline")
            return
        }
        
        guard !isSyncing else {
            Logger.sync.info("Sync already in progress")
            return
        }
        
        syncQueue.async {
            self.uploadPendingChanges()
        }
    }
    
    // MARK: - WebSocket Methods
    
    // Register WebSocket message handlers
    private func registerWebSocketHandlers() {
        // Handle item created remotely
        webSocketManager.registerHandler(for: "item.created") { [weak self] message in
            guard let self = self else { return }
            
            // Extract item data from payload
            if let itemData = try? JSONSerialization.data(withJSONObject: message.payload.value),
               let item = try? JSONDecoder().decode(Item.self, from: itemData) {
                
                // Process the new item
                self.handleRemoteItemCreated(item)
            }
        }
        
        // Handle item updated remotely
        webSocketManager.registerHandler(for: "item.updated") { [weak self] message in
            guard let self = self else { return }
            
            // Extract item data from payload
            if let itemData = try? JSONSerialization.data(withJSONObject: message.payload.value),
               let item = try? JSONDecoder().decode(Item.self, from: itemData) {
                
                // Process the updated item
                self.handleRemoteItemUpdated(item)
            }
        }
        
        // Handle item deleted remotely
        webSocketManager.registerHandler(for: "item.deleted") { [weak self] message in
            guard let self = self else { return }
            
            // Extract item ID from payload
            if let payload = message.payload.value as? [String: Any],
               let itemId = payload["id"] as? String {
                
                // Process the deleted item
                self.handleRemoteItemDeleted(itemId)
            }
        }
        
        // Handle sync request
        webSocketManager.registerHandler(for: "sync.request") { [weak self] _ in
            guard let self = self else { return }
            
            // Server is requesting a sync
            self.syncItemsFromAPI()
        }
    }
    
    // Handle remote item creation
    private func handleRemoteItemCreated(_ item: Item) {
        Task {
            do {
                // Check if item already exists locally
                let existingItem = try await coreDataManager.fetchItem(id: item.id)
                
                if existingItem == nil {
                    // Save new item to Core Data
                    try await coreDataManager.saveItem(item, needsSync: false)
                    
                    // Notify about new item
                    DispatchQueue.main.async {
                        NotificationCenter.default.post(name: .itemCreatedRemotely, object: item)
                    }
                    
                    Logger.sync.info("Saved remotely created item: \(item.id)")
                }
            } catch {
                Logger.sync.error("Failed to process remote item creation: \(error.localizedDescription)")
            }
        }
    }
    
    // Handle remote item update
    private func handleRemoteItemUpdated(_ item: Item) {
        Task {
            do {
                // Check if item exists locally
                if let existingItem = try await coreDataManager.fetchItem(id: item.id) {
                    // Only update if remote version is newer
                    if item.updatedAt > existingItem.updatedAt && !existingItem.needsSync {
                        // Save updated item to Core Data
                        try await coreDataManager.saveItem(item, needsSync: false)
                        
                        // Notify about updated item
                        DispatchQueue.main.async {
                            NotificationCenter.default.post(name: .itemUpdatedRemotely, object: item)
                        }
                        
                        Logger.sync.info("Updated item from remote: \(item.id)")
                    } else {
                        Logger.sync.info("Ignoring remote update for item \(item.id) - local version is newer or has pending changes")
                    }
                } else {
                    // Item doesn't exist locally, save it
                    try await coreDataManager.saveItem(item, needsSync: false)
                    Logger.sync.info("Saved remotely updated item that didn't exist locally: \(item.id)")
                }
            } catch {
                Logger.sync.error("Failed to process remote item update: \(error.localizedDescription)")
            }
        }
    }
    
    // Handle remote item deletion
    private func handleRemoteItemDeleted(_ itemId: String) {
        Task {
            do {
                // Delete item from Core Data
                try await coreDataManager.deleteItem(id: itemId)
                
                // Notify about deleted item
                DispatchQueue.main.async {
                    NotificationCenter.default.post(name: .itemDeletedRemotely, object: itemId)
                }
                
                Logger.sync.info("Deleted item from remote: \(itemId)")
            } catch {
                Logger.sync.error("Failed to process remote item deletion: \(error.localizedDescription)")
            }
        }
    }
    
    // Send item changes through WebSocket
    private func notifyItemChanges(_ item: Item, changeType: String) {
        // Only notify if connected to WebSocket
        guard webSocketManager.connectionState == .connected else {
            return
        }
        
        // Send appropriate message type based on change type
        switch changeType {
        case "created":
            webSocketManager.send(type: "item.created", payload: item)
        case "updated":
            webSocketManager.send(type: "item.updated", payload: item)
        case "deleted":
            webSocketManager.send(type: "item.deleted", payload: ["id": item.id])
        default:
            break
        }
    }
    
    // MARK: - Private Methods
    
    // Setup observers for connectivity and app state changes
    private func setupObservers() {
        // Observe network state changes
        networkMonitor.onConnectionChange { [weak self] isConnected in
            guard let self = self else { return }
            
            if isConnected {
                // Reconnect WebSocket when coming online
                self.connectWebSocket()
                
                // Sync pending changes when coming online
                self.syncLocalChangesToAPI()
            } else {
                // Optionally disconnect WebSocket when going offline
                // self.webSocketManager.disconnect()
            }
        }
        
        // Observe Core Data changes
        NotificationCenter.default.addObserver(self, 
                                             selector: #selector(handleCoreDataChanges(_:)), 
                                             name: .NSManagedObjectContextDidSave, 
                                             object: coreDataManager.viewContext)
        
        // Observe authentication changes
        NotificationCenter.default.addObserver(self, 
                                             selector: #selector(handleAuthStateChanged(_:)), 
                                             name: .authStateChanged, 
                                             object: nil)
    }
    
    // Check if initial sync is needed
    private func needsInitialSync() -> Bool {
        // Get last sync date from UserDefaults
        if let lastSync = UserDefaults.standard.object(forKey: "lastSyncDate") as? Date {
            // If last sync was more than 1 hour ago, sync again
            return Date().timeIntervalSince(lastSync) > 3600
        }
        
        // No previous sync, so initial sync is needed
        return true
    }
    
    // Perform full sync
    private func performSync() {
        DispatchQueue.main.async {
            self.isSyncing = true
            self.syncState = .syncing
        }
        
        Task {
            do {
                // First upload any pending changes
                try await uploadPendingChanges()
                
                // Then fetch latest data from API
                let response = try await apiClient.fetchTimeline(page: 1, limit: 100)
                
                // Save items to Core Data
                try await coreDataManager.saveItems(response.items, needsSync: false)
                
                // Update last sync date
                let now = Date()
                UserDefaults.standard.set(now, forKey: "lastSyncDate")
                
                DispatchQueue.main.async {
                    self.lastSyncDate = now
                    self.isSyncing = false
                    self.syncState = .completed
                    
                    // Notify about sync completion
                    NotificationCenter.default.post(name: .syncCompleted, object: nil)
                }
                
                Logger.sync.info("Sync completed successfully")
            } catch {
                DispatchQueue.main.async {
                    self.isSyncing = false
                    self.syncState = .failed(error)
                    
                    // Notify about sync failure
                    NotificationCenter.default.post(name: .syncFailed, object: error)
                }
                
                Logger.sync.error("Sync failed: \(error.localizedDescription)")
            }
        }
    }
    
    // Upload pending local changes
    private func uploadPendingChanges() async throws {
        DispatchQueue.main.async {
            self.isSyncing = true
        }
        
        // Get items that need to be synced
        let itemsToSync = try await coreDataManager.fetchItemsNeedingSync()
        
        if itemsToSync.isEmpty {
            DispatchQueue.main.async {
                self.isSyncing = false
            }
            return
        }
        
        Logger.sync.info("Uploading \(itemsToSync.count) pending changes")
        
        // Process each item
        for item in itemsToSync {
            do {
                // If item is marked for deletion
                if item.isDeleted {
                    // Delete from server
                    try await apiClient.deleteItem(id: item.id)
                    
                    // Delete locally
                    try await coreDataManager.deleteItem(id: item.id)
                    
                    // Notify through WebSocket
                    notifyItemChanges(item, changeType: "deleted")
                } else {
                    // Check if item exists on server
                    let isNew: Bool
                    
                    do {
                        _ = try await apiClient.fetchItem(id: item.id)
                        isNew = false
                    } catch {
                        isNew = true
                    }
                    
                    if isNew {
                        // Create item on server
                        try await apiClient.createItem(item)
                        
                        // Notify through WebSocket
                        notifyItemChanges(item, changeType: "created")
                    } else {
                        // Update item on server
                        try await apiClient.updateItem(item)
                        
                        // Notify through WebSocket
                        notifyItemChanges(item, changeType: "updated")
                    }
                    
                    // Mark as synced
                    try await coreDataManager.markItemAsSynced(id: item.id)
                }
            } catch {
                Logger.sync.error("Failed to sync item \(item.id): \(error.localizedDescription)")
                // Continue with next item
            }
        }
        
        DispatchQueue.main.async {
            self.isSyncing = false
        }
    }
    
    // Handle Core Data changes
    @objc private func handleCoreDataChanges(_ notification: Notification) {
        // Get inserted and updated objects
        guard let userInfo = notification.userInfo else { return }
        
        // Process inserted objects
        if let insertedObjects = userInfo[NSInsertedObjectsKey] as? Set<NSManagedObject> {
            for object in insertedObjects {
                if let cdItem = object as? CDItem {
                    // If online and WebSocket connected, notify about change
                    if networkMonitor.isConnected && webSocketManager.connectionState == .connected {
                        let item = Item(managedObject: cdItem)
                        notifyItemChanges(item, changeType: "created")
                    }
                }
            }
        }
        
        // Process updated objects
        if let updatedObjects = userInfo[NSUpdatedObjectsKey] as? Set<NSManagedObject> {
            for object in updatedObjects {
                if let cdItem = object as? CDItem, cdItem.needsSync {
                    // If online and WebSocket connected, notify about change
                    if networkMonitor.isConnected && webSocketManager.connectionState == .connected {
                        let item = Item(managedObject: cdItem)
                        notifyItemChanges(item, changeType: "updated")
                    }
                }
            }
        }
        
        // Process deleted objects
        if let deletedObjects = userInfo[NSDeletedObjectsKey] as? Set<NSManagedObject> {
            for object in deletedObjects {
                if let cdItem = object as? CDItem {
                    // If online and WebSocket connected, notify about deletion
                    if networkMonitor.isConnected && webSocketManager.connectionState == .connected {
                        let item = Item(managedObject: cdItem)
                        notifyItemChanges(item, changeType: "deleted")
                    }
                }
            }
        }
    }
    
    // Handle authentication state changes
    @objc private func handleAuthStateChanged(_ notification: Notification) {
        if let authState = notification.object as? AuthState {
            switch authState {
            case .authenticated:
                // Connect WebSocket with new token
                connectWebSocket()
                
                // Perform initial sync
                syncItemsFromAPI()
                
            case .unauthenticated:
                // Disconnect WebSocket
                webSocketManager.disconnect()
                
            default:
                break
            }
        }
    }
}

// Notification names
extension Notification.Name {
    static let syncCompleted = Notification.Name("SyncCompleted")
    static let syncFailed = Notification.Name("SyncFailed")
    static let itemCreatedRemotely = Notification.Name("ItemCreatedRemotely")
    static let itemUpdatedRemotely = Notification.Name("ItemUpdatedRemotely")
    static let itemDeletedRemotely = Notification.Name("ItemDeletedRemotely")
    static let authStateChanged = Notification.Name("AuthStateChanged")
}

// Helper to convert CDItem to Item
extension Item {
    init(managedObject: CDItem) {
        self.id = managedObject.id ?? UUID().uuidString
        self.title = managedObject.title ?? ""
        self.content = managedObject.content ?? ""
        self.createdAt = managedObject.createdAt ?? Date()
        self.updatedAt = managedObject.updatedAt ?? Date()
        // Map other properties as needed
    }
}
```

### 2.3 Connection Status Component

```swift
// IMPLEMENT: UI component for WebSocket connection status
struct ConnectionStatusView: View {
    @ObservedObject var webSocketManager: WebSocketManager
    var showDetailedStatus: Bool = false
    
    // Event when connection state changes
    var onConnectionChange: ((Bool) -> Void)?
    
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        HStack(spacing: 6) {
            // Status indicator
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            
            // Status text
            if showDetailedStatus {
                Text(statusText)
                    .font(.caption)
                    .foregroundColor(textColor)
            }
        }
        .padding(.vertical, 4)
        .padding(.horizontal, 8)
        .background(backgroundColor)
        .cornerRadius(12)
        .onChange(of: webSocketManager.connectionState) { oldValue, newValue in
            // Call the connection change handler
            onConnectionChange?(newValue == .connected)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Connection status: \(statusText)")
    }
    
    // Status color based on connection state
    private var statusColor: Color {
        switch webSocketManager.connectionState {
        case .connected:
            return .green
        case .connecting, .reconnecting:
            return .yellow
        case .disconnected:
            return .red
        }
    }
    
    // Status text based on connection state
    private var statusText: String {
        switch webSocketManager.connectionState {
        case .connected:
            return "Connected"
        case .connecting:
            return "Connecting"
        case .reconnecting:
            return "Reconnecting"
        case .disconnected:
            return "Disconnected"
        }
    }
    
    // Text color based on theme
    private var textColor: Color {
        return colorScheme == .dark ? .white : .black
    }
    
    // Background color based on theme
    private var backgroundColor: Color {
        return colorScheme == .dark ? Color.gray.opacity(0.3) : Color.gray.opacity(0.1)
    }
}

// IMPLEMENT: Live activity indicator for item synchronization
struct ItemSyncStatusView: View {
    let item: Item
    @ObservedObject var syncManager: SyncManager
    
    var body: some View {
        if item.needsSync {
            HStack(spacing: 4) {
                if syncManager.isSyncing {
                    // Show spinning indicator when actively syncing
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .blue))
                        .scaleEffect(0.7)
                    
                    Text("Syncing")
                        .font(.caption)
                        .foregroundColor(.secondary)
                } else {
                    // Show pending sync indicator
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.caption)
                        .foregroundColor(.orange)
                    
                    Text("Pending")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.vertical, 2)
            .padding(.horizontal, 6)
            .background(Color.secondary.opacity(0.1))
            .cornerRadius(4)
            .accessibilityElement(children: .combine)
            .accessibilityLabel(syncManager.isSyncing ? "Syncing" : "Pending synchronization")
        } else {
            // Show synced indicator
            HStack(spacing: 4) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.green)
                
                Text("Synced")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 2)
            .padding(.horizontal, 6)
            .background(Color.green.opacity(0.1))
            .cornerRadius(4)
            .accessibilityElement(children: .combine)
            .accessibilityLabel("Synchronized")
        }
    }
}
```

## 3. Real-Time Features Implementation

### 3.1 Timeline Live Updates

```swift
// IMPLEMENT: Timeline view model with WebSocket updates
class TimelineViewModel: ObservableObject {
    // Published properties
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var error: Error?
    @Published var currentPage = 1
    @Published var hasMoreItems = true
    @Published var isOffline = false
    
    // WebSocket-related properties
    @Published var isWebSocketConnected = false
    
    // Presentation state
    @Published var showCreateItem = false
    @Published var showSearch = false
    
    // Dependencies
    private let apiClient: APIClient
    private let coreDataManager: CoreDataManager
    private let networkMonitor: NetworkMonitor
    private let syncManager: SyncManager
    private let webSocketManager: WebSocketManager
    
    // Initialize with dependencies
    init(apiClient: APIClient = APIClient.shared,
         coreDataManager: CoreDataManager = CoreDataManager.shared,
         networkMonitor: NetworkMonitor = NetworkMonitor.shared,
         syncManager: SyncManager = SyncManager.shared) {
        
        self.apiClient = apiClient
        self.coreDataManager = coreDataManager
        self.networkMonitor = networkMonitor
        self.syncManager = syncManager
        self.webSocketManager = syncManager.webSocketManager
        
        // Set initial offline state
        self.isOffline = !networkMonitor.isConnected
        
        // Set initial WebSocket state
        self.isWebSocketConnected = webSocketManager.connectionState == .connected
        
        // Setup observers
        setupObservers()
    }
    
    // MARK: - Public Methods
    
    // Load timeline data
    func loadTimeline() async {
        DispatchQueue.main.async {
            self.isLoading = true
            self.error = nil
        }
        
        // Check if device is online
        if networkMonitor.isConnected {
            // Online mode - fetch from API
            do {
                let response = try await apiClient.fetchTimeline(page: 1, limit: 20)
                
                // Save to Core Data
                try await coreDataManager.saveItems(response.items)
                
                // Update UI
                DispatchQueue.main.async {
                    self.items = response.items
                    self.currentPage = 1
                    self.hasMoreItems = response.items.count >= 20
                    self.isLoading = false
                }
            } catch {
                // If API fails, fall back to local data
                await loadFromLocalStorage()
                
                DispatchQueue.main.async {
                    self.error = error
                    self.isLoading = false
                }
            }
        } else {
            // Offline mode - load from Core Data
            await loadFromLocalStorage()
        }
    }
    
    // Load more items (pagination)
    func loadMoreItems() async {
        guard hasMoreItems && !isLoading && networkMonitor.isConnected else {
            return
        }
        
        DispatchQueue.main.async {
            self.isLoading = true
        }
        
        let nextPage = currentPage + 1
        
        do {
            let response = try await apiClient.fetchTimeline(page: nextPage, limit: 20)
            
            // Save to Core Data
            try await coreDataManager.saveItems(response.items)
            
            // Update UI
            DispatchQueue.main.async {
                self.items.append(contentsOf: response.items)
                self.currentPage = nextPage
                self.hasMoreItems = response.items.count >= 20
                self.isLoading = false
            }
        } catch {
            DispatchQueue.main.async {
                self.error = error
                self.isLoading = false
            }
        }
    }
    
    // Refresh timeline
    func refreshTimeline() async {
        await loadTimeline()
    }
    
    // MARK: - Private Methods
    
    // Load items from local storage
    private func loadFromLocalStorage() async {
        do {
            let localItems = try await coreDataManager.fetchAllItems(limit: 50)
            
            DispatchQueue.main.async {
                self.items = localItems
                self.isLoading = false
            }
        } catch {
            DispatchQueue.main.async {
                self.error = error
                self.isLoading = false
            }
        }
    }
    
    // Setup observers for various events
    private func setupObservers() {
        // Observe network state changes
        networkMonitor.onConnectionChange { [weak self] isConnected in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.isOffline = !isConnected
                
                // When coming back online, refresh data
                if isConnected {
                    Task {
                        await self.loadTimeline()
                    }
                }
            }
        }
        
        // Observe WebSocket connection state
        NotificationCenter.default.addObserver(self,
                                               selector: #selector(handleWebSocketConnected),
                                               name: .webSocketConnected,
                                               object: nil)
        
        NotificationCenter.default.addObserver(self,
                                               selector: #selector(handleWebSocketDisconnected),
                                               name: .webSocketDisconnected,
                                               object: nil)
        
        // Observe item changes from WebSocket
        NotificationCenter.default.addObserver(self,
                                               selector: #selector(handleRemoteItemCreated(_:)),
                                               name: .itemCreatedRemotely,
                                               object: nil)
        
        NotificationCenter.default.addObserver(self,
                                               selector: #selector(handleRemoteItemUpdated(_:)),
                                               name: .itemUpdatedRemotely,
                                               object: nil)
        
        NotificationCenter.default.addObserver(self,
                                               selector: #selector(handleRemoteItemDeleted(_:)),
                                               name: .itemDeletedRemotely,
                                               object: nil)
    }
    
    // Handle WebSocket connected event
    @objc private func handleWebSocketConnected() {
        DispatchQueue.main.async {
            self.isWebSocketConnected = true
        }
    }
    
    // Handle WebSocket disconnected event
    @objc private func handleWebSocketDisconnected() {
        DispatchQueue.main.async {
            self.isWebSocketConnected = false
        }
    }
    
    // Handle remote item creation
    @objc private func handleRemoteItemCreated(_ notification: Notification) {
        guard let newItem = notification.object as? Item else { return }
        
        DispatchQueue.main.async {
            // Check if item already exists
            if !self.items.contains(where: { $0.id == newItem.id }) {
                // Add to the beginning of the timeline
                self.items.insert(newItem, at: 0)
            }
        }
    }
    
    // Handle remote item update
    @objc private func handleRemoteItemUpdated(_ notification: Notification) {
        guard let updatedItem = notification.object as? Item else { return }
        
        DispatchQueue.main.async {
            // Find and update the item
            if let index = self.items.firstIndex(where: { $0.id == updatedItem.id }) {
                self.items[index] = updatedItem
            }
        }
    }
    
    // Handle remote item deletion
    @objc private func handleRemoteItemDeleted(_ notification: Notification) {
        guard let itemId = notification.object as? String else { return }
        
        DispatchQueue.main.async {
            // Remove the item
            self.items.removeAll(where: { $0.id == itemId })
        }
    }
}
```

### 3.2 Real-Time Item Detail

```swift
// IMPLEMENT: Item detail view with live updates
struct ItemDetailView: View {
    @StateObject private var viewModel: ItemDetailViewModel
    @State private var isWebSocketConnected = false
    
    init(item: Item) {
        self._viewModel = StateObject(wrappedValue: ItemDetailViewModel(item: item))
    }
    
    var body: some View {
        ZStack {
            // Main content
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Title section
                    VStack(alignment: .leading, spacing: 8) {
                        Text(viewModel.item.title)
                            .font(.title)
                            .bold()
                            .accessibilityIdentifier("item-title")
                        
                        HStack {
                            Text(DateFormatter.mediumFormat.string(from: viewModel.item.updatedAt))
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .accessibilityIdentifier("item-date")
                            
                            Spacer()
                            
                            // Sync status indicator
                            ItemSyncStatusView(item: viewModel.item, syncManager: viewModel.syncManager)
                        }
                    }
                    
                    Divider()
                    
                    // Content section
                    Text(viewModel.item.content)
                        .accessibilityIdentifier("item-content")
                    
                    // Attachments section
                    if let attachments = viewModel.item.attachments, !attachments.isEmpty {
                        Divider()
                        
                        Text("Attachments")
                            .font(.headline)
                            .padding(.top, 8)
                        
                        ForEach(attachments) { attachment in
                            AttachmentView(attachment: attachment)
                        }
                    }
                    
                    // Tags section
                    if let tags = viewModel.item.tags, !tags.isEmpty {
                        Divider()
                        
                        Text("Tags")
                            .font(.headline)
                            .padding(.top, 8)
                        
                        FlowLayout(tags, spacing: 8) { tag in
                            Text(tag)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 4)
                                .background(Color.secondary.opacity(0.1))
                                .cornerRadius(12)
                        }
                    }
                    
                    // Live indicator when someone is viewing/editing
                    if viewModel.activeViewers.count > 0 {
                        Divider()
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Currently Viewing")
                                .font(.headline)
                                .padding(.top, 8)
                            
                            HStack {
                                ForEach(viewModel.activeViewers, id: \.self) { viewer in
                                    UserAvatarView(username: viewer)
                                }
                            }
                        }
                        .transition(.opacity)
                        .animation(.easeInOut, value: viewModel.activeViewers)
                    }
                }
                .padding()
            }
            
            // Connection status overlay (when disconnected)
            if !isWebSocketConnected {
                VStack {
                    Spacer()
                    
                    HStack {
                        Spacer()
                        
                        ConnectionStatusView(
                            webSocketManager: viewModel.webSocketManager,
                            showDetailedStatus: true,
                            onConnectionChange: handleConnectionChange
                        )
                        
                        Spacer()
                    }
                    .padding(.bottom, 20)
                }
            }
        }
        .navigationTitle("Item Details")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: {
                    viewModel.isEditing = true
                }) {
                    Text("Edit")
                }
                .disabled(viewModel.isCurrentlyBeingEdited)
                .accessibilityIdentifier("edit-button")
            }
            
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button(action: viewModel.shareItem) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                    .accessibilityIdentifier("share-button")
                    
                    if !viewModel.isCurrentlyBeingEdited {
                        Button(action: viewModel.confirmDelete) {
                            Label("Delete", systemImage: "trash")
                        }
                        .foregroundColor(.red)
                        .accessibilityIdentifier("delete-button")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .imageScale(.large)
                }
                .accessibilityIdentifier("more-options-button")
            }
        }
        .sheet(isPresented: $viewModel.isEditing) {
            EditItemView(item: viewModel.item, onSave: viewModel.updateItem)
        }
        .alert("Confirm Deletion", isPresented: $viewModel.showingDeleteConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive, action: viewModel.deleteItem)
        } message: {
            Text("Are you sure you want to delete this item? This action cannot be undone.")
        }
        .alert(isPresented: $viewModel.showEditingConflictAlert) {
            Alert(
                title: Text("Item is Being Edited"),
                message: Text("This item is currently being edited by \(viewModel.currentEditor ?? "another user"). Please try again later."),
                dismissButton: .default(Text("OK"))
            )
        }
        .overlay(
            viewModel.isCurrentlyBeingEdited ?
                AnyView(
                    VStack {
                        HStack {
                            Image(systemName: "pencil.circle.fill")
                                .foregroundColor(.orange)
                            Text("\(viewModel.currentEditor ?? "Someone") is editing...")
                                .foregroundColor(.secondary)
                                .font(.callout)
                        }
                        .padding(8)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(8)
                    }
                    .padding(.top, 8)
                    .transition(.move(edge: .top))
                    .animation(.spring(), value: viewModel.isCurrentlyBeingEdited)
                )
                : AnyView(EmptyView())
            , alignment: .top
        )
        .onAppear {
            viewModel.startViewingItem()
        }
        .onDisappear {
            viewModel.stopViewingItem()
        }
    }
    
    // Handle WebSocket connection changes
    private func handleConnectionChange(_ isConnected: Bool) {
        isWebSocketConnected = isConnected
    }
}

// IMPLEMENT: Item detail view model with real-time features
class ItemDetailViewModel: ObservableObject {
    // Published properties
    @Published var item: Item
    @Published var isLoading = false
    @Published var error: Error?
    @Published var isEditing = false
    @Published var showingDeleteConfirmation = false
    @Published var activeViewers: [String] = []
    @Published var isCurrentlyBeingEdited = false
    @Published var currentEditor: String?
    @Published var showEditingConflictAlert = false
    
    // Dependencies
    let apiClient: APIClient
    let coreDataManager: CoreDataManager
    let webSocketManager: WebSocketManager
    let syncManager: SyncManager
    
    // User info
    private let username: String
    
    // Initialize with item
    init(item: Item,
         apiClient: APIClient = APIClient.shared,
         coreDataManager: CoreDataManager = CoreDataManager.shared,
         syncManager: SyncManager = SyncManager.shared) {
        
        self.item = item
        self.apiClient = apiClient
        self.coreDataManager = coreDataManager
        self.syncManager = syncManager
        self.webSocketManager = syncManager.webSocketManager
        
        // Get username from UserDefaults or keychain
        if let storedUsername = UserDefaults.standard.string(forKey: "username") {
            self.username = storedUsername
        } else {
            // Fallback to a device identifier
            self.username = UIDevice.current.name
        }
        
        // Setup observers
        setupObservers()
    }
    
    // MARK: - Public Methods
    
    // Notify server that user is viewing this item
    func startViewingItem() {
        // Only send if WebSocket is connected
        guard webSocketManager.connectionState == .connected else { return }
        
        // Send viewing status
        webSocketManager.send(type: "item.viewing", payload: [
            "item_id": item.id,
            "username": username,
            "action": "start"
        ])
    }
    
    // Notify server that user stopped viewing this item
    func stopViewingItem() {
        // Only send if WebSocket is connected
        guard webSocketManager.connectionState == .connected else { return }
        
        // Send stopped viewing status
        webSocketManager.send(type: "item.viewing", payload: [
            "item_id": item.id,
            "username": username,
            "action": "stop"
        ])
    }
    
    // Start editing this item
    func startEditingItem() {
        // Only send if WebSocket is connected
        guard webSocketManager.connectionState == .connected else { return }
        
        // Send editing status
        webSocketManager.send(type: "item.editing", payload: [
            "item_id": item.id,
            "username": username,
            "action": "start"
        ])
    }
    
    // Stop editing this item
    func stopEditingItem() {
        // Only send if WebSocket is connected
        guard webSocketManager.connectionState == .connected else { return }
        
        // Send stopped editing status
        webSocketManager.send(type: "item.editing", payload: [
            "item_id": item.id,
            "username": username,
            "action": "stop"
        ])
    }
    
    // Update item after editing
    func updateItem(_ updatedItem: Item) {
        Task {
            do {
                // Save to Core Data
                try await coreDataManager.saveItem(updatedItem)
                
                // Update local state
                DispatchQueue.main.async {
                    self.item = updatedItem
                    self.isEditing = false
                }
                
                // Stop editing notification
                stopEditingItem()
            } catch {
                DispatchQueue.main.async {
                    self.error = error
                }
            }
        }
    }
    
    // Share item
    func shareItem() {
        // Implementation would depend on sharing mechanism
    }
    
    // Show delete confirmation
    func confirmDelete() {
        showingDeleteConfirmation = true
    }
    
    // Delete item
    func deleteItem() {
        Task {
            do {
                // Delete from Core Data
                try await coreDataManager.deleteItem(id: item.id)
                
                // Post notification that item was deleted
                DispatchQueue.main.async {
                    NotificationCenter.default.post(name: .itemDeleted, object: self.item.id)
                }
            } catch {
                DispatchQueue.main.async {
                    self.error = error
                }
            }
        }
    }
    
    // MARK: - Private Methods
    
    // Setup observers for WebSocket messages
    private func setupObservers() {
        // Register handlers for WebSocket messages
        webSocketManager.registerHandler(for: "item.viewing.update") { [weak self] message in
            self?.handleViewingUpdate(message)
        }
        
        webSocketManager.registerHandler(for: "item.editing.update") { [weak self] message in
            self?.handleEditingUpdate(message)
        }
        
        webSocketManager.registerHandler(for: "item.updated") { [weak self] message in
            self?.handleItemUpdate(message)
        }
        
        // Remove handlers when view model is deallocated
        NotificationCenter.default.addObserver(
            forName: .webSocketConnected,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.startViewingItem()
        }
    }
    
    // Handle viewing update messages
    private func handleViewingUpdate(_ message: WebSocketMessage) {
        guard let payload = message.payload.value as? [String: Any],
              let itemId = payload["item_id"] as? String,
              let viewers = payload["viewers"] as? [String] else {
            return
        }
        
        // Only process if this is for our item
        guard itemId == item.id else { return }
        
        // Update active viewers list
        DispatchQueue.main.async {
            self.activeViewers = viewers.filter { $0 != self.username }
        }
    }
    
    // Handle editing update messages
    private func handleEditingUpdate(_ message: WebSocketMessage) {
        guard let payload = message.payload.value as? [String: Any],
              let itemId = payload["item_id"] as? String else {
            return
        }
        
        // Only process if this is for our item
        guard itemId == item.id else { return }
        
        // Check if someone is editing
        if let editor = payload["editor"] as? String {
            DispatchQueue.main.async {
                self.isCurrentlyBeingEdited = editor != self.username
                self.currentEditor = editor != self.username ? editor : nil
                
                // If we're trying to edit but someone else is already editing
                if self.isEditing && self.isCurrentlyBeingEdited {
                    self.isEditing = false
                    self.showEditingConflictAlert = true
                }
            }
        } else {
            // No one is editing
            DispatchQueue.main.async {
                self.isCurrentlyBeingEdited = false
                self.currentEditor = nil
            }
        }
    }
    
    // Handle item update messages
    private func handleItemUpdate(_ message: WebSocketMessage) {
        // Extract item data from payload
        if let itemData = try? JSONSerialization.data(withJSONObject: message.payload.value),
           let updatedItem = try? JSONDecoder().decode(Item.self, from: itemData) {
            
            // Only process if this is for our item
            guard updatedItem.id == item.id else { return }
            
            // Update item if the update is from someone else
            DispatchQueue.main.async {
                self.item = updatedItem
            }
        }
    }
    
    // Clean up when deallocated
    deinit {
        webSocketManager.unregisterHandler(for: "item.viewing.update")
        webSocketManager.unregisterHandler(for: "item.editing.update")
        webSocketManager.unregisterHandler(for: "item.updated")
    }
}

// IMPLEMENT: User avatar view
struct UserAvatarView: View {
    let username: String
    
    var body: some View {
        ZStack {
            Circle()
                .fill(avatarColor)
                .frame(width: 32, height: 32)
            
            Text(avatarInitial)
                .foregroundColor(.white)
                .font(.system(size: 14, weight: .semibold))
        }
        .overlay(
            Circle()
                .stroke(Color.green, lineWidth: 2)
        )
        .accessibilityLabel("\(username) is viewing")
    }
    
    // Get initials from username
    private var avatarInitial: String {
        let initial = username.first?.uppercased() ?? "U"
        return String(initial)
    }
    
    // Generate consistent color from username
    private var avatarColor: Color {
        let colors: [Color] = [
            .blue, .indigo, .purple, .pink, .red, .orange, .yellow, .green, .teal
        ]
        
        // Hash the username to get a consistent index
        let hash = username.utf8.reduce(0) { $0 + Int($1) }
        let index = hash % colors.count
        
        return colors[index]
    }
}

extension Notification.Name {
    static let itemDeleted = Notification.Name("ItemDeleted")
}
```

### 3.3 Collaborative Editing

```swift
// IMPLEMENT: Basic collaborative editing support
class CollaborativeEditingManager {
    // Singleton instance
    static let shared = CollaborativeEditingManager()
    
    // WebSocket manager reference
    private let webSocketManager: WebSocketManager
    
    // Currently editing items (itemId: username)
    private var editingSessions: [String: String] = [:]
    
    // Operation transformations for conflict resolution
    private var pendingOperations: [String: [EditOperation]] = [:]
    
    // Initialize with WebSocket manager
    init(webSocketManager: WebSocketManager = SyncManager.shared.webSocketManager) {
        self.webSocketManager = webSocketManager
        
        // Register WebSocket handlers
        setupWebSocketHandlers()
    }
    
    // MARK: - Public Methods
    
    // Start editing session for an item
    func startEditing(itemId: String, username: String) -> Bool {
        // Check if someone else is editing
        if let currentEditor = editingSessions[itemId], currentEditor != username {
            // Item is being edited by someone else
            return false
        }
        
        // Mark item as being edited by this user
        editingSessions[itemId] = username
        
        // Initialize operations array
        pendingOperations[itemId] = []
        
        // Notify others via WebSocket
        notifyEditingState(itemId: itemId, username: username, isEditing: true)
        
        return true
    }
    
    // Stop editing session for an item
    func stopEditing(itemId: String, username: String) {
        // Only if this user is the current editor
        if editingSessions[itemId] == username {
            // Remove editing session
            editingSessions.removeValue(forKey: itemId)
            pendingOperations.removeValue(forKey: itemId)
            
            // Notify others via WebSocket
            notifyEditingState(itemId: itemId, username: username, isEditing: false)
        }
    }
    
    // Record an edit operation
    func recordOperation(itemId: String, username: String, operation: EditOperation) {
        // Only if this user is the current editor
        guard editingSessions[itemId] == username else {
            return
        }
        
        // Add operation to pending list
        if pendingOperations[itemId] == nil {
            pendingOperations[itemId] = []
        }
        pendingOperations[itemId]?.append(operation)
        
        // Send operation via WebSocket
        sendOperation(itemId: itemId, username: username, operation: operation)
    }
    
    // Check if an item is being edited
    func isBeingEdited(itemId: String) -> Bool {
        return editingSessions[itemId] != nil
    }
    
    // Get the username of the editor for an item
    func editorFor(itemId: String) -> String? {
        return editingSessions[itemId]
    }
    
    // MARK: - Private Methods
    
    // Setup WebSocket handlers
    private func setupWebSocketHandlers() {
        // Handle editing state messages
        webSocketManager.registerHandler(for: "item.editing.state") { [weak self] message in
            self?.handleEditingStateMessage(message)
        }
        
        // Handle edit operation messages
        webSocketManager.registerHandler(for: "item.editing.operation") { [weak self] message in
            self?.handleEditOperationMessage(message)
        }
    }
    
    // Handle editing state messages
    private func handleEditingStateMessage(_ message: WebSocketMessage) {
        guard let payload = message.payload.value as? [String: Any],
              let itemId = payload["item_id"] as? String,
              let username = payload["username"] as? String,
              let isEditing = payload["is_editing"] as? Bool else {
            return
        }
        
        if isEditing {
            // Someone started editing
            editingSessions[itemId] = username
        } else {
            // Someone stopped editing
            if editingSessions[itemId] == username {
                editingSessions.removeValue(forKey: itemId)
            }
        }
        
        // Notify observers
        NotificationCenter.default.post(
            name: .editingStateChanged,
            object: nil,
            userInfo: [
                "itemId": itemId,
                "username": username,
                "isEditing": isEditing
            ]
        )
    }
    
    // Handle edit operation messages
    private func handleEditOperationMessage(_ message: WebSocketMessage) {
        guard let payload = message.payload.value as? [String: Any],
              let itemId = payload["item_id"] as? String,
              let operationData = payload["operation"] as? [String: Any],
              let operation = EditOperation.from(dictionary: operationData) else {
            return
        }
        
        // Store the operation
        if pendingOperations[itemId] == nil {
            pendingOperations[itemId] = []
        }
        pendingOperations[itemId]?.append(operation)
        
        // Notify observers
        NotificationCenter.default.post(
            name: .editOperationReceived,
            object: nil,
            userInfo: [
                "itemId": itemId,
                "operation": operation
            ]
        )
    }
    
    // Notify editing state via WebSocket
    private func notifyEditingState(itemId: String, username: String, isEditing: Bool) {
        webSocketManager.send(type: "item.editing.state", payload: [
            "item_id": itemId,
            "username": username,
            "is_editing": isEditing
        ])
    }
    
    // Send operation via WebSocket
    private func sendOperation(itemId: String, username: String, operation: EditOperation) {
        webSocketManager.send(type: "item.editing.operation", payload: [
            "item_id": itemId,
            "username": username,
            "operation": operation.toDictionary()
        ])
    }
}

// Edit operation struct
struct EditOperation: Codable {
    enum OperationType: String, Codable {
        case insert
        case delete
        case replace
    }
    
    let type: OperationType
    let position: Int
    let text: String
    let length: Int
    let timestamp: Date
    
    // Convert to dictionary
    func toDictionary() -> [String: Any] {
        return [
            "type": type.rawValue,
            "position": position,
            "text": text,
            "length": length,
            "timestamp": timestamp.timeIntervalSince1970
        ]
    }
    
    // Create from dictionary
    static func from(dictionary: [String: Any]) -> EditOperation? {
        guard let typeString = dictionary["type"] as? String,
              let type = OperationType(rawValue: typeString),
              let position = dictionary["position"] as? Int,
              let text = dictionary["text"] as? String,
              let length = dictionary["length"] as? Int,
              let timestampValue = dictionary["timestamp"] as? TimeInterval else {
            return nil
        }
        
        let timestamp = Date(timeIntervalSince1970: timestampValue)
        
        return EditOperation(
            type: type,
            position: position,
            text: text,
            length: length,
            timestamp: timestamp
        )
    }
}

// Notification names
extension Notification.Name {
    static let editingStateChanged = Notification.Name("EditingStateChanged")
    static let editOperationReceived = Notification.Name("EditOperationReceived")
}
```

## 4. Backend WebSocket Implementation

The following Node.js code illustrates how the backend WebSocket server should be implemented to support the iOS client:

```javascript
// IMPLEMENT: WebSocket server (Node.js with Socket.IO)
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const jwt = require('jsonwebtoken');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Active connections
const connections = new Map();

// Active viewers by item
const itemViewers = new Map();

// Active editors by item
const itemEditors = new Map();

// JWT secret (should match API server)
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Authenticate socket connections
io.use((socket, next) => {
  const token = socket.handshake.auth.token || socket.handshake.query.token;
  
  if (!token) {
    return next(new Error('Authentication required'));
  }
  
  try {
    // Verify JWT token
    const decoded = jwt.verify(token, JWT_SECRET);
    socket.user = decoded;
    next();
  } catch (err) {
    next(new Error('Invalid token'));
  }
});

// Handle socket connections
io.on('connection', (socket) => {
  console.log(`User connected: ${socket.user.username} (${socket.id})`);
  
  // Store connection
  connections.set(socket.id, {
    id: socket.id,
    userId: socket.user.id,
    username: socket.user.username
  });
  
  // Send initial connection event
  socket.emit('connection.established', {
    status: 'connected',
    user: {
      id: socket.user.id,
      username: socket.user.username
    }
  });
  
  // Handle item viewing
  socket.on('item.viewing', (data) => {
    const { item_id, action } = data;
    const username = socket.user.username;
    
    if (!item_id) return;
    
    if (action === 'start') {
      // Add user to viewers for this item
      if (!itemViewers.has(item_id)) {
        itemViewers.set(item_id, new Set());
      }
      itemViewers.get(item_id).add(username);
    } else if (action === 'stop') {
      // Remove user from viewers for this item
      if (itemViewers.has(item_id)) {
        itemViewers.get(item_id).delete(username);
        
        if (itemViewers.get(item_id).size === 0) {
          itemViewers.delete(item_id);
        }
      }
    }
    
    // Broadcast updated viewers list
    broadcastViewers(item_id);
  });
  
  // Handle item editing
  socket.on('item.editing', (data) => {
    const { item_id, action } = data;
    const username = socket.user.username;
    
    if (!item_id) return;
    
    if (action === 'start') {
      // Set user as editor for this item
      itemEditors.set(item_id, username);
    } else if (action === 'stop') {
      // Remove user as editor for this item
      if (itemEditors.get(item_id) === username) {
        itemEditors.delete(item_id);
      }
    }
    
    // Broadcast updated editor
    broadcastEditor(item_id);
  });
  
  // Handle edit operations
  socket.on('item.editing.operation', (data) => {
    const { item_id, operation } = data;
    
    if (!item_id || !operation) return;
    
    // Only allow operations from the current editor
    if (itemEditors.get(item_id) !== socket.user.username) {
      return;
    }
    
    // Broadcast operation to all clients except sender
    socket.broadcast.emit('item.editing.operation', {
      item_id,
      username: socket.user.username,
      operation
    });
  });
  
  // Handle ping messages
  socket.on('ping', (data) => {
    socket.emit('pong', { timestamp: Date.now() });
  });
  
  // Handle disconnection
  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.user.username} (${socket.id})`);
    
    const username = socket.user.username;
    
    // Remove from connections
    connections.delete(socket.id);
    
    // Remove from all item viewers
    for (const [itemId, viewers] of itemViewers.entries()) {
      if (viewers.has(username)) {
        viewers.delete(username);
        
        if (viewers.size === 0) {
          itemViewers.delete(itemId);
        } else {
          broadcastViewers(itemId);
        }
      }
    }
    
    // Remove from all item editors
    for (const [itemId, editor] of itemEditors.entries()) {
      if (editor === username) {
        itemEditors.delete(itemId);
        broadcastEditor(itemId);
      }
    }
  });
});

// Broadcast viewers for an item
function broadcastViewers(itemId) {
  const viewers = Array.from(itemViewers.get(itemId) || []);
  
  io.emit('item.viewing.update', {
    item_id: itemId,
    viewers
  });
}

// Broadcast editor for an item
function broadcastEditor(itemId) {
  const editor = itemEditors.get(itemId);
  
  io.emit('item.editing.update', {
    item_id: itemId,
    editor
  });
}

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`WebSocket server running on port ${PORT}`);
});
```

## 5. WebSocket Message Protocol

### 5.1 Message Format

All WebSocket messages follow this JSON format:

```json
{
  "type": "message.type",
  "payload": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

### 5.2 Message Types

| Direction | Type | Description | Payload |
|-----------|------|-------------|---------|
| Client→Server | `ping` | Heartbeat | `{ "timestamp": 1625097600000 }` |
| Server→Client | `pong` | Heartbeat response | `{ "timestamp": 1625097600100 }` |
| Client→Server | `item.viewing` | User viewing item | `{ "item_id": "123", "username": "user1", "action": "start\|stop" }` |
| Server→Client | `item.viewing.update` | Viewers list update | `{ "item_id": "123", "viewers": ["user1", "user2"] }` |
| Client→Server | `item.editing` | User editing item | `{ "item_id": "123", "username": "user1", "action": "start\|stop" }` |
| Server→Client | `item.editing.update` | Editor update | `{ "item_id": "123", "editor": "user1" }` |
| Client→Server | `item.editing.operation` | Edit operation | `{ "item_id": "123", "username": "user1", "operation": {...} }` |
| Server→Client | `item.created` | Item created | `{ "id": "123", "title": "New Item", ... }` |
| Server→Client | `item.updated` | Item updated | `{ "id": "123", "title": "Updated Item", ... }` |
| Server→Client | `item.deleted` | Item deleted | `{ "id": "123" }` |
| Server→Client | `sync.request` | Server requests sync | `{ "reason": "data_updated" }` |

## 6. Network Considerations

### 6.1 Handling Connectivity Changes

```swift
// IMPLEMENT: Enhanced NetworkMonitor with WebSocket reconnection
class NetworkMonitor {
    // Singleton instance
    static let shared = NetworkMonitor()
    
    // Current connectivity status
    private(set) var isConnected = false
    private(set) var connectionType: ConnectionType = .unknown
    
    // Path monitor
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    
    // Connection types
    enum ConnectionType {
        case wifi
        case cellular
        case ethernet
        case unknown
    }
    
    // Connection quality
    enum ConnectionQuality {
        case poor
        case moderate
        case good
        case excellent
        case unknown
        
        // Get max concurrent operations based on quality
        var maxConcurrentOperations: Int {
            switch self {
            case .poor: return 1
            case .moderate: return 2
            case .good: return 4
            case .excellent: return 6
            case .unknown: return 2
            }
        }
    }
    
    // Current connection quality
    private(set) var connectionQuality: ConnectionQuality = .unknown
    
    // Connection handler closure
    private var connectionHandler: ((Bool) -> Void)?
    
    // Quality change handler closure
    private var qualityHandler: ((ConnectionQuality) -> Void)?
    
    // Initialize
    init() {
        // Set up path monitor
        monitor.pathUpdateHandler = { [weak self] path in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                // Update connection status
                self.isConnected = path.status == .satisfied
                
                // Update connection type
                self.connectionType = self.getConnectionType(from: path)
                
                // Estimate connection quality
                self.connectionQuality = self.estimateConnectionQuality(from: path)
                
                // Call connection handler
                self.connectionHandler?(self.isConnected)
                
                // Call quality handler
                self.qualityHandler?(self.connectionQuality)
                
                // Log connection status
                Logger.network.info("Network status: \(self.isConnected ? "Connected" : "Disconnected") via \(self.connectionType)")
            }
        }
    }
    
    // Start monitoring
    func startMonitoring() {
        monitor.start(queue: queue)
    }
    
    // Stop monitoring
    func stopMonitoring() {
        monitor.cancel()
    }
    
    // Set connection change handler
    func onConnectionChange(_ handler: @escaping (Bool) -> Void) {
        connectionHandler = handler
        
        // Call immediately with current state
        handler(isConnected)
    }
    
    // Set quality change handler
    func onQualityChange(_ handler: @escaping (ConnectionQuality) -> Void) {
        qualityHandler = handler
        
        // Call immediately with current state
        handler(connectionQuality)
    }
    
    // Get connection type from path
    private func getConnectionType(from path: NWPath) -> ConnectionType {
        if path.usesInterfaceType(.wifi) {
            return .wifi
        } else if path.usesInterfaceType(.cellular) {
            return .cellular
        } else if path.usesInterfaceType(.wiredEthernet) {
            return .ethernet
        } else {
            return .unknown
        }
    }
    
    // Estimate connection quality from path
    private func estimateConnectionQuality(from path: NWPath) -> ConnectionQuality {
        // Not connected
        if path.status != .satisfied {
            return .unknown
        }
        
        // Ethernet is typically excellent
        if path.usesInterfaceType(.wiredEthernet) {
            return .excellent
        }
        
        // WiFi can be good to excellent
        if path.usesInterfaceType(.wifi) {
            return path.isExpensive ? .good : .excellent
        }
        
        // Cellular varies
        if path.usesInterfaceType(.cellular) {
            return path.isConstrained ? .poor : .moderate
        }
        
        // Other types
        return .moderate
    }
}
```

### 6.2 Data Compression

```swift
// IMPLEMENT: WebSocket message compression
extension WebSocketManager {
    // Compress message data
    private func compressMessageData(_ data: Data) -> Data? {
        // Skip compression for small messages
        guard data.count > 1024 else {
            return data
        }
        
        do {
            // Create a compression context
            return try (data as NSData).compressed(using: .lzfse) as Data
        } catch {
            Logger.network.error("Failed to compress WebSocket data: \(error.localizedDescription)")
            return data
        }
    }
    
    // Decompress message data
    private func decompressMessageData(_ data: Data) -> Data? {
        do {
            // Create a decompression context
            return try (data as NSData).decompressed(using: .lzfse) as Data
        } catch {
            Logger.network.error("Failed to decompress WebSocket data: \(error.localizedDescription)")
            return data
        }
    }
    
    // Send compressed message
    func sendCompressed<T: Encodable>(type: String, payload: T) {
        guard connectionState == .connected, let webSocket = webSocket else {
            Logger.network.error("Cannot send message - WebSocket not connected")
            return
        }
        
        do {
            // Create message object
            let message = WebSocketMessage(type: type, payload: payload)
            
            // Encode to JSON
            let encoder = JSONEncoder()
            let data = try encoder.encode(message)
            
            // Compress data
            if let compressedData = compressMessageData(data) {
                // Send as binary
                webSocket.send(.data(compressedData)) { [weak self] error in
                    if let error = error {
                        self?.handleError(error)
                    }
                }
                
                Logger.network.debug("WebSocket sent compressed message of type: \(type)")
            }
        } catch {
            handleError(error)
        }
    }
    
    // Process incoming message with decompression
    private func processIncomingMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            // Process as normal text message
            handleStringMessage(text)
            
        case .data(let data):
            // Decompress data
            if let decompressedData = decompressMessageData(data) {
                // Convert to string
                if let text = String(data: decompressedData, encoding: .utf8) {
                    handleStringMessage(text)
                } else {
                    Logger.network.error("Could not convert decompressed WebSocket data to string")
                }
            }
            
        @unknown default:
            Logger.network.error("Unknown WebSocket message type received")
        }
    }
    
    // Handle string message
    private func handleStringMessage(_ text: String) {
        // Decode JSON message
        guard let data = text.data(using: .utf8) else {
            Logger.network.error("Could not convert WebSocket message to data")
            return
        }
        
        do {
            let decoder = JSONDecoder()
            let webSocketMessage = try decoder.decode(WebSocketMessage.self, from: data)
            
            // Dispatch to appropriate handler
            DispatchQueue.main.async {
                // Find handler for this message type
                if let handler = self.messageHandlers[webSocketMessage.type] {
                    handler(webSocketMessage)
                } else {
                    Logger.network.warning("No handler registered for WebSocket message type: \(webSocketMessage.type)")
                }
            }
            
            Logger.network.debug("WebSocket received message of type: \(webSocketMessage.type)")
        } catch {
            Logger.network.error("Failed to decode WebSocket message: \(error.localizedDescription)")
        }
    }
}
```

### 6.3 Battery Efficiency

```swift
// IMPLEMENT: Battery-aware WebSocket management
extension WebSocketManager {
    // Adjust behavior based on battery level
    func adjustForBatteryLevel() {
        // Get current battery level and state
        let device = UIDevice.current
        device.isBatteryMonitoringEnabled = true
        
        let batteryLevel = device.batteryLevel
        let batteryState = device.batteryState
        
        // Reset to default behavior
        heartbeatInterval = 30.0
        
        // Low battery adjustments
        if batteryLevel < 0.2 || batteryState == .unplugged {
            // Reduce heartbeat frequency to save battery
            heartbeatInterval = 60.0
            
            // Consider disconnecting in background
            NotificationCenter.default.post(name: .lowBatteryModeEnabled, object: nil)
        }
        
        // Update heartbeat timer
        restartHeartbeatTimer()
    }
    
    // Restart heartbeat timer with current interval
    private func restartHeartbeatTimer() {
        stopHeartbeatTimer()
        startHeartbeatTimer()
    }
    
    // Set up battery monitoring
    private func setupBatteryMonitoring() {
        let device = UIDevice.current
        device.isBatteryMonitoringEnabled = true
        
        // Observe battery level changes
        NotificationCenter.default.addObserver(self,
                                             selector: #selector(batteryLevelChanged),
                                             name: UIDevice.batteryLevelDidChangeNotification,
                                             object: nil)
        
        // Observe battery state changes
        NotificationCenter.default.addObserver(self,
                                             selector: #selector(batteryStateChanged),
                                             name: UIDevice.batteryStateDidChangeNotification,
                                             object: nil)
    }
    
    // Handle battery level changes
    @objc private func batteryLevelChanged() {
        adjustForBatteryLevel()
    }
    
    // Handle battery state changes
    @objc private func batteryStateChanged() {
        adjustForBatteryLevel()
    }
}

// Battery status notification
extension Notification.Name {
    static let lowBatteryModeEnabled = Notification.Name("LowBatteryModeEnabled")
}
```

## 7. Security Considerations

### 7.1 WebSocket Authentication

```swift
// IMPLEMENT: JWT-based WebSocket authentication
extension WebSocketManager {
    // Connect with JWT authentication
    func connectWithJWT(jwt: String) {
        guard connectionState != .connected && connectionState != .connecting else {
            return
        }
        
        // Store JWT
        self.authToken = jwt
        
        // Update connection state
        connectionState = .connecting
        
        // Create WebSocket URL with auth token
        var urlComponents = URLComponents(url: serverURL, resolvingAgainstBaseURL: true)
        let queryItem = URLQueryItem(name: "token", value: jwt)
        urlComponents?.queryItems = [queryItem]
        
        guard let url = urlComponents?.url else {
            handleError(WebSocketError.invalidURL)
            return
        }
        
        // Create WebSocket task
        var request = URLRequest(url: url)
        request.timeoutInterval = 30
        
        // Add authorization header as well (belt and suspenders)
        request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        
        webSocket = session.webSocketTask(with: request)
        
        // Start receiving messages
        receiveMessage()
        
        // Connect
        webSocket?.resume()
        
        // Start heartbeat timer
        startHeartbeatTimer()
        
        Logger.network.info("WebSocket connecting to \(url.absoluteString)")
    }
    
    // Refresh authentication token
    func refreshAuthentication(jwt: String) {
        // Store new JWT
        self.authToken = jwt
        
        // If connected, disconnect and reconnect with new token
        if connectionState == .connected || connectionState == .connecting {
            disconnect()
            connectWithJWT(jwt: jwt)
        }
    }
}
```

### 7.2 Secure Communication

```swift
// IMPLEMENT: Enhanced WebSocket security
extension WebSocketManager: URLSessionDelegate {
    // Configure secure URLSession
    private func configureSecureSession() -> URLSession {
        let configuration = URLSessionConfiguration.default
        
        // Add secure headers
        configuration.httpAdditionalHeaders = [
            "X-Client-Version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0",
            "X-Client-Platform": "iOS"
        ]
        
        // Create session with certificate pinning delegate
        return URLSession(configuration: configuration, delegate: self, delegateQueue: .main)
    }
    
    // Handle authentication challenge (certificate pinning)
    func urlSession(_ session: URLSession,
                   didReceive challenge: URLAuthenticationChallenge,
                   completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        // Use certificate pinning if enabled
        if enableCertificatePinning {
            guard let serverTrust = challenge.protectionSpace.serverTrust else {
                completionHandler(.cancelAuthenticationChallenge, nil)
                return
            }
            
            // Get server certificate
            guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
                completionHandler(.cancelAuthenticationChallenge, nil)
                return
            }
            
            // Get public key data
            let serverPublicKey = SecCertificateCopyKey(serverCertificate)
            let serverPublicKeyData = SecKeyCopyExternalRepresentation(serverPublicKey!, nil)! as Data
            
            // Hash the public key
            let serverPublicKeyHash = serverPublicKeyData.sha256()
            
            // Compare with pinned hash
            let pinnedHash = Data(base64Encoded: pinnedPublicKeyHash)!
            
            if serverPublicKeyHash == pinnedHash {
                // Certificate is valid
                let credential = URLCredential(trust: serverTrust)
                completionHandler(.useCredential, credential)
            } else {
                // Certificate is invalid
                completionHandler(.cancelAuthenticationChallenge, nil)
                Logger.security.error("WebSocket certificate pinning failed")
            }
        } else {
            // Default handling
            completionHandler(.performDefaultHandling, nil)
        }
    }
    
    // SHA-256 hash extension
    private func sha256() -> Data {
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        self.withUnsafeBytes {
            _ = CC_SHA256($0.baseAddress, CC_LONG(self.count), &hash)
        }
        return Data(hash)
    }
}
```

### 7.3 Message Validation

```swift
// IMPLEMENT: WebSocket message validation
extension WebSocketMessage {
    // Validate message structure
    static func validate(_ data: Data) -> Bool {
        do {
            // Attempt to decode as JSON first
            guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                return false
            }
            
            // Validate required fields
            guard let type = json["type"] as? String, !type.isEmpty,
                  json["payload"] != nil else {
                return false
            }
            
            // Validate type format (no injection)
            let validTypePattern = "^[a-zA-Z0-9]+(\\.[a-zA-Z0-9]+)*$"
            let typeRegex = try NSRegularExpression(pattern: validTypePattern)
            let typeRange = NSRange(type.startIndex..<type.endIndex, in: type)
            let matches = typeRegex.matches(in: type, range: typeRange)
            
            return !matches.isEmpty
        } catch {
            return false
        }
    }
    
    // Validate specific message types
    static func validateSpecificType(_ message: WebSocketMessage) -> Bool {
        switch message.type {
        case "item.viewing":
            // Validate viewing message
            guard let payload = message.payload.value as? [String: Any],
                  let itemId = payload["item_id"] as? String, !itemId.isEmpty,
                  let action = payload["action"] as? String,
                  action == "start" || action == "stop" else {
                return false
            }
            return true
            
        case "item.editing":
            // Validate editing message
            guard let payload = message.payload.value as? [String: Any],
                  let itemId = payload["item_id"] as? String, !itemId.isEmpty,
                  let action = payload["action"] as? String,
                  action == "start" || action == "stop" else {
                return false
            }
            return true
            
        case "item.editing.operation":
            // Validate operation message
            guard let payload = message.payload.value as? [String: Any],
                  let itemId = payload["item_id"] as? String, !itemId.isEmpty,
                  let operation = payload["operation"] as? [String: Any],
                  let type = operation["type"] as? String,
                  ["insert", "delete", "replace"].contains(type) else {
                return false
            }
            return true
            
        default:
            // For other message types, just check for non-empty payload
            return message.payload.value != nil
        }
    }
}
```

## 8. Testing Strategy

### 8.1 Unit Testing

```swift
// IMPLEMENT: WebSocket manager unit tests
final class WebSocketManagerTests: XCTestCase {
    var webSocketManager: WebSocketManager!
    var mockURLSession: MockURLSession!
    
    override func setUp() {
        super.setUp()
        
        // Create mock URL session
        mockURLSession = MockURLSession()
        
        // Create WebSocket manager with mock session
        let serverURL = URL(string: "wss://api.prsnl.com/ws")!
        webSocketManager = WebSocketManager(serverURL: serverURL, session: mockURLSession)
    }
    
    override func tearDown() {
        webSocketManager = nil
        mockURLSession = nil
        super.tearDown()
    }
    
    func testConnectionStateChanges() {
        // Test initial state
        XCTAssertEqual(webSocketManager.connectionState, .disconnected)
        
        // Connect
        webSocketManager.connect()
        XCTAssertEqual(webSocketManager.connectionState, .connecting)
        
        // Simulate connection success
        mockURLSession.simulateWebSocketOpen()
        XCTAssertEqual(webSocketManager.connectionState, .connected)
        
        // Disconnect
        webSocketManager.disconnect()
        XCTAssertEqual(webSocketManager.connectionState, .disconnected)
    }
    
    func testMessageSending() {
        // Connect first
        webSocketManager.connect()
        mockURLSession.simulateWebSocketOpen()
        
        // Send a message
        let testPayload = ["test": "data"]
        webSocketManager.send(type: "test.message", payload: testPayload)
        
        // Verify message was sent
        XCTAssertEqual(mockURLSession.sentMessages.count, 1)
        
        // Verify message content
        if case .string(let messageString) = mockURLSession.sentMessages.first {
            // Parse message to verify structure
            let data = messageString.data(using: .utf8)!
            do {
                let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                XCTAssertEqual(json["type"] as? String, "test.message")
                XCTAssertNotNil(json["payload"])
            } catch {
                XCTFail("Failed to parse message JSON: \(error)")
            }
        } else {
            XCTFail("Message was not sent as string")
        }
    }
    
    func testMessageReceiving() {
        // Set up expectation for message handler
        let messageExpectation = expectation(description: "Message received")
        
        // Register handler
        webSocketManager.registerHandler(for: "test.response") { message in
            // Verify message content
            XCTAssertEqual(message.type, "test.response")
            messageExpectation.fulfill()
        }
        
        // Connect
        webSocketManager.connect()
        mockURLSession.simulateWebSocketOpen()
        
        // Simulate receiving a message
        let responseJson = """
        {
            "type": "test.response",
            "payload": {
                "status": "success",
                "data": "test"
            }
        }
        """
        mockURLSession.simulateWebSocketMessage(.string(responseJson))
        
        // Wait for handler to be called
        wait(for: [messageExpectation], timeout: 1.0)
    }
    
    func testReconnection() {
        // Connect
        webSocketManager.connect()
        mockURLSession.simulateWebSocketOpen()
        XCTAssertEqual(webSocketManager.connectionState, .connected)
        
        // Simulate disconnect with error
        mockURLSession.simulateWebSocketClose(closeCode: .abnormalClosure)
        
        // Should be reconnecting
        XCTAssertEqual(webSocketManager.connectionState, .reconnecting)
        
        // Simulate successful reconnection
        mockURLSession.simulateWebSocketOpen()
        XCTAssertEqual(webSocketManager.connectionState, .connected)
    }
    
    func testHeartbeat() {
        // Set short heartbeat interval for testing
        webSocketManager.heartbeatInterval = 0.1
        
        // Connect
        webSocketManager.connect()
        mockURLSession.simulateWebSocketOpen()
        
        // Wait for heartbeat
        let heartbeatExpectation = expectation(description: "Heartbeat sent")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            // Check if heartbeat was sent
            let hasPing = self.mockURLSession.sentMessages.contains { message in
                if case .string(let messageString) = message {
                    return messageString.contains("\"type\":\"ping\"")
                }
                return false
            }
            
            XCTAssertTrue(hasPing, "Heartbeat ping was not sent")
            heartbeatExpectation.fulfill()
        }
        
        wait(for: [heartbeatExpectation], timeout: 1.0)
    }
}

// Mock URL session for WebSocket testing
class MockURLSession: URLSessionProtocol {
    // Mock delegate
    weak var delegate: URLSessionWebSocketDelegate?
    
    // Mock WebSocket task
    var mockWebSocketTask: MockWebSocketTask?
    
    // Track sent messages
    var sentMessages: [URLSessionWebSocketTask.Message] = []
    
    // Create WebSocket task
    func webSocketTask(with request: URLRequest) -> URLSessionWebSocketTask {
        let task = MockWebSocketTask(request: request)
        task.mockSession = self
        self.mockWebSocketTask = task
        return task
    }
    
    // Simulate WebSocket open
    func simulateWebSocketOpen() {
        DispatchQueue.main.async {
            self.delegate?.urlSession?(URLSession.shared,
                                     webSocketTask: self.mockWebSocketTask!,
                                     didOpenWithProtocol: "")
        }
    }
    
    // Simulate WebSocket close
    func simulateWebSocketClose(closeCode: URLSessionWebSocketTask.CloseCode, reason: Data? = nil) {
        DispatchQueue.main.async {
            self.delegate?.urlSession?(URLSession.shared,
                                     webSocketTask: self.mockWebSocketTask!,
                                     didCloseWith: closeCode,
                                     reason: reason)
        }
    }
    
    // Simulate WebSocket message
    func simulateWebSocketMessage(_ message: URLSessionWebSocketTask.Message) {
        guard let completionHandler = mockWebSocketTask?.receivingCompletionHandler else {
            return
        }
        
        DispatchQueue.main.async {
            completionHandler(.success(message))
        }
    }
}

// Mock WebSocket task
class MockWebSocketTask: URLSessionWebSocketTask {
    // Original request
    let originalRequest: URLRequest
    
    // Mock session
    weak var mockSession: MockURLSession?
    
    // Completion handler for receiving
    var receivingCompletionHandler: ((Result<URLSessionWebSocketTask.Message, Error>) -> Void)?
    
    // Initialize with request
    init(request: URLRequest) {
        self.originalRequest = request
        super.init()
    }
    
    // Send message
    override func send(_ message: URLSessionWebSocketTask.Message, completionHandler: @escaping (Error?) -> Void) {
        mockSession?.sentMessages.append(message)
        completionHandler(nil)
    }
    
    // Receive message
    override func receive(completionHandler: @escaping (Result<URLSessionWebSocketTask.Message, Error>) -> Void) {
        receivingCompletionHandler = completionHandler
    }
    
    // Resume task
    override func resume() {
        // Task resumed, simulate connection process
    }
    
    // Cancel task
    override func cancel(with closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        // Task cancelled
    }
}
```

### 8.2 Integration Testing

```swift
// IMPLEMENT: WebSocket integration tests
final class WebSocketIntegrationTests: XCTestCase {
    var syncManager: SyncManager!
    var coreDataManager: CoreDataManager!
    var apiClient: MockAPIClient!
    var webSocketManager: WebSocketManager!
    var networkMonitor: MockNetworkMonitor!
    
    override func setUp() {
        super.setUp()
        
        // Set up dependencies
        coreDataManager = CoreDataManager(inMemory: true)
        apiClient = MockAPIClient()
        
        // Create WebSocket manager with test server
        let wsURL = URL(string: "wss://api.prsnl.test/ws")!
        webSocketManager = WebSocketManager(serverURL: wsURL)
        
        // Create network monitor
        networkMonitor = MockNetworkMonitor()
        networkMonitor.isConnected = true
        
        // Create sync manager
        syncManager = SyncManager(
            apiClient: apiClient,
            coreDataManager: coreDataManager,
            networkMonitor: networkMonitor,
            webSocketManager: webSocketManager
        )
    }
    
    override func tearDown() {
        syncManager = nil
        coreDataManager = nil
        apiClient = nil
        webSocketManager = nil
        networkMonitor = nil
        super.tearDown()
    }
    
    func testItemCreationPropagation() {
        // Create expectation for WebSocket message
        let messageSentExpectation = expectation(description: "WebSocket message sent")
        
        // Mock WebSocket connected state
        syncManager.webSocketManager = MockWebSocketManager(messageSentExpectation: messageSentExpectation)
        
        // Create a new item
        let newItem = Item(
            id: UUID().uuidString,
            title: "Test Item",
            content: "Test Content",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        // Save item to trigger WebSocket notification
        Task {
            try await coreDataManager.saveItem(newItem)
            
            // Wait for WebSocket message
            await fulfillment(of: [messageSentExpectation], timeout: 2.0)
        }
    }
    
    func testRemoteItemUpdate() {
        // Create expectation for item update
        let itemUpdatedExpectation = expectation(description: "Item updated")
        
        // Register observer for item updates
        let observer = NotificationCenter.default.addObserver(
            forName: .itemUpdatedRemotely,
            object: nil,
            queue: .main
        ) { notification in
            if let updatedItem = notification.object as? Item {
                XCTAssertEqual(updatedItem.id, "test-id")
                XCTAssertEqual(updatedItem.title, "Updated Title")
                itemUpdatedExpectation.fulfill()
            }
        }
        
        // Simulate receiving WebSocket message
        let updatedItem = Item(
            id: "test-id",
            title: "Updated Title",
            content: "Updated Content",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        // Prepare Core Data with original item
        Task {
            let originalItem = Item(
                id: "test-id",
                title: "Original Title",
                content: "Original Content",
                createdAt: Date(),
                updatedAt: Date().addingTimeInterval(-3600) // 1 hour ago
            )
            
            try await coreDataManager.saveItem(originalItem)
            
            // Simulate WebSocket message
            let message = WebSocketMessage(type: "item.updated", payload: updatedItem)
            syncManager.handleRemoteItemUpdated(updatedItem)
            
            // Wait for item update
            await fulfillment(of: [itemUpdatedExpectation], timeout: 2.0)
            
            // Clean up observer
            NotificationCenter.default.removeObserver(observer)
        }
    }
    
    func testNetworkTransitionHandling() {
        // Create expectations
        let disconnectExpectation = expectation(description: "WebSocket disconnected")
        let reconnectExpectation = expectation(description: "WebSocket reconnected")
        
        // Mock WebSocket manager
        let mockWebSocketManager = MockWebSocketManager()
        syncManager.webSocketManager = mockWebSocketManager
        
        // Set up disconnect observer
        mockWebSocketManager.onDisconnect = {
            disconnectExpectation.fulfill()
        }
        
        // Set up connect observer
        mockWebSocketManager.onConnect = {
            reconnectExpectation.fulfill()
        }
        
        // Simulate network transition
        networkMonitor.simulateConnectionChange(connected: false)
        
        // Wait for disconnect
        wait(for: [disconnectExpectation], timeout: 1.0)
        
        // Simulate network coming back online
        networkMonitor.simulateConnectionChange(connected: true)
        
        // Wait for reconnect
        wait(for: [reconnectExpectation], timeout: 1.0)
    }
}

// Mock WebSocket manager for integration tests
class MockWebSocketManager: WebSocketManager {
    var messageSentExpectation: XCTestExpectation?
    var onConnect: (() -> Voi