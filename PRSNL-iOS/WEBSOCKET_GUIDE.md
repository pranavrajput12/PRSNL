# PRSNL iOS WebSocket Implementation Guide

## Overview
PRSNL provides WebSocket endpoints for real-time features like AI streaming responses and live tag suggestions.

## WebSocket Endpoints

### 1. AI Stream
- **URL**: `ws://localhost:8000/ws/ai-stream/{client_id}`
- **Purpose**: Stream AI responses in real-time
- **Use Case**: Show AI processing results as they're generated

### 2. AI Tag Stream  
- **URL**: `ws://localhost:8000/ws/ai-tag-stream/{client_id}`
- **Purpose**: Stream AI tag suggestions in real-time
- **Use Case**: Live tag suggestions while user types

## Message Formats

### Sending Messages
```json
{
    "content": "User's query or content to process"
}
```

### Receiving Messages
```json
// Success chunk
{
    "chunk": "Partial response text..."
}

// Error message
{
    "error": "Error description"
}

// Other message types (from frontend)
{
    "type": "progress",    // Processing progress
    "type": "update",      // General updates
    "type": "notification", // User notifications
    "type": "error"        // Error messages
}
```

## iOS Implementation

### Using URLSessionWebSocketTask

```swift
import Foundation
import Combine

class WebSocketManager: ObservableObject {
    private var webSocketTask: URLSessionWebSocketTask?
    private let session = URLSession.shared
    
    @Published var messages: [String] = []
    @Published var isConnected = false
    @Published var error: Error?
    
    private let clientId = UUID().uuidString
    
    func connect(to endpoint: WebSocketEndpoint) {
        guard let url = buildURL(for: endpoint) else { return }
        
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true
        
        receiveMessage()
    }
    
    private func buildURL(for endpoint: WebSocketEndpoint) -> URL? {
        let baseURL = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
        let wsURL = baseURL.replacingOccurrences(of: "http", with: "ws")
        
        switch endpoint {
        case .aiStream:
            return URL(string: "\(wsURL)/ws/ai-stream/\(clientId)")
        case .tagStream:
            return URL(string: "\(wsURL)/ws/ai-tag-stream/\(clientId)")
        }
    }
    
    func send(_ content: String) {
        let message = WebSocketMessage(content: content)
        
        guard let data = try? JSONEncoder().encode(message) else { return }
        let string = String(data: data, encoding: .utf8)!
        
        webSocketTask?.send(.string(string)) { [weak self] error in
            if let error = error {
                DispatchQueue.main.async {
                    self?.error = error
                }
            }
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                
                // Continue receiving
                self?.receiveMessage()
                
            case .failure(let error):
                DispatchQueue.main.async {
                    self?.error = error
                    self?.isConnected = false
                }
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let response = try? JSONDecoder().decode(WebSocketResponse.self, from: data) else {
            return
        }
        
        DispatchQueue.main.async {
            if let chunk = response.chunk {
                self.messages.append(chunk)
            } else if let error = response.error {
                self.error = WebSocketError.serverError(error)
            }
        }
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        isConnected = false
        messages.removeAll()
    }
}

// MARK: - Supporting Types

enum WebSocketEndpoint {
    case aiStream
    case tagStream
}

struct WebSocketMessage: Codable {
    let content: String
}

struct WebSocketResponse: Codable {
    let chunk: String?
    let error: String?
}

enum WebSocketError: LocalizedError {
    case serverError(String)
    
    var errorDescription: String? {
        switch self {
        case .serverError(let message):
            return "Server error: \(message)"
        }
    }
}
```

### Using in SwiftUI Views

```swift
struct AIStreamView: View {
    @StateObject private var webSocket = WebSocketManager()
    @State private var inputText = ""
    @State private var streamedResponse = ""
    
    var body: some View {
        VStack {
            TextEditor(text: $inputText)
                .frame(height: 100)
                .padding()
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )
            
            Button("Process with AI") {
                processWithAI()
            }
            .disabled(!webSocket.isConnected || inputText.isEmpty)
            
            ScrollView {
                Text(streamedResponse)
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            
            if let error = webSocket.error {
                Text(error.localizedDescription)
                    .foregroundColor(.red)
                    .padding()
            }
        }
        .padding()
        .onAppear {
            webSocket.connect(to: .aiStream)
        }
        .onDisappear {
            webSocket.disconnect()
        }
        .onReceive(webSocket.$messages) { messages in
            streamedResponse = messages.joined()
        }
    }
    
    private func processWithAI() {
        streamedResponse = ""
        webSocket.send(inputText)
    }
}
```

