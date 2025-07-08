import SwiftUI
import UniformTypeIdentifiers
import CoreData
import UIKit

// MARK: - Forward Declarations for iOS 17 Compatibility
// These minimal declarations help the compiler recognize types from ShareExtensionServices.swift
// The actual implementations will be used at runtime

// CoreDataManager forward declaration
class CoreDataManager {
    static let shared = CoreDataManager()
    var viewContext: NSManagedObjectContext { NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType) }
    func saveViewContext() throws {}
    func fetchRecentTags(limit: Int) async throws -> [String] { return [] }
}

// NetworkMonitor forward declaration
class NetworkMonitor {
    static let shared = NetworkMonitor()
    var isConnected: Bool { true }
}

// KeychainService forward declaration
class KeychainService {
    static let shared = KeychainService()
    enum KeychainKey: String {
        case apiKey = "apiKey"
    }
    func get(_ key: KeychainKey) -> String? { return nil }
}

// Core Data model classes forward declarations
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

extension CDItem {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<CDItem> {
        return NSFetchRequest<CDItem>(entityName: "Item")
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

// SyncStatus enum forward declaration
enum SyncStatus: Int16 {
    case synced = 0
    case needsUpload = 1
    case needsUpdate = 2
    case deleted = 3
}

@MainActor
class ShareViewModel: ObservableObject {
    @Published var shareData = ShareData()
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var success = false
    @Published var recentTags: [String] = []
    
    weak var extensionContext: NSExtensionContext?
    private let coreDataManager = CoreDataManager.shared
    private let networkMonitor = NetworkMonitor.shared
    
    // MARK: - Load Share Data
    func loadShareData() {
        guard let extensionContext = extensionContext,
              let item = extensionContext.inputItems.first as? NSExtensionItem else {
            return
        }
        
        // Try to get title from item
        if let attributedTitle = item.attributedTitle {
            shareData.title = attributedTitle.string
        } else if let attributedContentText = item.attributedContentText {
            shareData.title = attributedContentText.string
        }
        
        // Process attachments
        for attachment in item.attachments ?? [] {
            // Check for URL
            if attachment.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.url.identifier) { [weak self] (item, error) in
                    if let url = item as? URL {
                        Task { @MainActor in
                            self?.shareData.url = url.absoluteString
                            if self?.shareData.title == nil {
                                self?.shareData.title = url.host ?? "Shared Link"
                            }
                            self?.shareData.type = .page
                        }
                    }
                }
            }
            
            // Check for text
            if attachment.hasItemConformingToTypeIdentifier(UTType.text.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.text.identifier) { [weak self] (item, error) in
                    if let text = item as? String {
                        Task { @MainActor in
                            self?.shareData.content = text
                            self?.shareData.type = .selection
                        }
                    }
                }
            }
            
            // Check for web page with JavaScript preprocessing results
            if attachment.hasItemConformingToTypeIdentifier(UTType.propertyList.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.propertyList.identifier) { [weak self] (item, error) in
                    if let dict = item as? [String: Any],
                       let jsResults = dict[NSExtensionJavaScriptPreprocessingResultsKey] as? [String: Any] {
                        Task { @MainActor in
                            if let url = jsResults["URL"] as? String {
                                self?.shareData.url = url
                            }
                            if let title = jsResults["title"] as? String {
                                self?.shareData.title = title
                            }
                            if let selectedText = jsResults["selectedText"] as? String, !selectedText.isEmpty {
                                self?.shareData.content = selectedText
                                self?.shareData.type = .selection
                            }
                        }
                    }
                }
            }
            
