# PRSNL Extensions Troubleshooting Guide

This document provides solutions for common issues that may arise when implementing or testing the PRSNL app widgets and share extension.

## Common Implementation Issues

### 1. App Group Identifier Issues

**Symptoms:**
- Widget shows no data
- Share extension fails to save items
- Error logs mentioning "container URL for security application group identifier"

**Solutions:**
- Verify app group identifier consistency in all entitlement files:
  ```
  PRSNL/PRSNL.entitlements
  PRSNLShareExtension/PRSNLShareExtension.entitlements
  PRSNLWidget/PRSNLWidget.entitlements
  ```
- Check project.yml for correct capability configuration
- Confirm the app group identifier follows the format: `group.com.yourcompany.PRSNL`
- With a free developer account, test using conditional Core Data setup that falls back to local storage

### 2. Core Data Context Issues

**Symptoms:**
- App crashes when accessing Core Data from extensions
- Thread-related errors in console
- Inconsistent data between main app and extensions

**Solutions:**
- Ensure each extension has its own NSPersistentContainer instance
- Verify proper context management:
  ```swift
  private lazy var managedObjectContext: NSManagedObjectContext = {
      let container = getPersistentContainer()
      let context = container.viewContext
      context.automaticallyMergesChangesFromParent = true
      return context
  }()
  ```
- For widget Timeline Providers, use a background context for queries
- Add proper error handling around Core Data operations
- Check that all Core Data operations occur on the appropriate thread

### 3. Keychain Access Issues

**Symptoms:**
- Unable to access credentials in extensions
- Authentication failures in extensions
- Console errors related to keychain access

**Solutions:**
- Verify keychain access group is configured in entitlements
- Ensure KeychainAccess wrapper is using the correct access group:
  ```swift
  let keychain = Keychain(service: "com.yourcompany.PRSNL")
      .accessGroup("your.keychain.access.group")
  ```
- For free developer accounts, implement a conditional fallback mechanism

### 4. Widget Configuration Issues

**Symptoms:**
- Widget doesn't appear in widget gallery
- Widget crashes when added to home screen
- Widget displays placeholder text only

**Solutions:**
- Check `WidgetBundle` implementation in main widget file
- Verify `IntentConfiguration` or `StaticConfiguration` setup
- Ensure widget sizes are properly supported:
  ```swift
  @main
  struct PRSNLWidgets: WidgetBundle {
      var body: some Widget {
          PRSNLWidget()
      }
  }
  
  struct PRSNLWidget: Widget {
      var body: some WidgetConfiguration {
          StaticConfiguration(
              kind: "com.yourcompany.PRSNL.widget",
              provider: PRSNLTimelineProvider(),
              content: { entry in
                  PRSNLWidgetView(entry: entry)
              }
          )
          .configurationDisplayName("PRSNL Items")
          .description("View your recent PRSNL items.")
          .supportedFamilies([.systemSmall, .systemMedium])
      }
  }
  ```
- Review widget preview provider for testing

### 5. XcodeGen Project Generation Issues

**Symptoms:**
- Missing files in generated project
- Build errors related to missing references
- Extensions not appearing in build schemes

**Solutions:**
- Update project.yml with all required targets and files
- Check target dependencies and embed instructions
- Regenerate project using:
  ```bash
  xcodegen generate
  ```
- Verify generated project includes all extensions in appropriate build schemes
- Check Info.plist configurations for each target

## Testing Without Paid Developer Account

### Widget Testing

1. Use the conditional Core Data setup that falls back to local storage
2. Test widget in Xcode's widget simulator:
   - Run the main app first
   - Stop the app but leave simulator running
   - Run the widget extension scheme
   - Select "Debug Widget" from Xcode menu

### Share Extension Testing

1. Build and run the main app in simulator
2. Navigate to an app that supports sharing (Safari, Notes)
3. Share content and select your extension
4. Verify data appears in main app after sharing
5. Check logs for any Core Data or container access errors

## Deployment Errors

### Archive Validation Issues

**Symptoms:**
- Archive fails validation
- App Store Connect upload errors
- Missing provisioning profiles

**Solutions:**
- For free accounts:
  - Disable App Groups capability
  - Use the conditional Core Data setup
  - Build for local testing only
- For paid accounts:
  - Verify all provisioning profiles
  - Check app group and keychain access group identifiers
  - Verify all entitlements match App Store Connect capabilities

### Privacy Manifest Issues

**Symptoms:**
- App Store rejection
- Privacy manifest validation errors

**Solutions:**
- Ensure PrivacyInfo.xcprivacy includes all required declarations:
  ```
  NSPrivacyTracking: false
  NSPrivacyTrackingDomains: []
  NSPrivacyCollectedDataTypes: []
  NSPrivacyAccessedAPITypes: 
    - NSPrivacyAccessedAPICategoryFileTimestamp
    - NSPrivacyAccessedAPICategorySystemBootTime
  ```
- Verify privacy manifest is included in all extension targets
- Check that required reason strings are provided in Info.plist files

## Thread Safety Issues

**Symptoms:**
- Random crashes
- Data corruption
- Deadlocks or UI freezes

**Solutions:**
- Use proper Core Data context management:
  ```swift
  // For background operations
  container.performBackgroundTask { context in
      // Perform operations
      try? context.save()
  }
  
  // For UI updates
  DispatchQueue.main.async {
      // Update UI
  }
  ```
- Implement proper error handling
- Use NSManagedObjectID for passing objects between contexts
- Verify all UI updates occur on main thread

## Resource Issues

**Symptoms:**
- Widget timeouts
- Memory warnings
- Performance degradation

**Solutions:**
- Limit data fetched in widgets
- Use efficient queries with NSFetchRequest limits
- Implement proper caching strategy
- Consider using lightweight Core Data migration options
- For widgets, implement proper timeline reload policies

## Battery Usage Issues

**Symptoms:**
- High battery consumption
- Background activity warnings
- Overheating during use

**Solutions:**
- Reduce widget update frequency
- Implement proper timeline reload policies:
  ```swift
  func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> Void) {
      // Create entries
      let timeline = Timeline(entries: entries, policy: .atEnd)
      completion(timeline)
  }
  ```
- Use efficient background refresh intervals
- Minimize network operations in extensions
- Implement proper caching strategies

## Tools for Diagnosing Issues

1. **Xcode Instruments:**
   - Use Time Profiler for performance issues
   - Use Allocations instrument for memory issues
   - Use Core Data instrument for database performance

2. **Console App:**
   - Filter logs by process name
   - Look for extension-specific errors

3. **Xcode Debugging:**
   - Set breakpoints in extension code
   - Use View Debugging for widget UI issues
   - Use LLDB commands to inspect Core Data:
     ```
     po context.registeredObjects