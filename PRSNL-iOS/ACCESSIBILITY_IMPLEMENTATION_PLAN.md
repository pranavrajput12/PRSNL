# PRSNL iOS: Accessibility Implementation Plan

This document outlines a comprehensive strategy to ensure the PRSNL iOS app is accessible to all users, including those with disabilities, following Apple's accessibility guidelines and best practices.

## 1. Accessibility Principles

### 1.1 Core Principles

- **Perceivable**: All information must be presentable to users in ways they can perceive
- **Operable**: Interface components must be navigable and usable by all users
- **Understandable**: Information and operation must be understandable to all users
- **Robust**: Content must be robust enough to work with assistive technologies

### 1.2 Apple's Accessibility Features

The implementation will fully support Apple's accessibility features:

- VoiceOver (screen reader)
- Dynamic Type (text size adjustment)
- Reduce Motion
- Increase Contrast
- Reduce Transparency
- Color Filters (color blindness accommodations)
- Bold Text
- Button Shapes
- On/Off Labels
- Voice Control
- Switch Control
- AssistiveTouch

## 2. Technical Implementation

### 2.1 Accessibility Identifiers and Labels

```swift
// IMPLEMENT: Consistent accessibility identifiers for UI testing
extension View {
    func accessibilityIdentifiable(_ identifier: String) -> some View {
        return self.accessibility(identifier: identifier)
    }
    
    func accessibilityLabeled(_ label: String) -> some View {
        return self.accessibility(label: Text(label))
    }
    
    func accessibilityDescribed(_ description: String) -> some View {
        return self.accessibility(hint: Text(description))
    }
    
    func accessibilityTraits(_ traits: AccessibilityTraits) -> some View {
        return self.accessibility(addTraits: traits)
    }
}

// Example usage in ItemDetailView
struct ItemDetailView: View {
    // Properties...
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(item.title)
                    .font(.largeTitle)
                    .bold()
                    .accessibilityIdentifiable("item-title")
                    .accessibilityTraits(.header)
                
                Text(DateFormatter.longFormat.string(from: item.updatedAt))
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .accessibilityIdentifiable("item-date")
                    .accessibilityLabeled("Last updated \(DateFormatter.longFormat.string(from: item.updatedAt))")
                
                Divider()
                
                Text(item.content)
                    .accessibilityIdentifiable("item-content")
                
                if let attachments = item.attachments, !attachments.isEmpty {
                    AttachmentsView(attachments: attachments)
                        .accessibilityIdentifiable("attachments-section")
                        .accessibilityLabeled("Attachments")
                        .accessibilityDescribed("Section containing \(attachments.count) attachments")
                }
                
                // More content...
            }
            .padding()
        }
        .navigationTitle("Item Details")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: editItem) {
                    Text("Edit")
                }
                .accessibilityIdentifiable("edit-button")
            }
        }
    }
}
```

### 2.2 VoiceOver Support

```swift
// IMPLEMENT: Enhanced VoiceOver support for custom UI components
struct TimelineItemRow: View {
    let item: Item
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(item.title)
                .font(.headline)
            
            Text(item.content.prefix(100))
                .font(.subheadline)
                .lineLimit(2)
            
            Text(DateFormatter.shortFormat.string(from: item.updatedAt))
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle()) // Makes entire cell tappable
        .accessibilityElement(children: .combine) // Combines children for VoiceOver
        .accessibilityLabel("\(item.title), last updated \(DateFormatter.shortFormat.string(from: item.updatedAt))")
        .accessibilityHint("Double tap to view item details")
        .accessibilityTraits(.button)
    }
}

// IMPLEMENT: Custom accessibility actions for complex interactions
struct AttachmentView: View {
    let attachment: Attachment
    @State private var isPresenting = false
    
    var body: some View {
        Button(action: {
            isPresenting = true
        }) {
            HStack {
                Image(systemName: iconName(for: attachment.type))
                Text(attachment.filename ?? "Attachment")
            }
            .padding()
            .background(Color(.secondarySystemBackground))
            .cornerRadius(8)
        }
        .accessibilityLabel("\(attachment.type) attachment: \(attachment.filename ?? "Untitled")")
        .accessibilityHint("Double tap to open")
        .accessibilityAction(named: "Share") {
            // Share functionality
        }
        .accessibilityAction(named: "Download") {
            // Download functionality
        }
        .sheet(isPresented: $isPresenting) {
            AttachmentDetailView(attachment: attachment)
        }
    }
    
    private func iconName(for type: String) -> String {
        switch type.lowercased() {
        case "image": return "photo"
        case "pdf", "document": return "doc"
        case "video": return "film"
        case "audio": return "waveform"
        default: return "paperclip"
        }
    }
}
```

### 2.3 Dynamic Type Support