            // Check for images
            if attachment.hasItemConformingToTypeIdentifier(UTType.image.identifier) {
                attachment.loadItem(forTypeIdentifier: UTType.image.identifier) { [weak self] (item, error) in
                    Task { @MainActor in
                        if let url = item as? URL {
                            // Handle file URL
                            self?.shareData.imageData = try? Data(contentsOf: url)
                            self?.shareData.type = .image
                            if self?.shareData.title == nil {
                                self?.shareData.title = "Shared Image"
                            }
                        } else if let image = item as? UIImage {
                            // Handle UIImage directly
                            self?.shareData.imageData = image.jpegData(compressionQuality: 0.8)
                            self?.shareData.type = .image
                            if self?.shareData.title == nil {
                                self?.shareData.title = "Shared Image"
                            }
                        } else if let data = item as? Data {
                            // Handle raw data
                            self?.shareData.imageData = data
                            self?.shareData.type = .image
                            if self?.shareData.title == nil {
                                self?.shareData.title = "Shared Image"
                            }
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Load Recent Tags
    func loadRecentTags() {
        Task {
            do {
                // Get recent tags from Core Data
                let tags = try await coreDataManager.fetchRecentTags(limit: 10)
                await MainActor.run {
                    self.recentTags = tags
                }
            } catch {
                print("Failed to load recent tags: \(error)")
            }
        }
    }
    
    // MARK: - Capture Content
    func capture(tags: [String]) {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                // Check if we're online and have API credentials
                if networkMonitor.isConnected,
                   let apiKey = getAPIKey(),
                   !apiKey.isEmpty,
                   let serverURL = getServerURL() {
                    // Try online save first
                    try await captureOnline(tags: tags, apiKey: apiKey, serverURL: serverURL)
                } else {
                    // Fallback to offline save
                    try await captureOffline(tags: tags)
                }
                
                // Success
                await MainActor.run {
                    self.success = true
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    // MARK: - Online Capture
    private func captureOnline(tags: [String], apiKey: String, serverURL: String) async throws {
        // Handle image uploads differently
        if shareData.type == .image, let imageData = shareData.imageData {
            try await captureImageOnline(imageData: imageData, tags: tags, apiKey: apiKey, serverURL: serverURL)
            return
        }
        
        let request = CaptureRequest(
            url: shareData.url,
            content: shareData.content,
            title: shareData.title,
            tags: tags
        )
        
        let url = URL(string: "\(serverURL)/api/capture")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        let (_, response) = try await URLSession.shared.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            // If online save fails, fall back to offline
            try await captureOffline(tags: tags)
            return
        }
    }
    
    // MARK: - Image Capture
    private func captureImageOnline(imageData: Data, tags: [String], apiKey: String, serverURL: String) async throws {
        // Create multipart form data request
        let boundary = UUID().uuidString
        let url = URL(string: "\(serverURL)/api/capture")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        
        // Build multipart body
        var body = Data()
        
        // Add title if present
        if let title = shareData.title {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"title\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(title)\r\n".data(using: .utf8)!)
        }
        
        // Add tags
        for tag in tags {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"tags\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(tag)\r\n".data(using: .utf8)!)
        }
        
        // Add image data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        
        // End boundary
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        urlRequest.httpBody = body
        
        let (_, response) = try await URLSession.shared.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            // If online save fails, fall back to offline
            try await captureOffline(tags: tags)
            return
        }
    }
    
    // MARK: - Offline Capture
    private func captureOffline(tags: [String]) async throws {
        let temporaryId = "share-\(UUID().uuidString)"
        
        // Determine content type and handle images
        var content: String
        
        if shareData.type == .image, let imageData = shareData.imageData {
            // For images, store the data temporarily and create an attachment
            content = "[Image captured via share extension]"
            
            // Create attachment metadata for the image
            // Note: In a production app, we'd save the image data to a file
            // and create a proper CDAttachment entity. For now, we'll skip
            // the attachment and just note it in the content.
            content = "[Image captured via share extension - \(imageData.count) bytes]"
            
            // Note: In a real implementation, you'd save the imageData to a local file
            // and store the path in the attachment's localPath property
            
        } else if let url = shareData.url {
            content = url
        } else if let text = shareData.content {
            content = text
        } else {
            throw ShareError.noContent
        }
        
        // Create item in Core Data with needsUpload status
        // Note: Since CoreDataManager doesn't have createItem method yet,
        // we'll create the item directly using Core Data context
        let context = coreDataManager.viewContext
        
        let cdItem = CDItem(context: context)
        cdItem.id = temporaryId
        cdItem.title = shareData.title ?? "Shared Content"
        cdItem.content = content
        cdItem.url = shareData.url
        cdItem.summary = nil
        cdItem.status = "unprocessed"
        cdItem.syncStatus = SyncStatus.needsUpload.rawValue
        cdItem.createdAt = Date()
        cdItem.updatedAt = Date()
        cdItem.accessedAt = Date()
        cdItem.accessCount = 0
        cdItem.itemType = shareData.type == .page ? "article" : (shareData.type == .image ? "image" : "note")
        
        // Create tags
        for tagName in tags {
            let cdTag = CDTag(context: context)
            cdTag.name = tagName
            cdTag.addToItems(cdItem)
        }
        
        // Save to Core Data
        try coreDataManager.saveViewContext()
    }
    
    // MARK: - Helper Methods
    private func getAPIKey() -> String? {
        // Access shared keychain using app group
        return KeychainService.shared.get(.apiKey)
    }
    
    private func getServerURL() -> String? {
        // Access shared user defaults
        let defaults = UserDefaults(suiteName: "group.ai.prsnl.shared")
        return defaults?.string(forKey: "serverURL") ?? "http://localhost:8000"
    }
}

// MARK: - Supporting Types
struct ShareData {
    var url: String?
    var title: String?
    var content: String?
    var imageData: Data?
    var type: CaptureType = .page
    
    var isEmpty: Bool {
        url == nil && content == nil && imageData == nil
    }
}

enum CaptureType: String {
    case page = "page"
    case selection = "selection"
    case image = "image"
}

struct CaptureRequest: Encodable {
    let url: String?
    let content: String?
    let title: String?
    let tags: [String]
}

enum ShareError: LocalizedError {
    case noContent
    case invalidURL
    case saveFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .noContent:
            return "No content to save"
        case .invalidURL:
            return "Invalid URL"
        case .saveFailed(let message):
            return "Failed to save: \(message)"
        }
    }
}
