import Foundation
import Combine
import UIKit

/// Manages WebSocket connections for real-time updates
@MainActor
class WebSocketManager: ObservableObject {
    // MARK: - Published Properties
    @Published private(set) var connectionState: ConnectionState = .disconnected
    @Published private(set) var lastError: Error?
    @Published private(set) var isReceivingUpdates = false
    
    // MARK: - Types
    enum ConnectionState: Equatable {
        case disconnected
        case connecting
        case connected
        case reconnecting
        
        var description: String {
            switch self {
            case .disconnected: return "Disconnected"
            case .connecting: return "Connecting"
            case .connected: return "Connected"
            case .reconnecting: return "Reconnecting"
            }
        }
    }
    
    enum WebSocketError: LocalizedError {
        case invalidURL
        case connectionFailed
        case authenticationFailed
        case messageDecodingFailed
        
        var errorDescription: String? {
            switch self {
            case .invalidURL: return "Invalid WebSocket URL"
            case .connectionFailed: return "Failed to connect to server"
            case .authenticationFailed: return "Authentication failed"
            case .messageDecodingFailed: return "Failed to decode message"
            }
        }
    }
    
    // MARK: - Message Types
    struct WebSocketMessage: Codable {
        let type: String
        let data: [String: Any]?
        let timestamp: Date
        
        enum CodingKeys: String, CodingKey {
            case type
            case data
            case timestamp
        }
        
        init(type: String, data: [String: Any]? = nil) {
            self.type = type
            self.data = data
            self.timestamp = Date()
        }
        
        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            type = try container.decode(String.self, forKey: .type)
            timestamp = try container.decode(Date.self, forKey: .timestamp)
            
