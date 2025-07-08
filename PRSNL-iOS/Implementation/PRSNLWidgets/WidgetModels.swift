import WidgetKit
import SwiftUI
import CoreData

// MARK: - Item Snapshot Model

/// Lightweight version of Item model for widget display
struct ItemSnapshot: Identifiable, Codable, Equatable, Hashable {
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

// MARK: - Timeline Widget Models

/// Entry for Timeline Widget
struct PRSNLTimelineEntry: WidgetKit.TimelineEntry, Equatable {
    let date: Date
    let items: [ItemSnapshot]
    
    // Implementing the Equatable protocol requirements
    static func == (lhs: PRSNLTimelineEntry, rhs: PRSNLTimelineEntry) -> Bool {
        return lhs.date == rhs.date && lhs.items == rhs.items
    }
}

/// Entry for Configurable Timeline Widget
struct ConfigurableTimelineEntry: WidgetKit.TimelineEntry, Equatable {
    let date: Date
    let items: [ItemSnapshot]
    let configuration: TimelineConfigurationIntent
    
    var showTime: Bool {
        return configuration.showTime ?? true
    }
    
    // Implementing the Equatable protocol requirements
    static func == (lhs: ConfigurableTimelineEntry, rhs: ConfigurableTimelineEntry) -> Bool {
        return lhs.date == rhs.date && lhs.items == rhs.items && lhs.configuration == rhs.configuration
    }
}

// MARK: - Quick Actions Widget Models

/// Entry for Quick Actions Widget
struct QuickActionsEntry: WidgetKit.TimelineEntry, Equatable {
    let date: Date
    
    // Implementing the Equatable protocol requirements
    static func == (lhs: QuickActionsEntry, rhs: QuickActionsEntry) -> Bool {
        return lhs.date == rhs.date
    }
}

/// Quick Action model
struct QuickAction: Identifiable, Hashable {
    let id: String
    let title: String
    let icon: String
    let deepLink: URL
    let color: Color
    
    // Implementing Hashable
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    // Implementing Equatable
    static func == (lhs: QuickAction, rhs: QuickAction) -> Bool {
        return lhs.id == rhs.id
    }
}

// MARK: - Stats Widget Models

/// Entry for Stats Widget
struct StatsEntry: WidgetKit.TimelineEntry, Equatable {
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
        guard let maxItem = itemsByType.max(by: { $0.value < $1.value }) else {
            return nil
        }
        return (type: maxItem.key, count: maxItem.value)
    }
    
    // Implementing the Equatable protocol requirements
    static func == (lhs: StatsEntry, rhs: StatsEntry) -> Bool {
        return lhs.date == rhs.date &&
               lhs.totalItems == rhs.totalItems &&
               lhs.itemsToday == rhs.itemsToday &&
               lhs.itemsThisWeek == rhs.itemsThisWeek &&
               lhs.itemsByType == rhs.itemsByType &&
               lhs.completedTasks == rhs.completedTasks &&
               lhs.pendingTasks == rhs.pendingTasks
    }
}

// MARK: - Widget Configuration Intent

/// Intent definition for configurable widgets
struct TimelineConfigurationIntent: Equatable, Hashable {
    // Item type filter
    var itemType: String?
    
    // Sort order - "newest" or "oldest"
    var sortOrder: String?
    
    // Show date/time
    var showTime: Bool?
    
    // Number of items to show
    var itemCount: Int?
    
    // Initialize with default values
    init(itemType: String? = nil, sortOrder: String? = "newest", showTime: Bool? = true, itemCount: Int? = 3) {
        self.itemType = itemType
        self.sortOrder = sortOrder
        self.showTime = showTime
        self.itemCount = itemCount
    }
    
    // Convert sortOrder string to bool for Core Data query
    var isAscending: Bool {
        return sortOrder == "oldest"
    }
    
    // Get actual item limit considering device constraints
    func getItemLimit(for family: WidgetFamily) -> Int {
        let defaultCount = family.maxItemCount
        guard let count = itemCount, count > 0 else {
            return defaultCount
        }
        return min(count, defaultCount)
    }
}

// MARK: - Protocol Definitions

// All TimelineEntry implementations now directly conform to WidgetKit.TimelineEntry and Equatable