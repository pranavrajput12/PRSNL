import WidgetKit
import SwiftUI

struct StatsWidget: Widget {
    private let kind: String = "StatsWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: StatsProvider()) { entry in
            StatsWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Stats & Insights")
        .description("View your PRSNL usage statistics")
        .supportedFamilies([.systemMedium, .systemLarge])
    }
}

struct StatsProvider: TimelineProvider {
    private let dataProvider = WidgetDataProvider.shared
    
    func placeholder(in context: TimelineProviderContext) -> StatsEntry {
        // Sample stats for placeholder
        StatsEntry(
            date: Date(),
            totalItems: 42,
            itemsToday: 3,
            itemsThisWeek: 12,
            itemsByType: ["note": 15, "task": 12, "event": 8, "link": 7],
            completedTasks: 8,
            pendingTasks: 4
        )
    }
    
    func getSnapshot(in context: TimelineProviderContext, completion: @escaping (StatsEntry) -> Void) {
        dataProvider.fetchStats { stats in
            let entry = context.isPreview ? placeholder(in: context) : stats
            completion(entry)
        }
    }
    
    func getTimeline(in context: TimelineProviderContext, completion: @escaping (Timeline<StatsEntry>) -> Void) {
        dataProvider.fetchStats { stats in
            let entry = context.isPreview ? placeholder(in: context) : stats
            
            // Refresh twice daily to keep stats up to date without draining battery
            let calendar = Calendar.current
            let now = Date()
            
            // Next refresh at noon or midnight, whichever comes first
            var nextRefreshComponents = DateComponents()
            let currentHour = calendar.component(.hour, from: now)
            
            if currentHour < 12 {
                nextRefreshComponents.hour = 12
                nextRefreshComponents.minute = 0
            } else {
                nextRefreshComponents.day = 1
                nextRefreshComponents.hour = 0
                nextRefreshComponents.minute = 0
            }
            
            let nextRefresh = calendar.nextDate(
                after: now,
                matching: nextRefreshComponents,
                matchingPolicy: .nextTime
            ) ?? calendar.date(byAdding: .hour, value: 12, to: now)!
            
            let timeline = Timeline(entries: [entry], policy: .after(nextRefresh))
            completion(timeline)
        }
    }
}

struct StatsWidgetEntryView: View {
    var entry: StatsEntry
    @Environment(\.widgetFamily) private var family
    @Environment(\.colorScheme) private var colorScheme
    
    var body: some View {
        switch family {
        case .systemMedium:
            mediumLayout
        case .systemLarge:
            largeLayout
        default:
            mediumLayout
        }
    }
    
    private var mediumLayout: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("PRSNL Stats")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
                Text(entry.date, style: .date)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            HStack(spacing: 20) {
                // Left column - item counts
                VStack(alignment: .leading, spacing: 8) {
                    statRow(label: "Total Items", value: "\(entry.totalItems)")
                    statRow(label: "Today", value: "\(entry.itemsToday)")
                    statRow(label: "This Week", value: "\(entry.itemsThisWeek)")
                }
                
                Divider()
                
                // Right column - completion rate
                VStack(alignment: .leading, spacing: 8) {
                    Text("Task Completion")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                    
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .frame(height: 8)
                            .foregroundColor(Color(UIColor.systemGray5))
                        
                        RoundedRectangle(cornerRadius: 4)
                            .frame(width: 120 * entry.completionRate, height: 8)
                            .foregroundColor(.green)
                    }
                    
                    Text("\(Int(entry.completionRate * 100))% Complete")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.primary)
                }
                .frame(width: 120)
            }
        }
        .padding()
        .widgetURL(URL(string: "prsnl://stats"))
    }
    
    private var largeLayout: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("PRSNL Stats & Insights")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
                Text(entry.date, style: .date)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            HStack(spacing: 20) {
                // Left column - item counts
                VStack(alignment: .leading, spacing: 10) {
                    statRow(label: "Total Items", value: "\(entry.totalItems)")
                    statRow(label: "Today", value: "\(entry.itemsToday)")
                    statRow(label: "This Week", value: "\(entry.itemsThisWeek)")
                    
                    if let primaryType = entry.primaryItemType {
                        statRow(
                            label: "Most Common",
                            value: "\(primaryType.type.capitalized) (\(primaryType.count))"
                        )
                    }
                }
                
                Divider()
                
                // Right column - charts
                VStack(alignment: .leading, spacing: 10) {
                    // Task completion rate
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Task Completion")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                        
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 4)
                                .frame(height: 8)
                                .foregroundColor(Color(UIColor.systemGray5))
                            
                            RoundedRectangle(cornerRadius: 4)
                                .frame(width: 140 * entry.completionRate, height: 8)
                                .foregroundColor(.green)
                        }
                        
                        Text("\(Int(entry.completionRate * 100))% Complete")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.primary)
                    }
                    
                    // Type distribution
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Item Types")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                        
                        HStack(spacing: 6) {
                            ForEach(sortedItemTypes, id: \.key) { type, count in
                                typeIndicator(type: type, count: count)
                            }
                        }
                    }
                }
                .frame(width: 140)
            }
            
            Spacer()
        }
        .padding()
        .widgetURL(URL(string: "prsnl://stats"))
    }
    
    private func statRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 13))
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.primary)
        }
    }
    
    private func typeIndicator(type: String, count: Int) -> some View {
        VStack(alignment: .center, spacing: 2) {
            ZStack {
                Circle()
                    .frame(width: 24, height: 24)
                    .foregroundColor(colorForType(type))
                
                Image(systemName: iconForType(type))
                    .font(.system(size: 12))
                    .foregroundColor(.white)
            }
            
            Text("\(count)")
                .font(.system(size: 10))
                .foregroundColor(.primary)
        }
    }
    
    private func colorForType(_ type: String) -> Color {
        switch type.lowercased() {
        case "task":
            return .blue
        case "note":
            return .purple
        case "event":
            return .red
        case "link":
            return .teal
        default:
            return .gray
        }
    }
    
    private func iconForType(_ type: String) -> String {
        switch type.lowercased() {
        case "task":
            return "checkmark"
        case "note":
            return "doc.text"
        case "event":
            return "calendar"
        case "link":
            return "link"
        default:
            return "doc"
        }
    }
    
    private var sortedItemTypes: [(key: String, value: Int)] {
        entry.itemsByType.sorted { $0.value > $1.value }
    }
}

struct StatsWidget_Previews: PreviewProvider {
    static var previews: some View {
        StatsWidgetEntryView(
            entry: StatsEntry(
                date: Date(),
                totalItems: 42,
                itemsToday: 3,
                itemsThisWeek: 12,
                itemsByType: ["note": 15, "task": 12, "event": 8, "link": 7],
                completedTasks: 8,
                pendingTasks: 4
            )
        )
        .previewContext(WidgetPreviewContext(family: .systemMedium))
        .previewDisplayName("Medium")
        
        StatsWidgetEntryView(
            entry: StatsEntry(
                date: Date(),
                totalItems: 42,
                itemsToday: 3,
                itemsThisWeek: 12,
                itemsByType: ["note": 15, "task": 12, "event": 8, "link": 7],
                completedTasks: 8,
                pendingTasks: 4
            )
        )
        .previewContext(WidgetPreviewContext(family: .systemLarge))
        .previewDisplayName("Large")
    }
}