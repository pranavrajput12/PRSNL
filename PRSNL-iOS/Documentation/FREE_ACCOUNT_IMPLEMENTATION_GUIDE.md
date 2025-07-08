# Implementing PRSNL Extensions with a Free Apple Developer Account

This guide provides detailed instructions for implementing and testing the PRSNL widget and share extension using a free Apple Developer account (no paid $99/year subscription).

## Understanding the Limitations

When using a free Apple Developer account, you'll face these key limitations:

1. **No App Groups capability**: You cannot share data between app and extensions using App Groups
2. **No iCloud capability**: You cannot use CloudKit for data synchronization
3. **No Keychain Sharing**: You cannot share keychain items between app and extensions
4. **Limited provisioning**: You can only deploy to a limited number of physical devices
5. **7-day app expiration**: Apps deployed with a free account expire after 7 days

Despite these limitations, we've implemented workarounds that allow our extensions to function properly with a free account.

## Core Data: Conditional Implementation

Our solution uses a conditional Core Data setup that automatically detects if App Groups are available, falling back to local storage when necessary:

```swift
func getPersistentContainer() -> NSPersistentContainer {
    let container = NSPersistentContainer(name: "PRSNLModel")
    
    // Try to use App Group container if available
    if let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier) {
        let storeURL = containerURL.appendingPathComponent("PRSNLModel.sqlite")
        let description = NSPersistentStoreDescription(url: storeURL)
        container.persistentStoreDescriptions = [description]
    } 
    // Otherwise use default local storage (free account)
    
    container.loadPersistentStores { (storeDescription, error) in
        if let error = error {
            fatalError("Failed to load Core Data stack: \(error)")
        }
    }
    
    return container
}
```

### What This Means for Your Implementation

1. **Main app**: Stores data in its own local Core Data store
2. **Widget**: Has its own isolated Core Data store
3. **Share extension**: Has its own isolated Core Data store

While this means data isn't shared between components with a free account, each component remains functional.

## Data Synchronization Workaround

Since direct data sharing is unavailable, we've implemented alternative synchronization:

1. **For widgets**: Load basic data in the main app first, then view widgets
2. **For share extension**: After using the share extension, open the main app to see new items

## Implementation Steps for Free Account

### 1. Project Setup

Ensure XcodeGen project.yml has conditional App Group setup:

```yaml
targets:
  PRSNL:
    # Normal app configuration...
    
    # Make entitlements conditional
    entitlements:
      path: PRSNL/PRSNL.entitlements
      properties:
        com.apple.security.application-groups:
          - group.com.yourcompany.PRSNL
        # Other entitlements...
```

### 2. Core Data Implementation

Use the conditional Core Data setup in all components:

```swift
// In each extension and main app
private lazy var managedObjectContext: NSManagedObjectContext = {
    let container = getPersistentContainer() // This function handles the conditional logic
    let context = container.viewContext
    context.automaticallyMergesChangesFromParent = true
    return context
}()
```

### 3. UI Feedback

Add visual indicators in the app showing if App Groups are available:

```swift
// In ContentView or similar
var body: some View {
    VStack {
        // Normal app content
        
        // Status indicator for developer account
        if FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier) != nil {
            Text("Full data sharing enabled (Paid account)")
                .foregroundColor(.green)
                .padding()
        } else {
            Text("Limited data sharing (Free account)")
                .foregroundColor(.orange)
                .padding()
        }
    }
}
```

### 4. Widget Implementation

Ensure widget handles the isolated data store:

```swift
struct Provider: TimelineProvider {
    func getSnapshot(in context: Context, completion: @escaping (SimpleEntry) -> Void) {
        // Use local Core Data store for free accounts
        let container = getPersistentContainer()
        let context = container.viewContext
        
        // Fetch a limited set of data
        let request = NSFetchRequest<Item>(entityName: "Item")
        request.fetchLimit = 5
        request.sortDescriptors = [NSSortDescriptor(key: "timestamp", ascending: false)]
        
        do {
            let items = try context.fetch(request)
            let entry = SimpleEntry(date: Date(), items: items.map { ItemViewModel(item: $0) })
            completion(entry)
        } catch {
            completion(SimpleEntry(date: Date(), items: []))
        }
    }
    
    // Similar approach for timeline
}
```

### 5. Share Extension Implementation

Ensure share extension saves to its own Core Data store:

```swift
func saveSharedItem(title: String, url: URL?, notes: String) {
    // Use isolated Core Data store
    let context = managedObjectContext
    
    let newItem = Item(context: context)
    newItem.id = UUID()
    newItem.title = title
    newItem.urlString = url?.absoluteString
    newItem.notes = notes
    newItem.timestamp = Date()
    
    do {
        try context.save()
        // Success - but data is only in share extension's store
        completion(true, nil)
    } catch {
        completion(false, error)
    }
}
```

## Testing With a Free Account

### 1. Building the App

When using a free account, you'll need to:

1. Select your personal team for code signing
2. Accept reduced capabilities in the signing dialog
3. Verify the app builds without entitlement errors

### 2. Testing the Widget

1. Run the main app first to populate its Core Data store
2. Stop the app but leave the simulator running
3. Run the widget extension target
4. Debug the widget in the simulator
5. Note that the widget only shows data from when it was last run, not real-time data from the main app

### 3. Testing the Share Extension

1. Run the main app in the simulator
2. Navigate to Safari or Notes
3. Share content using the share extension
4. Verify the UI works correctly
5. Return to the main app and note that shared items aren't visible (expected with free account)

## Deployment to Physical Device

With a free account, you can deploy to your personal device with these limitations:

1. The app will expire after 7 days
2. You must be connected to Xcode for installation
3. You can only use a limited number of registered devices

Steps:
1. Connect your iOS device via USB
2. In Xcode, select your personal team for signing
3. Select your device as the run destination
4. Build and run the app
5. Trust the developer certificate on your device when prompted

## Best Practices for Free Account Development

1. **Clear expectations**: Understand data isolation between components
2. **Regular testing**: Test all components individually
3. **Consider workarounds**: Implement UI that communicates the free account limitations
4. **Prepare for paid upgrade**: Structure code to seamlessly work with App Groups when a paid account is available
5. **Document known issues**: Keep track of limitations to address when upgrading

## Transitioning to Paid Account

When upgrading to a paid Apple Developer account:

1. The conditional Core Data implementation will automatically use App Groups
2. Data will be shared between all components
3. Keychain items can be shared between components
4. Your app can be deployed to the App Store
5. Deployed apps won't expire after 7 days

No code changes are needed thanks to our conditional implementation - just update your provisioning profiles and capabilities in App Store Connect.

## Troubleshooting Free Account Issues

### "Missing entitlements" Errors

If you see "missing entitlements" errors during build:

1. Open the target's Build Settings
2. Set "Code Signing Entitlements" to empty for debug builds
3. Use a conditional approach in entitlements files

### Simulator Testing Issues

If the extensions don't appear in the simulator:

1. Clean the build folder (Product > Clean Build Folder)
2. Reset the simulator (Device > Erase All Content and Settings)
3. Rebuild and run the app

### Widget Not Showing Data

If the widget shows no data with a free account:

1. Run the main app first to populate its store
2. Verify the widget is using the conditional Core Data setup
3. Check if the widget is using the same model as the main app
4. Add debug logging to verify data fetching