```swift
// IMPLEMENT: Scaling font sizes with Dynamic Type
struct ScalableFont: ViewModifier {
    @Environment(\.sizeCategory) var sizeCategory
    var size: CGFloat
    var weight: Font.Weight
    var design: Font.Design = .default
    
    func body(content: Content) -> some View {
        content
            .font(.system(size: size, weight: weight, design: design))
            .lineLimit(calculateLineLimit())
            .minimumScaleFactor(calculateScaleFactor())
    }
    
    private func calculateLineLimit() -> Int? {
        // Increase line limits for larger text sizes to prevent truncation
        switch sizeCategory {
        case .accessibilityExtraExtraExtraLarge:
            return nil // No limit for largest sizes
        case .accessibilityExtraExtraLarge:
            return 10
        case .accessibilityExtraLarge:
            return 8
        case .accessibilityLarge:
            return 6
        case .accessibilityMedium:
            return 5
        default:
            return 3
        }
    }
    
    private func calculateScaleFactor() -> CGFloat {
        // Allow text to scale down slightly in constrained spaces
        switch sizeCategory {
        case .accessibilityLarge, .accessibilityExtraLarge, .accessibilityExtraExtraLarge, .accessibilityExtraExtraExtraLarge:
            return 0.7
        default:
            return 0.9
        }
    }
}

extension View {
    func scalableFont(size: CGFloat, weight: Font.Weight = .regular, design: Font.Design = .default) -> some View {
        self.modifier(ScalableFont(size: size, weight: weight, design: design))
    }
}

// Example usage in TimelineView
struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    
    var body: some View {
        List {
            ForEach(viewModel.items) { item in
                NavigationLink(destination: ItemDetailView(item: item)) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.title)
                            .scalableFont(size: 17, weight: .semibold)
                        
                        Text(item.content.prefix(100))
                            .scalableFont(size: 14)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .navigationTitle("Timeline")
    }
}
```

### 2.4 Color and Contrast

```swift
// IMPLEMENT: Accessible color system with contrast awareness
struct AccessibleColors {
    // Primary colors with sufficient contrast against both light and dark backgrounds
    static let primary = Color("AccentColor") // Defined in asset catalog with light/dark variants
    
    // Secondary interactive colors
    static let secondary = Color("SecondaryColor")
    
    // Alert/Status colors with light/dark variants for proper contrast
    static let success = Color("SuccessColor")
    static let warning = Color("WarningColor")
    static let error = Color("ErrorColor")
    
    // Background colors
    static let background = Color("BackgroundColor")
    static let secondaryBackground = Color("SecondaryBackgroundColor")
    static let tertiaryBackground = Color("TertiaryBackgroundColor")
    
    // Text colors with proper contrast against backgrounds
    static let primaryText = Color("PrimaryTextColor")
    static let secondaryText = Color("SecondaryTextColor")
    static let tertiaryText = Color("TertiaryTextColor")
    
    // Helper to get a color with verified contrast ratio
    static func withVerifiedContrast(foreground: Color, background: Color, minimumRatio: Double = 4.5) -> Color {
        // In a real implementation, this would check the contrast ratio
        // and adjust the foreground color if needed
        return foreground
    }
}

// Example usage in StatusIndicator
struct StatusIndicator: View {
    enum Status {
        case online, offline, syncing, error
    }
    
    let status: Status
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            
            Text(statusText)
                .font(.caption)
                .foregroundColor(AccessibleColors.withVerifiedContrast(
                    foreground: AccessibleColors.secondaryText,
                    background: AccessibleColors.background
                ))
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(statusText)
    }
    
    private var statusColor: Color {
        switch status {
        case .online: return AccessibleColors.success
        case .offline: return AccessibleColors.warning
        case .syncing: return AccessibleColors.primary
        case .error: return AccessibleColors.error
        }
    }
    
    private var statusText: String {
        switch status {
        case .online: return "Online"
        case .offline: return "Offline"
        case .syncing: return "Syncing"
        case .error: return "Error"
        }
    }
}
```

### 2.5 Motion and Animations

```swift
// IMPLEMENT: Motion sensitivity-aware animations
extension View {
    func accessibleAnimation<Value: Equatable>(
        _ animation: Animation? = .default,
        value: Value
    ) -> some View {
        // Check for Reduce Motion setting
        return self.modifier(AccessibleAnimationModifier(animation: animation, value: value))
    }
}

struct AccessibleAnimationModifier<Value: Equatable>: ViewModifier {
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    let animation: Animation?
    let value: Value
    
    func body(content: Content) -> some View {
        if reduceMotion {
            // Use minimal or no animation when Reduce Motion is enabled
            return content.animation(nil, value: value)
        } else {
            return content.animation(animation, value: value)
        }
    }
}

// Example usage in LoadingIndicator
struct LoadingIndicator: View {
    @State private var isAnimating = false
    
    var body: some View {
        Circle()
            .trim(from: 0, to: 0.7)
            .stroke(AccessibleColors.primary, lineWidth: 2)
            .frame(width: 24, height: 24)
            .rotationEffect(Angle(degrees: isAnimating ? 360 : 0))
            .accessibleAnimation(.linear(duration: 1).repeatForever(autoreverses: false), value: isAnimating)
            .onAppear {
                isAnimating = true
            }
            .accessibilityLabel("Loading")
            .accessibilityHidden(false)
    }
}

// IMPLEMENT: Alternative indicators for Reduce Motion
struct SyncStatusView: View {
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @State private var isAnimating = false
    let isSyncing: Bool
    
    var body: some View {
        HStack {
            if isSyncing {
                if reduceMotion {
                    // Static alternative for reduced motion
                    Text("Syncing...")
                        .foregroundColor(AccessibleColors.primary)
                        .font(.caption)
                } else {
                    // Animated version
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .rotationEffect(Angle(degrees: isAnimating ? 360 : 0))
                        .accessibleAnimation(.linear(duration: 1).repeatForever(autoreverses: false), value: isAnimating)
                        .onAppear {
                            isAnimating = true
                        }
                    
                    Text("Syncing")
                        .font(.caption)
                }
            } else {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(AccessibleColors.success)
                
                Text("Synced")
                    .font(.caption)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(isSyncing ? "Currently syncing" : "Sync complete")
    }
}
```

