import WidgetKit
import SwiftUI

struct QuickActionsWidget: Widget {
    private let kind: String = "QuickActionsWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: QuickActionsProvider()) { entry in
            QuickActionsWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Quick Actions")
        .description("Quick access to common PRSNL actions")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

struct QuickActionsProvider: TimelineProvider {
    func placeholder(in context: TimelineProviderContext) -> QuickActionsEntry {
        QuickActionsEntry(date: Date())
    }
    
    func getSnapshot(in context: TimelineProviderContext, completion: @escaping (QuickActionsEntry) -> Void) {
        let entry = QuickActionsEntry(date: Date())
        completion(entry)
    }
    
    func getTimeline(in context: TimelineProviderContext, completion: @escaping (Timeline<QuickActionsEntry>) -> Void) {
        // This widget doesn't need frequent updates as the actions are static
        let entry = QuickActionsEntry(date: Date())
        
        // Refresh once per day to ensure any UI/theme updates are reflected
        let nextUpdateDate = Calendar.current.date(byAdding: .day, value: 1, to: Date()) ?? Date()
        let timeline = Timeline(entries: [entry], policy: .after(nextUpdateDate))
        completion(timeline)
    }
}

struct QuickActionsWidgetEntryView: View {
    var entry: QuickActionsEntry
    @Environment(\.widgetFamily) private var family
    
    // Standard actions that are always available
    private let standardActions: [QuickAction] = [
        QuickAction(
            id: "new",
            title: "New Item",
            icon: "plus.circle.fill",
            deepLink: URL(string: "prsnl://new")!,
            color: .blue
        ),
        QuickAction(
            id: "search",
            title: "Search",
            icon: "magnifyingglass",
            deepLink: URL(string: "prsnl://search")!,
            color: .orange
        ),
        QuickAction(
            id: "timeline",
            title: "Timeline",
            icon: "list.bullet",
            deepLink: URL(string: "prsnl://timeline")!,
            color: .green
        ),
        QuickAction(
            id: "settings",
            title: "Settings",
            icon: "gear",
            deepLink: URL(string: "prsnl://settings")!,
            color: .gray
        )
    ]
    
    // Additional actions for medium-sized widgets
    private let additionalActions: [QuickAction] = [
        QuickAction(
            id: "new-task",
            title: "New Task",
            icon: "checkmark.circle.fill",
            deepLink: URL(string: "prsnl://new?type=task")!,
            color: .blue
        ),
        QuickAction(
            id: "new-note",
            title: "New Note",
            icon: "note.text",
            deepLink: URL(string: "prsnl://new?type=note")!,
            color: .purple
        ),
        QuickAction(
            id: "new-event",
            title: "New Event",
            icon: "calendar",
            deepLink: URL(string: "prsnl://new?type=event")!,
            color: .red
        ),
        QuickAction(
            id: "new-link",
            title: "Save Link",
            icon: "link",
            deepLink: URL(string: "prsnl://new?type=link")!,
            color: .teal
        )
    ]
    
    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Text("Quick Actions")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
            }
            .padding(.bottom, 6)
            
            switch family {
            case .systemSmall:
                smallLayout
            case .systemMedium:
                mediumLayout
            default:
                smallLayout
            }
        }
        .padding()
    }
    
    var smallLayout: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            ForEach(standardActions) { action in
                actionButton(for: action)
            }
        }
    }
    
    var mediumLayout: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            // Show a mix of standard and specialized actions
            ForEach(Array(standardActions.prefix(2) + additionalActions.prefix(6))) { action in
                actionButton(for: action)
            }
        }
    }
    
    func actionButton(for action: QuickAction) -> some View {
        Link(destination: action.deepLink) {
            VStack(spacing: 4) {
                Image(systemName: action.icon)
                    .font(.system(size: 20))
                    .foregroundColor(action.color)
                
                if family == .systemMedium {
                    Text(action.title)
                        .font(.system(size: 10))
                        .foregroundColor(.primary)
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(UIColor.secondarySystemBackground))
            .cornerRadius(10)
        }
    }
}

struct QuickActionsWidget_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            QuickActionsWidgetEntryView(entry: QuickActionsEntry(date: Date()))
                .previewContext(WidgetPreviewContext(family: .systemSmall))
                .previewDisplayName("Small")
            
            QuickActionsWidgetEntryView(entry: QuickActionsEntry(date: Date()))
                .previewContext(WidgetPreviewContext(family: .systemMedium))
                .previewDisplayName("Medium")
        }
    }
}