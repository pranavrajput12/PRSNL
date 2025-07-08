import SwiftUI

struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    @State private var selectedItem: Item?
    
    var body: some View {
        NavigationStack {
            ZStack {
                if viewModel.items.isEmpty && !viewModel.isLoading {
                    emptyStateView
                } else {
                    timelineList
                }
                
                if viewModel.isLoading && viewModel.items.isEmpty {
                    ProgressView("Loading timeline...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color(.systemBackground))
                }
            }
            .navigationTitle("Timeline")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task { await viewModel.refresh() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(viewModel.isLoading)
                }
            }
        }
        .alert("Error", isPresented: Binding(
            get: { viewModel.errorMessage != nil },
            set: { _ in viewModel.errorMessage = nil }
        )) {
            Button("OK") {
                viewModel.errorMessage = nil
            }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .sheet(item: $selectedItem) { item in
            ItemDetailView(item: item)
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No items in timeline")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Your captured knowledge will appear here")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.top)
            }
            
            Button("Load Timeline") {
                Task { await viewModel.refresh() }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
    
    private var timelineList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(viewModel.items) { item in
                    TimelineItemCard(item: item)
                        .onTapGesture {
                            selectedItem = item
                        }
                        .onAppear {
                            if item.id == viewModel.items.last?.id {
                                Task { await viewModel.loadMore() }
                            }
                        }
                }
                
                if viewModel.isLoading && !viewModel.items.isEmpty {
                    ProgressView()
                        .padding()
                }
            }
            .padding()
        }
        .refreshable {
            await viewModel.refresh()
        }
    }
}

struct TimelineItemCard: View {
    let item: Item
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label(item.itemType.displayName, systemImage: item.itemType.icon)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(item.createdAt.relative)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text(item.title)
                .font(.headline)
                .lineLimit(2)
            
            if let summary = item.summary {
                Text(summary)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            } else {
                Text(item.content)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }
            
            if !item.tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(item.tags, id: \.self) { tag in
                            Text("#\(tag)")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.blue.opacity(0.1))
                                .foregroundColor(.blue)
                                .cornerRadius(8)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
}

// MARK: - Extensions
extension Date {
    var relative: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: self, relativeTo: Date())
    }
}

extension ItemType {
    var displayName: String {
        switch self {
        case .article: return "Article"
        case .note: return "Note"
        case .video: return "Video"
        case .image: return "Image"
        case .audio: return "Audio"
        case .document: return "Document"
        case .link: return "Link"
        case .other: return "Other"
        }
    }
    
    var icon: String {
        switch self {
        case .article: return "doc.text"
        case .note: return "note.text"
        case .video: return "play.rectangle"
        case .image: return "photo"
        case .audio: return "waveform"
        case .document: return "doc"
        case .link: return "link"
        case .other: return "questionmark.circle"
        }
    }
}

#Preview {
    TimelineView()
}