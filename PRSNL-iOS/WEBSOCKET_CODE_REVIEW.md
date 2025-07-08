# WebSocket Implementation Code Review

## Critical Issues Found

### 1. WebSocketManager Issues

#### 🔴 Race Condition in Connection State
```swift
// Line 159: Setting connected before actually connected
connectionState = .connected
reconnectAttempts = 0
```
**Issue:** The connection state is set to `.connected` immediately after calling `resume()`, but the actual connection may not be established yet.
**Fix:** Should wait for a successful handshake or connection confirmation from the server.

#### 🔴 Memory Leak in Timer Handling
```swift
// Line 313: Timer holds strong reference to self
reconnectTimer = Timer.scheduledTimer(withTimeInterval: reconnectDelay * Double(reconnectAttempts), repeats: false) { [weak self] _ in
```
**Issue:** While the closure captures `self` weakly, the timer itself may still hold a reference.
**Fix:** Should invalidate timers before reassigning.

#### 🟡 Missing Message Queue
**Issue:** Messages sent while connecting or reconnecting are lost.
**Fix:** Implement a message queue that buffers messages during connection establishment.

#### 🟡 Unsafe Force Casting
```swift
// Line 411, 413, 415, 417, 419: Force casting to K
try encode(val, forKey: key as! K)
```
**Issue:** Force unwrapping could crash if types don't match.
**Fix:** Use proper type checking or generic constraints.

### 2. LiveTagService Issues

#### 🔴 Potential UI Thread Blocking
```swift
// Multiple UI updates without proper threading
@MainActor
class LiveTagService: ObservableObject {
```
**Issue:** All operations are on main thread, including potentially heavy operations.
**Fix:** Move non-UI operations to background queues.

#### 🟡 Cache Size Management
```swift
// Line 167: Simple FIFO cache removal
let keysToRemove = Array(suggestionCache.keys.prefix(10))
```
**Issue:** Removes oldest entries regardless of usage frequency.
**Fix:** Implement LRU (Least Recently Used) cache.

#### 🟡 Missing Error Handling
**Issue:** No error handling for failed WebSocket sends.
**Fix:** Add proper error handling and user feedback.

### 3. RealtimeUpdateService Issues

#### 🔴 Core Data Thread Safety
```swift
// Direct Core Data access from various threads
coreDataManager.createItem(...)
coreDataManager.updateItem(...)
```
**Issue:** Core Data operations should be performed on proper context queues.
**Fix:** Ensure all Core Data operations use the correct context.

#### 🟡 Missing Deduplication
**Issue:** Same update could be processed multiple times.
**Fix:** Track processed update IDs to prevent duplicates.

## Performance Concerns

### 1. Excessive Timer Usage
- Heartbeat timer runs every 30 seconds regardless of activity
- Consider using exponential backoff for reconnection delays
- Timers should be paused when app is backgrounded

### 2. Message Processing Overhead
- JSON encoding/decoding for every message
- Consider using more efficient protocols (MessagePack, Protocol Buffers)
- Batch message processing where possible

### 3. Memory Usage
- Unbounded message handler storage
- No cleanup of old pending updates
- Tag suggestion cache grows without bounds

## Security Concerns

### 1. Token Exposure
- Auth token stored in UserDefaults (not secure)
- Token sent in clear text over WebSocket
- No token refresh mechanism

### 2. Message Validation
- No validation of incoming message structure
- No sanitization of data from server
- Potential for malicious payloads

## Stress Testing Scenarios

### 1. Connection Stability
- Rapid connect/disconnect cycles
- Network switching (WiFi to cellular)
- Server restart while connected
- Invalid/expired auth tokens

### 2. Message Flooding
- Receive 1000+ messages per second
- Send messages while disconnected
- Large message payloads (>1MB)
- Malformed JSON messages

### 3. Memory Pressure
- Long-running connections (hours/days)
- Accumulation of pending updates
- Large tag suggestion responses
- Multiple reconnection attempts

## Recommended Improvements

### 1. Connection Management
```swift
// Add connection state machine
enum ConnectionState {
    case disconnected(Error?)
    case connecting
    case handshaking
    case authenticated
    case connected
    case reconnecting(attempt: Int)
}

// Add message queue
private var messageQueue: [WebSocketMessage] = []
private let messageQueueLimit = 100
```

### 2. Error Recovery
```swift
// Add exponential backoff
private func calculateReconnectDelay(attempt: Int) -> TimeInterval {
    let baseDelay = 1.0
    let maxDelay = 60.0
    let delay = min(baseDelay * pow(2.0, Double(attempt)), maxDelay)
    return delay + Double.random(in: 0...1) // Add jitter
}
```

### 3. Resource Management
```swift
// Add cleanup timers
private func startCleanupTimer() {
    Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
        self?.cleanupOldHandlers()
        self?.cleanupPendingUpdates()
        self?.trimCaches()
    }
}
```

### 4. Thread Safety
```swift
// Use actors for thread safety
actor WebSocketConnection {
    private var task: URLSessionWebSocketTask?
    
    func send(_ message: WebSocketMessage) async throws {
        guard let task = task else { throw WebSocketError.notConnected }
        try await task.send(.string(message.encoded()))
    }
}
```

### 5. Monitoring
```swift
// Add metrics collection
struct WebSocketMetrics {
    var messagesReceived = 0
    var messagesSent = 0
    var reconnectAttempts = 0
    var connectionDuration: TimeInterval = 0
    var lastError: Error?
}
```

## Testing Recommendations

1. **Unit Tests**
   - Mock WebSocket connections
   - Test message encoding/decoding
   - Test error handling paths

2. **Integration Tests**
   - Test with real backend
   - Test auth flows
   - Test reconnection scenarios

3. **Performance Tests**
   - Message throughput benchmarks
   - Memory usage under load
   - CPU usage during heavy updates

4. **Stress Tests**
   - Network failure simulation
   - Server overload scenarios
   - Malicious input testing

## Priority Fixes

1. **High Priority**
   - Fix connection state race condition
   - Add proper Core Data threading
   - Implement message queuing
   - Fix force unwrapping issues

2. **Medium Priority**
   - Add exponential backoff
   - Implement LRU cache
   - Add message deduplication
   - Improve error handling

3. **Low Priority**
   - Add metrics collection
   - Optimize JSON processing
   - Implement connection pooling
   - Add compression support