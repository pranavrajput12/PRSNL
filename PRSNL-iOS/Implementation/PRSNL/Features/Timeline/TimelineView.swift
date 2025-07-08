import SwiftUI

// Import the standalone ItemDetailView
import Foundation

struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    @State private var showingTagFilter = false
    
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background
                Color.prsnlBackground
                    .ignoresSafeArea()
                
                // Content
                if viewModel.items.isEmpty && !viewModel.isLoading {
                    // Empty state
                    emptyStateView
                } else {
                    // Timeline list
                    timelineListView
                    
                    // Offline banner
                    if viewModel.isOfflineMode {
                        offlineBanner
                    }
                    
                    // Sync status banner
                    if case .syncing = viewModel.syncStatus {
                        syncingBanner
                    }
                    
                    // Real-time updates disabled in minimal version
                    // TODO: Re-enable when AppState is restored
                }
                
                // Error banner
                if let error = viewModel.error {
                    VStack {
                        Text(error)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.red)
                            .cornerRadius(8)
                            .padding()
                        
                        Spacer()
                    }
                }
            }
            .navigationTitle("Timeline")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingTagFilter.toggle()
                    }) {
                        Image(systemName: "tag")
                            .foregroundColor(viewModel.selectedTags.isEmpty ? .white : .red)
                    }
                }
            }
            .sheet(isPresented: $showingTagFilter) {
                tagFilterView
            }
            .task {
                await viewModel.loadInitialTimeline()
            }
            // Real-time updates disabled in minimal version
            // TODO: Re-enable when AppState is restored
        }
    }
    
    // MARK: - Subviews
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 64))
                .foregroundColor(.prsnlTextSecondary)
            
            Text("No items found")
                .font(.title2)
                .foregroundColor(.prsnlText)
            
            if !viewModel.selectedTags.isEmpty {
                Text("Try removing some tag filters")
                    .foregroundColor(.prsnlTextSecondary)
                
                Button("Clear Filters") {
                    viewModel.selectedTags = []
                    Task {
                        await viewModel.loadInitialTimeline()
                    }
                }
                .padding()
                .background(Color.red)
                .foregroundColor(.white)
                .cornerRadius(8)
            }
        }
    }
    
    private var timelineListView: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(viewModel.items) { item in
                    NavigationLink(destination: ItemDetailView(itemId: item.id)) {
                        TimelineItemView(item: item, viewModel: viewModel)
                            .onAppear {
                                // Load more when reaching end of list
                                if item.id == viewModel.items.last?.id {
                                    Task {
                                        await viewModel.loadMoreItems()
                                    }
                                }
                            }
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                
                if viewModel.isLoading {
                    ProgressView()
                        .padding()
                        .frame(maxWidth: .infinity)
                }
            }
            .padding()
        }
        .refreshable {
            await viewModel.refresh()
        }
    }
    
    private var tagFilterView: some View {
        NavigationView {
            ZStack {
                Color.prsnlBackground.ignoresSafeArea()
                
                VStack {
                    Text("Filter by tags")
                        .font(.headline)
                        .foregroundColor(.prsnlText)
                        .padding(.top)
                    
                    // Selected tags
                    if !viewModel.selectedTags.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                ForEach(viewModel.selectedTags, id: \.self) { tag in
                                    HStack {
                                        Text(tag)
                                            .foregroundColor(.white)
                                        
                                        Button(action: {
                                            viewModel.toggleTag(tag)
                                        }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundColor(.white.opacity(0.7))
                                        }
                                    }
                                    .padding(.vertical, 4)
                                    .padding(.horizontal, 8)
                                    .background(Color.red)
                                    .cornerRadius(16)
                                }
                            }
                            .padding(.horizontal)
                        }
                        .padding(.vertical, 8)
                    }
                    
                    // Available tags
                    List {
                        ForEach(viewModel.availableTags, id: \.self) { tag in
                            Button(action: {
                                viewModel.toggleTag(tag)
                            }) {
                                HStack {
                                    Text(tag)
                                        .foregroundColor(.prsnlText)
                                    
                                    Spacer()
                                    
                                    if viewModel.selectedTags.contains(tag) {
                                        Image(systemName: "checkmark")
                                            .foregroundColor(.red)
                                    }
                                }
                            }
                            .listRowBackground(Color.prsnlSurface)
                        }
                    }
                    .listStyle(PlainListStyle())
                }
            }
            .navigationTitle("Tag Filter")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        showingTagFilter = false
                    }
                }
            }
        }
    }
    
    // Real-time updates banner disabled in minimal version
    // TODO: Re-enable when AppState is restored
}