            if let dataDict = try? container.decode([String: Any].self, forKey: .data) {
                data = dataDict
            } else {
                data = nil
            }
        }
        
        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(type, forKey: .type)
            try container.encode(timestamp, forKey: .timestamp)
            if let data = data {
                try container.encode(data, forKey: .data)
            }
        }
    }
    
    // MARK: - Private Properties
    private var webSocketTask: URLSessionWebSocketTask?
    private let session: URLSession
    private var authToken: String?
    private var messageHandlers: [String: (WebSocketMessage) -> Void] = [:]
    private var cancellables = Set<AnyCancellable>()
    
    // Reconnection
    private var reconnectTimer: Timer?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    private let reconnectDelay: TimeInterval = 3.0
    
    // Heartbeat
    private var heartbeatTimer: Timer?
    private let heartbeatInterval: TimeInterval = 30.0
    
    // Message queue for offline/connecting states
    private var messageQueue: [WebSocketMessage] = []
    private let messageQueueLimit = 100
    
    // Configuration
    private let baseURL: String
    
    // MARK: - Initialization
    init(baseURL: String = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://localhost:8000") {
        self.baseURL = baseURL
        
        // Use background configuration for WebSocket persistence
        let configuration = URLSessionConfiguration.background(withIdentifier: "ai.prsnl.websocket")
        configuration.timeoutIntervalForRequest = 60
        configuration.timeoutIntervalForResource = 300
        configuration.sessionSendsLaunchEvents = true
        configuration.shouldUseExtendedBackgroundIdleMode = true
        
        self.session = URLSession(configuration: configuration)
        
        setupNotificationObservers()
    }
    
    deinit {
        Task { @MainActor [weak self] in
            self?.disconnect()
        }
    }
    
    // MARK: - Public Methods
    func connect(authToken: String? = nil) {
        guard connectionState == .disconnected else { return }
        
        self.authToken = authToken ?? UserDefaults.standard.string(forKey: "auth_token")
        connectionState = .connecting
        
        // Convert HTTP URL to WebSocket URL
        let wsURLString = baseURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
        
        guard let url = URL(string: "\(wsURLString)/ws") else {
            lastError = WebSocketError.invalidURL
            connectionState = .disconnected
            return
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 10
        
        // Add auth token if available
        if let token = self.authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        webSocketTask = session.webSocketTask(with: request)
        webSocketTask?.resume()
        
        receiveMessage()
        startHeartbeat()
        
        // Send initial connection message
        Task {
            await sendMessage(WebSocketMessage(type: "connection", data: ["client": "ios"]))
        }
        
        // Don't set connected until we receive confirmation
        // connectionState will be set to .connected after successful handshake
        reconnectAttempts = 0
    }
    
    @MainActor
    func disconnect() {
        guard connectionState != .disconnected else { return }
        
        connectionState = .disconnected
        
        // Cancel timers
        heartbeatTimer?.invalidate()
        heartbeatTimer = nil
        reconnectTimer?.invalidate()
        reconnectTimer = nil
        
        // Close WebSocket
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        
        isReceivingUpdates = false
    }
    
    func send(type: String, data: [String: Any]? = nil) async {
        let message = WebSocketMessage(type: type, data: data)
        
        // Queue message if not connected
        if connectionState != .connected {
            await queueMessage(message)
        } else {
            await sendMessage(message)
        }
    }
    
    func registerHandler(for messageType: String, handler: @escaping (WebSocketMessage) -> Void) {
        messageHandlers[messageType] = handler
    }
    
    func removeHandler(for messageType: String) {
        messageHandlers.removeValue(forKey: messageType)
    }
    
    // MARK: - Private Methods
    private func sendMessage(_ message: WebSocketMessage) async {
        guard connectionState == .connected,
              let webSocketTask = webSocketTask else { return }
        
        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            let data = try encoder.encode(message)
            let string = String(data: data, encoding: .utf8) ?? "{}"
            
            try await webSocketTask.send(.string(string))
        } catch {
            print("Failed to send WebSocket message: \(error)")
            handleError(error)
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .success(let message):
                Task { @MainActor [weak self] in
                    guard let self = self else { return }
                    self.handleMessage(message)
                    self.receiveMessage() // Continue receiving
                }
                
            case .failure(let error):
                Task { @MainActor [weak self] in
                    self?.handleError(error)
                }
            }
        }
    }
    
    @MainActor
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            guard let data = text.data(using: .utf8) else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                
                // Try to decode as WebSocketMessage
                if let wsMessage = try? decoder.decode(WebSocketMessage.self, from: data) {
                    handleWebSocketMessage(wsMessage)
                } else {
                    // Handle raw JSON
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let type = json["type"] as? String {
                        let wsMessage = WebSocketMessage(type: type, data: json)
                        handleWebSocketMessage(wsMessage)
                    }
                }
                
                isReceivingUpdates = true
            } catch {
                print("Failed to decode WebSocket message: \(error)")
            }
            
        case .data(let data):
            print("Received binary data: \(data.count) bytes")
            
        @unknown default:
            break
        }
    }
    
    private func handleWebSocketMessage(_ message: WebSocketMessage) {
        // Handle system messages
        switch message.type {
        case "connection_confirmed":
            // Now we're truly connected
            connectionState = .connected
            isReceivingUpdates = true
            // Process any queued messages
            Task {
                await processMessageQueue()
            }
            
        case "pong":
            // Heartbeat response
            return
            
        case "error":
            if let errorMessage = message.data?["message"] as? String {
                print("WebSocket error: \(errorMessage)")
            }
            
        case "auth_required":
            // Server requires authentication
            Task {
                await sendAuthToken()
            }
            
        default:
            // Call registered handler for this message type
            if let handler = messageHandlers[message.type] {
                handler(message)
            }
        }
    }
    
    @MainActor
    private func handleError(_ error: Error) {
        lastError = error
        print("WebSocket error: \(error)")
        
        if connectionState == .connected || connectionState == .connecting {
            connectionState = .disconnected
            scheduleReconnect()
        }
    }
    
    private func scheduleReconnect() {
        guard reconnectAttempts < maxReconnectAttempts else {
            print("Max reconnection attempts reached")
            return
        }
        
        reconnectAttempts += 1
        connectionState = .reconnecting
        
        // Calculate exponential backoff with jitter
        let baseDelay = 1.0
        let maxDelay = 60.0
        let delay = min(baseDelay * pow(2.0, Double(reconnectAttempts - 1)), maxDelay)
        let jitter = Double.random(in: 0...1)
        let finalDelay = delay + jitter
        
        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: finalDelay, repeats: false) { [weak self] _ in
            guard let self = self else { return }
            Task { @MainActor [weak self] in
                self?.connect(authToken: self?.authToken)
            }
        }
    }
    
    private func startHeartbeat() {
        heartbeatTimer?.invalidate()
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: heartbeatInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                await self?.send(type: "ping")
            }
        }
    }
    
    private func sendAuthToken() async {
        if let token = authToken {
            await send(type: "auth", data: ["token": token])
        }
    }
    
    private func queueMessage(_ message: WebSocketMessage) async {
        // Limit queue size
        if messageQueue.count >= messageQueueLimit {
            messageQueue.removeFirst()
        }
        messageQueue.append(message)
    }
    
    private func processMessageQueue() async {
        let messages = messageQueue
        messageQueue.removeAll()
        
        for message in messages {
            await sendMessage(message)
        }
    }
    
    private func setupNotificationObservers() {
        // App lifecycle
        NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)
            .sink { [weak self] _ in
                Task { @MainActor in
                    if self?.connectionState == .disconnected {
                        self?.connect()
                    }
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIApplication.willResignActiveNotification)
            .sink { [weak self] _ in
                Task { @MainActor in
                    self?.disconnect()
                }
            }
            .store(in: &cancellables)
        
        // Network status changes
        NetworkMonitor.shared.$isConnected
            .removeDuplicates()
            .sink { [weak self] isConnected in
                Task { @MainActor in
                    if isConnected && self?.connectionState == .disconnected {
                        self?.connect()
                    } else if !isConnected {
                        self?.disconnect()
                    }
                }
            }
            .store(in: &cancellables)
    }
}

