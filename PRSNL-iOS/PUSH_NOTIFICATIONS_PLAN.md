# PRSNL iOS: Push Notifications Implementation Plan

This document outlines a comprehensive strategy for implementing push notifications in the PRSNL iOS app, enabling timely alerts, engagement features, and important updates for users even when the app is not actively in use.

## 1. Notification Architecture

### 1.1 Overview

The push notification system will create a direct communication channel between the PRSNL backend and the iOS app, allowing for timely delivery of important updates and engagement features. This will enable:

- Real-time alerts for new content and updates
- Reminder notifications for scheduled tasks
- Personalized engagement based on user behavior
- Interactive notification actions
- Silent background updates for data synchronization

### 1.2 System Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│   PRSNL iOS     │◄────────┤  Apple Push     │◄────────┤  PRSNL Backend  │
│   Application   │         │  Notification   │         │  Notification   │
│                 │────────►│  Service (APNS) │────────►│  Service        │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## 2. iOS Notification Implementation

### 2.1 NotificationManager Class

```swift
// IMPLEMENT: Core notification manager
class NotificationManager: ObservableObject {
    // Singleton instance
    static let shared = NotificationManager()
    
    // Published properties
    @Published private(set) var hasPermission = false
    @Published private(set) var pendingNotifications: [UNNotificationRequest] = []
    
    // User notification center
    private let center = UNUserNotificationCenter.current()
    
    // Notification categories
    enum NotificationCategory: String {
        case newItem = "new_item"
        case reminder = "reminder"
        case update = "update"
        case message = "message"
    }
    
    // Private initializer for singleton
    private init() {
        // Configure notification categories
        configureNotificationCategories()
        
        // Check permission status
        checkPermissionStatus()
    }
    
    // MARK: - Public Methods
    
    // Request notification permission
    func requestPermission() async -> Bool {
        do {
            // Request authorization for alerts, sounds, and badges
            let options: UNAuthorizationOptions = [.alert, .sound, .badge]
            let granted = try await center.requestAuthorization(options: options)
            
            // Update permission status
            DispatchQueue.main.async {
                self.hasPermission = granted
            }
            
            // Register for remote notifications on the main thread
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
            
            Logger.notifications.info("Notification permission \(granted ? "granted" : "denied")")
            return granted
        } catch {
            Logger.notifications.error("Failed to request notification permission: \(error.localizedDescription)")
            return false
        }
    }
    
    // Register device token with backend
    func registerDeviceToken(_ deviceToken: Data) {
        // Convert token to string
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        // Register with API
        Task {
            do {
                try await APIClient.shared.registerPushToken(token: tokenString)
                Logger.notifications.info("Device token registered successfully")
            } catch {
                Logger.notifications.error("Failed to register device token: \(error.localizedDescription)")
            }
        }
    }
    
    // Schedule local notification
    func scheduleLocalNotification(title: String, body: String, category: NotificationCategory, userInfo: [AnyHashable: Any]? = nil, timeInterval: TimeInterval? = nil, calendar: DateComponents? = nil) {
        // Create content
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.categoryIdentifier = category.rawValue
        
        // Add user info if provided
        if let userInfo = userInfo {
            content.userInfo = userInfo
        }
        
        // Create trigger
        var trigger: UNNotificationTrigger?
        
        if let timeInterval = timeInterval {
            // Time interval trigger
            trigger = UNTimeIntervalNotificationTrigger(timeInterval: timeInterval, repeats: false)
        } else if let calendar = calendar {
            // Calendar trigger
            trigger = UNCalendarNotificationTrigger(dateMatching: calendar, repeats: false)
        }
        
        // Create request with random identifier
        let identifier = UUID().uuidString
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)
        
        // Add request to notification center
        center.add(request) { error in
            if let error = error {
                Logger.notifications.error("Failed to schedule notification: \(error.localizedDescription)")
            } else {
                Logger.notifications.info("Local notification scheduled with ID: \(identifier)")
            }
        }
    }
    
    // Schedule notification for new item
    func scheduleNewItemNotification(item: Item) {
        // Create user info
        let userInfo: [AnyHashable: Any] = [
            "item_id": item.id,
            "notification_type": "new_item"
        ]
        
        // Schedule notification
        scheduleLocalNotification(
            title: "New Item Added",
            body: "A new item titled '\(item.title)' has been added",
            category: .newItem,
            userInfo: userInfo
        )
    }
    
    // Schedule reminder notification
    func scheduleReminderNotification(item: Item, date: Date) {
        // Create calendar components
        let components = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
        
        // Create user info
        let userInfo: [AnyHashable: Any] = [
            "item_id": item.id,
            "notification_type": "reminder"
        ]
        
        // Schedule notification
        scheduleLocalNotification(
            title: "Reminder",
            body: "Reminder for: \(item.title)",
            category: .reminder,
            userInfo: userInfo,
            calendar: components
        )
    }
    
    // Remove pending notifications for an item
    func removePendingNotifications(for itemId: String) {
        // Get pending notification requests
        center.getPendingNotificationRequests { requests in
            // Find notifications for this item
            let identifiers = requests.filter { request in
                guard let notificationItemId = request.content.userInfo["item_id"] as? String else {
                    return false
                }
                return notificationItemId == itemId
            }.map { $0.identifier }
            
            // Remove notifications
            if !identifiers.isEmpty {
                self.center.removePendingNotificationRequests(withIdentifiers: identifiers)
                Logger.notifications.info("Removed \(identifiers.count) pending notifications for item \(itemId)")
            }
        }
    }
    
    // Remove all pending notifications
    func removeAllPendingNotifications() {
        center.removeAllPendingNotificationRequests()
        Logger.notifications.info("Removed all pending notifications")
    }
    
    // Reset badge count
    func resetBadgeCount() {
        DispatchQueue.main.async {
            UIApplication.shared.applicationIconBadgeNumber = 0
        }
    }
    
    // Get pending notifications
    func refreshPendingNotifications() {
        center.getPendingNotificationRequests { requests in
            DispatchQueue.main.async {
                self.pendingNotifications = requests
            }
        }
    }
    
    // Handle received notification
    func handleReceivedNotification(userInfo: [AnyHashable: Any]) {
        guard let notificationType = userInfo["notification_type"] as? String else {
            return
        }
        
        switch notificationType {
        case "new_item":
            if let itemId = userInfo["item_id"] as? String {
                handleNewItemNotification(itemId: itemId)
            }
            
        case "reminder":
            if let itemId = userInfo["item_id"] as? String {
                handleReminderNotification(itemId: itemId)
            }
            
        case "update":
            if let itemId = userInfo["item_id"] as? String {
                handleUpdateNotification(itemId: itemId)
            }
            
        case "message":
            if let messageId = userInfo["message_id"] as? String {
                handleMessageNotification(messageId: messageId)
            }
            
        default:
            Logger.notifications.warning("Received unknown notification type: \(notificationType)")
        }
    }
    
    // MARK: - Private Methods
    
    // Configure notification categories and actions
    private func configureNotificationCategories() {
        // New item category
        let viewItemAction = UNNotificationAction(
            identifier: "VIEW_ITEM",
            title: "View",
            options: .foreground
        )
        
        let newItemCategory = UNNotificationCategory(
            identifier: NotificationCategory.newItem.rawValue,
            actions: [viewItemAction],
            intentIdentifiers: [],
            options: .customDismissAction
        )
        
        // Reminder category
        let completeAction = UNNotificationAction(
            identifier: "COMPLETE_TASK",
            title: "Complete",
            options: [.foreground]
        )
        
        let snoozeAction = UNNotificationAction(
            identifier: "SNOOZE",
            title: "Snooze",
            options: []
        )
        
        let reminderCategory = UNNotificationCategory(
            identifier: NotificationCategory.reminder.rawValue,
            actions: [completeAction, snoozeAction],
            intentIdentifiers: [],
            options: .customDismissAction
        )
        
        // Update category
        let updateCategory = UNNotificationCategory(
            identifier: NotificationCategory.update.rawValue,
            actions: [viewItemAction],
            intentIdentifiers: [],
            options: .customDismissAction
        )
        
        // Message category
        let replyAction = UNTextInputNotificationAction(
            identifier: "REPLY",
            title: "Reply",
            options: [],
            textInputButtonTitle: "Send",
            textInputPlaceholder: "Type your reply..."
        )
        
        let messageCategory = UNNotificationCategory(
            identifier: NotificationCategory.message.rawValue,
            actions: [replyAction, viewItemAction],
            intentIdentifiers: [],
            options: .customDismissAction
        )
        
        // Register categories
        center.setNotificationCategories([
            newItemCategory,
            reminderCategory,
            updateCategory,
            messageCategory
        ])
    }
    
    // Check notification permission status
    private func checkPermissionStatus() {
        center.getNotificationSettings { settings in
            DispatchQueue.main.async {
                self.hasPermission = settings.authorizationStatus == .authorized
            }
        }
    }
    
    // Handle new item notification
    private func handleNewItemNotification(itemId: String) {
        // Fetch item details if needed
        // Navigate to item detail screen
        NavigationManager.shared.navigateToItemDetail(itemId: itemId)
        
        // Publish notification event
        NotificationCenter.default.post(
            name: .didReceiveNewItemNotification,
            object: nil,
            userInfo: ["itemId": itemId]
        )
    }
    
    // Handle reminder notification
    private func handleReminderNotification(itemId: String) {
        // Fetch item details if needed
        // Navigate to item detail screen
        NavigationManager.shared.navigateToItemDetail(itemId: itemId)
        
        // Publish notification event
        NotificationCenter.default.post(
            name: .didReceiveReminderNotification,
            object: nil,
            userInfo: ["itemId": itemId]
        )
    }
    
    // Handle update notification
    private func handleUpdateNotification(itemId: String) {
        // Fetch item details if needed
        // Navigate to item detail screen
        NavigationManager.shared.navigateToItemDetail(itemId: itemId)
        
        // Publish notification event
        NotificationCenter.default.post(
            name: .didReceiveUpdateNotification,
            object: nil,
            userInfo: ["itemId": itemId]
        )
    }
    
    // Handle message notification
    private func handleMessageNotification(messageId: String) {
        // Navigate to messages screen
        NavigationManager.shared.navigateToMessages(messageId: messageId)
        
        // Publish notification event
        NotificationCenter.default.post(
            name: .didReceiveMessageNotification,
            object: nil,
            userInfo: ["messageId": messageId]
        )
    }
}

// Notification names
extension Notification.Name {
    static let didReceiveNewItemNotification = Notification.Name("DidReceiveNewItemNotification")
    static let didReceiveReminderNotification = Notification.Name("DidReceiveReminderNotification")
    static let didReceiveUpdateNotification = Notification.Name("DidReceiveUpdateNotification")
    static let didReceiveMessageNotification = Notification.Name("DidReceiveMessageNotification")
}

// Simple navigation manager for handling notification navigation
class NavigationManager {
    // Singleton instance
    static let shared = NavigationManager()
    
    // Navigation state
    enum NavigationDestination: Equatable {
        case itemDetail(itemId: String)
        case messages(messageId: String?)
    }
    
    // Published navigation destination
    @Published var activeDestination: NavigationDestination?
    
    // Private initializer for singleton
    private init() {}
    
    // Navigate to item detail
    func navigateToItemDetail(itemId: String) {
        DispatchQueue.main.async {
            self.activeDestination = .itemDetail(itemId: itemId)
        }
    }
    
    // Navigate to messages
    func navigateToMessages(messageId: String? = nil) {
        DispatchQueue.main.async {
            self.activeDestination = .messages(messageId: messageId)
        }
    }
    
    // Clear active destination
    func clearDestination() {
        DispatchQueue.main.async {
            self.activeDestination = nil
        }
    }
}
```