### Tag Suggestions Implementation

```swift
struct TagSuggestionView: View {
    @StateObject private var webSocket = WebSocketManager()
    @State private var inputText = ""
    @State private var suggestedTags: [String] = []
    @State private var selectedTags: Set<String> = []
    
    var body: some View {
        VStack {
            TextField("Enter content for tag suggestions", text: $inputText)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .onSubmit {
                    getSuggestions()
                }
            
            if !suggestedTags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(suggestedTags, id: \.self) { tag in
                            TagChip(
                                tag: tag,
                                isSelected: selectedTags.contains(tag)
                            ) {
                                toggleTag(tag)
                            }
                        }
                    }
                    .padding(.horizontal)
                }
            }
            
            if !selectedTags.isEmpty {
                VStack(alignment: .leading) {
                    Text("Selected Tags:")
                        .font(.headline)
                    
                    Text(selectedTags.joined(separator: ", "))
                        .foregroundColor(.secondary)
                }
                .padding()
            }
        }
        .padding()
        .onAppear {
            webSocket.connect(to: .tagStream)
        }
        .onDisappear {
            webSocket.disconnect()
        }
        .onChange(of: webSocket.messages) { messages in
            // Parse tag suggestions from streamed chunks
            parseTags(from: messages)
        }
    }
    
    private func getSuggestions() {
        suggestedTags.removeAll()
        webSocket.send(inputText)
    }
    
    private func toggleTag(_ tag: String) {
        if selectedTags.contains(tag) {
            selectedTags.remove(tag)
        } else {
            selectedTags.insert(tag)
        }
    }
    
    private func parseTags(from messages: [String]) {
        // Parse comma-separated tags from AI response
        let fullResponse = messages.joined()
        suggestedTags = fullResponse
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }
}

struct TagChip: View {
    let tag: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(tag)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.prsnlRed : Color.gray.opacity(0.2))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(15)
        }
    }
}
```

## Reconnection Strategy

```swift
extension WebSocketManager {
    func setupAutoReconnect() {
        Timer.publish(every: 30, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.sendPing()
            }
            .store(in: &cancellables)
    }
    
    private func sendPing() {
        webSocketTask?.sendPing { [weak self] error in
            if let error = error {
                print("Ping failed: \(error)")
                self?.reconnect()
            }
        }
    }
    
    private func reconnect() {
        disconnect()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
            self?.connect(to: self?.currentEndpoint ?? .aiStream)
        }
    }
}
```

## Best Practices

1. **Unique Client IDs**: Always use unique client IDs (UUID) for each connection
2. **Error Handling**: Implement robust error handling and reconnection logic
3. **Memory Management**: Use weak references to avoid retain cycles
4. **Thread Safety**: Update UI on main thread
5. **Connection Lifecycle**: Connect on appear, disconnect on disappear
6. **Message Parsing**: Validate JSON before parsing
7. **Rate Limiting**: Don't send messages too frequently

## Testing WebSocket Features

```swift
// For testing without backend
class MockWebSocketManager: WebSocketManager {
    override func connect(to endpoint: WebSocketEndpoint) {
        super.isConnected = true
        
        // Simulate AI responses
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.messages = ["This ", "is ", "a ", "simulated ", "response."]
        }
    }
    
    override func send(_ content: String) {
        // Simulate processing
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            if content.contains("tag") {
                self.messages = ["technology", "ai", "swift", "ios"]
            } else {
                self.messages = ["Processed: \(content)"]
            }
        }
    }
}
```

## Integration with API Client

The WebSocket features complement the REST API:
- Use REST API for CRUD operations
- Use WebSocket for real-time updates
- Combine both for responsive UX

Example: When capturing content, use REST to save, then WebSocket to stream AI processing results.