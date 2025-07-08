import SwiftUI

struct SearchView: View {
    @StateObject private var viewModel = SearchViewModel()
    @State private var selectedItem: Item? = nil
    @State private var showingItemDetail = false
    
    var body: some View {
        // Using NavigationStack for iOS 17+
        NavigationStack {
            ZStack {
                VStack(spacing: 0) {
                    // Search Bar
                    searchBar
                    
                    // Results Count
                    if viewModel.hasResults() {
                        resultsCountView
                    }
                    
                    // Content based on state
                    contentView
                    
                    // No need for hidden NavigationLink with NavigationStack
                    // Navigation will use the navigationDestination modifier
                }
                
                // Offline banner
                if viewModel.isOfflineMode {
                    VStack {
                        offlineBanner
                        Spacer()
                    }
                }
                
                // Sync status banner
                if case .syncing = viewModel.syncStatus {
                    VStack {
                        syncingBanner
                        Spacer()
                    }
                }
            }
            .navigationTitle("Search")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(item: $selectedItem) { item in
                ItemDetailView(item: item)
            }
        }
        // No need for navigationViewStyle with NavigationStack
    }
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search articles, notes, documents...", text: $viewModel.query)
                .autocorrectionDisabled()
                .textInputAutocapitalization(.never)
            
            if !viewModel.query.isEmpty {
                Button(action: {
                    viewModel.query = ""
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color(.systemGray6))
        .cornerRadius(10)
        .padding(.horizontal)
        .padding(.top, 8)
        .padding(.bottom, 8)
    }
    
    private var resultsCountView: some View {
        HStack {
            Text(viewModel.resultsCountText)
                .font(.caption)
                .foregroundColor(.secondary)
            Spacer()
        }
        .padding(.horizontal)
        .padding(.bottom, 8)
    }
    
    private var contentView: some View {
        Group {
            switch viewModel.state {
            case .idle:
                emptyStateView
            case .loading:
                loadingView
            case .results(let response):
                if response.items.isEmpty {
                    noResultsView
                } else {
                    resultsListView(items: response.items)
                }
            case .error(let error):
                errorView(error: error)
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "magnifyingglass")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            Text("Search your knowledge base")
                .font(.title2)
                .foregroundColor(.secondary)
            Text("Enter keywords above to find items in your personal knowledge base")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            Spacer()
        }
    }
    
    private var loadingView: some View {
        VStack {
            Spacer()
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle())
                .scaleEffect(1.5)
            Text("Searching...")
                .font(.callout)
                .foregroundColor(.secondary)
                .padding(.top, 16)
            Spacer()
        }
    }
    
    private var noResultsView: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "questionmark.circle")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            Text("No results found")
                .font(.title2)
                .foregroundColor(.secondary)
            Text("Try different keywords or check your spelling")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            Spacer()
        }
    }
    
    private func errorView(error: Error) -> some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 64))
                .foregroundColor(.orange)
            Text("Search Error")
                .font(.title2)
            Text(error.localizedDescription)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            Button("Try Again") {
                if !viewModel.query.isEmpty {
                    viewModel.resetSearch()
                    viewModel.performSearch(query: viewModel.query)
                }
            }
            .buttonStyle(.borderedProminent)
            .tint(Color("AccentColor"))
            .padding(.top, 10)
            Spacer()
        }
    }
    
    private func resultsListView(items: [Item]) -> some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(items) { item in
                    SearchResultRow(item: item)
                        .onTapGesture {
                            selectedItem = item
                            showingItemDetail = true
                        }
                        .onAppear {
                            viewModel.loadMoreResultsIfNeeded(currentItem: item)
                        }
                }
                
                if viewModel.isSearching && !items.isEmpty {
                    ProgressView()
                        .padding()
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
        .refreshable {
            await viewModel.refresh()
        }
    }
}

struct SearchResultRow: View {
    let item: Item
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Title and type icon
            HStack(alignment: .top) {
                Image(systemName: iconForItemType(item.itemType))
                    .foregroundColor(colorForItemType(item.itemType))
                    .frame(width: 24)
                
                Text(item.title)
                    .font(.headline)
                    .lineLimit(2)
            }
            
            // Summary if available
            if let summary = item.summary, !summary.isEmpty {
                Text(summary)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
                    .padding(.leading, 30)
            }
            
            // Tags
            if !item.tags.isEmpty {
                HStack {
                    Image(systemName: "tag")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(width: 24)
                    
                    Text(item.formattedTags)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            
            // Date
            HStack {
                Image(systemName: "calendar")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 24)
                
                Text(item.formattedCreationDate)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
    
    private func iconForItemType(_ type: ItemType) -> String {
        switch type {
        case .note:
            return "note.text"
        case .article:
            return "doc.text"
        case .video:
            return "video"
        case .audio:
            return "waveform"
        case .image:
            return "photo"
        case .document:
            return "doc"
        case .other:
            return "questionmark.square"
        }
    }
    
    private func colorForItemType(_ type: ItemType) -> Color {
        switch type {
        case .note:
            return .blue
        case .article:
            return .purple
        case .video:
            return .red
        case .audio:
            return .green
        case .image:
            return .orange
        case .document:
            return .teal
        case .other:
            return .gray
        }
    }
}

// MARK: - Status Banners

extension SearchView {
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

struct SearchView_Previews: PreviewProvider {
    static var previews: some View {
        SearchView()
    }
}