### 2.6 Touch Targets and Controls

```swift
// IMPLEMENT: Appropriately sized touch targets
struct AccessibleButton<Label: View>: View {
    let action: () -> Void
    let label: Label
    
    init(action: @escaping () -> Void, @ViewBuilder label: () -> Label) {
        self.action = action
        self.label = label()
    }
    
    var body: some View {
        Button(action: action) {
            label
                .contentShape(Rectangle()) // Makes entire area tappable
        }
        .buttonStyle(AccessibleButtonStyle())
    }
}

struct AccessibleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding()
            .frame(minWidth: 44, minHeight: 44) // Minimum touch target size
            .background(configuration.isPressed ? Color.gray.opacity(0.2) : Color.clear)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeOut(duration: 0.1), value: configuration.isPressed)
    }
}

// Example usage in CreateItemView
struct CreateItemView: View {
    @State private var title = ""
    @State private var content = ""
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Title")) {
                    TextField("Enter title", text: $title)
                        .accessibilityIdentifier("title-field")
                }
                
                Section(header: Text("Content")) {
                    TextEditor(text: $content)
                        .frame(minHeight: 200)
                        .accessibilityIdentifier("content-field")
                }
                
                Section {
                    HStack {
                        Spacer()
                        
                        AccessibleButton(action: saveItem) {
                            Text("Save")
                                .bold()
                                .foregroundColor(AccessibleColors.primary)
                        }
                        .disabled(title.isEmpty)
                        .accessibilityIdentifier("save-button")
                        .accessibilityHint(title.isEmpty ? "Title is required" : "Save this item")
                        
                        Spacer()
                    }
                }
            }
            .navigationTitle("Create Item")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    AccessibleButton(action: {
                        presentationMode.wrappedValue.dismiss()
                    }) {
                        Text("Cancel")
                    }
                    .accessibilityIdentifier("cancel-button")
                }
            }
        }
    }
    
    private func saveItem() {
        // Save functionality
        presentationMode.wrappedValue.dismiss()
    }
}
```

### 2.7 Keyboard Support

```swift
// IMPLEMENT: Improved keyboard navigation
struct SearchView: View {
    @StateObject private var viewModel = SearchViewModel()
    @FocusState private var focusedField: FocusField?
    
    enum FocusField {
        case searchField
    }
    
    var body: some View {
        VStack {
            HStack {
                TextField("Search", text: $viewModel.searchQuery)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .focused($focusedField, equals: .searchField)
                    .submitLabel(.search)
                    .onSubmit {
                        performSearch()
                    }
                    .accessibilityIdentifier("search-field")
                
                Button(action: performSearch) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(AccessibleColors.primary)
                }
                .accessibilityIdentifier("search-button")
                .accessibilityLabel("Search")
            }
            .padding()
            
            if viewModel.isLoading {
                LoadingIndicator()
            } else if viewModel.searchResults.isEmpty && !viewModel.searchQuery.isEmpty {
                EmptyResultsView()
            } else {
                SearchResultsList(results: viewModel.searchResults)
                    .accessibilityIdentifier("search-results")
            }
            
            Spacer()
        }
        .navigationTitle("Search")
        .onAppear {
            // Automatically focus the search field
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                focusedField = .searchField
            }
        }
    }
    
    private func performSearch() {
        Task {
            await viewModel.search()
        }
    }
}

// For macOS support - keyboard shortcuts
extension SearchView {
    func keyboardShortcuts() -> some View {
        self
            .keyboardShortcut("f", modifiers: [.command]) // Command+F to focus search
            .onKeyPress(.escape) {
                // Clear search or dismiss
                viewModel.searchQuery = ""
                return .handled
            }
    }
}
```

## 3. Accessibility for Specific Features

### 3.1 Timeline Screen

