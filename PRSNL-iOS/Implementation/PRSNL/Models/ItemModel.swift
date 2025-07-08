import Foundation
import SwiftUI

/// Represents a knowledge item in the PRSNL system
struct Item: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let content: String
    let url: String?
    let summary: String?
    let status: ItemStatus
    let createdAt: Date
    let updatedAt: Date
    let accessCount: Int
    let accessedAt: Date?
    let tags: [String]
    let itemType: ItemType
    let attachments: [Attachment]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case content
        case url
        case summary
        case status
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case accessCount = "access_count"
        case accessedAt = "accessed_at"
        case tags
        case itemType = "item_type"
        case attachments
    }
}

/// The status of a knowledge item
enum ItemStatus: String, Codable {
    case active
    case archived
    case deleted
}

/// The type of knowledge item
enum ItemType: String, Codable {
    case note
    case article
    case video
    case audio
    case image
    case document
    case other
}

/// Represents an attachment to a PRSNL item
struct Attachment: Codable, Hashable {
    let id: String
    let fileType: String  // "image" or "video"
    let filePath: String  // Relative path like /media/attachments/...
    let mimeType: String  // e.g., "image/jpeg"
    let metadata: AttachmentMetadata?
    
    enum CodingKeys: String, CodingKey {
        case id
        case fileType = "file_type"
        case filePath = "file_path"
        case mimeType = "mime_type"
        case metadata
    }
}

struct AttachmentMetadata: Codable, Hashable {
    let alt: String?
    let title: String?
    let isRemote: Bool?
    let index: Int?
    
    enum CodingKeys: String, CodingKey {
        case alt
        case title
        case isRemote = "is_remote"
        case index
    }
}

// Extend Item with helper methods
extension Item {
    /// Returns a formatted string with comma-separated tags
    var formattedTags: String {
        return tags.joined(separator: ", ")
    }
    
    /// Returns whether this item has any attachments
    var hasAttachments: Bool {
        return attachments?.isEmpty == false
    }
    
    /// Returns a readable timestamp for the item's creation date
    var formattedCreationDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: createdAt)
    }
    
    /// Returns the full URL for an attachment
    func getFullAttachmentURL(for attachment: Attachment, baseURL: String) -> URL? {
        if let meta = attachment.metadata, meta.isRemote == true, 
           let url = URL(string: attachment.filePath) {
            return url
        } else {
            // For local files, prepend the base URL to the relative path
            let urlString = baseURL.hasSuffix("/") 
                ? baseURL + attachment.filePath.dropFirst()  // Remove leading slash if base URL has trailing slash
                : baseURL + attachment.filePath
            return URL(string: urlString)
        }
    }
}