# PRSNL Widget Integration Guide

This document provides instructions for integrating the PRSNL widget extension with the main app.

## Overview

We've implemented three widget types for the PRSNL app:

1. **Timeline Widget**: Shows recent items in a timeline format
2. **Quick Actions Widget**: Provides quick access to common app actions
3. **Stats Widget**: Displays usage statistics and insights

## Integration Steps

### 1. Configure App Group Entitlements

To share data between the main app and widget extension, you need to configure App Groups:

1. In Xcode, select the project file and go to the "Signing & Capabilities" tab
2. Click "+" and add "App Groups" capability to both the main app target and widget extension target
3. Create a new App Group ID: `group.ai.prsnl.shared`
4. Ensure both targets use the same App Group ID

### 2. Update CoreDataManager to Support Widget Access

The CoreDataManager needs to use a shared container URL for Core Data persistence:

```swift
// In CoreDataManager.swift

class CoreDataManager {
    static let shared = CoreDataManager()
    
    // This must match the App Group identifier used in entitlements
    private let appGroupIdentifier = "group.ai.prsnl.shared"
    
    private init() {
        // Use shared container for Core Data
    }
    
    // Update the container URL to use App Group container
    private lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "PRSNLModel")
        
        // Set up shared container URL for App Group
        if let storeURL = container.persistentStoreDescriptions.first?.url {
            let groupStoreURL = FileManager.default
                .containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier)?
                .appendingPathComponent(storeURL.lastPathComponent)
            
            if let groupStoreURL = groupStoreURL {
                container.persistentStoreDescriptions.first?.url = groupStoreURL
            }
        }
        
        container.loadPersistentStores { _, error in
            if let error = error as NSError? {
                fatalError("Unresolved error \(error), \(error.userInfo)")
            }
        }
        
        return container
    }()
}
```

### 3. Set Up Widget Refresh Triggers

Add code to trigger widget refreshes when app data changes:

```swift
// In AppDelegate.swift or any relevant data management class

import WidgetKit

// Call this function whenever data changes that should update widgets
func refreshWidgets() {
    WidgetCenter.shared.reloadAllTimelines()
}

// Examples of when to call refreshWidgets():
// - After adding/updating/deleting items
// - After completing synchronization with the backend
// - After user-triggered data refreshes
```

### 4. Configure Widget Extension in Xcode

1. Create a new "Widget Extension" target in Xcode if you haven't already
2. Set the product name to "PRSNLWidgets"
3. Ensure the extension's deployment target and Swift version match the main app
4. Add the App Groups capability to the widget extension
5. Select the same App Group ID used for the main app
6. Copy the widget implementation files to the widget extension target

### 5. Add Deep Linking Support

Update your main app's SceneDelegate to handle deep links from widgets:

```swift
// In SceneDelegate.swift

func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
    guard let url = URLContexts.first?.url else { return }
    
    // Handle deep links from widgets
    if url.scheme == "prsnl" {
        handleDeepLink(url)
    }
}

private func handleDeepLink(_ url: URL) {
    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else { return }
    
    // Extract path components
    let path = components.path
    
    // Handle different paths
    switch path {
    case "/timeline":
        // Navigate to timeline
        navigateToTimeline()
        
    case "/item":
        // Extract item ID from query parameters
        if let itemID = components.queryItems?.first(where: { $0.name == "id" })?.value {
            navigateToItem(itemID)
        }
        
    case "/new":
        // Extract item type from query parameters
        let itemType = components.queryItems?.first(where: { $0.name == "type" })?.value
        navigateToNewItem(type: itemType)
        
    case "/search":
        navigateToSearch()
        
    case "/settings":
        navigateToSettings()
        
    default:
        // Unknown path, do nothing or navigate to default screen
        break
    }
}
```

### 6. Update Info.plist for URL Scheme

Add the custom URL scheme to your main app's Info.plist:

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleTypeRole</key>
        <string>Editor</string>
        <key>CFBundleURLName</key>
        <string>ai.prsnl</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>prsnl</string>
        </array>
    </dict>
</array>
```

## Testing Widgets

1. Build and run the main app on a device or simulator
2. Create some test data in the app
3. Go to the Home Screen
4. Long press on an empty area and tap the "+" button
5. Scroll down or search for "PRSNL"
6. Add the different widget types to your Home Screen
7. Test widget functionality and deep links

## Widget Performance Considerations

- Widgets use caching to minimize resource usage
- The refresh rate adapts based on battery level
- Widgets access Core Data directly but in read-only mode
- Complex operations should be avoided in widget code

## Troubleshooting

If widgets don't appear or show outdated data:

1. Ensure App Group entitlements are properly configured
2. Verify that the CoreDataManager is using the shared container
3. Check that widgets are being refreshed when data changes
4. Restart the device or simulator
5. Delete and re-add the widgets to the Home Screen

## Additional Resources

- [Apple's WidgetKit Documentation](https://developer.apple.com/documentation/widgetkit)
- [WWDC20 - Build SwiftUI views for widgets](https://developer.apple.com/videos/play/wwdc2020/10033/)
- [WWDC20 - Widgets Code-along](https://developer.apple.com/videos/play/wwdc2020/10034/)