```swift
// IMPLEMENT: Enhanced timeline accessibility
struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    
    var body: some View {
        ZStack {
            List {
                ForEach(viewModel.items) { item in
                    NavigationLink(destination: ItemDetailView(item: item)) {
                        TimelineItemRow(item: item)
                    }
                    .accessibilityIdentifier("timeline-item-\(item.id)")
                    // Add a hint about the item's age for VoiceOver users
                    .accessibilityHint(accessibilityDateHint(for: item.updatedAt))
                }
                
                if viewModel.hasMoreItems {
                    HStack {
                        Spacer()
                        LoadingIndicator()
                        Spacer()
                    }
                    .onAppear {
                        Task {
                            await viewModel.loadMoreItems()
                        }
                    }
                    .accessibilityIdentifier("loading-more-indicator")
                    .accessibilityLabel("Loading more items")
                }
            }
            .refreshable {
                await viewModel.refreshTimeline()
            }
            .accessibilityIdentifier("timeline-list")
            
            // Show loading view when initially loading
            if viewModel.isLoading && viewModel.items.isEmpty {
                VStack {
                    LoadingIndicator()
                    Text("Loading Timeline")
                        .foregroundColor(.secondary)
                        .padding(.top, 8)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(AccessibleColors.background)
                .accessibilityIdentifier("loading-indicator")
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Loading timeline")
            }
            
            // Show error view when there's an error
            if let error = viewModel.error {
                ErrorView(message: error.localizedDescription) {
                    Task {
                        await viewModel.refreshTimeline()
                    }
                }
                .accessibilityIdentifier("error-view")
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Error loading timeline")
                .accessibilityAction(named: "Retry") {
                    Task {
                        await viewModel.refreshTimeline()
                    }
                }
            }
        }
        .navigationTitle("Timeline")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: {
                    viewModel.showCreateItem = true
                }) {
                    Image(systemName: "plus")
                        .imageScale(.large)
                }
                .accessibilityIdentifier("create-item-button")
                .accessibilityLabel("Create new item")
            }
            
            ToolbarItem(placement: .navigationBarLeading) {
                Button(action: {
                    viewModel.showSearch = true
                }) {
                    Image(systemName: "magnifyingglass")
                        .imageScale(.large)
                }
                .accessibilityIdentifier("search-button")
                .accessibilityLabel("Search items")
            }
        }
        .sheet(isPresented: $viewModel.showCreateItem) {
            CreateItemView()
        }
        .sheet(isPresented: $viewModel.showSearch) {
            SearchView()
        }
        .onAppear {
            if viewModel.items.isEmpty {
                Task {
                    await viewModel.loadTimeline()
                }
            }
        }
    }
    
    // Provide contextual date information for VoiceOver
    private func accessibilityDateHint(for date: Date) -> String {
        let calendar = Calendar.current
        let now = Date()
        
        if calendar.isDateInToday(date) {
            return "Created today"
        } else if calendar.isDateInYesterday(date) {
            return "Created yesterday"
        } else {
            let formatter = DateFormatter()
            formatter.dateStyle = .medium
            return "Created on \(formatter.string(from: date))"
        }
    }
}
```

### 3.2 Item Detail Screen

```swift
// IMPLEMENT: Enhanced item detail accessibility
struct ItemDetailView: View {
    let item: Item
    @StateObject private var viewModel: ItemDetailViewModel
    @Environment(\.accessibilityDifferentiateWithoutColor) var differentiateWithoutColor
    
    init(item: Item) {
        self.item = item
        self._viewModel = StateObject(wrappedValue: ItemDetailViewModel(item: item))
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header section with title and date
                VStack(alignment: .leading, spacing: 8) {
                    Text(item.title)
                        .font(.title)
                        .bold()
                        .accessibilityAddTraits(.isHeader)
                        .accessibilityIdentifier("item-title")
                    
                    HStack {
                        if differentiateWithoutColor {
                            // For users who can't distinguish colors, add a symbol
                            Image(systemName: item.isOffline ? "wifi.slash" : "checkmark.circle")
                                .imageScale(.small)
                        }
                        
                        Text(DateFormatter.mediumFormat.string(from: item.updatedAt))
                            .font(.subheadline)
                            .foregroundColor(item.isOffline ? AccessibleColors.warning : AccessibleColors.secondaryText)
                    }
                    .accessibilityIdentifier("item-date")
                    .accessibilityLabel("Last updated \(DateFormatter.mediumFormat.string(from: item.updatedAt))")
                    .accessibilityHint(item.isOffline ? "This item is pending synchronization" : "This item is synchronized")
                }
                
                Divider()
                
                // Content section
                Text(item.content)
                    .fixedSize(horizontal: false, vertical: true) // Allows text to expand properly
                    .accessibilityIdentifier("item-content")
                
                // Attachments section (if any)
                if let attachments = item.attachments, !attachments.isEmpty {
                    Divider()
                    
                    Text("Attachments")
                        .font(.headline)
                        .padding(.top, 8)
                        .accessibilityAddTraits(.isHeader)
                    
                    ForEach(attachments) { attachment in
                        AttachmentView(attachment: attachment)
                            .accessibilityIdentifier("attachment-\(attachment.id)")
                    }
                    .accessibilityElement(children: .contain)
                    .accessibilityLabel("Attachments")
                }
                
                // Tags section (if any)
                if let tags = item.tags, !tags.isEmpty {
                    Divider()
                    
                    Text("Tags")
                        .font(.headline)
                        .padding(.top, 8)
                        .accessibilityAddTraits(.isHeader)
                    
                    FlowLayout(tags, spacing: 8) { tag in
                        Text(tag)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(AccessibleColors.secondaryBackground)
                            .cornerRadius(12)
                            .accessibilityIdentifier("tag-\(tag)")
                    }
                    .accessibilityElement(children: .combine)
                    .accessibilityLabel("Tags: \(tags.joined(separator: ", "))")
                }
            }
            .padding()
        }
        .navigationTitle("Details")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: {
                    viewModel.isEditing = true
                }) {
                    Text("Edit")
                }
                .accessibilityIdentifier("edit-button")
            }
            
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button(action: shareItem) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                    .accessibilityIdentifier("share-button")
                    
                    Button(action: deleteItem) {
                        Label("Delete", systemImage: "trash")
                    }
                    .foregroundColor(.red)
                    .accessibilityIdentifier("delete-button")
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .imageScale(.large)
                }
                .accessibilityIdentifier("more-options-button")
                .accessibilityLabel("More options")
            }
        }
        .sheet(isPresented: $viewModel.isEditing) {
            EditItemView(item: item, onSave: { updatedItem in
                viewModel.updateItem(updatedItem)
            })
        }
        .alert("Confirm Deletion", isPresented: $viewModel.showingDeleteConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                viewModel.confirmDelete()
            }
        } message: {
            Text("Are you sure you want to delete this item? This action cannot be undone.")
        }
    }
    
    private func shareItem() {
        viewModel.shareItem()
    }
    
    private func deleteItem() {
        viewModel.showingDeleteConfirmation = true
    }
}

// Accessible flow layout for tags
struct FlowLayout<T: Hashable, Content: View>: View {
    let items: [T]
    let spacing: CGFloat
    let content: (T) -> Content
    
    init(_ items: [T], spacing: CGFloat = 8, @ViewBuilder content: @escaping (T) -> Content) {
        self.items = items
        self.spacing = spacing
        self.content = content
    }
    
    var body: some View {
        GeometryReader { geometry in
            self.generateContent(in: geometry)
        }
    }
    
    private func generateContent(in geometry: GeometryProxy) -> some View {
        var width = CGFloat.zero
        var height = CGFloat.zero
        
        return ZStack(alignment: .topLeading) {
            ForEach(items, id: \.self) { item in
                content(item)
                    .padding(.trailing, spacing)
                    .padding(.bottom, spacing)
                    .alignmentGuide(.leading) { dimension in
                        if abs(width - dimension.width) > geometry.size.width {
                            width = 0
                            height -= dimension.height
                        }
                        
                        let result = width
                        if item == items.last {
                            width = 0
                        } else {
                            width -= dimension.width
                        }
                        return result
                    }
                    .alignmentGuide(.top) { _ in
                        let result = height
                        if item == items.last {
                            height = 0
                        }
                        return result
                    }
            }
        }
    }
}
```

