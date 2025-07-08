# PRSNL App Extensions Integration Guide

This document provides details on how the PRSNL iOS app's extensions (Widget Extension and Share Extension) integrate with the main app through shared data access and communication channels.

## Overview

The PRSNL app ecosystem consists of three main components:
1. **Main App**: The primary PRSNL iOS application
2. **Widget Extension**: Home screen widgets providing quick access to recent items
3. **Share Extension**: System share sheet extension for saving content from other apps

These components need to share data seamlessly while maintaining security and performance. This is achieved through App Groups, a shared Core Data store, and keychain access groups.

## Shared Data Architecture

### App Groups

All three components are part of the same App Group, allowing them to share files and defaults:

```swift
// App Group identifier used throughout the app and extensions
let appGroupIdentifier = "group.ai.prsnl.shared"
```

This App Group identifier is configured in the entitlements files:
- `PRSNL/PRSNL.entitlements`
- `PRSNLWidgets/PRSNLWidgets.entitlements`
- `PRSNLShareExtension/PRSNLShareExtension.entitlements`

### Core Data Shared Container

The Core Data store is located in the shared container so it can be accessed by all components:

```swift
// Code to access the shared Core Data store
if let storeURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier)?
    .appendingPathComponent("PRSNLModel.sqlite") {
    
    let storeDescription = NSPersistentStoreDescription(url: storeURL)
    container.persistentStoreDescriptions = [storeDescription]
}
```

### Keychain Access

Secure credentials are shared through a keychain access group:

```swift
// Keychain access group
private let accessGroup = "$(AppIdentifierPrefix)ai.prsnl.shared"
```

## Widget Extension Integration

### Data Flow

1. **Reading Data**: The widget extension reads data from the shared Core Data store to display recent items:
   ```swift
   // WidgetProvider.swift
   func getTimeline(in context: Context, completion: @escaping (Timeline<WidgetEntry>) -> Void) {
       let entries = fetchEntriesFromCoreData()
       let timeline = Timeline(entries: entries, policy: .atEnd)
       completion(timeline)
   }
   ```

2. **Refresh Mechanism**: Widgets are refreshed at regular intervals and when the main app updates data:
   ```swift
   // In main app after data changes
   WidgetCenter.shared.reloadAllTimelines()
   ```

3. **Deep Linking**: Tapping a widget item opens the main app and navigates to that specific item:
   ```swift
   // In widget view
   Link(destination: URL(string: "prsnl://item/\(item.id)")!) {
       ItemWidgetView(item: item)
   }
   ```

## Share Extension Integration

### Data Flow

1. **Content Extraction**: The share extension extracts content from the share sheet:
   ```swift
   // In ShareViewController
   private func extractSharedContent() {
       // Extract URLs, text, or images from extensionContext
   }
   ```

2. **Data Storage**: The extension saves directly to the shared Core Data store:
   ```swift
   private func saveToSharedContainer() {
       // Create and save a new Item entity in the shared Core Data context
   }
   ```

3. **User Interface**: The share extension provides a simplified version of the Capture interface, focusing on quick content saving with optional notes.

## Main App Integration Points

### Core Data Manager

The CoreDataManager handles all Core Data operations and provides a unified interface for all components:

```swift
// In CoreDataManager.swift
class CoreDataManager {
    static let shared = CoreDataManager()
    
    private let persistentContainer: NSPersistentContainer
    
    init() {
        // Initialize with the shared container
    }
    
    // CRUD operations used by main app and extensions
}
```

### Deep Linking Handler

The main app handles deep links from widgets:

```swift
// In PRSNLApp.swift
func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
    if let url = URLContexts.first?.url {
        handleDeepLink(url)
    }
}
```

### Sync Manager

The SyncManager ensures data is properly synchronized when the app returns to the foreground:

```swift
// In SyncManager.swift
func applicationWillEnterForeground() {
    syncPendingItems()
}
```

## Threading Considerations

All three components must respect Core Data threading rules:

1. **Main App**: Uses the main context for UI operations and background contexts for operations.
2. **Widget Extension**: Uses a dedicated view context that automatically merges changes.
3. **Share Extension**: Uses its own managed object context that properly merges with the main store.

Each component should perform Core Data operations on the appropriate queue:

```swift
private func performBackgroundTask(_ task: @escaping (NSManagedObjectContext) -> Void) {
    persistentContainer.performBackgroundTask { context in
        task(context)
    }
}
```

## Security Considerations

1. **Keychain Access**: All components use the same keychain access group but implement proper access control.
2. **Data Validation**: Each component validates data before saving to the shared store.
3. **Error Handling**: All components implement proper error handling to prevent data corruption.

## Testing Extensions

1. **Widget Testing**: Test widgets with different data scenarios and refresh intervals.
2. **Share Extension Testing**: Test sharing different content types from various apps.
3. **Cross-Component Testing**: Verify that data created in one component appears correctly in others.

## Troubleshooting

Common issues and solutions:

1. **Widget Not Updating**: Ensure `WidgetCenter.shared.reloadAllTimelines()` is called after data changes.
2. **Share Extension Crashes**: Verify app group entitlements and Core Data setup.
3. **Data Not Appearing**: Check that all components are using the same app group identifier.
4. **Performance Issues**: Monitor Core Data fetch requests in extensions to ensure they're efficient.

## Future Improvements

1. **Background App Refresh**: Enhance widget updates with background refresh capabilities.
2. **Share Extension Enhancements**: Add advanced content processing features.
3. **Syncing Indicators**: Add visual indicators when data is being synchronized between components.