### 2.2 AppDelegate Implementation

```swift
// IMPLEMENT: AppDelegate with Push Notification handling
class AppDelegate: NSObject, UIApplicationDelegate {
    // App did finish launching
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        // Request notification permission
        Task {
            await NotificationManager.shared.requestPermission()
        }
        
        // Setup delegate for notification center
        UNUserNotificationCenter.current().delegate = self
        
        return true
    }
    
    // Did register for remote notifications
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        // Register token with backend
        NotificationManager.shared.registerDeviceToken(deviceToken)
    }
    
    // Did fail to register for remote notifications
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        Logger.notifications.error("Failed to register for remote notifications: \(error.localizedDescription)")
    }
    
    // Did receive remote notification
    func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable: Any], fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        // Handle notification
        handleRemoteNotification(userInfo: userInfo, completionHandler: completionHandler)
    }
    
    // MARK: - Private Methods
    
    // Handle remote notification
    private func handleRemoteNotification(userInfo: [AnyHashable: Any], completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        // Check if this is a silent notification for background sync
        if let isSilent = userInfo["silent"] as? Bool, isSilent {
            // Perform background sync
            performBackgroundSync(completionHandler: completionHandler)
        } else {
            // Regular notification, handle it
            NotificationManager.shared.handleReceivedNotification(userInfo: userInfo)
            completionHandler(.noData)
        }
    }
    
    // Perform background sync
    private func performBackgroundSync(completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        Task {
            do {
                // Perform sync operation
                let hasNewData = try await SyncManager.shared.syncItemsFromAPI()
                
                // Call completion handler with result
                completionHandler(hasNewData ? .newData : .noData)
            } catch {
                Logger.sync.error("Background sync failed: \(error.localizedDescription)")
                completionHandler(.failed)
            }
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension AppDelegate: UNUserNotificationCenterDelegate {
    // Will present notification
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Get user info
        let userInfo = notification.request.content.userInfo
        
        // Handle notification if needed
        NotificationManager.shared.handleReceivedNotification(userInfo: userInfo)
        
        // Show notification banner and play sound
        completionHandler([.banner, .sound, .list, .badge])
    }
    
    // Did receive response
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        // Get user info
        let userInfo = response.notification.request.content.userInfo
        
        // Handle action based on identifier
        switch response.actionIdentifier {
        case UNNotificationDefaultActionIdentifier:
            // Default action (tapping the notification)
            NotificationManager.shared.handleReceivedNotification(userInfo: userInfo)
            
        case "VIEW_ITEM":
            // View item action
            if let itemId = userInfo["item_id"] as? String {
                NavigationManager.shared.navigateToItemDetail(itemId: itemId)
            }
            
        case "COMPLETE_TASK":
            // Complete task action
            if let itemId = userInfo["item_id"] as? String {
                completeTask(itemId: itemId)
            }
            
        case "SNOOZE":
            // Snooze action
            if let itemId = userInfo["item_id"] as? String {
                snoozeReminder(itemId: itemId)
            }
            
        case "REPLY":
            // Reply action for messages
            if let response = response as? UNTextInputNotificationResponse,
               let messageId = userInfo["message_id"] as? String {
                sendReply(messageId: messageId, text: response.userText)
            }
            
        default:
            break
        }
        
        // Call completion handler
        completionHandler()
    }
    
    // MARK: - Action Handlers
    
    // Complete task
    private func completeTask(itemId: String) {
        Task {
            do {
                // Mark task as completed
                try await TaskManager.shared.completeTask(itemId: itemId)
                
                // Remove pending notifications for this item
                NotificationManager.shared.removePendingNotifications(for: itemId)
            } catch {
                Logger.tasks.error("Failed to complete task: \(error.localizedDescription)")
            }
        }
    }
    
    // Snooze reminder
    private func snoozeReminder(itemId: String) {
        Task {
            do {
                // Get item
                if let item = try await CoreDataManager.shared.fetchItem(id: itemId) {
                    // Schedule reminder for 15 minutes later
                    let snoozeDate = Date().addingTimeInterval(15 * 60)
                    NotificationManager.shared.scheduleReminderNotification(item: item, date: snoozeDate)
                }
            } catch {
                Logger.notifications.error("Failed to snooze reminder: \(error.localizedDescription)")
            }
        }
    }
    
    // Send reply to message
    private func sendReply(messageId: String, text: String) {
        Task {
            do {
                // Send reply via API
                try await APIClient.shared.sendMessageReply(messageId: messageId, text: text)
            } catch {
                Logger.messages.error("Failed to send reply: \(error.localizedDescription)")
            }
        }
    }
}
```