### 3.3 Search Screen

```swift
// IMPLEMENT: Accessible search experience
struct SearchView: View {
    @StateObject private var viewModel = SearchViewModel()
    @FocusState private var isSearchFieldFocused: Bool
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @Environment(\.accessibilityVoiceOverEnabled) var voiceOverEnabled
    
    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.gray)
                
                TextField("Search items", text: $viewModel.searchQuery)
                    .disableAutocorrection(true)
                    .focused($isSearchFieldFocused)
                    .submitLabel(.search)
                    .onSubmit {
                        Task {
                            await viewModel.search()
                        }
                    }
                    .onChange(of: viewModel.searchQuery) { _, newValue in
                        viewModel.updateSearchQuery(newValue)
                    }
                    .accessibilityIdentifier("search-field")
                
                if !viewModel.searchQuery.isEmpty {
                    Button(action: {
                        viewModel.searchQuery = ""
                        isSearchFieldFocused = true
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.gray)
                    }
                    .transition(.scale.combined(with: .opacity))
                    .accessibilityIdentifier("clear-search-button")
                    .accessibilityLabel("Clear search")
                }
            }
            .padding()
            .background(AccessibleColors.secondaryBackground)
            
            // Recent searches
            if viewModel.searchQuery.isEmpty && !viewModel.recentSearches.isEmpty {
                List {
                    Section(header: Text("Recent Searches")
                        .accessibilityAddTraits(.isHeader)) {
                        ForEach(viewModel.recentSearches, id: \.self) { search in
                            Button(action: {
                                viewModel.searchQuery = search
                                Task {
                                    await viewModel.search()
                                }
                            }) {
                                HStack {
                                    Image(systemName: "clock")
                                        .foregroundColor(.gray)
                                    Text(search)
                                    Spacer()
                                    Image(systemName: "arrow.up.left")
                                        .foregroundColor(.gray)
                                        .accessibilityHidden(true) // Hide icon from VoiceOver
                                }
                            }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("recent-search-\(search)")
                            .accessibilityHint("Search again for \(search)")
                        }
                    }
                }
                .accessibleAnimation(.default, value: viewModel.recentSearches)
            }
            
            // Search results
            if !viewModel.searchQuery.isEmpty {
                ZStack {
                    if viewModel.isLoading {
                        VStack {
                            LoadingIndicator()
                            Text("Searching...")
                                .foregroundColor(.secondary)
                                .padding(.top, 8)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .accessibilityIdentifier("search-loading-indicator")
                        .accessibilityElement(children: .combine)
                        .accessibilityLabel("Searching for \(viewModel.searchQuery)")
                    } else if viewModel.searchResults.isEmpty {
                        VStack(spacing: 16) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 48))
                                .foregroundColor(.gray)
                            
                            Text("No results found for "\(viewModel.searchQuery)"")
                                .multilineTextAlignment(.center)
                            
                            Text("Try another search term or browse the timeline")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .accessibilityIdentifier("no-results-view")
                        .accessibilityElement(children: .combine)
                        .accessibilityLabel("No results found for \(viewModel.searchQuery)")
                    } else {
                        List {
                            ForEach(viewModel.searchResults) { item in
                                NavigationLink(destination: ItemDetailView(item: item)) {
                                    SearchResultRow(item: item, searchTerm: viewModel.searchQuery)
                                }
                                .accessibilityIdentifier("search-result-\(item.id)")
                            }
                            
                            if viewModel.hasMoreResults {
                                HStack {
                                    Spacer()
                                    LoadingIndicator()
                                    Spacer()
                                }
                                .onAppear {
                                    Task {
                                        await viewModel.loadMoreResults()
                                    }
                                }
                                .accessibilityIdentifier("loading-more-results")
                                .accessibilityLabel("Loading more results")
                            }
                        }
                        .accessibilityIdentifier("search-results-list")
                    }
                }
                .accessibleAnimation(reduceMotion ? nil : .default, value: viewModel.searchResults)
            }
        }
        .navigationTitle("Search")
        .onAppear {
            // Automatically focus search field when view appears
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                isSearchFieldFocused = true
            }
            
            // Announce to VoiceOver users
            if voiceOverEnabled {
                DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                    UIAccessibility.post(notification: .announcement, argument: "Search screen. Search field is active.")
                }
            }
        }
    }
}

// Highlight search terms in results
struct SearchResultRow: View {
    let item: Item
    let searchTerm: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(item.title)
                .font(.headline)
                .lineLimit(1)
                .accessibilityIdentifier("result-title")
            
            if let highlightedContent = highlightedContent {
                Text(highlightedContent)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
                    .accessibilityIdentifier("result-content")
            } else {
                Text(item.content.prefix(100))
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
                    .accessibilityIdentifier("result-content")
            }
            
            Text(DateFormatter.shortFormat.string(from: item.updatedAt))
                .font(.caption)
                .foregroundColor(.secondary)
                .accessibilityIdentifier("result-date")
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(item.title), containing search term \(searchTerm)")
    }
    
    // For visual users, highlight matching text
    // For VoiceOver, this is ignored as we use the custom label above
    private var highlightedContent: AttributedString? {
        guard !searchTerm.isEmpty else { return nil }
        
        let content = item.content.prefix(200)
        guard let range = content.range(of: searchTerm, options: [.caseInsensitive, .diacriticInsensitive]) else {
            return nil
        }
        
        var attributedString = AttributedString(content)
        if let highlightRange = Range(range, in: attributedString) {
            attributedString[highlightRange].backgroundColor = AccessibleColors.primary.opacity(0.3)
            attributedString[highlightRange].foregroundColor = AccessibleColors.primaryText
            attributedString[highlightRange].font = .body.bold()
        }
        
        return attributedString
    }
}
```

