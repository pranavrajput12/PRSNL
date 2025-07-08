# PRSNL iOS: Widgets Implementation Plan

This document outlines a comprehensive strategy for implementing iOS home screen widgets for the PRSNL app, allowing users to access important information and perform quick actions without opening the app.

## 1. Widget Architecture

### 1.1 Overview

The PRSNL iOS widgets will extend the app's functionality to the iOS home screen, providing users with quick access to their most important items and information. This implementation will enable:

- At-a-glance view of recent items
- Quick actions without opening the app
- Timeline-based data updates
- Multiple widget sizes and configurations
- Deep linking to relevant app sections

### 1.2 System Architecture

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│                 │     │                   │     │                 │
│  PRSNL iOS App  │◄───►│  Shared Container │◄───►│  PRSNL Widgets  │
│                 │     │  (App Group)      │     │  Extension      │
└─────────────────┘     └───────────────────┘     └─────────────────┘
                                   ▲
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │                     │
                        │  Core Data / Cache  │
                        │                     │
                        └─────────────────────┘
```

## 2. Widget Types and Sizes

### 2.1 Timeline Widget

Displays a chronological list of recent items from the user's timeline.

**Sizes:**
- Small: Shows the most recent item with title and icon
- Medium: Shows the 3 most recent items with titles
- Large: Shows the 5 most recent items with titles and previews

### 2.2 Quick Actions Widget

Provides quick action buttons to create new items or access frequently used features.

**Sizes:**
- Small: 1 primary action (create new item)
- Medium: 4 action buttons in a grid
- Large: 8 action buttons in a grid with labels

### 2.3 Stats Widget

Displays statistics and metrics about the user's items and usage patterns.

**Sizes:**
- Small: Shows a single primary metric
- Medium: Shows 3-4 key metrics
- Large: Shows 6-8 metrics with mini-charts

## 3. Widget Implementation

### 3.1 Widget Extension Setup

```swift
// IMPLEMENT: Widget extension main entry point
import WidgetKit
import SwiftUI

@main
struct PRSNLWidgets: WidgetBundle {
    var body: some Widget {
        TimelineWidget()
        QuickActionsWidget()
        StatsWidget()
    }
}
```

### 3.2 Timeline Widget Implementation

```swift
// IMPLEMENT: Timeline widget
import WidgetKit
import SwiftUI
import CoreData

// MARK: - Widget Definition

struct TimelineWidget: Widget {
    private let kind = "TimelineWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(
            kind: kind,
            provider: TimelineProvider()
        ) { entry in
            TimelineWidgetView(entry: entry)
        }
        .configurationDisplayName("Recent Items")
        .description("View your most recent items at a glance.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// MARK: - Timeline Provider

struct TimelineProvider: TimelineProvider {
    typealias Entry = TimelineEntry
    
    // Placeholder for widget gallery
    func placeholder(in context: Context) -> TimelineEntry {
        TimelineEntry(date: Date(), items: [
            ItemSnapshot(id: "1", title: "Meeting with Design Team", content: "Discuss new UI components", createdAt: Date(), type: "note"),
            ItemSnapshot(id: "2", title: "Grocery Shopping", content: "Milk, Eggs, Bread", createdAt: Date().addingTimeInterval(-3600), type: "task"),
            ItemSnapshot(id: "3", title: "Project Deadline", content: "Submit final deliverables", createdAt: Date().addingTimeInterval(-7200), type: "event"),
            ItemSnapshot(id: "4", title: "Workout Plan", content: "30 min cardio, strength training", createdAt: Date().addingTimeInterval(-10800), type: "note"),
            ItemSnapshot(id: "5", title: "Book Recommendation", content: "Clean Architecture by Robert Martin", createdAt: Date().addingTimeInterval(-14400), type: "note")
        ])
    }
    
    // Snapshot for widget gallery
    func getSnapshot(in context: Context, completion: @escaping (TimelineEntry) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                let items = try await dataProvider.fetchRecentItems(limit: 5)
                let entry = TimelineEntry(date: Date(), items: items)
                completion(entry)
            } catch {
                // Fallback to placeholder data
                completion(placeholder(in: context))
            }
        }
    }
    
    // Timeline for updating the widget
    func getTimeline(in context: Context, completion: @escaping (Timeline<TimelineEntry>) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                let items = try await dataProvider.fetchRecentItems(limit: 5)
                let entry = TimelineEntry(date: Date(), items: items)
                
                // Refresh the timeline after 15 minutes
                let refreshDate = Calendar.current.date(byAdding: .minute, value: 15, to: Date()) ?? Date()
                let timeline = Timeline(entries: [entry], policy: .after(refreshDate))
                
                completion(timeline)
            } catch {
                // Fallback to placeholder with shorter refresh
                let entry = placeholder(in: context)
                let timeline = Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(60)))
                completion(timeline)
            }
        }
    }
}

// MARK: - Timeline Entry

struct TimelineEntry: TimelineEntry {
    let date: Date
    let items: [ItemSnapshot]
}

// MARK: - Item Snapshot Model