### 2.3 SwiftUI Integration with NotificationManager

```swift
// IMPLEMENT: MainView with notification handling
struct MainView: View {
    // Environment objects
    @StateObject private var notificationManager = NotificationManager.shared
    @StateObject private var navigationManager = NavigationManager.shared
    
    var body: some View {
        TabView {
            // Timeline tab
            NavigationStack {
                TimelineView()
            }
            .tabItem {
                Label("Timeline", systemImage: "list.bullet")
            }
            
            // Search tab
            NavigationStack {
                SearchView()
            }
            .tabItem {
                Label("Search", systemImage: "magnifyingglass")
            }
            
            // Settings tab
            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Settings", systemImage: "gear")
            }
        }
        .onAppear {
            // Reset badge count when app appears
            notificationManager.resetBadgeCount()
        }
        .onChange(of: navigationManager.activeDestination) { _, destination in
            // Handle navigation based on destination
            if let destination = destination {
                handleNavigation(destination)
            }
        }
    }
    
    // Handle navigation from notifications
    private func handleNavigation(_ destination: NavigationManager.NavigationDestination) {
        switch destination {
        case .itemDetail(let itemId):
            // Navigate to item detail
            // This would depend on your app's navigation structure
            print("Navigate to item detail: \(itemId)")
            
        case .messages(let messageId):
            // Navigate to messages, optionally to a specific message
            print("Navigate to messages\(messageId != nil ? " with message ID: \(messageId!)" : "")")
        }
        
        // Clear destination
        navigationManager.clearDestination()
    }
}

// IMPLEMENT: NotificationPermissionView
struct NotificationPermissionView: View {
    @ObservedObject private var notificationManager = NotificationManager.shared
    @State private var isRequesting = false
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "bell.badge.fill")
                .font(.system(size: 60))
                .foregroundColor(.blue)
                .padding(.bottom, 10)
            
            Text("Stay Updated")
                .font(.title)
                .bold()
            
            Text("Enable notifications to stay informed about new items, updates, and reminders.")
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            if notificationManager.hasPermission {
                // Permissions already granted
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    
                    Text("Notifications Enabled")
                        .foregroundColor(.green)
                        .bold()
                }
                .padding()
                .background(Color.green.opacity(0.1))
                .cornerRadius(8)
            } else {
                // Request permission button
                Button(action: {
                    requestPermission()
                }) {
                    HStack {
                        Text("Enable Notifications")
                            .bold()
                        
                        if isRequesting {
                            ProgressView()
                                .padding(.leading, 5)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(isRequesting)
                .padding(.horizontal)
                
                Button(action: {
                    // Skip for now
                }) {
                    Text("Skip for Now")
                        .foregroundColor(.secondary)
                }
                .padding(.top, 10)
            }
        }
        .padding()
        .frame(maxWidth: 400)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Notification Permission Request")
    }
    
    // Request notification permission
    private func requestPermission() {
        isRequesting = true
        
        Task {
            let granted = await notificationManager.requestPermission()
            
            DispatchQueue.main.async {
                isRequesting = false
                
                // Show alert if denied
                if !granted {
                    // Show instructions to enable in settings
                }
            }
        }
    }
}

// IMPLEMENT: SettingsView with notification settings
struct NotificationSettingsView: View {
    @ObservedObject private var notificationManager = NotificationManager.shared
    @State private var newItemNotificationsEnabled = true
    @State private var reminderNotificationsEnabled = true
    @State private var updateNotificationsEnabled = true
    @State private var messageNotificationsEnabled = true
    
    var body: some View {
        List {
            Section(header: Text("Push Notifications")) {
                // Permission status
                HStack {
                    Text("Status")
                    Spacer()
                    Text(notificationManager.hasPermission ? "Enabled" : "Disabled")
                        .foregroundColor(notificationManager.hasPermission ? .green : .red)
                }
                
                // Open settings button if disabled
                if !notificationManager.hasPermission {
                    Button("Enable in Settings") {
                        if let url = URL(string: UIApplication.openSettingsURLString) {
                            UIApplication.shared.open(url)
                        }
                    }
                }
            }
            
            if notificationManager.hasPermission {
                Section(header: Text("Notification Types")) {
                    // New item notifications
                    Toggle("New Items", isOn: $newItemNotificationsEnabled)
                        .onChange(of: newItemNotificationsEnabled) { _, isEnabled in
                            updateNotificationSettings()
                        }
                    
                    // Reminder notifications
                    Toggle("Reminders", isOn: $reminderNotificationsEnabled)
                        .onChange(of: reminderNotificationsEnabled) { _, isEnabled in
                            updateNotificationSettings()
                        }
                    
                    // Update notifications
                    Toggle("Updates", isOn: $updateNotificationsEnabled)
                        .onChange(of: updateNotificationsEnabled) { _, isEnabled in
                            updateNotificationSettings()
                        }
                    
                    // Message notifications
                    Toggle("Messages", isOn: $messageNotificationsEnabled)
                        .onChange(of: messageNotificationsEnabled) { _, isEnabled in
                            updateNotificationSettings()
                        }
                }
                
                Section(header: Text("Pending Notifications")) {
                    // Show number of pending notifications
                    HStack {
                        Text("Scheduled Notifications")
                        Spacer()
                        Text("\(notificationManager.pendingNotifications.count)")
                            .foregroundColor(.secondary)
                    }
                    
                    // Clear all button
                    Button("Clear All Pending Notifications", role: .destructive) {
                        notificationManager.removeAllPendingNotifications()
                        notificationManager.refreshPendingNotifications()
                    }
                    .disabled(notificationManager.pendingNotifications.isEmpty)
                }
            }
        }
        .navigationTitle("Notification Settings")
        .onAppear {
            // Refresh pending notifications
            notificationManager.refreshPendingNotifications()
            
            // Load current settings
            loadNotificationSettings()
        }
    }
    
    // Load notification settings from UserDefaults
    private func loadNotificationSettings() {
        let defaults = UserDefaults.standard
        newItemNotificationsEnabled = defaults.bool(forKey: "newItemNotificationsEnabled", defaultValue: true)
        reminderNotificationsEnabled = defaults.bool(forKey: "reminderNotificationsEnabled", defaultValue: true)
        updateNotificationsEnabled = defaults.bool(forKey: "updateNotificationsEnabled", defaultValue: true)
        messageNotificationsEnabled = defaults.bool(forKey: "messageNotificationsEnabled", defaultValue: true)
    }
    
    // Update notification settings
    private func updateNotificationSettings() {
        let defaults = UserDefaults.standard
        defaults.set(newItemNotificationsEnabled, forKey: "newItemNotificationsEnabled")
        defaults.set(reminderNotificationsEnabled, forKey: "reminderNotificationsEnabled")
        defaults.set(updateNotificationsEnabled, forKey: "updateNotificationsEnabled")
        defaults.set(messageNotificationsEnabled, forKey: "messageNotificationsEnabled")
        
        // Update categories based on settings
        updateNotificationCategories()
    }
    
    // Update notification categories based on settings
    private func updateNotificationCategories() {
        // This would update the backend to send only the enabled notification types
        Task {
            do {
                try await APIClient.shared.updateNotificationPreferences(
                    newItems: newItemNotificationsEnabled,
                    reminders: reminderNotificationsEnabled,
                    updates: updateNotificationsEnabled,
                    messages: messageNotificationsEnabled
                )
            } catch {
                Logger.notifications.error("Failed to update notification preferences: \(error.localizedDescription)")
            }
        }
    }
}

// Extension for UserDefaults convenience
extension UserDefaults {
    func bool(forKey key: String, defaultValue: Bool) -> Bool {
        if object(forKey: key) == nil {
            return defaultValue
        }
        return bool(forKey: key)
    }
}
```