### 3.4 Error States and Feedback

```swift
// IMPLEMENT: Accessible error handling
struct ErrorView: View {
    let message: String
    var retryAction: (() -> Void)?
    
    @Environment(\.accessibilityVoiceOverEnabled) var voiceOverEnabled
    @Environment(\.accessibilityDifferentiateWithoutColor) var differentiateWithoutColor
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(differentiateWithoutColor ? .primary : AccessibleColors.error)
            
            Text("Error")
                .font(.title2)
                .bold()
            
            Text(message)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            if let retryAction = retryAction {
                Button(action: {
                    retryAction()
                }) {
                    HStack {
                        Image(systemName: "arrow.clockwise")
                        Text("Try Again")
                    }
                    .padding()
                    .background(AccessibleColors.primary)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                }
                .accessibilityIdentifier("retry-button")
            }
        }
        .padding()
        .background(AccessibleColors.background)
        .cornerRadius(12)
        .shadow(radius: 4)
        .onAppear {
            if voiceOverEnabled {
                UIAccessibility.post(notification: .announcement, argument: "Error: \(message)")
            }
        }
    }
}

// Accessible toast notifications
struct ToastView: View {
    let message: String
    let type: ToastType
    
    enum ToastType {
        case success, error, info
    }
    
    @Environment(\.accessibilityVoiceOverEnabled) var voiceOverEnabled
    @Environment(\.accessibilityDifferentiateWithoutColor) var differentiateWithoutColor
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: iconName)
                .foregroundColor(iconColor)
            
            Text(message)
                .foregroundColor(AccessibleColors.primaryText)
            
            if differentiateWithoutColor {
                // Add a visual indicator for those who can't distinguish colors
                Text(typeText)
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(AccessibleColors.background)
                    .cornerRadius(4)
            }
        }
        .padding()
        .background(backgroundColor)
        .cornerRadius(8)
        .shadow(radius: 2)
        .onAppear {
            if voiceOverEnabled {
                UIAccessibility.post(notification: .announcement, argument: "\(typeText): \(message)")
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(typeText): \(message)")
    }
    
    private var iconName: String {
        switch type {
        case .success: return "checkmark.circle.fill"
        case .error: return "exclamationmark.triangle.fill"
        case .info: return "info.circle.fill"
        }
    }
    
    private var iconColor: Color {
        if differentiateWithoutColor {
            return AccessibleColors.primaryText
        }
        
        switch type {
        case .success: return AccessibleColors.success
        case .error: return AccessibleColors.error
        case .info: return AccessibleColors.primary
        }
    }
    
    private var backgroundColor: Color {
        if differentiateWithoutColor {
            return AccessibleColors.secondaryBackground
        }
        
        switch type {
        case .success: return AccessibleColors.success.opacity(0.2)
        case .error: return AccessibleColors.error.opacity(0.2)
        case .info: return AccessibleColors.primary.opacity(0.2)
        }
    }
    
    private var typeText: String {
        switch type {
        case .success: return "Success"
        case .error: return "Error"
        case .info: return "Information"
        }
    }
}
```

