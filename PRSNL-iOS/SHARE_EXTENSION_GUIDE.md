# PRSNL iOS Share Extension Guide

## Overview
The iOS Share Extension should replicate the Chrome extension's capture functionality, allowing users to save content from any app directly to their PRSNL knowledge base.

## Chrome Extension Feature Parity

### Core Functionality to Replicate
1. **Full Page Capture** - Save URL and title
2. **Selection Capture** - Save selected text with source
3. **Tag Management** - Add tags before saving
4. **Visual Feedback** - Success/error notifications

### Data Format (Must Match Exactly)
```json
{
    "url": "https://example.com",
    "title": "Page Title", 
    "content": "Selected text or empty for full page",
    "tags": ["tag1", "tag2"],
    "type": "page" or "selection"
}
```

## iOS Share Extension Implementation

### 1. Project Setup

Create Share Extension target:
1. File → New → Target → Share Extension
2. Name: "PRSNL Share"
3. Minimum iOS: 17.0

### 2. Info.plist Configuration

```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionAttributes</key>
    <dict>
        <key>NSExtensionActivationRule</key>
        <dict>
            <key>NSExtensionActivationSupportsWebURLWithMaxCount</key>
            <integer>1</integer>
            <key>NSExtensionActivationSupportsText</key>
            <true/>
            <key>NSExtensionActivationSupportsWebPageWithMaxCount</key>
            <integer>1</integer>
        </dict>
    </dict>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.share-services</string>
    <key>NSExtensionPrincipalClass</key>
    <string>$(PRODUCT_MODULE_NAME).ShareViewController</string>
</dict>
```

### 3. Share View Controller

```swift
import SwiftUI
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Use SwiftUI for the interface
        let contentView = ShareView(extensionContext: extensionContext)
        let hostingController = UIHostingController(rootView: contentView)
        
        addChild(hostingController)
        view.addSubview(hostingController.view)
        hostingController.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            hostingController.view.topAnchor.constraint(equalTo: view.topAnchor),
            hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            hostingController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        hostingController.didMove(toParent: self)
    }
}

struct ShareView: View {
    let extensionContext: NSExtensionContext?
    @State private var shareData = ShareData()
    @State private var tags: [String] = []
    @State private var tagInput = ""
    @State private var isLoading = false
    @State private var error: String?
    @State private var success = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                // Source Preview
                if !shareData.isEmpty {
                    SharePreview(data: shareData)
                        .padding(.horizontal)
                }
                
                // Tag Input
                VStack(alignment: .leading, spacing: 8) {
                    Text("Tags")
                        .font(.headline)
                    
                    HStack {
                        TextField("Add tags", text: $tagInput)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .onSubmit {
                                addTag()
                            }
                        
                        Button("Add", action: addTag)
                            .disabled(tagInput.isEmpty)
                    }
                    
                    // Tag Chips
                    if !tags.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                ForEach(tags, id: \.self) { tag in
                                    TagChip(tag: tag) {
                                        removeTag(tag)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal)
                
                Spacer()
                
                // Error Display
                if let error = error {
                    Text(error)
                        .foregroundColor(.red)
                        .padding(.horizontal)
                }
                
                // Action Buttons
                HStack {
                    Button("Cancel") {
                        cancel()
                    }
                    .foregroundColor(.red)
                    
                    Spacer()
                    
                    Button(action: capture) {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle())
                        } else {
                            Text("Save to PRSNL")
                        }
                    }
                    .disabled(isLoading || shareData.isEmpty)
                    .buttonStyle(.borderedProminent)
                    .tint(.prsnlRed)
                }
                .padding()
            }
            .navigationTitle("Save to PRSNL")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onAppear {
            loadShareData()
        }
        .onChange(of: success) { success in
            if success {
                // Auto-dismiss after success
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    self.extensionContext?.completeRequest(returningItems: nil)
                }
            }
        }
    }
    
    private func loadShareData() {
        guard let extensionContext = extensionContext,
              let item = extensionContext.inputItems.first as? NSExtensionItem else {
            return
        }
        
        for attachment in item.attachments ?? [] {
            if attachment.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.url.identifier) { (url, error) in
                    if let url = url as? URL {
                        DispatchQueue.main.async {
                            self.shareData.url = url.absoluteString
                            self.shareData.title = item.attributedContentText?.string ?? url.host ?? "Untitled"
                            self.shareData.type = .page
                        }
                    }
                }
            }
            
            if attachment.hasItemConformingToTypeIdentifier(UTType.text.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.text.identifier) { (text, error) in
                    if let text = text as? String {
                        DispatchQueue.main.async {
                            self.shareData.content = text
                            self.shareData.type = .selection
                        }
                    }
                }
            }
        }
    }
    
    private func addTag() {
        let sanitized = tagInput
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
        
        if !sanitized.isEmpty && !tags.contains(sanitized) {
            tags.append(sanitized)
            tagInput = ""
        }
    }
    
    private func removeTag(_ tag: String) {
        tags.removeAll { $0 == tag }
    }
    
    private func capture() {
        isLoading = true
        error = nil
        
        Task {
            do {
                // Get API configuration from app group
                let apiURL = getAPIURL()
                let apiKey = getAPIKey()
                
                // Prepare request
                let captureRequest = CaptureRequest(
                    url: shareData.url,
                    content: shareData.content,
                    title: shareData.title,
                    tags: tags
                )
                
                // Send to backend
                try await sendCapture(captureRequest, to: apiURL, with: apiKey)
                
                await MainActor.run {
                    success = true
                    showSuccessAnimation()
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
    
    private func cancel() {
        extensionContext?.completeRequest(returningItems: nil)
    }
    
    private func showSuccessAnimation() {
        // Visual feedback matching Chrome extension
        withAnimation(.easeInOut(duration: 0.3)) {
            // Show success state
        }
    }
}

// MARK: - Supporting Types

struct ShareData {
    var url: String?
    var title: String?
    var content: String?
    var type: CaptureType = .page
    
    var isEmpty: Bool {
        url == nil && content == nil
    }
}

enum CaptureType: String {
    case page = "page"
    case selection = "selection"
}

struct SharePreview: View {
    let data: ShareData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let title = data.title {
                Text(title)
                    .font(.headline)
                    .lineLimit(1)
            }
            
            if let url = data.url {
                Text(url)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            
            if let content = data.content {
                Text(content)
                    .font(.body)
                    .lineLimit(3)
                    .padding(.top, 4)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
}

struct TagChip: View {
    let tag: String
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(tag)
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.prsnlRed.opacity(0.2))
        .foregroundColor(.prsnlRed)
        .cornerRadius(15)
    }
}
```