### 2.4 Rich Notification Extensions

```swift
// IMPLEMENT: Notification Service Extension (in separate target)
// This is used to process rich notifications with attachments and modify content before delivery

import UserNotifications
import UIKit

class NotificationService: UNNotificationServiceExtension {
    var contentHandler: ((UNNotificationContent) -> Void)?
    var bestAttemptContent: UNMutableNotificationContent?
    
    override func didReceive(_ request: UNNotificationRequest, withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void) {
        self.contentHandler = contentHandler
        bestAttemptContent = (request.content.mutableCopy() as? UNMutableNotificationContent)
        
        guard let bestAttemptContent = bestAttemptContent else {
            contentHandler(request.content)
            return
        }
        
        // Decode notification payload
        guard let userInfo = bestAttemptContent.userInfo as? [String: Any] else {
            contentHandler(bestAttemptContent)
            return
        }
        
        // Process rich notification
        processRichNotification(userInfo: userInfo, content: bestAttemptContent) { processedContent in
            contentHandler(processedContent)
        }
    }
    
    override func serviceExtensionTimeWillExpire() {
        // Called just before the extension will be terminated by the system.
        // If contentHandler hasn't been called, call it with the original content
        if let contentHandler = contentHandler, let bestAttemptContent = bestAttemptContent {
            contentHandler(bestAttemptContent)
        }
    }
    
    // Process rich notification with attachments
    private func processRichNotification(userInfo: [String: Any], content: UNMutableNotificationContent, completion: @escaping (UNNotificationContent) -> Void) {
        // Check for rich attachment
        if let attachmentURL = userInfo["attachment-url"] as? String, let url = URL(string: attachmentURL) {
            // Download attachment
            downloadAttachment(from: url) { attachment in
                if let attachment = attachment {
                    // Add attachment to notification
                    content.attachments = [attachment]
                }
                
                // Process additional content modifications
                self.processAdditionalContent(userInfo: userInfo, content: content)
                
                // Deliver notification
                completion(content)
            }
        } else {
            // No attachment, just process additional content
            processAdditionalContent(userInfo: userInfo, content: content)
            
            // Deliver notification
            completion(content)
        }
    }
    
    // Download attachment from URL
    private func downloadAttachment(from url: URL, completion: @escaping (UNNotificationAttachment?) -> Void) {
        let session = URLSession(configuration: .default)
        
        let task = session.downloadTask(with: url) { tempFileURL, response, error in
            guard let tempFileURL = tempFileURL, error == nil else {
                completion(nil)
                return
            }
            
            // Get file extension
            var fileExtension = "file"
            if let mimeType = response?.mimeType {
                fileExtension = self.fileExtension(from: mimeType)
            } else if let pathExtension = url.pathExtension, !pathExtension.isEmpty {
                fileExtension = pathExtension
            }
            
            // Create temporary file URL with extension
            let fileManager = FileManager.default
            let tempDirectory = URL(fileURLWithPath: NSTemporaryDirectory())
            let fileName = ProcessInfo.processInfo.globallyUniqueString
            let targetURL = tempDirectory.appendingPathComponent("\(fileName).\(fileExtension)")
            
            do {
                try fileManager.moveItem(at: tempFileURL, to: targetURL)
                
                // Create attachment
                let attachment = try UNNotificationAttachment(identifier: fileName, url: targetURL)
                completion(attachment)
            } catch {
                completion(nil)
            }
        }
        
        task.resume()
    }
    
    // Process additional content modifications
    private func processAdditionalContent(userInfo: [String: Any], content: UNMutableNotificationContent) {
        // Add thread identifier if available
        if let threadId = userInfo["thread-id"] as? String {
            content.threadIdentifier = threadId
        }
        
        // Add summary if available
        if let summary = userInfo["summary"] as? String {
            content.summaryArgument = summary
        }
        
        // Add relevance score if available (0.0 to 1.0)
        if let relevanceScore = userInfo["relevance-score"] as? Double {
            content.relevanceScore = max(0.0, min(1.0, relevanceScore))
        }
        
        // Add sound if available
        if let soundName = userInfo["sound"] as? String {
            content.sound = UNNotificationSound(named: UNNotificationSoundName(rawValue: soundName))
        }
        
        // Add badge number if available
        if let badgeNumber = userInfo["badge"] as? NSNumber {
            content.badge = badgeNumber
        }
    }
    
    // Get file extension from MIME type
    private func fileExtension(from mimeType: String) -> String {
        switch mimeType {
        case "image/jpeg":
            return "jpg"
        case "image/png":
            return "png"
        case "image/gif":
            return "gif"
        case "video/mp4":
            return "mp4"
        case "audio/mpeg":
            return "mp3"
        case "audio/mp4":
            return "m4a"
        default:
            return "dat"
        }
    }
}

// IMPLEMENT: Notification Content Extension (in separate target)
// This is used to provide a custom UI for notifications

import UIKit
import UserNotifications
import UserNotificationsUI

class NotificationViewController: UIViewController, UNNotificationContentExtension {
    // UI elements
    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var bodyLabel: UILabel!
    @IBOutlet weak var imageView: UIImageView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Configure UI
        imageView.contentMode = .scaleAspectFill
        imageView.layer.cornerRadius = 8
        imageView.clipsToBounds = true
    }
    
    // Notification will be displayed
    func didReceive(_ notification: UNNotification) {
        // Get content
        let content = notification.request.content
        
        // Set title and body
        titleLabel.text = content.title
        bodyLabel.text = content.body
        
        // Check for attachments
        if let attachment = content.attachments.first {
            if attachment.url.startAccessingSecurityScopedResource() {
                // Load image
                if attachment.url.pathExtension.lowercased() == "jpg" ||
                   attachment.url.pathExtension.lowercased() == "png" ||
                   attachment.url.pathExtension.lowercased() == "gif" {
                    let image = UIImage(contentsOfFile: attachment.url.path)
                    imageView.image = image
                    imageView.isHidden = false
                } else {
                    imageView.isHidden = true
                }
                
                attachment.url.stopAccessingSecurityScopedResource()
            }
        } else {
            imageView.isHidden = true
        }
    }
    
    // Handle notification actions
    func didReceive(_ response: UNNotificationResponse, completionHandler completion: @escaping (UNNotificationContentExtensionResponseOption) -> Void) {
        // Handle specific actions
        switch response.actionIdentifier {
        case "VIEW_ITEM":
            // Dismiss and launch app
            completion(.dismissAndForwardAction)
            
        case "COMPLETE_TASK":
            // Handle in extension UI
            showCompletionConfirmation()
            completion(.doNotDismiss)
            
        case "SNOOZE":
            // Show snooze options
            showSnoozeOptions()
            completion(.doNotDismiss)
            
        default:
            // Forward other actions to app
            completion(.dismissAndForwardAction)
        }
    }
    
    // Show completion confirmation UI
    private func showCompletionConfirmation() {
        // Show animation or confirmation UI
        UIView.animate(withDuration: 0.3) {
            self.titleLabel.text = "Task Completed!"
            self.bodyLabel.text = "The task has been marked as complete."
        }
    }
    
    // Show snooze options UI
    private func showSnoozeOptions() {
        // Implementation would show snooze options UI
        UIView.animate(withDuration: 0.3) {
            self.titleLabel.text = "Reminder Snoozed"
            self.bodyLabel.text = "You'll be reminded again in 15 minutes."
        }
    }
}
```