## 4. Accessibility Testing

### 4.1 Automated Testing

```swift
// IMPLEMENT: Accessibility-specific unit tests
final class AccessibilityTests: XCTestCase {
    func testDynamicTypeSupport() {
        // Test that views adapt to different content size categories
        for sizeCategory in ContentSizeCategory.allCases {
            let environment = EnvironmentValues()
            environment.sizeCategory = sizeCategory
            
            // Create and test various views
            let itemRow = TimelineItemRow(item: createTestItem())
            let itemRowContainer = _ViewHosting.Host(rootView: itemRow, environment: environment)
            
            // Render the view
            let frame = CGRect(x: 0, y: 0, width: 375, height: 100)
            itemRowContainer.view.frame = frame
            itemRowContainer.view.layoutIfNeeded()
            
            // Verify that the view has a reasonable height for the content size
            // This would need a more sophisticated check in a real test
            XCTAssertGreaterThan(itemRowContainer.view.frame.height, 0)
        }
    }
    
    func testVoiceOverAccessibilityLabels() {
        // Create test views
        let item = createTestItem()
        let itemRow = TimelineItemRow(item: item)
        
        // Verify accessibility traits
        let accessibilityElements = findAccessibilityElements(in: itemRow)
        XCTAssertTrue(accessibilityElements.count > 0, "Should have at least one accessibility element")
        
        // Check that the accessibility label contains the item title
        let labels = accessibilityElements.compactMap { ($0 as? NSObject)?.accessibilityLabel }
        XCTAssertTrue(labels.contains { $0.contains(item.title) }, "Accessibility label should contain item title")
    }
    
    func testReduceMotionCompliance() {
        // Test that animations are disabled when reduce motion is enabled
        let environment = EnvironmentValues()
        environment.accessibilityReduceMotion = true
        
        // Create and test animation-using view
        let loadingIndicator = LoadingIndicator()
        let hostingView = _ViewHosting.Host(rootView: loadingIndicator, environment: environment)
        
        // Inspect the view hierarchy for animations
        // This would need a more sophisticated check in a real test
        // You might need to use UI testing for more thorough verification
    }
    
    // Helper method to create a test item
    private func createTestItem() -> Item {
        return Item(
            id: "test-id",
            title: "Test Item",
            content: "This is test content for accessibility testing",
            createdAt: Date(),
            updatedAt: Date()
        )
    }
    
    // Helper method to find accessibility elements in a SwiftUI view
    private func findAccessibilityElements(in view: some View) -> [Any] {
        let hostingView = _ViewHosting.Host(rootView: view)
        hostingView.view.frame = CGRect(x: 0, y: 0, width: 375, height: 100)
        hostingView.view.layoutIfNeeded()
        
        var elements: [Any] = []
        findAccessibilityElements(in: hostingView.view, into: &elements)
        return elements
    }
    
    private func findAccessibilityElements(in view: UIView, into elements: inout [Any]) {
        if let axElements = view.accessibilityElements {
            elements.append(contentsOf: axElements)
        } else if view.isAccessibilityElement {
            elements.append(view)
        }
        
        for subview in view.subviews {
            findAccessibilityElements(in: subview, into: &elements)
        }
    }
}
```

### 4.2 UI Testing

```swift
// IMPLEMENT: Accessibility-focused UI tests
final class AccessibilityUITests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        
        app = XCUIApplication()
        app.launchArguments = ["UI-TESTING"]
        
        // Enable accessibility features for testing
        app.launchEnvironment = [
            "UIAccessibilityInvertColorsEnabled": "YES",
            "UIAccessibilityReduceMotionEnabled": "YES",
            "UIAccessibilityDarkerSystemColorsEnabled": "YES"
        ]
        
        app.launch()
    }
    
    func testVoiceOverNavigation() {
        // This test simulates VoiceOver navigation through the app
        
        // Enable VoiceOver simulation
        XCUIDevice.shared.press(.home)
        
        // Navigate to timeline
        let timelineNav = app.navigationBars["Timeline"]
        XCTAssertTrue(timelineNav.waitForExistence(timeout: 2))
        
        // Check that the first item is accessible
        let firstCell = app.cells.element(boundBy: 0)
        XCTAssertTrue(firstCell.isAccessibilityElement)
        
        // Navigate to item detail
        firstCell.tap()
        
        // Check that item detail elements are accessible
        let detailView = app.scrollViews.firstMatch
        XCTAssertTrue(detailView.waitForExistence(timeout: 2))
        
        // Check for important accessibility elements
        XCTAssertTrue(app.staticTexts["item-title"].isAccessibilityElement)
        XCTAssertTrue(app.staticTexts["item-content"].isAccessibilityElement)
        
        // Navigate back
        app.navigationBars.buttons.element(boundBy: 0).tap()
        
        // Check we're back at timeline
        XCTAssertTrue(timelineNav.exists)
    }
    
    func testDynamicTypeAccessibility() {
        // Set larger text
        let settings = XCUIApplication(bundleIdentifier: "com.apple.Preferences")
        settings.launch()
        
        // Navigate to accessibility settings and increase text size
        // This is challenging to automate and would typically be manual
        
        // Return to app and verify text scaling
        app.activate()
        
        // Check that text elements are still visible and not truncated
        // This would require specific assertions based on your app's layout
    }
    
    func testColorContrastWithInvertColors() {
        // Test app with inverted colors
        // Check that all elements remain visible and functional
        
        // This test is mostly visual verification, but we can check
        // that elements are still present and interactive
        
        let timelineNav = app.navigationBars["Timeline"]
        XCTAssertTrue(timelineNav.exists)
        
        let createButton = app.buttons["create-item-button"]
        XCTAssertTrue(createButton.exists)
        XCTAssertTrue(createButton.isHittable)
        
        // Tap create button
        createButton.tap()
        
        // Verify create view appears
        XCTAssertTrue(app.navigationBars["Create Item"].waitForExistence(timeout: 2))
    }
}
```

