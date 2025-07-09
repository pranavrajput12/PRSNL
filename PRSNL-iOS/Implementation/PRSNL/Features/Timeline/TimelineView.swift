import SwiftUI

struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    @State private var selectedItem: Item?
    @State private var showingAddView = false
    @State private var refreshRotation = 0.0
    @State private var showingFilters = false
    @Namespace private var animation
    @State private var rollingScore = 0
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background gradient
                LinearGradient(
                    colors: [
                        Color(UIColor.systemBackground),
                        DesignSystem.Colors.gray50.opacity(0.3)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                
                if viewModel.items.isEmpty && !viewModel.isLoading {
                    emptyStateView
                } else {
                    timelineContent
                }
                
                // Floating Action Button
                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        FloatingActionButton(icon: "plus") {
                            showingAddView = true
                        }
                        .padding(DesignSystem.Spacing.space4)
                    }
                }
            }
            .navigationBarHidden(true)
            .toolbar(content: {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: DesignSystem.Spacing.space3) {
                        // Filter Button
                        Button(action: {
                            withAnimation(DesignSystem.Animation.smooth) {
                                showingFilters.toggle()
                            }
                        }) {
                            ZStack {
                                Circle()
                                    .fill(showingFilters ? DesignSystem.Colors.primaryRed : Color.clear)
                                    .frame(width: 36, height: 36)
                                
                                Image(systemName: "line.3.horizontal.decrease.circle")
                                    .foregroundColor(showingFilters ? .white : DesignSystem.Colors.gray600)
                                    .font(.system(size: 22))
                                    .rotationEffect(.degrees(showingFilters ? 180 : 0))
                            }
                        }
                        
                        NavigationLink(destination: SettingsView()) {
                            Image(systemName: "gearshape.fill")
                                .foregroundColor(DesignSystem.Colors.gray600)
                                .font(.system(size: 20))
                        }
                    }
                }
            })
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
        .sheet(isPresented: $showingAddView) {
            Text("Content Capture Coming Soon")
                .font(.title2)
                .padding()
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: DesignSystem.Spacing.space6) {
            // Animated icon
            ZStack {
                Circle()
                    .fill(DesignSystem.Colors.primaryRed.opacity(0.1))
                    .frame(width: 120, height: 120)
                    .scaleEffect(1.2)
                    .animation(
                        Animation.easeInOut(duration: 2)
                            .repeatForever(autoreverses: true),
                        value: true
                    )
                
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: 60))
                    .foregroundColor(DesignSystem.Colors.primaryRed)
                    .rotationEffect(.degrees(refreshRotation))
                    .onAppear {
                        withAnimation(Animation.linear(duration: 3).repeatForever(autoreverses: false)) {
                            refreshRotation = 360
                        }
                    }
            }
            
            VStack(spacing: DesignSystem.Spacing.space3) {
                Text("No items in timeline")
                    .font(DesignSystem.Typography.inter(DesignSystem.Typography.text3XL, weight: .bold))
                    .foregroundColor(Color(UIColor.label))
                
                Text("Your captured knowledge will appear here")
                    .font(DesignSystem.Typography.inter(DesignSystem.Typography.textLG))
                    .foregroundColor(DesignSystem.Colors.gray600)
                    .multilineTextAlignment(.center)
            }
            
            Button(action: {
                Task { await viewModel.refresh() }
            }) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Load Timeline")
                }
                .primaryButtonStyle()
            }
        }
        .padding()
    }
    
    private var timelineContent: some View {
        VStack(spacing: 0) {
            // Top padding for clean look
            Spacer()
                .frame(height: 40)
            
            // Short pun - much more concise
            if let inspiration = viewModel.dailyInspiration {
                dailyInspirationSection(inspiration)
                    .padding(.bottom, 20)
            }
            
            // Restore the stats card - this wasn't the problem
            personalizedHeroSection
                .padding(.bottom, 20)
            
            // Rolling Quote Section - shorter and punchier
            if let inspiration = viewModel.dailyInspiration {
                rollingQuoteSection(inspiration)
                    .padding(.bottom, 40)
            }
            
            // Filter Pills (shown when filter is active)
            if showingFilters {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: DesignSystem.Spacing.space2) {
                        FilterPill(title: "All", isSelected: true)
                        FilterPill(title: "Articles", isSelected: false)
                        FilterPill(title: "Videos", isSelected: false)
                        FilterPill(title: "Notes", isSelected: false)
                        FilterPill(title: "Recent", isSelected: false)
                    }
                    .padding(.horizontal)
                    .padding(.vertical, DesignSystem.Spacing.space2)
                }
                .transition(.move(edge: .top).combined(with: .opacity))
            }
            
            ScrollView {
                LazyVStack(spacing: DesignSystem.Spacing.space3) {
                    ForEach(groupedItems, id: \.key) { date, items in
                        VStack(alignment: .leading, spacing: DesignSystem.Spacing.space3) {
                            // Date header with sticky effect
                            HStack {
                                Text(date)
                                    .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM, weight: .semibold))
                                    .foregroundColor(DesignSystem.Colors.gray600)
                                    .padding(.horizontal, DesignSystem.Spacing.space3)
                                    .padding(.vertical, DesignSystem.Spacing.space1)
                                    .background(
                                        Capsule()
                                            .fill(DesignSystem.Colors.gray100)
                                    )
                                
                                Rectangle()
                                    .fill(DesignSystem.Colors.gray200)
                                    .frame(height: 1)
                            }
                            .padding(.horizontal, DesignSystem.Spacing.space2)
                            
                            ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                                TimelineItemCard(item: item)
                                    .onTapGesture {
                                        selectedItem = item
                                    }
                                    .onAppear {
                                        if item.id == viewModel.items.last?.id {
                                            Task { await viewModel.loadMore() }
                                        }
                                    }
                                    .transition(.asymmetric(
                                        insertion: .opacity.combined(with: .scale(scale: 0.9)).combined(with: .offset(x: 50)),
                                        removal: .opacity.combined(with: .scale(scale: 0.9))
                                    ))
                                    .animation(
                                        DesignSystem.Animation.smooth.delay(Double(index) * 0.1),
                                        value: items.count
                                    )
                            }
                        }
                    }
                    
                    if viewModel.isLoading && !viewModel.items.isEmpty {
                        LoadingDots()
                            .padding()
                    }
                }
                .padding(.vertical)
            }
            .refreshable {
                await viewModel.refresh()
            }
        }
    }
    
    private var personalizedHeroSection: some View {
        VStack(spacing: DesignSystem.Spacing.space3) {
            // Stats and Score Section
            HStack {
                VStack(alignment: .leading, spacing: DesignSystem.Spacing.space2) {
                    HStack(spacing: DesignSystem.Spacing.space3) {
                        HStack(spacing: DesignSystem.Spacing.space1) {
                            Image(systemName: "flame.fill")
                                .foregroundColor(.orange)
                                .font(.system(size: 16))
                            Text("12 day streak")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.primary)
                        }
                        
                        HStack(spacing: DesignSystem.Spacing.space1) {
                            Image(systemName: "doc.fill")
                                .foregroundColor(.blue)
                                .font(.system(size: 16))
                            Text("\(viewModel.items.count) items")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.primary)
                        }
                    }
                }
                
                Spacer()
                
                // Enhanced knowledge score circle
                ZStack {
                    Circle()
                        .stroke(Color.gray.opacity(0.2), lineWidth: 4)
                        .frame(width: 60, height: 60)
                    
                    Circle()
                        .trim(from: 0, to: 0.85)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    DesignSystem.Colors.primaryRed,
                                    Color.orange,
                                    DesignSystem.Colors.primaryRed
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 4
                        )
                        .frame(width: 60, height: 60)
                        .rotationEffect(.degrees(-90))
                        .animation(
                            Animation.easeInOut(duration: 2.0)
                                .repeatForever(autoreverses: false),
                            value: true
                        )
                    
                    Text("\(rollingScore)")
                        .font(.system(size: 16, weight: .black))
                        .foregroundColor(.primary)
                        .onAppear {
                            startRollingScore()
                        }
                }
            }
            
            // Quick Actions
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: DesignSystem.Spacing.space3) {
                    ForEach(Array(quickActions.enumerated()), id: \.element.title) { index, action in
                        VStack(spacing: DesignSystem.Spacing.space1) {
                            ZStack {
                                Circle()
                                    .fill(action.color.opacity(0.1))
                                    .frame(width: 36, height: 36)
                                    .scaleEffect(1.0)
                                    .animation(
                                        Animation.easeInOut(duration: 1.5)
                                            .repeatForever(autoreverses: true)
                                            .delay(Double(index) * 0.3),
                                        value: true
                                    )
                                
                                Image(systemName: action.icon)
                                    .foregroundColor(action.color)
                                    .font(.system(size: 16, weight: .medium))
                                    .scaleEffect(1.0)
                                    .animation(
                                        Animation.easeInOut(duration: 1.2)
                                            .repeatForever(autoreverses: true)
                                            .delay(Double(index) * 0.2),
                                        value: true
                                    )
                            }
                            
                            Text(action.title)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(.secondary)
                        }
                        .frame(width: 60)
                    }
                }
                .padding(.horizontal)
            }
        }
        .padding()
        .background(
            ZStack {
                // Modern gradient background with depth
                LinearGradient(
                    colors: [
                        Color.white,
                        Color.gray.opacity(0.1),
                        DesignSystem.Colors.primaryRed.opacity(0.05),
                        Color.white.opacity(0.95)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                
                // Subtle pattern overlay
                heroGridBackgroundView()
                
                // Glassmorphism effect with better contrast
                Color.white.opacity(0.7)
            }
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24)
                .stroke(
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0.8),
                            DesignSystem.Colors.primaryRed.opacity(0.4),
                            Color.orange.opacity(0.3),
                            Color.white.opacity(0.6)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 2
                )
        )
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .shadow(
            color: DesignSystem.Colors.primaryRed.opacity(0.2),
            radius: 20,
            x: 0,
            y: 10
        )
        .shadow(
            color: Color.black.opacity(0.05),
            radius: 5,
            x: 0,
            y: 2
        )
        .padding(.horizontal)
    }
    
    private func dailyInspirationSection(_ inspiration: DailyInspiration) -> some View {
        VStack(spacing: DesignSystem.Spacing.space4) {
            // Clean Pun - Just text, no clutter
            Text(inspiration.pun.text)
                .font(.system(size: 22, weight: .black))
                .foregroundStyle(
                    LinearGradient(
                        colors: [
                            DesignSystem.Colors.primaryRed,
                            Color.orange,
                            DesignSystem.Colors.primaryRed
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .multilineTextAlignment(.center)
                .shadow(
                    color: DesignSystem.Colors.primaryRed.opacity(0.3),
                    radius: 2,
                    x: 1,
                    y: 1
                )
                .padding(.horizontal, DesignSystem.Spacing.space4)
        }
    }
    
    private func rollingQuoteSection(_ inspiration: DailyInspiration) -> some View {
        VStack(spacing: 0) {
            // Modern, clean quote display
            ModernQuoteView(text: inspiration.quote.text, author: inspiration.quote.author)
                .frame(height: 140)
                .padding(.horizontal, DesignSystem.Spacing.space4)
        }
    }
    
    private func gridBackgroundView() -> some View {
        Canvas { context, size in
            let gridSize: CGFloat = 15
            let gridColor = Color.white.opacity(0.1)
            
            // Vertical lines
            for i in stride(from: 0, through: size.width, by: gridSize) {
                let path = Path { path in
                    path.move(to: CGPoint(x: i, y: 0))
                    path.addLine(to: CGPoint(x: i, y: size.height))
                }
                context.stroke(path, with: .color(gridColor), lineWidth: 0.5)
            }
            
            // Horizontal lines
            for i in stride(from: 0, through: size.height, by: gridSize) {
                let path = Path { path in
                    path.move(to: CGPoint(x: 0, y: i))
                    path.addLine(to: CGPoint(x: size.width, y: i))
                }
                context.stroke(path, with: .color(gridColor), lineWidth: 0.5)
            }
        }
    }
    
    private func heroGridBackgroundView() -> some View {
        Canvas { context, size in
            let gridSize: CGFloat = 12
            let gridColor = Color.white.opacity(0.08)
            
            // Vertical lines
            for i in stride(from: 0, through: size.width, by: gridSize) {
                let path = Path { path in
                    path.move(to: CGPoint(x: i, y: 0))
                    path.addLine(to: CGPoint(x: i, y: size.height))
                }
                context.stroke(path, with: .color(gridColor), lineWidth: 0.3)
            }
            
            // Horizontal lines
            for i in stride(from: 0, through: size.height, by: gridSize) {
                let path = Path { path in
                    path.move(to: CGPoint(x: 0, y: i))
                    path.addLine(to: CGPoint(x: size.width, y: i))
                }
                context.stroke(path, with: .color(gridColor), lineWidth: 0.3)
            }
        }
    }
    
    private func modernPatternOverlay() -> some View {
        Canvas { context, size in
            let dotSize: CGFloat = 3
            let spacing: CGFloat = 20
            let dotColor = Color.white.opacity(0.1)
            
            // Create subtle dot pattern
            for x in stride(from: 0, through: size.width, by: spacing) {
                for y in stride(from: 0, through: size.height, by: spacing) {
                    let rect = CGRect(x: x, y: y, width: dotSize, height: dotSize)
                    let path = Path(ellipseIn: rect)
                    context.fill(path, with: .color(dotColor))
                }
            }
            
            // Add diagonal lines for extra texture
            let lineColor = Color.white.opacity(0.05)
            for i in stride(from: -size.height, through: size.width, by: 40) {
                let path = Path { path in
                    path.move(to: CGPoint(x: i, y: 0))
                    path.addLine(to: CGPoint(x: i + size.height, y: size.height))
                }
                context.stroke(path, with: .color(lineColor), lineWidth: 0.5)
            }
        }
    }
    
    private func startRollingScore() {
        withAnimation(.easeInOut(duration: 2.0)) {
            rollingScore = 85
        }
    }
    
    private var quickActions: [(title: String, icon: String, color: Color)] {
        [
            ("Capture", "brain.head.profile", DesignSystem.Colors.primaryRed),
            ("Voice", "waveform.path.ecg", DesignSystem.Colors.primaryGreen),
            ("Scan", "viewfinder", DesignSystem.Colors.primaryPurple),
            ("AI Chat", "bubble.left.and.bubble.right", Color.orange)
        ]
    }
    
    private var greetingMessage: String {
        let hour = Calendar.current.component(.hour, from: Date())
        let name = "Pranav"
        
        switch hour {
        case 5..<12:
            return "Good morning, \(name)!"
        case 12..<17:
            return "Good afternoon, \(name)!"
        case 17..<21:
            return "Good evening, \(name)!"
        default:
            return "Hello, \(name)!"
        }
    }
    
    private var groupedItems: [(key: String, value: [Item])] {
        let calendar = Calendar.current
        let grouped = Dictionary(grouping: viewModel.items) { item in
            calendar.startOfDay(for: item.createdAt)
        }
        
        return grouped.sorted { $0.key > $1.key }.map { date, items in
            let formatter = DateFormatter()
            
            if calendar.isDateInToday(date) {
                return (key: "Today", value: items)
            } else if calendar.isDateInYesterday(date) {
                return (key: "Yesterday", value: items)
            } else {
                formatter.dateFormat = "MMMM d"
                return (key: formatter.string(from: date), value: items)
            }
        }
    }
}

struct ModernQuoteView: View {
    let text: String
    let author: String
    @State private var showContent = false
    @State private var textScale: CGFloat = 0.95
    
    var body: some View {
        ZStack {
            // Clean, modern background with subtle glassmorphism
            RoundedRectangle(cornerRadius: 20)
                .fill(
                    .regularMaterial,
                    style: FillStyle()
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(
                            .white.opacity(0.2),
                            lineWidth: 0.5
                        )
                )
            
            // Content with proper spacing and typography
            VStack(spacing: 24) {
                // Quote text with modern typography
                Text(text)
                    .font(.system(size: 22, weight: .medium, design: .rounded))
                    .foregroundStyle(.primary)
                    .multilineTextAlignment(.center)
                    .lineLimit(nil)
                    .scaleEffect(textScale)
                    .opacity(showContent ? 1.0 : 0.0)
                    .animation(.easeInOut(duration: 0.8).delay(0.2), value: showContent)
                
                // Author with subtle styling
                Text("— \(author)")
                    .font(.system(size: 16, weight: .regular, design: .rounded))
                    .foregroundStyle(.secondary)
                    .italic()
                    .opacity(showContent ? 0.8 : 0.0)
                    .offset(y: showContent ? 0 : 10)
                    .animation(.easeInOut(duration: 0.6).delay(0.5), value: showContent)
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 28)
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
                textScale = 1.02
            }
            
            showContent = true
        }
        .shadow(
            color: .black.opacity(0.1),
            radius: 10,
            x: 0,
            y: 5
        )
    }
}


struct TimelineItemCard: View {
    let item: Item
    @State private var isPressed = false
    @State private var showContent = false
    
    var body: some View {
        HStack(spacing: 0) {
            // Left accent bar
            Rectangle()
                .fill(colorForItemType(item.itemType))
                .frame(width: 4)
                .cornerRadius(2)
            
            HStack {
                VStack(alignment: .leading, spacing: DesignSystem.Spacing.space2) {
                    // Header
                    HStack {
                        Text(item.createdAt.dayMonthFormat)
                            .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM))
                            .foregroundColor(DesignSystem.Colors.gray600)
                        
                        Spacer()
                        
                        // Animated item type icon
                        ZStack {
                            Circle()
                                .fill(colorForItemType(item.itemType).opacity(0.1))
                                .frame(width: 32, height: 32)
                            
                            itemTypeIcon
                                .scaleEffect(showContent ? 1.2 : 1.0)
                                .animation(DesignSystem.Animation.bounce, value: showContent)
                        }
                    }
                    
                    // Title with animation
                    Text(item.title)
                        .font(DesignSystem.Typography.inter(DesignSystem.Typography.textLG, weight: .semibold))
                        .foregroundColor(Color(UIColor.label))
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)
                    
                    // Content preview
                    Text(item.summary ?? item.content)
                        .font(DesignSystem.Typography.inter(DesignSystem.Typography.textBase))
                        .foregroundColor(DesignSystem.Colors.gray700)
                        .lineLimit(showContent ? nil : 2)
                        .animation(DesignSystem.Animation.smooth, value: showContent)
                    
                    // Tags with animation
                    if !item.tags.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: DesignSystem.Spacing.space2) {
                                ForEach(Array(item.tags.prefix(3)), id: \.self) { tag in
                                    TagView(tag: tag)
                                        .transition(.scale.combined(with: .opacity))
                                }
                                if item.tags.count > 3 {
                                    Text("+\(item.tags.count - 3)")
                                        .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM, weight: .medium))
                                        .foregroundColor(DesignSystem.Colors.gray600)
                                        .padding(.horizontal, DesignSystem.Spacing.space2)
                                        .padding(.vertical, DesignSystem.Spacing.space1)
                                        .background(
                                            Capsule()
                                                .fill(DesignSystem.Colors.gray100)
                                        )
                                }
                            }
                        }
                    }
                    
                    // Interaction stats
                    HStack(spacing: DesignSystem.Spacing.space4) {
                        HStack(spacing: DesignSystem.Spacing.space1) {
                            Image(systemName: "eye")
                                .font(.system(size: 12))
                            Text("\(item.accessCount)")
                                .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM))
                        }
                        .foregroundColor(DesignSystem.Colors.gray500)
                        
                        if let category = item.category {
                            HStack(spacing: DesignSystem.Spacing.space1) {
                                Image(systemName: "folder")
                                    .font(.system(size: 12))
                                Text(category)
                                    .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM))
                            }
                            .foregroundColor(DesignSystem.Colors.gray500)
                        }
                    }
                }
                
                Image(systemName: "chevron.right")
                    .font(.system(size: 14))
                    .foregroundColor(DesignSystem.Colors.gray400)
                    .rotationEffect(.degrees(isPressed ? 90 : 0))
            }
            .padding(DesignSystem.Spacing.space4)
        }
        .background(
            RoundedRectangle(cornerRadius: DesignSystem.Radius.large)
                .fill(Color(UIColor.secondarySystemBackground))
        )
        .overlay(
            RoundedRectangle(cornerRadius: DesignSystem.Radius.large)
                .stroke(isPressed ? DesignSystem.Colors.primaryRed.opacity(0.3) : Color.clear, lineWidth: 2)
        )
        .shadow(
            color: isPressed ? DesignSystem.Colors.primaryRed.opacity(0.2) : Color.black.opacity(0.05),
            radius: isPressed ? 15 : 5,
            x: 0,
            y: isPressed ? 8 : 2
        )
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .padding(.horizontal)
        .onAppear {
            withAnimation(DesignSystem.Animation.smooth.delay(0.2)) {
                showContent = true
            }
        }
        .onTapGesture {
            impact()
            withAnimation(DesignSystem.Animation.snappy) {
                isPressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                withAnimation(DesignSystem.Animation.snappy) {
                    isPressed = false
                }
            }
        }
    }
    
    @ViewBuilder
    private var itemTypeIcon: some View {
        Image(systemName: iconForItemType(item.itemType))
            .foregroundColor(colorForItemType(item.itemType))
            .font(.system(size: 16, weight: .medium))
    }
    
    private func iconForItemType(_ type: ItemType) -> String {
        switch type {
        case .video: return "play.fill"
        case .article: return "doc.text.fill"
        case .note: return "note.text"
        case .image: return "photo.fill"
        case .audio: return "waveform"
        case .document: return "doc.fill"
        case .link: return "link"
        case .other: return "questionmark.circle"
        }
    }
    
    private func colorForItemType(_ type: ItemType) -> Color {
        switch type {
        case .video: return DesignSystem.Colors.primaryRed
        case .article: return DesignSystem.Colors.info
        case .note: return DesignSystem.Colors.primaryPurple
        case .image: return DesignSystem.Colors.warning
        case .audio: return DesignSystem.Colors.primaryGreen
        case .document: return DesignSystem.Colors.gray600
        case .link: return DesignSystem.Colors.info
        case .other: return DesignSystem.Colors.gray500
        }
    }
    
    private func impact() {
        let impactFeedback = UIImpactFeedbackGenerator(style: .light)
        impactFeedback.impactOccurred()
    }
}

struct FilterPill: View {
    let title: String
    let isSelected: Bool
    
    var body: some View {
        Text(title)
            .font(DesignSystem.Typography.inter(DesignSystem.Typography.textSM, weight: .medium))
            .foregroundColor(isSelected ? .white : DesignSystem.Colors.gray700)
            .padding(.horizontal, DesignSystem.Spacing.space3)
            .padding(.vertical, DesignSystem.Spacing.space2)
            .background(
                Capsule()
                    .fill(isSelected ? DesignSystem.Colors.primaryRed : DesignSystem.Colors.gray100)
            )
            .overlay(
                Capsule()
                    .stroke(isSelected ? Color.clear : DesignSystem.Colors.gray200, lineWidth: 1)
            )
    }
}

// MARK: - Extensions
extension Date {
    var relative: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: self, relativeTo: Date())
    }
    
    var dayMonthFormat: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d"
        return formatter.string(from: self)
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