### 4. App Group Configuration

For sharing data between main app and extension:

1. Add App Group capability to both targets
2. Use group identifier: `group.ai.prsnl.shared`

```swift
// Shared configuration access
extension ShareView {
    private func getAPIURL() -> String {
        let defaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
        return defaults?.string(forKey: "apiURL") ?? "http://localhost:8000"
    }
    
    private func getAPIKey() -> String? {
        // Access shared keychain
        return KeychainService.shared.get(.apiKey)
    }
    
    private func sendCapture(_ request: CaptureRequest, to baseURL: String, with apiKey: String?) async throws {
        let url = URL(string: "\(baseURL)/api/capture")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let apiKey = apiKey {
            urlRequest.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        
        urlRequest.httpBody = try JSONEncoder.prsnlEncoder.encode(request)
        
        let (data, response) = try await URLSession.shared.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            let error = try? JSONDecoder().decode(APIError.self, from: data)
            throw error ?? APIError.unknown(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0, 
                                           message: "Capture failed")
        }
    }
}
```

### 5. Keyboard Shortcuts (Main App)

To match Chrome extension's Cmd+Shift+S:

```swift
// In main app's ContentView
.keyboardShortcut("s", modifiers: [.command, .shift])
.onReceive(NotificationCenter.default.publisher(for: .captureShortcut)) { _ in
    showQuickCapture()
}
```

## Special Considerations

### Video URL Detection
The iOS share extension should detect video platforms like the Chrome extension:

```swift
extension String {
    var isVideoURL: Bool {
        let videoPatterns = [
            "youtube.com/watch",
            "youtu.be/",
            "instagram.com/reel",
            "instagram.com/p/",
            "tiktok.com/",
            "twitter.com/.*/status"
        ]
        
        return videoPatterns.contains { self.contains($0) }
    }
}
```

### Offline Handling
```swift
// Queue captures when offline
class CaptureQueue {
    static let shared = CaptureQueue()
    
    func queueCapture(_ request: CaptureRequest) {
        // Save to Core Data or file
        // Retry when connection restored
    }
}
```

## Testing

1. **Test Share Sources**:
   - Safari web pages
   - Selected text from Notes
   - URLs from other apps
   - Social media posts

2. **Error Scenarios**:
   - No network connection
   - Invalid API key
   - Backend down
   - Rate limiting

3. **Edge Cases**:
   - Very long text
   - Special characters in tags
   - Multiple attachments

This implementation provides full feature parity with the Chrome extension while following iOS design patterns.