struct ItemSnapshot: Identifiable {
    let id: String
    let title: String
    let content: String
    let createdAt: Date
    let type: String
    
    var iconName: String {
        switch type {
        case "task":
            return "checklist"
        case "event":
            return "calendar"
        case "link":
            return "link"
        default:
            return "doc.text"
        }
    }
    
    var timeAgo: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: createdAt, relativeTo: Date())
    }
}

// MARK: - Widget Views

struct TimelineWidgetView: View {
    var entry: TimelineProvider.Entry
    @Environment(\.widgetFamily) var family
    
    var body: some View {
        switch family {
        case .systemSmall:
            SmallTimelineWidgetView(entry: entry)
        case .systemMedium:
            MediumTimelineWidgetView(entry: entry)
        case .systemLarge:
            LargeTimelineWidgetView(entry: entry)
        default:
            SmallTimelineWidgetView(entry: entry)
        }
    }
}

// Small widget view
struct SmallTimelineWidgetView: View {
    var entry: TimelineProvider.Entry
    
    var body: some View {
        if let item = entry.items.first {
            Link(destination: URL(string: "prsnl://item/\(item.id)")!) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: item.iconName)
                            .font(.system(size: 12))
                            .foregroundColor(.blue)
                        
                        Text("Latest Item")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Text(item.timeAgo)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Text(item.title)
                        .font(.headline)
                        .fontWeight(.semibold)
                        .lineLimit(2)
                    
                    Spacer()
                    
                    Text(item.content)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
                .padding()
            }
        } else {
            VStack(spacing: 8) {
                Image(systemName: "doc.text")
                    .font(.system(size: 24))
                    .foregroundColor(.blue)
                
                Text("No Recent Items")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Button("Create New") {
                    // Deep link to create new item
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
            .padding()
        }
    }
}