// MARK: - Extensions for JSON Encoding/Decoding
extension KeyedDecodingContainer {
    func decode(_ type: [String: Any].Type, forKey key: K) throws -> [String: Any] {
        let container = try nestedContainer(keyedBy: JSONCodingKey.self, forKey: key)
        return try container.decode(type)
    }
    
    func decode(_ type: [String: Any].Type) throws -> [String: Any] {
        var dictionary = [String: Any]()
        
        for key in allKeys {
            if let value = try? decode(Bool.self, forKey: key) {
                dictionary[key.stringValue] = value
            } else if let value = try? decode(Int.self, forKey: key) {
                dictionary[key.stringValue] = value
            } else if let value = try? decode(Double.self, forKey: key) {
                dictionary[key.stringValue] = value
            } else if let value = try? decode(String.self, forKey: key) {
                dictionary[key.stringValue] = value
            } else if let value = try? decode([String: Any].self, forKey: key) {
                dictionary[key.stringValue] = value
            }
        }
        
        return dictionary
    }
}

extension KeyedEncodingContainer {
    mutating func encode(_ value: [String: Any], forKey key: K) throws {
        var container = nestedContainer(keyedBy: JSONCodingKey.self, forKey: key)
        try container.encode(value)
    }
    
    mutating func encode(_ value: [String: Any]) throws {
        for (key, val) in value {
            let key = JSONCodingKey(stringValue: key)
            
            guard let typedKey = key as? K else { continue }
            
            if let val = val as? Bool {
                try encode(val, forKey: typedKey)
            } else if let val = val as? Int {
                try encode(val, forKey: typedKey)
            } else if let val = val as? Double {
                try encode(val, forKey: typedKey)
            } else if let val = val as? String {
                try encode(val, forKey: typedKey)
            } else if let val = val as? [String: Any] {
                try encode(val, forKey: typedKey)
            }
        }
    }
}

struct JSONCodingKey: CodingKey {
    var stringValue: String
    var intValue: Int?
    
    init(stringValue: String) {
        self.stringValue = stringValue
    }
    
    init?(intValue: Int) {
        self.intValue = intValue
        self.stringValue = "\(intValue)"
    }
}