struct TimelineItemView: View {
    let item: Item
    let viewModel: TimelineViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Title
            Text(item.title)
                .font(.headline)
                .foregroundColor(.prsnlText)
                .lineLimit(2)
            
            // Content preview
            Text(item.content)
                .font(.body)
                .foregroundColor(.prsnlTextSecondary)
                .lineLimit(3)
            
            // Item type badge
            HStack {
                Text(item.itemType.rawValue.capitalized)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(itemTypeColor(for: item.itemType))
                    .foregroundColor(.white)
                    .cornerRadius(4)
                
                if item.status == .archived {
                    Text("Archived")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(4)
                }
                
                Spacer()
                
                // Access count if more than 1
                if item.accessCount > 1 {
                    Text("\(item.accessCount) views")
                        .font(.caption)
                        .foregroundColor(.prsnlTextSecondary)
                }
            }
            
            HStack {
                // Tags
                if !item.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(item.tags.prefix(3), id: \.self) { tag in
                                Text(tag)
                                    .font(.caption)
                                    .foregroundColor(.white)
                                    .padding(.vertical, 2)
                                    .padding(.horizontal, 6)
                                    .background(Color.red)
                                    .cornerRadius(4)
                            }
                            
                            if item.tags.count > 3 {
                                Text("+\(item.tags.count - 3)")
                                    .font(.caption)
                                    .foregroundColor(.prsnlTextSecondary)
                            }
                        }
                    }
                    .frame(height: 24)
                }
                
                Spacer()
                
                // Timestamp
                Text(item.formattedCreationDate)
                    .font(.caption)
                    .foregroundColor(.prsnlTextSecondary)
                
                // Attachment indicator
                if item.hasAttachments {
                    Image(systemName: attachmentIcon(for: item))
                        .foregroundColor(.prsnlTextSecondary)
                }
            }
            
            // Summary if available
            if let summary = item.summary, !summary.isEmpty {
                Text("Summary: \(summary)")
                    .font(.caption)
                    .foregroundColor(.prsnlTextSecondary)
                    .lineLimit(2)
                    .padding(.top, 4)
            }
        }
        .padding()
        .background(Color.prsnlSurface)
        .cornerRadius(12)
    }
    
    // Helper to determine item type color
    private func itemTypeColor(for type: ItemType) -> Color {
        switch type {
        case .note:
            return Color.blue
        case .article:
            return Color.green
        case .video:
            return Color.red
        case .audio:
            return Color.purple
        case .image:
            return Color.orange
        case .document:
            return Color.cyan
        case .other:
            return Color.gray
        }
    }
    
    // Helper to determine attachment icon
    private func attachmentIcon(for item: Item) -> String {
        guard let attachments = item.attachments, !attachments.isEmpty else {
            return "paperclip"
        }
        
        // Get first attachment type to determine icon
        let firstType = attachments[0].fileType.lowercased()
        
        if firstType.contains("image") {
            return "photo"
        } else if firstType.contains("video") {
            return "video"
        } else if firstType.contains("audio") {
            return "music.note"
        } else if firstType.contains("pdf") {
            return "doc.text"
        } else {
            return "paperclip"
        }
    }
}

// ItemDetailView moved to its own file

// MARK: - Status Banners

extension TimelineView {
    /// Banner shown when the app is in offline mode
    var offlineBanner: some View {
        VStack {
            HStack {
                Image(systemName: "wifi.slash")
                    .foregroundColor(.white)
                
                Text("Offline Mode")
                    .font(.caption.bold())
                    .foregroundColor(.white)
                
                Spacer()
                
                Button(action: {
                    Task {
                        await viewModel.refresh()
                    }
                }) {
                    Text("Try again")
                        .font(.caption)
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.white.opacity(0.3))
                        .cornerRadius(4)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(Color.orange)
        }
        .frame(maxWidth: .infinity)
        .transition(.move(edge: .top))
    }
    
    /// Banner shown when syncing is in progress
    var syncingBanner: some View {
        VStack {
            HStack {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    .scaleEffect(0.7)
                
                Text("Syncing...")
                    .font(.caption.bold())
                    .foregroundColor(.white)
                
                Spacer()
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(Color.blue)
        }
        .frame(maxWidth: .infinity)
        .transition(.move(edge: .top))
    }
}

struct TimelineView_Previews: PreviewProvider {
    static var previews: some View {
        TimelineView()
    }
}