## 3. API Client Integration

### 3.1 APIClient Extension for Push Notifications

```swift
// IMPLEMENT: API client extension for push notifications
extension APIClient {
    // Register device token with backend
    func registerPushToken(token: String) async throws {
        // Create request body
        let body: [String: Any] = [
            "device_token": token,
            "device_type": "ios",
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0",
            "environment": isProduction ? "production" : "development"
        ]
        
        // Create request
        let request = APIRequest(
            endpoint: "/devices/register",
            method: .post,
            body: body,
            requiresAuth: true
        )
        
        // Send request
        try await sendRequest(request, responseType: EmptyResponse.self)
    }
    
    // Update notification preferences
    func updateNotificationPreferences(newItems: Bool, reminders: Bool, updates: Bool, messages: Bool) async throws {
        // Create request body
        let body: [String: Any] = [
            "preferences": [
                "new_items": newItems,
                "reminders": reminders,
                "updates": updates,
                "messages": messages
            ]
        ]
        
        // Create request
        let request = APIRequest(
            endpoint: "/users/notification-preferences",
            method: .put,
            body: body,
            requiresAuth: true
        )
        
        // Send request
        try await sendRequest(request, responseType: EmptyResponse.self)
    }
    
    // Send message reply
    func sendMessageReply(messageId: String, text: String) async throws {
        // Create request body
        let body: [String: Any] = [
            "message_id": messageId,
            "text": text
        ]
        
        // Create request
        let request = APIRequest(
            endpoint: "/messages/reply",
            method: .post,
            body: body,
            requiresAuth: true
        )
        
        // Send request
        try await sendRequest(request, responseType: EmptyResponse.self)
    }
    
    // Empty response type for endpoints that don't return data
    struct EmptyResponse: Decodable {}
    
    // Check if running in production environment
    private var isProduction: Bool {
        #if DEBUG
        return false
        #else
        return true
        #endif
    }
}
```