// Medium widget view
struct MediumTimelineWidgetView: View {
    var entry: TimelineProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Recent Items")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text(Date(), style: .date)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            
            if entry.items.isEmpty {
                HStack {
                    Spacer()
                    Text("No items yet")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .padding(.vertical, 20)
            } else {
                ForEach(entry.items.prefix(3)) { item in
                    Link(destination: URL(string: "prsnl://item/\(item.id)")!) {
                        HStack {
                            Image(systemName: item.iconName)
                                .font(.system(size: 14))
                                .foregroundColor(.blue)
                                .frame(width: 24, height: 24)
                            
                            VStack(alignment: .leading) {
                                Text(item.title)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                    .foregroundColor(.primary)
                                    .lineLimit(1)
                            }
                            
                            Spacer()
                            
                            Text(item.timeAgo)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// Large widget view
struct LargeTimelineWidgetView: View {
    var entry: TimelineProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Items")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text(Date(), style: .date)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            
            if entry.items.isEmpty {
                HStack {
                    Spacer()
                    
                    VStack(spacing: 8) {
                        Image(systemName: "doc.text")
                            .font(.system(size: 24))
                            .foregroundColor(.blue)
                        
                        Text("No items yet")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                }
                .padding(.vertical, 40)
            } else {
                ForEach(entry.items) { item in
                    Link(destination: URL(string: "prsnl://item/\(item.id)")!) {
                        HStack(alignment: .top) {
                            Image(systemName: item.iconName)
                                .font(.system(size: 14))
                                .foregroundColor(.blue)
                                .frame(width: 24, height: 24)
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text(item.title)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                    .foregroundColor(.primary)
                                    .lineLimit(1)
                                
                                Text(item.content)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .lineLimit(1)
                            }
                            
                            Spacer()
                            
                            Text(item.timeAgo)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
}
```

### 3.3 Quick Actions Widget Implementation

```swift
// IMPLEMENT: Quick Actions widget
import WidgetKit
import SwiftUI

// MARK: - Widget Definition

struct QuickActionsWidget: Widget {
    private let kind = "QuickActionsWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(
            kind: kind,
            provider: QuickActionsProvider()
        ) { entry in
            QuickActionsWidgetView(entry: entry)
        }
        .configurationDisplayName("Quick Actions")
        .description("Quickly create new items or access features.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// MARK: - Quick Actions Provider

struct QuickActionsProvider: TimelineProvider {
    typealias Entry = QuickActionsEntry
    
    // Placeholder for widget gallery
    func placeholder(in context: Context) -> QuickActionsEntry {
        QuickActionsEntry(date: Date())
    }
    
    // Snapshot for widget gallery
    func getSnapshot(in context: Context, completion: @escaping (QuickActionsEntry) -> Void) {
        let entry = QuickActionsEntry(date: Date())
        completion(entry)
    }
    
    // Timeline for updating the widget
    func getTimeline(in context: Context, completion: @escaping (Timeline<QuickActionsEntry>) -> Void) {
        // Create a single entry as this widget doesn't need frequent updates
        let entry = QuickActionsEntry(date: Date())
        
        // Refresh once per day
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Date()) ?? Date()
        let midnight = Calendar.current.startOfDay(for: tomorrow)
        
        let timeline = Timeline(entries: [entry], policy: .after(midnight))
        completion(timeline)
    }
}

// MARK: - Quick Actions Entry

struct QuickActionsEntry: TimelineEntry {
    let date: Date
}

// MARK: - Action Model

struct QuickAction: Identifiable {
    let id: String
    let title: String
    let icon: String
    let deepLink: URL
    let color: Color
}

// MARK: - Widget Views

struct QuickActionsWidgetView: View {
    var entry: QuickActionsProvider.Entry
    @Environment(\.widgetFamily) var family
    
    // Define common actions
    let actions: [QuickAction] = [
        QuickAction(
            id: "new_note",
            title: "New Note",
            icon: "note.text",
            deepLink: URL(string: "prsnl://create/note")!,
            color: .blue
        ),
        QuickAction(
            id: "new_task",
            title: "New Task",
            icon: "checklist",
            deepLink: URL(string: "prsnl://create/task")!,
            color: .green
        ),
        QuickAction(
            id: "new_event",
            title: "New Event",
            icon: "calendar",
            deepLink: URL(string: "prsnl://create/event")!,
            color: .orange
        ),
        QuickAction(
            id: "new_link",
            title: "Save Link",
            icon: "link",
            deepLink: URL(string: "prsnl://create/link")!,
            color: .purple
        ),
        QuickAction(
            id: "search",
            title: "Search",
            icon: "magnifyingglass",
            deepLink: URL(string: "prsnl://search")!,
            color: .gray
        ),
        QuickAction(
            id: "timeline",
            title: "Timeline",
            icon: "list.bullet",
            deepLink: URL(string: "prsnl://timeline")!,
            color: .blue
        ),
        QuickAction(
            id: "favorites",
            title: "Favorites",
            icon: "star",
            deepLink: URL(string: "prsnl://favorites")!,
            color: .yellow
        ),
        QuickAction(
            id: "settings",
            title: "Settings",
            icon: "gear",
            deepLink: URL(string: "prsnl://settings")!,
            color: .gray
        )
    ]
    
    var body: some View {
        switch family {
        case .systemSmall:
            SmallQuickActionsWidgetView(actions: actions)
        case .systemMedium:
            MediumQuickActionsWidgetView(actions: actions)
        case .systemLarge:
            LargeQuickActionsWidgetView(actions: actions)
        default:
            SmallQuickActionsWidgetView(actions: actions)
        }
    }
}

// Small widget view
struct SmallQuickActionsWidgetView: View {
    let actions: [QuickAction]
    
    var body: some View {
        // Show only the primary action (New Note)
        if let primaryAction = actions.first {
            Link(destination: primaryAction.deepLink) {
                VStack(spacing: 12) {
                    Image(systemName: primaryAction.icon)
                        .font(.system(size: 28))
                        .foregroundColor(primaryAction.color)
                    
                    Text(primaryAction.title)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("Tap to create")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(UIColor.systemBackground))
            }
        }
    }
}

// Medium widget view
struct MediumQuickActionsWidgetView: View {
    let actions: [QuickAction]
    
    var body: some View {
        // Show a 2x2 grid of actions
        let gridActions = Array(actions.prefix(4))
        
        VStack(spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
                .padding(.top, 8)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                ForEach(gridActions) { action in
                    Link(destination: action.deepLink) {
                        VStack(spacing: 8) {
                            Image(systemName: action.icon)
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .frame(width: 36, height: 36)
                                .background(action.color)
                                .cornerRadius(8)
                            
                            Text(action.title)
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                    }
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 8)
        }
    }
}

// Large widget view
struct LargeQuickActionsWidgetView: View {
    let actions: [QuickAction]
    
    var body: some View {
        // Show a 4x2 grid of actions
        VStack(spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
                .padding(.top, 8)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                ForEach(actions) { action in
                    Link(destination: action.deepLink) {
                        VStack(spacing: 8) {
                            Image(systemName: action.icon)
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .frame(width: 36, height: 36)
                                .background(action.color)
                                .cornerRadius(8)
                            
                            Text(action.title)
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                    }
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 8)
        }
    }
}
```

### 3.4 Stats Widget Implementation

```swift
// IMPLEMENT: Stats widget
import WidgetKit
import SwiftUI

// MARK: - Widget Definition

struct StatsWidget: Widget {
    private let kind = "StatsWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(
            kind: kind,
            provider: StatsProvider()
        ) { entry in
            StatsWidgetView(entry: entry)
        }
        .configurationDisplayName("Stats")
        .description("View statistics about your items.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// MARK: - Stats Provider

struct StatsProvider: TimelineProvider {
    typealias Entry = StatsEntry
    
    // Placeholder for widget gallery
    func placeholder(in context: Context) -> StatsEntry {
        StatsEntry(
            date: Date(),
            totalItems: 42,
            itemsToday: 3,
            itemsThisWeek: 12,
            itemsByType: [
                "note": 18,
                "task": 14,
                "event": 7,
                "link": 3
            ],
            completedTasks: 8,
            pendingTasks: 6
        )
    }
    
    // Snapshot for widget gallery
    func getSnapshot(in context: Context, completion: @escaping (StatsEntry) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                let stats = try await dataProvider.fetchStats()
                completion(stats)
            } catch {
                // Fallback to placeholder data
                completion(placeholder(in: context))
            }
        }
    }
    
    // Timeline for updating the widget
    func getTimeline(in context: Context, completion: @escaping (Timeline<StatsEntry>) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                let stats = try await dataProvider.fetchStats()
                
                // Refresh hourly
                let nextHour = Calendar.current.date(byAdding: .hour, value: 1, to: Date()) ?? Date()
                let timeline = Timeline(entries: [stats], policy: .after(nextHour))
                
                completion(timeline)
            } catch {
                // Fallback to placeholder with shorter refresh
                let entry = placeholder(in: context)
                let timeline = Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(300)))
                completion(timeline)
            }
        }
    }
}

// MARK: - Stats Entry

struct StatsEntry: TimelineEntry {
    let date: Date
    let totalItems: Int
    let itemsToday: Int
    let itemsThisWeek: Int
    let itemsByType: [String: Int]
    let completedTasks: Int
    let pendingTasks: Int
    
    // Computed properties for derived stats
    var completionRate: Double {
        let total = completedTasks + pendingTasks
        guard total > 0 else { return 0 }
        return Double(completedTasks) / Double(total)
    }
    
    var primaryItemType: (type: String, count: Int)? {
        itemsByType.max { $0.value < $1.value }
    }
}

// MARK: - Widget Views

struct StatsWidgetView: View {
    var entry: StatsProvider.Entry
    @Environment(\.widgetFamily) var family
    
    var body: some View {
        switch family {
        case .systemSmall:
            SmallStatsWidgetView(entry: entry)
        case .systemMedium:
            MediumStatsWidgetView(entry: entry)
        case .systemLarge:
            LargeStatsWidgetView(entry: entry)
        default:
            SmallStatsWidgetView(entry: entry)
        }
    }
}

// Small widget view
struct SmallStatsWidgetView: View {
    var entry: StatsProvider.Entry
    
    var body: some View {
        Link(destination: URL(string: "prsnl://stats")!) {
            VStack(spacing: 8) {
                Text("Your Items")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("\(entry.totalItems)")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundColor(.primary)
                
                HStack {
                    VStack(alignment: .leading) {
                        Text("Today")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        
                        Text("\(entry.itemsToday)")
                            .font(.caption)
                            .foregroundColor(.primary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        Text("This Week")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        
                        Text("\(entry.itemsThisWeek)")
                            .font(.caption)
                            .foregroundColor(.primary)
                    }
                }
                .padding(.top, 4)
            }
            .padding()
        }
    }
}

// Medium widget view
struct MediumStatsWidgetView: View {
    var entry: StatsProvider.Entry
    
    var body: some View {
        Link(destination: URL(string: "prsnl://stats")!) {
            HStack {
                // Left side - Total count
                VStack(spacing: 8) {
                    Text("Total Items")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("\(entry.totalItems)")
                        .font(.system(size: 36, weight: .bold))
                        .foregroundColor(.primary)
                    
                    if let primaryType = entry.primaryItemType {
                        Text("Mostly \(primaryType.type)s")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .frame(maxWidth: .infinity)
                
                Divider()
                
                // Right side - Item breakdown
                VStack(alignment: .leading, spacing: 8) {
                    Text("Breakdown")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    ForEach(Array(entry.itemsByType.keys.prefix(4)), id: \.self) { type in
                        if let count = entry.itemsByType[type] {
                            HStack {
                                Text(type.capitalized)
                                    .font(.caption)
                                    .foregroundColor(.primary)
                                
                                Spacer()
                                
                                Text("\(count)")
                                    .font(.caption)
                                    .foregroundColor(.primary)
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity)
            }
            .padding()
        }
    }
}

// Large widget view
struct LargeStatsWidgetView: View {
    var entry: StatsProvider.Entry
    
    var body: some View {
        Link(destination: URL(string: "prsnl://stats")!) {
            VStack(spacing: 16) {
                // Header
                Text("PRSNL Stats")
                    .font(.headline)
                    .padding(.top, 8)
                
                // Top section - Overall stats
                HStack(spacing: 20) {
                    StatCard(title: "Total Items", value: "\(entry.totalItems)")
                    StatCard(title: "Today", value: "\(entry.itemsToday)")
                    StatCard(title: "This Week", value: "\(entry.itemsThisWeek)")
                }
                
                Divider()
                
                // Middle section - Task completion
                VStack(alignment: .leading, spacing: 8) {
                    Text("Task Completion")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Text("\(entry.completedTasks) of \(entry.completedTasks + entry.pendingTasks) tasks complete")
                            .font(.caption)
                        
                        Spacer()
                        
                        Text("\(Int(entry.completionRate * 100))%")
                            .font(.caption)
                            .bold()
                    }
                    
                    ProgressView(value: entry.completionRate)
                        .progressViewStyle(LinearProgressViewStyle())
                }
                .padding(.horizontal)
                
                Divider()
                
                // Bottom section - Item type breakdown
                VStack(alignment: .leading, spacing: 8) {
                    Text("Item Types")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        ForEach(Array(entry.itemsByType.keys.prefix(4)), id: \.self) { type in
                            if let count = entry.itemsByType[type] {
                                VStack {
                                    Text("\(count)")
                                        .font(.callout)
                                        .bold()
                                    
                                    Text(type.capitalized)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .frame(maxWidth: .infinity)
                            }
                        }
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical, 8)
        }
    }
}

// Reusable stat card component
struct StatCard: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}
```

## 4. Data Sharing Implementation

### 4.1 Widget Data Provider

```swift
// IMPLEMENT: Widget data provider for shared Core Data access
import Foundation
import CoreData
import SwiftUI

// MARK: - Widget Data Provider

class WidgetDataProvider {
    // Shared Core Data stack
    private let coreDataManager: CoreDataManager
    
    init() {
        // Initialize Core Data manager with shared container
        coreDataManager = CoreDataManager(containerName: "PRSNLData", inMemory: false, isWidget: true)
    }
    
    // MARK: - Data Fetch Methods
    
    // Fetch recent items for Timeline widget
    func fetchRecentItems(limit: Int = 5) async throws -> [ItemSnapshot] {
        // Create fetch request
        let request = NSFetchRequest<CDItem>(entityName: "CDItem")
        request.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: false)]
        request.fetchLimit = limit
        
        // Execute fetch on background context
        return try await coreDataManager.backgroundContext.perform {
            let results = try request.execute()
            
            // Convert to snapshot items
            return results.map { cdItem in
                ItemSnapshot(
                    id: cdItem.id ?? UUID().uuidString,
                    title: cdItem.title ?? "Untitled",
                    content: cdItem.content ?? "",
                    createdAt: cdItem.createdAt ?? Date(),
                    type: cdItem.type ?? "note"
                )
            }
        }
    }
    
    // Fetch stats for Stats widget
    func fetchStats() async throws -> StatsEntry {
        let backgroundContext = coreDataManager.backgroundContext
        
        return try await backgroundContext.perform {
            // Get total items count
            let totalRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            totalRequest.resultType = .countResultType
            let totalItems = try backgroundContext.count(for: totalRequest)
            
            // Get today's items count
            let todayRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            todayRequest.resultType = .countResultType
            todayRequest.predicate = NSPredicate(
                format: "createdAt >= %@",
                Calendar.current.startOfDay(for: Date()) as NSDate
            )
            let itemsToday = try backgroundContext.count(for: todayRequest)
            
            // Get this week's items count
            let weekStartDate = Calendar.current.date(
                byAdding: .day,
                value: -7,
                to: Calendar.current.startOfDay(for: Date())
            )!
            let weekRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            weekRequest.resultType = .countResultType
            weekRequest.predicate = NSPredicate(
                format: "createdAt >= %@",
                weekStartDate as NSDate
            )
            let itemsThisWeek = try backgroundContext.count(for: weekRequest)
            
            // Get items by type
            let typeRequest = NSFetchRequest<NSDictionary>(entityName: "CDItem")
            typeRequest.resultType = .dictionaryResultType
            typeRequest.propertiesToFetch = ["type"]
            typeRequest.propertiesToGroupBy = ["type"]
            typeRequest.propertiesToFetch = ["type", "count"]
            
            let typeResults = try backgroundContext.fetch(typeRequest)
            var itemsByType: [String: Int] = [:]
            
            for result in typeResults {
                if let type = result["type"] as? String,
                   let count = result["count"] as? Int {
                    itemsByType[type] = count
                }
            }
            
            // Get completed tasks count
            let completedRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            completedRequest.resultType = .countResultType
            completedRequest.predicate = NSPredicate(
                format: "type == %@ AND isCompleted == %@",
                "task", NSNumber(value: true)
            )
            let completedTasks = try backgroundContext.count(for: completedRequest)
            
            // Get pending tasks count
            let pendingRequest = NSFetchRequest<NSNumber>(entityName: "CDItem")
            pendingRequest.resultType = .countResultType
            pendingRequest.predicate = NSPredicate(
                format: "type == %@ AND isCompleted == %@",
                "task", NSNumber(value: false)
            )
            let pendingTasks = try backgroundContext.count(for: pendingRequest)
            
            // Create stats entry
            return StatsEntry(
                date: Date(),
                totalItems: totalItems,
                itemsToday: itemsToday,
                itemsThisWeek: itemsThisWeek,
                itemsByType: itemsByType,
                completedTasks: completedTasks,
                pendingTasks: pendingTasks
            )
        }
    }
}
```

### 4.2 App Group and Shared Core Data Setup

```swift
// IMPLEMENT: Modified Core Data manager with app group support
import CoreData
import Foundation

class CoreDataManager {
    // MARK: - Properties
    
    // Singleton instance for main app
    static let shared = CoreDataManager()
    
    // Container name
    private let containerName: String
    
    // App group identifier
    private let appGroupIdentifier = "group.com.yourcompany.prsnl"
    
    // Managed object contexts
    let viewContext: NSManagedObjectContext
    let backgroundContext: NSManagedObjectContext
    
    // Persistent container
    private let container: NSPersistentContainer
    
    // MARK: - Initialization
    
    init(containerName: String = "PRSNLData", inMemory: Bool = false, isWidget: Bool = false) {
        self.containerName = containerName
        
        // Create persistent container
        container = NSPersistentContainer(name: containerName)
        
        // Configure persistent store description
        if let description = container.persistentStoreDescriptions.first {
            // Enable remote notifications
            description.setOption(true as NSNumber, forKey: NSPersistentStoreRemoteChangeNotificationPostOptionKey)
            
            // Set up shared app group container
            if !inMemory {
                let storeURL = FileManager.default.containerURL(
                    forSecurityApplicationGroupIdentifier: appGroupIdentifier
                )?.appendingPathComponent("\(containerName).sqlite")
                
                if let storeURL = storeURL {
                    description.url = storeURL
                }
            }
        }
        
        // Load persistent stores
        container.loadPersistentStores { _, error in
            if let error = error as NSError? {
                fatalError("Failed to load persistent stores: \(error), \(error.userInfo)")
            }
        }
        
        // Enable automatic merges from parent
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        
        // Set view context
        viewContext = container.viewContext
        
        // Create background context
        backgroundContext = container.newBackgroundContext()
        backgroundContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        
        // Set up change notifications if not in widget
        if !isWidget {
            setUpChangeNotifications()
        }
    }
    
    // MARK: - Change Notifications
    
    private func setUpChangeNotifications() {
        // Register for remote change notifications
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(storeRemoteChange(_:)),
            name: .NSPersistentStoreRemoteChange,
            object: container.persistentStoreCoordinator
        )
    }
    
    @objc private func storeRemoteChange(_ notification: Notification) {
        // Process changes and update UI if needed
        viewContext.perform {
            self.viewContext.refreshAllObjects()
        }
    }
    
    // MARK: - Data Update Methods
    
    // Save new or updated item
    func saveItem(_ item: Item, needsSync: Bool = true) async throws {
        // Use background context
        try await backgroundContext.perform {
            // Check if item already exists
            let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
            fetchRequest.predicate = NSPredicate(format: "id == %@", item.id)
            
            let existingItems = try fetchRequest.execute()
            let cdItem: CDItem
            
            if let existingItem = existingItems.first {
                // Update existing item
                cdItem = existingItem
            } else {
                // Create new item
                cdItem = CDItem(context: self.backgroundContext)
                cdItem.id = item.id
                cdItem.createdAt = item.createdAt
            }
            
            // Update properties
            cdItem.title = item.title
            cdItem.content = item.content
            cdItem.updatedAt = Date()
            cdItem.type = item.type
            cdItem.needsSync = needsSync
            
            // Save context
            try self.backgroundContext.save()
            
            // Notify the widget to update
            self.notifyWidgetDataChanged()
        }
    }
    
    // MARK: - Widget Notification
    
    // Notify widgets about data changes
    private func notifyWidgetDataChanged() {
        #if !EXTENSION
        WidgetCenter.shared.reloadAllTimelines()
        #endif
    }
}

// Import WidgetKit only in the main app target
#if !EXTENSION
import WidgetKit
#endif
```

### 4.3 Deep Link Handling

```swift
// IMPLEMENT: Deep link handler for widgets
import SwiftUI

// MARK: - Deep Link Handler

class DeepLinkManager: ObservableObject {
    // Singleton instance
    static let shared = DeepLinkManager()
    
    // Published properties
    @Published var currentRoute: Route?
    
    // Define app routes
    enum Route: Equatable {
        case itemDetail(id: String)
        case createItem(type: String)
        case timeline
        case search
        case favorites
        case stats
        case settings
    }
    
    // Private initializer for singleton
    private init() {}
    
    // Handle deep link URL
    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true),
              let host = components.host else {
            return
        }
        
        let pathComponents = components.path.components(separatedBy: "/").filter { !$0.isEmpty }
        
        // Parse route
        switch host {
        case "item":
            if pathComponents.count > 0 {
                let itemId = pathComponents[0]
                currentRoute = .itemDetail(id: itemId)
            }
            
        case "create":
            if pathComponents.count > 0 {
                let itemType = pathComponents[0]
                currentRoute = .createItem(type: itemType)
            }
            
        case "timeline":
            currentRoute = .timeline
            
        case "search":
            currentRoute = .search
            
        case "favorites":
            currentRoute = .favorites
            
        case "stats":
            currentRoute = .stats
            
        case "settings":
            currentRoute = .settings
            
        default:
            break
        }
    }
}

// MARK: - App Deep Link Handler

struct DeepLinkHandler: ViewModifier {
    @ObservedObject var deepLinkManager = DeepLinkManager.shared
    @Binding var selectedTab: Int
    
    // Mapping of routes to tab indices
    let tabIndices: [DeepLinkManager.Route: Int] = [
        .timeline: 0,
        .search: 1,
        .favorites: 2,
        .stats: 3,
        .settings: 4
    ]
    
    // Sheet presentation state
    @State private var showItemDetail = false
    @State private var selectedItemId: String?
    @State private var showCreateItem = false
    @State private var createItemType: String?
    
    func body(content: Content) -> some View {
        content
            .onChange(of: deepLinkManager.currentRoute) { _, route in
                handleRoute(route)
            }
            .sheet(isPresented: $showItemDetail) {
                if let itemId = selectedItemId {
                    ItemDetailView(itemId: itemId)
                }
            }
            .sheet(isPresented: $showCreateItem) {
                if let itemType = createItemType {
                    CreateItemView(itemType: itemType)
                }
            }
    }
    
    private func handleRoute(_ route: DeepLinkManager.Route?) {
        guard let route = route else { return }
        
        // Handle navigation
        switch route {
        case .itemDetail(let id):
            selectedItemId = id
            showItemDetail = true
            
        case .createItem(let type):
            createItemType = type
            showCreateItem = true
            
        default:
            // Handle tab-based routes
            if let tabIndex = tabIndices[route] {
                selectedTab = tabIndex
            }
        }
        
        // Reset current route
        deepLinkManager.currentRoute = nil
    }
}

// Extension for View
extension View {
    func handleDeepLink(selectedTab: Binding<Int>) -> some View {
        self.modifier(DeepLinkHandler(selectedTab: selectedTab))
    }
}
```

## 5. Configuration and App Integration

### 5.1 Widget Configuration Intent

```swift
// IMPLEMENT: Widget configuration intent for customization
import WidgetKit
import SwiftUI
import IntentsUI

// MARK: - Configuration Intent

struct TimelineConfigurationIntent: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "Configure Timeline Widget"
    static var description: LocalizedStringResource = "Customize how your timeline widget appears."
    
    // Item type filter
    @Parameter(title: "Item Type")
    var itemType: ItemTypeEnum?
    
    // Sort order
    @Parameter(title: "Sort Order")
    var sortOrder: SortOrderEnum?
    
    // Show date/time
    @Parameter(title: "Show Time")
    var showTime: Bool?
}

// Item type enum
enum ItemTypeEnum: String, CaseIterable, Identifiable {
    case all = "all"
    case notes = "note"
    case tasks = "task"
    case events = "event"
    case links = "link"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .all: return "All Items"
        case .notes: return "Notes Only"
        case .tasks: return "Tasks Only"
        case .events: return "Events Only"
        case .links: return "Links Only"
        }
    }
}

// Sort order enum
enum SortOrderEnum: String, CaseIterable, Identifiable {
    case newest = "newest"
    case oldest = "oldest"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .newest: return "Newest First"
        case .oldest: return "Oldest First"
        }
    }
}

// MARK: - Configurable Widget

struct ConfigurableTimelineWidget: Widget {
    private let kind = "ConfigurableTimelineWidget"
    
    var body: some WidgetConfiguration {
        IntentConfiguration(
            kind: kind,
            intent: TimelineConfigurationIntent.self,
            provider: ConfigurableTimelineProvider()
        ) { entry in
            ConfigurableTimelineWidgetView(entry: entry)
        }
        .configurationDisplayName("Timeline")
        .description("View your most recent items with customizable filters.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// MARK: - Configurable Provider

struct ConfigurableTimelineProvider: IntentTimelineProvider {
    typealias Entry = ConfigurableTimelineEntry
    typealias Intent = TimelineConfigurationIntent
    
    // Placeholder for widget gallery
    func placeholder(in context: Context) -> ConfigurableTimelineEntry {
        ConfigurableTimelineEntry(
            date: Date(),
            items: [
                ItemSnapshot(id: "1", title: "Meeting Notes", content: "Discuss new UI components", createdAt: Date(), type: "note"),
                ItemSnapshot(id: "2", title: "Grocery Shopping", content: "Milk, Eggs, Bread", createdAt: Date().addingTimeInterval(-3600), type: "task"),
                ItemSnapshot(id: "3", title: "Project Deadline", content: "Submit final deliverables", createdAt: Date().addingTimeInterval(-7200), type: "event")
            ],
            configuration: TimelineConfigurationIntent()
        )
    }
    
    // Snapshot for widget gallery
    func getSnapshot(for configuration: TimelineConfigurationIntent, in context: Context, completion: @escaping (ConfigurableTimelineEntry) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                // Apply configuration to fetch
                let items = try await dataProvider.fetchConfigurableItems(
                    itemType: configuration.itemType?.rawValue,
                    sortOrder: configuration.sortOrder?.rawValue == "oldest",
                    limit: 5
                )
                
                let entry = ConfigurableTimelineEntry(
                    date: Date(),
                    items: items,
                    configuration: configuration
                )
                
                completion(entry)
            } catch {
                // Fallback to placeholder data
                completion(placeholder(in: context))
            }
        }
    }
    
    // Timeline for updating the widget
    func getTimeline(for configuration: TimelineConfigurationIntent, in context: Context, completion: @escaping (Timeline<ConfigurableTimelineEntry>) -> Void) {
        let dataProvider = WidgetDataProvider()
        
        Task {
            do {
                // Apply configuration to fetch
                let items = try await dataProvider.fetchConfigurableItems(
                    itemType: configuration.itemType?.rawValue,
                    sortOrder: configuration.sortOrder?.rawValue == "oldest",
                    limit: 5
                )
                
                let entry = ConfigurableTimelineEntry(
                    date: Date(),
                    items: items,
                    configuration: configuration
                )
                
                // Refresh the timeline after 15 minutes
                let refreshDate = Calendar.current.date(byAdding: .minute, value: 15, to: Date()) ?? Date()
                let timeline = Timeline(entries: [entry], policy: .after(refreshDate))
                
                completion(timeline)
            } catch {
                // Fallback to placeholder with shorter refresh
                let entry = placeholder(in: context)
                let timeline = Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(60)))
                completion(timeline)
            }
        }
    }
}

// MARK: - Configurable Timeline Entry

struct ConfigurableTimelineEntry: TimelineEntry {
    let date: Date
    let items: [ItemSnapshot]
    let configuration: TimelineConfigurationIntent
    
    var showTime: Bool {
        return configuration.showTime ?? true
    }
}

// MARK: - Configurable Widget View

struct ConfigurableTimelineWidgetView: View {
    var entry: ConfigurableTimelineProvider.Entry
    @Environment(\.widgetFamily) var family
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                Text("Recent Items")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                if entry.showTime {
                    Text(Date(), style: .time)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            
            // Item list
            if entry.items.isEmpty {
                HStack {
                    Spacer()
                    Text("No items")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .padding(.vertical, 20)
            } else {
                let itemsToShow = family == .systemSmall ? 1 : (family == .systemMedium ? 3 : 5)
                
                ForEach(entry.items.prefix(itemsToShow)) { item in
                    Link(destination: URL(string: "prsnl://item/\(item.id)")!) {
                        HStack {
                            Image(systemName: item.iconName)
                                .font(.system(size: 14))
                                .foregroundColor(.blue)
                                .frame(width: 24, height: 24)
                            
                            VStack(alignment: .leading) {
                                Text(item.title)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                    .foregroundColor(.primary)
                                    .lineLimit(1)
                                
                                if family == .systemLarge {
                                    Text(item.content)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)
                                }
                            }
                            
                            Spacer()
                            
                            if entry.showTime {
                                Text(item.timeAgo)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Extended Widget Data Provider

extension WidgetDataProvider {
    // Fetch items with configuration options
    func fetchConfigurableItems(itemType: String?, sortOrder: Bool?, limit: Int = 5) async throws -> [ItemSnapshot] {
        // Create fetch request
        let request = NSFetchRequest<CDItem>(entityName: "CDItem")
        
        // Configure sort descriptors
        let isAscending = sortOrder ?? false
        request.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: isAscending)]
        
        // Apply item type filter
        if let itemType = itemType, itemType != "all" {
            request.predicate = NSPredicate(format: "type == %@", itemType)
        }
        
        request.fetchLimit = limit
        
        // Execute fetch on background context
        return try await coreDataManager.backgroundContext.perform {
            let results = try request.execute()
            
            // Convert to snapshot items
            return results.map { cdItem in
                ItemSnapshot(
                    id: cdItem.id ?? UUID().uuidString,
                    title: cdItem.title ?? "Untitled",
                    content: cdItem.content ?? "",
                    createdAt: cdItem.createdAt ?? Date(),
                    type: cdItem.type ?? "note"
                )
            }
        }
    }
}
```

### 5.2 App Integration

```swift
// IMPLEMENT: App delegate with widget support
import UIKit
import WidgetKit
import CoreData

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        // Initialize Core Data stack with shared container
        _ = CoreDataManager.shared
        
        // Register for remote notifications
        registerForRemoteNotifications()
        
        return true
    }
    
    // Handle URL scheme for deep links
    func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
        // Handle deep link
        DeepLinkManager.shared.handleDeepLink(url)
        return true
    }
    
    // Handle widget data updates
    func applicationDidBecomeActive(_ application: UIApplication) {
        // Refresh widget timelines
        WidgetCenter.shared.reloadAllTimelines()
    }
    
    // Register for remote notifications
    private func registerForRemoteNotifications() {
        UIApplication.shared.registerForRemoteNotifications()
    }
    
    // Handle successful registration
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        // Convert token to string
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("Push token: \(tokenString)")
        
        // Store token for API registration
        UserDefaults.standard.set(tokenString, forKey: "deviceToken")
        
        // Register with backend
        Task {
            try? await APIClient.shared.registerPushToken(token: tokenString)
        }
    }
    
    // Handle registration failure
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("Failed to register for remote notifications: \(error)")
    }
}

// IMPLEMENT: SwiftUI app with widget support
import SwiftUI
import WidgetKit

struct PRSNLApp: App {
    // App delegate
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
