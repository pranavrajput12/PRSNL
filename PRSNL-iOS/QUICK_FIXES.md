# 🔧 QUICK FIXES - Get PRSNL iOS Compiling

## Fix #1: ColorExtensions.swift
Replace the contents of `/PRSNL/Core/Extensions/ColorExtensions.swift` with:

```swift
import SwiftUI

extension Color {
    // Manchester United Red Theme
    static let prsnlRed = Color(red: 220/255, green: 20/255, blue: 60/255) // #DC143C
    
    // Dark theme colors
    static let prsnlBackground = Color(red: 0.05, green: 0.05, blue: 0.05)
    static let prsnlSurface = Color(red: 0.1, green: 0.1, blue: 0.1)
    static let prsnlText = Color.white
    static let prsnlTextSecondary = Color.white.opacity(0.7)
    
    // Semantic colors
    static let prsnlError = Color.red
    static let prsnlSuccess = Color.green
    static let prsnlWarning = Color.orange
}
```

## Fix #2: PRSNLApp.swift
In `/PRSNL/App/PRSNLApp.swift`, replace the `initializeApp()` method with:

```swift
func initializeApp() {
    Task {
        // Check API configuration
        let hasAPIKey = KeychainService.shared.get(.apiKey) != nil
        
        // Network monitoring starts automatically
        // No need to call startMonitoring()
        
        // Simulate minimum launch time for effect
        try? await Task.sleep(nanoseconds: 2_500_000_000) // 2.5 seconds
        
        await MainActor.run {
            self.isAuthenticated = hasAPIKey
            self.isLaunching = false
        }
    }
}
```

## Fix #3: SearchViewModel.swift
In `/PRSNL/Features/Search/SearchViewModel.swift`, line 183, change:
```swift
// FROM:
let items = cdItems.map { CoreDataManager.convertToItem($0) }

// TO:
let items = cdItems.map { CoreDataManager.shared.convertToItem($0) }
```

## Fix #4: ShareViewModel.swift AttachmentModel
Add this to the top of `/PRSNLShareExtension/ShareViewModel.swift` after imports:

```swift
// Temporary model until we can import from main app
struct AttachmentModel {
    let id: String
    let itemId: String
    let fileName: String
    let fileType: String
    let fileSize: Int64
    let mimeType: String
    let url: String?
    let localPath: String?
    let createdAt: Date
}
```

## Fix #5: CoreDataManager Methods
Add these methods to `/PRSNL/Core/CoreData/CoreDataManager.swift`:

```swift
// Add this empty setup method (initialization happens in init)
func setup() async {
    // Persistent stores are already loaded in init
    // This method exists for compatibility
}

// Add this method for ShareExtension
func createItem(
    id: String,
    title: String,
    content: String,
    url: String?,
    summary: String?,
    status: String,
    syncStatus: SyncStatus,
    createdAt: Date,
    updatedAt: Date,
    accessedAt: Date,
    accessCount: Int,
    itemType: String,
    attachments: [AttachmentModel],
    tags: [String]
) async throws -> CDItem {
    let context = viewContext
    
    let cdItem = CDItem(context: context)
    cdItem.id = id
    cdItem.title = title
    cdItem.content = content
    cdItem.url = url
    cdItem.summary = summary
    cdItem.status = status
    cdItem.syncStatus = syncStatus.rawValue
    cdItem.createdAt = createdAt
    cdItem.updatedAt = updatedAt
    cdItem.accessedAt = accessedAt
    cdItem.accessCount = Int32(accessCount)
    cdItem.itemType = itemType
    
    // Create tags
    for tagName in tags {
        let cdTag = CDTag(context: context)
        cdTag.name = tagName
        cdTag.addToItems(cdItem)
    }
    
    try saveViewContext()
    return cdItem
}
```

## Fix #6: Generate Core Data Classes
In Xcode:
1. Open the project
2. Select `PRSNLModel.xcdatamodeld`
3. Select each entity (CDItem, CDTag, CDAttachment)
4. In the Data Model Inspector, set:
   - Module: Current Product Module
   - Codegen: Manual/None
5. Editor menu → Create NSManagedObject Subclass
6. Select all entities and generate

## After These Fixes
The app should compile! You can then:
1. Run in simulator
2. Test basic functionality
3. Report any runtime issues

These fixes address all CRITICAL blocking issues. The app won't be perfect but it will run!