### 3.2 SyncManager Extension for Background Updates

```swift
// IMPLEMENT: SyncManager extension for background updates
extension SyncManager {
    // Sync items from API in background
    func syncItemsFromAPI() async throws -> Bool {
        guard networkMonitor.isConnected else {
            Logger.sync.warning("Cannot sync: Device is offline")
            return false
        }
        
        do {
            // Get last sync date
            let lastSync = UserDefaults.standard.object(forKey: "lastSyncDate") as? Date ?? Date(timeIntervalSince1970: 0)
            
            // Fetch changes since last sync
            let response = try await apiClient.fetchChanges(since: lastSync)
            
            // No changes
            if response.items.isEmpty {
                return false
            }
            
            // Save items to Core Data
            try await coreDataManager.saveItems(response.items)
            
            // Update last sync date
            let now = Date()
            UserDefaults.standard.set(now, forKey: "lastSyncDate")
            
            // Notify about new items if app is not active
            if UIApplication.shared.applicationState != .active {
                // Check if notification preferences allow new item notifications
                let shouldNotify = UserDefaults.standard.bool(forKey: "newItemNotificationsEnabled", defaultValue: true)
                
                if shouldNotify {
                    // Get only new items
                    let newItems = response.items.filter { $0.createdAt > lastSync }
                    
                    // Schedule notifications for new items
                    for item in newItems {
                        NotificationManager.shared.scheduleNewItemNotification(item: item)
                    }
                }
            }
            
            return true
        } catch {
            Logger.sync.error("Background sync failed: \(error.localizedDescription)")
            throw error
        }
    }
}
```