### 4.3 Manual Testing Checklist

```markdown
# Accessibility Manual Testing Checklist

## VoiceOver Testing
- [ ] Navigate through the entire app using VoiceOver
- [ ] Verify all elements have appropriate accessibility labels
- [ ] Check that custom actions are available and working
- [ ] Ensure content is read in a logical order
- [ ] Verify focus is properly managed during transitions

## Dynamic Type Testing
- [ ] Test with text size set to "Accessibility XL"
- [ ] Verify no text is truncated
- [ ] Check that layout adjusts appropriately
- [ ] Ensure interactive elements remain usable
- [ ] Test with bold text enabled

## Motion & Animation Testing
- [ ] Enable Reduce Motion
- [ ] Verify animations are simplified or eliminated
- [ ] Check that all functionality remains available
- [ ] Test transitions between screens

## Color & Contrast Testing
- [ ] Enable Increase Contrast
- [ ] Verify all text is readable
- [ ] Test with Smart Invert Colors
- [ ] Test with Classic Invert Colors
- [ ] Test with Color Filters (Protanopia, Deuteranopia, Tritanopia)

## Keyboard & Switch Control Testing
- [ ] Test full keyboard navigation (connected keyboard)
- [ ] Verify focus indicators are visible
- [ ] Test Switch Control compatibility
- [ ] Check tab order is logical

## Voice Control Testing
- [ ] Enable Voice Control
- [ ] Test navigation commands ("tap", "show numbers")
- [ ] Verify custom commands work with app elements

## Hearing Accessibility Testing
- [ ] Ensure no critical information is conveyed by sound alone
- [ ] Test with captioning enabled (if app has videos)
- [ ] Verify visual alternatives for audio cues

## Device Orientation & Sizing
- [ ] Test in portrait and landscape orientations
- [ ] Verify accessibility features work in all orientations
- [ ] Test on different device sizes

## Specific Feature Testing
- [ ] Timeline: VoiceOver can navigate through items
- [ ] Search: Screen reader announces results
- [ ] Item Detail: All content is accessible
- [ ] Create/Edit: Forms work with accessibility features
- [ ] Error states: Errors are properly announced
- [ ] Loading states: Progress is communicated
```

## 5. Implementation Timeline

### Phase 1: Foundation (Week 1-2)
1. Implement basic accessibility identifiers throughout the app
2. Add proper VoiceOver support for core screens
3. Fix any critical accessibility issues
4. Create custom accessibility extensions

### Phase 2: Enhanced Support (Week 3-4)
1. Improve Dynamic Type support across all screens
2. Implement motion reduction alternatives
3. Enhance color contrast and differentiation
4. Add keyboard navigation support

### Phase 3: Testing & Refinement (Week 5-6)
1. Create automated accessibility tests
2. Perform manual testing with all accessibility features
3. Fix issues discovered in testing
4. Document accessibility features for users

### Phase 4: Advanced Features (Week 7-8)
1. Implement custom accessibility actions
2. Add voice control optimizations
3. Enhance switch control support
4. Fine-tune accessibility experience based on feedback

## 6. Success Metrics

- Score 100% on basic accessibility audits
- App is fully navigable using VoiceOver only
- All content remains readable with largest Dynamic Type setting
- App functions properly with all accessibility features enabled
- Zero accessibility-related crashes or blockers
- Positive feedback from accessibility testers

## 7. Resources

- [Apple Accessibility Guidelines](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- [SwiftUI Accessibility Documentation](https://developer.apple.com/documentation/swiftui/accessibility)
- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [Accessibility Scanner Tools](https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/OSXAXTestingApps.html)

## 8. Conclusion

Implementing this accessibility plan will ensure the PRSNL iOS app is usable by people with a wide range of abilities. By building accessibility in from the ground up rather than treating it as an afterthought, we create a better experience for all users while meeting Apple's guidelines and ethical standards for inclusive design.