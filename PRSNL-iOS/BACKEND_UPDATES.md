# PRSNL Backend Updates for iOS Development

## Recent Changes (2025-07-07)

### 🆕 Attachments Support Added

The backend now supports attachments (images) for articles. This is a **breaking change** for the Item model.

#### Updated Item Model
```swift
// Add to your Item struct
let attachments: [Attachment]?

// New Attachment model
struct Attachment: Codable {
    let id: String
    let fileType: String    // "image" or "video"
    let filePath: String    // Relative path like /media/attachments/...
    let mimeType: String    // e.g., "image/jpeg"
    let metadata: AttachmentMetadata?
    
    enum CodingKeys: String, CodingKey {
        case id
        case fileType = "file_type"
        case filePath = "file_path"
        case mimeType = "mime_type"
        case metadata
    }
}

struct AttachmentMetadata: Codable {
    let alt: String?        // Alt text for images
    let title: String?      // Image title
    let isRemote: Bool?     // If image is external
    let index: Int?         // Order in article
}
```

#### What This Means for iOS
1. **Article images are now available** - Backend extracts images from articles
2. **Display in ItemCard** - Show first image as thumbnail
3. **Gallery in Detail View** - Show all images in article
4. **Image URLs** - Construct full URL: `baseURL + attachment.filePath`

### Example API Response with Attachments
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Article with Images",
    "content": "...",
    "attachments": [
        {
            "id": "abc123",
            "file_type": "image",
            "file_path": "/media/attachments/2025/01/image1.jpg",
            "mime_type": "image/jpeg",
            "metadata": {
                "alt": "Description of image",
                "title": "Image Title",
                "isRemote": false,
                "index": 0
            }
        }
    ]
}
```

### 🔧 Other Backend Status

1. **WebSocket Authentication**: Currently public (no auth required)
2. **AI Suggestions**: Some connection issues being debugged
3. **Analytics Endpoints**: Fully functional with new advanced endpoints
4. **Semantic Search**: Working with Ollama embeddings

### 📝 Notes for Kilo Code

1. **Update your Item model** to include optional attachments array
2. **Image Display Logic**:
   ```swift
   // In ItemCard
   if let firstImage = item.attachments?.first(where: { $0.fileType == "image" }) {
       // Show as thumbnail
   }
   
   // Full image URL
   let imageURL = baseURL + firstImage.filePath
   ```

3. **Handle Missing Attachments**: Array might be nil or empty for older items

4. **Test with Real Data**: Create new articles to see attachments

This is the only significant backend change that affects the iOS app. The core API contract remains the same.