## 4. Server-Side Implementation

### 4.1 Node.js Implementation

```javascript
// IMPLEMENT: Server-side push notification service (Node.js)
const express = require('express');
const router = express.Router();
const apn = require('apn'); // Apple Push Notification Service
const admin = require('firebase-admin'); // For Android FCM
const { Device, User, NotificationLog } = require('../models');

// Initialize Firebase Admin SDK for Android
admin.initializeApp({
  credential: admin.credential.applicationDefault(),
  databaseURL: process.env.FIREBASE_DATABASE_URL
});

// Initialize APN provider for iOS
const apnProvider = new apn.Provider({
  token: {
    key: process.env.APN_KEY_PATH,
    keyId: process.env.APN_KEY_ID,
    teamId: process.env.APN_TEAM_ID,
  },
  production: process.env.NODE_ENV === 'production'
});

// Register device token
router.post('/devices/register', async (req, res) => {
  try {
    const { device_token, device_type, app_version, environment } = req.body;
    const userId = req.user.id;
    
    // Find or create device
    const [device, created] = await Device.findOrCreate({
      where: { token: device_token },
      defaults: {
        userId,
        type: device_type,
        appVersion: app_version,
        environment,
        active: true
      }
    });
    
    // Update device if it exists
    if (!created) {
      await device.update({
        userId,
        appVersion: app_version,
        environment,
        active: true
      });
    }
    
    res.status(200).json({ message: 'Device registered successfully' });
  } catch (error) {
    console.error('Error registering device:', error);
    res.status(500).json({ error: 'Failed to register device' });
  }
});

// Update notification preferences
router.put('/users/notification-preferences', async (req, res) => {
  try {
    const { preferences } = req.body;
    const userId = req.user.id;
    
    // Update user preferences
    await User.update({ notificationPreferences: preferences }, {
      where: { id: userId }
    });
    
    res.status(200).json({ message: 'Notification preferences updated successfully' });
  } catch (error) {
    console.error('Error updating notification preferences:', error);
    res.status(500).json({ error: 'Failed to update notification preferences' });
  }
});

// Send push notification to a user
async function sendPushNotification(userId, notification) {
  try {
    // Get user devices
    const devices = await Device.findAll({
      where: { userId, active: true }
    });
    
    if (devices.length === 0) {
      return;
    }
    
    // Get user preferences
    const user = await User.findByPk(userId);
    const preferences = user.notificationPreferences || {
      new_items: true,
      reminders: true,
      updates: true,
      messages: true
    };
    
    // Check if this notification type is enabled
    const notificationType = notification.type || 'new_item';
    const prefKey = {
      'new_item': 'new_items',
      'reminder': 'reminders',
      'update': 'updates',
      'message': 'messages'
    }[notificationType];
    
    if (!preferences[prefKey]) {
      return; // User has disabled this notification type
    }
    
    // Group devices by type
    const iosDevices = devices.filter(d => d.type === 'ios');
    const androidDevices = devices.filter(d => d.type === 'android');
    
    // Send to iOS devices
    if (iosDevices.length > 0) {
      await sendToApns(iosDevices, notification);
    }
    
    // Send to Android devices
    if (androidDevices.length > 0) {
      await sendToFcm(androidDevices, notification);
    }
    
    // Log notification
    await NotificationLog.create({
      userId,
      type: notificationType,
      title: notification.title,
      body: notification.body,
      data: notification.data
    });
  } catch (error) {
    console.error('Error sending push notification:', error);
  }
}

// Send to Apple Push Notification Service
async function sendToApns(devices, notification) {
  try {
    // Create APN notification
    const apnNotification = new apn.Notification();
    
    // Set expiry (1 hour)
    apnNotification.expiry = Math.floor(Date.now() / 1000) + 3600;
    
    // Set alert
    apnNotification.alert = {
      title: notification.title,
      body: notification.body
    };
    
    // Set sound
    apnNotification.sound = notification.sound || 'default';
    
    // Set badge
    if (notification.badge) {
      apnNotification.badge = notification.badge;
    }
    
    // Set custom data
    apnNotification.payload = notification.data || {};
    
    // Set category
    if (notification.category) {
      apnNotification.category = notification.category;
    }
    
    // Set thread ID for grouping
    if (notification.threadId) {
      apnNotification.threadId = notification.threadId;
    }
    
    // Set mutable-content flag for rich notifications
    if (notification.mutableContent) {
      apnNotification.mutableContent = 1;
    }
    
    // Send to each device
    const deviceTokens = devices.map(d => d.token);
    const result = await apnProvider.send(apnNotification, deviceTokens);
    
    // Handle failed devices
    if (result.failed.length > 0) {
      // Mark failed devices as inactive
      const failedTokens = result.failed.map(item => item.device);
      await Device.update({ active: false }, {
        where: { token: failedTokens }
      });
    }
    
    return result;
  } catch (error) {
    console.error('Error sending to APNS:', error);
    throw error;
  }
}

// Send to Firebase Cloud Messaging (for Android)
async function sendToFcm(devices, notification) {
  try {
    // Create FCM message
    const message = {
      notification: {
        title: notification.title,
        body: notification.body
      },
      data: notification.data || {},
      android: {
        notification: {
          sound: notification.sound || 'default',
          channelId: notification.channelId || 'default',
          priority: notification.priority || 'high'
        }
      }
    };
    
    // Send to each device
    const deviceTokens = devices.map(d => d.token);
    const result = await admin.messaging().sendToDevice(deviceTokens, message);
    
    // Handle failed devices
    if (result.failureCount > 0) {
      // Get failed tokens
      const failedTokens = [];
      result.responses.forEach((response, index) => {
        if (!response.success) {
          failedTokens.push(deviceTokens[index]);
        }
      });
      
      // Mark failed devices as inactive
      await Device.update({ active: false }, {
        where: { token: failedTokens }
      });
    }
    
    return result;
  } catch (error) {
    console.error('Error sending to FCM:', error);
    throw error;
  }
}

// Send silent notification for background refresh
async function sendSilentNotification(userId) {
  try {
    // Get iOS devices
    const devices = await Device.findAll({
      where: { userId, type: 'ios', active: true }
    });
    
    if (devices.length === 0) {
      return;
    }
    
    // Create silent notification
    const notification = new apn.Notification();
    notification.contentAvailable = 1;
    notification.pushType = 'background';
    notification.payload = {
      silent: true,
      timestamp: Date.now()
    };
    
    // Send to each device
    const deviceTokens = devices.map(d => d.token);
    await apnProvider.send(notification, deviceTokens);
  } catch (error) {
    console.error('Error sending silent notification:', error);
  }
}

// Export router and utility functions
module.exports = {
  router,
  sendPushNotification,
  sendSilentNotification
};
```

