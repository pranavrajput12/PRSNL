# PRSNL Extensions: Next Steps Implementation Plan

This document outlines the critical path forward to implement and test the PRSNL widget and share extension, focusing on practical steps that can be completed regardless of Mac storage constraints or Apple Developer account type.

## Critical Path Steps

### Phase 1: Project Setup (1-2 hours)

1. **Generate Xcode project with minimal targets**
   ```bash
   # From PRSNL-iOS directory
   xcodegen generate
   ```
   
   If XcodeGen fails due to space constraints:
   ```bash
   # Create minimal project.yml with just the main app target
   cat > minimal-project.yml << EOL
   name: PRSNL
   options:
     bundleIdPrefix: com.yourcompany
   targets:
     PRSNL:
       type: application
       platform: iOS
       deploymentTarget: "15.0"
       sources: [Implementation/PRSNL]
       info:
         path: Implementation/PRSNL/Info.plist
       entitlements:
         path: Implementation/PRSNL/PRSNL.entitlements
   EOL
   
   xcodegen generate --spec minimal-project.yml
   ```

2. **Verify Core Data model**
   - Open PRSNLModel.xcdatamodeld
   - Confirm all entities are properly defined
   - Check relationships and constraints

### Phase 2: Core Functionality (2-3 hours)

1. **Implement conditional Core Data container**
   - Create `ConditionalCoreDataSetup.swift` if not already done
   - Ensure it properly detects App Groups availability
   - Test with simple data creation/fetching

2. **Test main app Core Data**
   - Create sample items
   - Verify persistence
   - Check view model data flow

### Phase 3: Share Extension (2-3 hours)

1. **Add share extension target manually if needed**
   - File > New > Target > Share Extension
   - Set up Info.plist with supported content types
   - Create entitlements file with conditional App Groups

2. **Implement basic UI**
   ```swift
   // ShareViewController.swift
   import UIKit
   import Social
   import CoreData
   
   class ShareViewController: SLComposeServiceViewController {
       private lazy var managedObjectContext: NSManagedObjectContext = {
           let container = getPersistentContainer()
           let context = container.viewContext
           context.automaticallyMergesChangesFromParent = true
           return context
       }()
       
       override func viewDidLoad() {
           super.viewDidLoad()
           self.title = "Add to PRSNL"
           self.placeholder = "Add notes..."
       }
       
       override func didSelectPost() {
           guard let text = contentText else {
               self.extensionContext?.completeRequest(returningItems: [], completionHandler: nil)
               return
           }
           
           // Create new item
           let context = managedObjectContext
           let newItem = Item(context: context)
           newItem.id = UUID()
           newItem.title = text.count > 30 ? String(text.prefix(30)) + "..." : text
           newItem.notes = text
           newItem.timestamp = Date()
           
           // Try to get URL if available
           if let inputItems = extensionContext?.inputItems as? [NSExtensionItem],
              let attachments = inputItems.first?.attachments,
              let urlProvider = attachments.first {
               
               urlProvider.loadItem(forTypeIdentifier: "public.url", options: nil) { (url, error) in
                   if let url = url as? URL {
                       newItem.urlString = url.absoluteString
                   }
                   
                   // Save and complete
                   do {
                       try context.save()
                   } catch {
                       print("Error saving: \(error)")
                   }
                   
                   self.extensionContext?.completeRequest(returningItems: [], completionHandler: nil)
               }
           } else {
               // No URL, just save text
               do {
                   try context.save()
               } catch {
                   print("Error saving: \(error)")
               }
               
               self.extensionContext?.completeRequest(returningItems: [], completionHandler: nil)
           }
       }
       
       override func didSelectCancel() {
           self.extensionContext?.completeRequest(returningItems: [], completionHandler: nil)
       }
   }
   ```

3. **Test share extension**
   - Run main app first
   - Share content from Safari
   - Verify data saving
   - Check that UI is responsive

### Phase 4: Widget Implementation (2-3 hours)

1. **Add widget extension target manually if needed**
   - File > New > Target > Widget Extension
   - Configure Info.plist for widget capabilities
   - Create entitlements file with conditional App Groups

