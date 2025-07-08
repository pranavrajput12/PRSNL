import WidgetKit
import SwiftUI
import CoreData

struct TimelineWidget: Widget {
    private let kind: String = "TimelineWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: TimelineWidgetProvider()) { entry in
            TimelineWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Recent Items")
        .description("View your most recent items in a timeline")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// Renamed from TimelineProvider to TimelineWidgetProvider to avoid confusion with the protocol
struct TimelineWidgetProvider: TimelineProvider {
    private let dataProvider = WidgetDataProvider.shared
    
    func placeholder(in context: TimelineProviderContext) -> PRSNLTimelineEntry {
        PRSNLTimelineEntry(date: Date(), items: sampleItems)
    }
    
    func getSnapshot(in context: TimelineProviderContext, completion: @escaping (PRSNLTimelineEntry) -> Void) {
        dataProvider.fetchRecentItems(limit: 10) { items in
            let entry = PRSNLTimelineEntry(
                date: Date(),
                items: items.isEmpty && !context.isPreview ? sampleItems : items
            )
            completion(entry)
        }
    }
    
    func getTimeline(in context: TimelineProviderContext, completion: @escaping (Timeline<PRSNLTimelineEntry>) -> Void) {
        dataProvider.fetchRecentItems(limit: 10) { items in
            let displayItems = items.isEmpty && !context.isPreview ? sampleItems : items
            
            // Create current entry
            let entry = PRSNLTimelineEntry(date: Date(), items: displayItems)
            
            // Determine next refresh based on battery state
            let refreshDate = dataProvider.nextRefreshDate()
            
            let timeline = Timeline(entries: [entry], policy: .after(refreshDate))
            completion(timeline)
        }
    }
    
    // Sample data for previews and placeholders
    private var sampleItems: [ItemSnapshot] {
        [
            ItemSnapshot(id: "1", title: "Meeting with team", content: "Discuss project progress", createdAt: Date().addingTimeInterval(-1800), type: "event"),
            ItemSnapshot(id: "2", title: "Buy groceries", content: "Milk, eggs, bread", createdAt: Date().addingTimeInterval(-7200), type: "task"),
            ItemSnapshot(id: "3", title: "Interesting article", content: "About Swift concurrency", createdAt: Date().addingTimeInterval(-10800), type: "link"),
            ItemSnapshot(id: "4", title: "Call Sarah", content: "About weekend plans", createdAt: Date().addingTimeInterval(-86400), type: "task"),
            ItemSnapshot(id: "5", title: "Project notes", content: "Implementation details for new feature", createdAt: Date().addingTimeInterval(-172800), type: "note")
        ]
    }
}

struct TimelineWidgetEntryView: View {
    var entry: PRSNLTimelineEntry
    @Environment(\.widgetFamily) private var family
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Recent Items")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
                Text(entry.date, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .padding(.bottom, 4)
            
            if entry.items.isEmpty {
                Spacer()
                Text("No recent items")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                Spacer()
            } else {
                itemsList
            }
        }
        .padding()
        .widgetURL(URL(string: "prsnl://timeline") ?? URL(string: "prsnl://")!)
    }
    
    @ViewBuilder
    private var itemsList: some View {
        switch family {
        case .systemSmall:
            smallLayout
        case .systemMedium:
            mediumLayout
        case .systemLarge:
            largeLayout
        default:
            mediumLayout
        }
    }
    
    private var smallLayout: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(entry.items.prefix(2)) { item in
                itemRow(item, showContent: false, showDate: false)
            }
        }
    }
    
    private var mediumLayout: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(entry.items.prefix(3)) { item in
                itemRow(item, showContent: true, showDate: true)
            }
        }
    }
    
    private var largeLayout: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(entry.items.prefix(5)) { item in
                itemRow(item, showContent: true, showDate: true)
            }
        }
    }
    
    private func itemRow(_ item: ItemSnapshot, showContent: Bool, showDate: Bool) -> some View {
        let itemURL = URL(string: "prsnl://item/\(item.id)") ?? URL(string: "prsnl://timeline")!
        return Link(destination: itemURL) {
            HStack(alignment: .center, spacing: 6) {
                Image(systemName: item.iconName)
                    .font(.system(size: 14))
                    .frame(width: 24, height: 24)
                    .foregroundColor(.accentColor)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(item.title)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.primary)
                        .lineLimit(1)
                    
                    if showContent {
                        Text(item.content)
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                    
                    if showDate {
                        Text(item.timeAgo)
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }
}

struct TimelineWidget_Previews: PreviewProvider {
    static var previews: some View {
        TimelineWidgetEntryView(
            entry: PRSNLTimelineEntry(
                date: Date(),
                items: [
                    ItemSnapshot(id: "1", title: "Meeting with team", content: "Discuss project progress", createdAt: Date().addingTimeInterval(-1800), type: "event"),
                    ItemSnapshot(id: "2", title: "Buy groceries", content: "Milk, eggs, bread", createdAt: Date().addingTimeInterval(-7200), type: "task"),
                    ItemSnapshot(id: "3", title: "Interesting article", content: "About Swift concurrency", createdAt: Date().addingTimeInterval(-10800), type: "link"),
                    ItemSnapshot(id: "4", title: "Call Sarah", content: "About weekend plans", createdAt: Date().addingTimeInterval(-86400), type: "task"),
                    ItemSnapshot(id: "5", title: "Project notes", content: "Implementation details for new feature", createdAt: Date().addingTimeInterval(-172800), type: "note")
                ]
            )
        )
        .previewContext(WidgetPreviewContext(family: .systemMedium))
    }
}