### 4.2 API Endpoints for Notification Management

```javascript
// IMPLEMENT: API endpoints for notification management
const express = require('express');
const router = express.Router();
const { sendPushNotification } = require('./notifications');
const { Item, User, UserItem, NotificationLog } = require('../models');

// Send notification for new item
router.post('/items/:id/notify', async (req, res) => {
  try {
    const itemId = req.params.id;
    const { userIds } = req.body;
    
    // Get item
    const item = await Item.findByPk(itemId);
    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    // Create notification
    const notification = {
      type: 'new_item',
      title: 'New Item Added',
      body: `A new item titled '${item.title}' has been added`,
      data: {
        notification_type: 'new_item',
        item_id: item.id
      },
      category: 'new_item',
      badge: 1
    };
    
    // If specific users are provided, send to them
    if (userIds && userIds.length > 0) {
      for (const userId of userIds) {
        await sendPushNotification(userId, notification);
      }
    } else {
      // Otherwise, get all users who should receive this notification
      const users = await User.findAll({
        include: [{
          model: UserItem,
          where: { itemId }
        }]
      });
      
      for (const user of users) {
        await sendPushNotification(user.id, notification);
      }
    }
    
    res.status(200).json({ message: 'Notifications sent successfully' });
  } catch (error) {
    console.error('Error sending notifications:', error);
    res.status(500).json({ error: 'Failed to send notifications' });
  }
});

// Send reminder notification
router.post('/items/:id/remind', async (req, res) => {
  try {
    const itemId = req.params.id;
    const { userId } = req.body;
    
    // Get item
    const item = await Item.findByPk(itemId);
    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    // Create notification
    const notification = {
      type: 'reminder',
      title: 'Reminder',
      body: `Reminder for: ${item.title}`,
      data: {
        notification_type: 'reminder',
        item_id: item.id
      },
      category: 'reminder',
      badge: 1,
      sound: 'reminder.caf'
    };
    
    // Send notification
    await sendPushNotification(userId, notification);
    
    res.status(200).json({ message: 'Reminder sent successfully' });
  } catch (error) {
    console.error('Error sending reminder:', error);
    res.status(500).json({ error: 'Failed to send reminder' });
  }
});

// Schedule a notification
router.post('/notifications/schedule', async (req, res) => {
  try {
    const { userId, type, title, body, data, scheduledFor } = req.body;
    
    // Validate scheduled time
    const scheduledTime = new Date(scheduledFor);
    if (isNaN(scheduledTime.getTime())) {
      return res.status(400).json({ error: 'Invalid scheduled time' });
    }
    
    // Create scheduled notification
    await NotificationLog.create({
      userId,
      type,
      title,
      body,
      data,
      scheduledFor: scheduledTime,
      status: 'scheduled'
    });
    
    res.status(200).json({ message: 'Notification scheduled successfully' });
  } catch (error) {
    console.error('Error scheduling notification:', error);
    res.status(500).json({ error: 'Failed to schedule notification' });
  }
});

// Get notification history for a user
router.get('/notifications/history', async (req, res) => {
  try {
    const userId = req.user.id;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    
    // Get notification logs
    const { count, rows } = await NotificationLog.findAndCountAll({
      where: { userId },
      order: [['createdAt', 'DESC']],
      limit,
      offset
    });
    
    res.status(200).json({
      notifications: rows,
      total: count,
      page,
      pages: Math.ceil(count / limit)
    });
  } catch (error) {