2. **Implement basic timeline provider**
   ```swift
   // PRSNLWidget.swift
   import WidgetKit
   import SwiftUI
   import CoreData
   
   struct SimpleEntry: TimelineEntry {
       let date: Date
       let items: [ItemViewModel]
   }
   
   struct ItemViewModel: Identifiable {
       let id: UUID
       let title: String
       let date: Date
       
       init(item: Item) {
           self.id = item.id ?? UUID()
           self.title = item.title ?? "Untitled"
           self.date = item.timestamp ?? Date()
       }
   }
   
   struct Provider: TimelineProvider {
       func placeholder(in context: Context) -> SimpleEntry {
           SimpleEntry(date: Date(), items: [])
       }
       
       func getSnapshot(in context: Context, completion: @escaping (SimpleEntry) -> Void) {
           let container = getPersistentContainer()
           let context = container.viewContext
           
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
       
       func getTimeline(in context: Context, completion: @escaping (Timeline<SimpleEntry>) -> Void) {
           let container = getPersistentContainer()
           let context = container.viewContext
           
           let request = NSFetchRequest<Item>(entityName: "Item")
           request.fetchLimit = 5
           request.sortDescriptors = [NSSortDescriptor(key: "timestamp", ascending: false)]
           
           do {
               let items = try context.fetch(request)
               let entry = SimpleEntry(date: Date(), items: items.map { ItemViewModel(item: $0) })
               
               // Update every 30 minutes
               let nextUpdate = Calendar.current.date(byAdding: .minute, value: 30, to: Date())!
               let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
               
               completion(timeline)
           } catch {
               // Handle error
               let entry = SimpleEntry(date: Date(), items: [])
               let timeline = Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(15 * 60)))
               completion(timeline)
           }
       }
   }
   
   struct PRSNLWidgetEntryView: View {
       var entry: Provider.Entry
       @Environment(\.widgetFamily) var family
       
       var body: some View {
           VStack(alignment: .leading, spacing: 4) {
               Text("Recent Items")
                   .font(.headline)
                   .padding(.bottom, 4)
               
               if entry.items.isEmpty {
                   Text("No items yet")
                       .font(.subheadline)
                       .foregroundColor(.secondary)
               } else {
                   ForEach(entry.items.prefix(family == .systemSmall ? 2 : 4)) { item in
                       Text(item.title)
                           .font(.subheadline)
                           .lineLimit(1)
                       
                       if family != .systemSmall {
                           Text(item.date, style: .relative)
                               .font(.caption)
                               .foregroundColor(.secondary)
                       }
                   }
               }
               
               Spacer()
               
               Text("Last updated: \(entry.date, style: .time)")
                   .font(.caption2)
                   .foregroundColor(.secondary)
           }
           .padding()
       }
   }
   
   struct PRSNLWidget: Widget {
       let kind: String = "PRSNLWidget"
       
       var body: some WidgetConfiguration {
           StaticConfiguration(kind: kind, provider: Provider()) { entry in
               PRSNLWidgetEntryView(entry: entry)
           }
           .configurationDisplayName("PRSNL Items")
           .description("View your recent items.")
           .supportedFamilies([.systemSmall, .systemMedium])
       }
   }
   
   @main
   struct PRSNLWidgets: WidgetBundle {
       var body: some Widget {
           PRSNLWidget()
       }
   }
   ```

3. **Test widget**
   - Run main app first to create data
   - Run widget extension target
   - Add to home screen in preview
   - Verify data display

### Phase 5: App Indicator for Free Accounts (1 hour)

1. **Add visual indicator in main app**
   - Update ContentView to show App Groups status
   - Provide clear explanation of data limitations

2. **Add diagnostic logging**
   ```swift
   // In AppDelegate or similar
   func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
       // Check and log App Groups status
       if let containerURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: "group.com.yourcompany.PRSNL") {
           print("✅ App Groups available: \(containerURL.path)")
       } else {
           print("⚠️ App Groups NOT available - using local storage")
       }
       
       return true
   }
   ```

### Phase 6: Testing (1-2 hours)

1. **Test the entire flow**
   - Create items in main app
   - Verify widget displays them (if using paid account)
   - Use share extension to create new items
   - Verify they appear in main app (if using paid account)

2. **Perform error testing**
   - Test with invalid data
   - Test with network disconnected
   - Verify proper error handling

## Storage-Constrained Implementation Options

If Mac storage remains an issue, consider these alternatives:

1. **Streamlined build with fewer targets**
   - Implement just the main app first
   - Add extensions one at a time as storage allows

2. **Clean build files regularly**
   ```bash
   # From terminal
   rm -rf ~/Library/Developer/Xcode/DerivedData/*
   ```

3. **Use lightweight storyboard-based UI** 
   - Reduce SwiftUI previews which consume cache space
   - Minimize asset catalogs

4. **Implement on physical device directly**
   - Build directly to device to avoid simulator caches
   - Use console logging instead of breakpoints

## Account-Type Adaptation

### For Free Apple Developer Account

- Use conditional Core Data implementation
- Expect data isolation between app components
- Test extensions individually
- Document limitations for users

### For Paid Apple Developer Account

- Enable full App Groups capability
- Share Core Data store between app components
- Implement full Keychain sharing
- Prepare for App Store submission

## Fallback Implementation Plan

If full extension implementation is not possible due to constraints:

1. **Simulate widget functionality in main app**
   - Create widget-like UI components in main app
   - Use these as demo/preview of future widget

2. **Simulate share functionality**
   - Add manual import options in main app
   - Implement clipboard monitoring for quick add

This stepwise approach allows for progressive implementation that works within storage constraints and developer account limitations.