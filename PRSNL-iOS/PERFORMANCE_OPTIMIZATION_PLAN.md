# PRSNL iOS: Performance Optimization Plan

This document outlines a comprehensive performance optimization strategy for the PRSNL iOS app, focusing on responsiveness, resource efficiency, and battery conservation.

## 1. Performance Audit

Before implementing optimizations, we should conduct a thorough performance audit using Xcode's Instruments to identify bottlenecks:

### 1.1 Areas to Profile

- **CPU Usage**: Identify methods consuming excessive CPU time
- **Memory Allocations**: Detect memory leaks and excessive allocations
- **Energy Impact**: Measure battery consumption
- **Network Activity**: Analyze API call patterns and response times
- **UI Rendering**: Identify slow rendering and scrolling performance
- **Disk I/O**: Measure Core Data read/write operations
- **App Launch Time**: Measure cold and warm start times

### 1.2 Audit Process

1. Profile app in both online and offline modes
2. Test with various dataset sizes (empty, moderate, large)
3. Focus on high-traffic screens (Timeline, Search, Capture)
4. Measure performance on different device models
5. Document baseline metrics for comparison

## 2. Core Data Optimizations

### 2.1 Fetch Request Efficiency

```swift
// OPTIMIZE: Replace this inefficient fetch
let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
fetchRequest.predicate = NSPredicate(format: "title CONTAINS[cd] %@", searchText)
let allItems = try context.fetch(fetchRequest)

// WITH: More efficient fetch with batch size and properties
let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
fetchRequest.predicate = NSPredicate(format: "title CONTAINS[cd] %@", searchText)
fetchRequest.fetchBatchSize = 20
fetchRequest.propertiesToFetch = ["id", "title", "content", "updatedAt"]
fetchRequest.sortDescriptors = [NSSortDescriptor(key: "updatedAt", ascending: false)]
```

### 2.2 Background Context Processing

```swift
// IMPLEMENT: Process batches in background context
func processBatchOperation(items: [Item]) {
    persistentContainer.performBackgroundTask { context in
        // Process items in background
        for item in items {
            let cdItem = CDItem(context: context)
            cdItem.id = item.id
            cdItem.title = item.title
            cdItem.content = item.content
            // ... other properties
        }
        
        try? context.save()
        
        // Notify main context of changes
        DispatchQueue.main.async {
            self.viewContext.refreshAllObjects()
            NotificationCenter.default.post(name: .CoreDataDidSaveRemoteChanges, object: nil)
        }
    }
}
```

### 2.3 Denormalization for Common Queries

```swift
// ADD: Search optimization fields
entity.addAttribute(NSAttributeDescription().with {
    $0.name = "searchableContent"
    $0.attributeType = .stringAttributeType
    $0.isOptional = true
})

// UPDATE: Maintain denormalized field
func updateSearchableContent(for item: CDItem) {
    // Combine frequently searched fields
    let searchContent = [
        item.title ?? "",
        item.content ?? "",
        (item.tags?.allObjects as? [CDTag])?.compactMap { $0.name }.joined(separator: " ") ?? ""
    ].joined(separator: " ").lowercased()
    
    item.searchableContent = searchContent
}
```

### 2.4 Indexing

```swift
// ADD: Core Data indexes for frequently queried attributes
// In CoreDataManager.swift

let titleIndex = NSFetchIndexDescription(name: "titleIndex", elements: [
    NSFetchIndexElementDescription(property: entity.propertiesByName["title"]!, collationType: .binary)
])

let searchableContentIndex = NSFetchIndexDescription(name: "searchableContentIndex", elements: [
    NSFetchIndexElementDescription(property: entity.propertiesByName["searchableContent"]!, collationType: .binary)
])

entity.indexes = [titleIndex, searchableContentIndex]
```

## 3. Image and Memory Management

### 3.1 Image Resizing and Caching

```swift
// IMPLEMENT: Efficient image loading with resizing
class ImageLoader {
    static let shared = ImageLoader()
    private let cache = NSCache<NSString, UIImage>()
    
    func loadImage(from url: URL, targetSize: CGSize? = nil) async throws -> UIImage {
        let key = url.absoluteString as NSString
        
        // Check cache first
        if let cachedImage = cache.object(forKey: key) {
            return cachedImage
        }
        
        // Download image
        let (data, _) = try await URLSession.shared.data(from: url)
        guard let originalImage = UIImage(data: data) else {
            throw NSError(domain: "ImageLoader", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid image data"])
        }
        
        // Resize if needed
        let finalImage: UIImage
        if let targetSize = targetSize {
            finalImage = originalImage.resized(to: targetSize)
        } else {
            finalImage = originalImage
        }
        
        // Cache the result
        cache.setObject(finalImage, forKey: key)
        
        return finalImage
    }
}

// UIImage extension for resizing
extension UIImage {
    func resized(to targetSize: CGSize) -> UIImage {
        let renderer = UIGraphicsImageRenderer(size: targetSize)
        return renderer.image { _ in
            self.draw(in: CGRect(origin: .zero, size: targetSize))
        }
    }
}
```

### 3.2 Cell Recycling Optimization

```swift
// IMPLEMENT: Better SwiftUI List recycling
struct OptimizedItemRow: View {
    let item: Item
    @State private var image: UIImage?
    @State private var isLoadingImage = false
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(item.title)
                    .font(.headline)
                Text(item.content.prefix(100))
                    .font(.subheadline)
                    .lineLimit(2)
            }
            
            if let image = image {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 60, height: 60)
                    .clipShape(RoundedRectangle(cornerRadius: 6))
            } else if let imageUrl = item.thumbnailUrl, !isLoadingImage {
                Color.gray.opacity(0.3)
                    .frame(width: 60, height: 60)
                    .clipShape(RoundedRectangle(cornerRadius: 6))
                    .onAppear {
                        loadImage(from: imageUrl)
                    }
            }
        }
        .onDisappear {
            // Cancel any pending image loads when cell disappears
            image = nil
            isLoadingImage = false
        }
    }
    
    private func loadImage(from urlString: String) {
        guard let url = URL(string: urlString) else { return }
        
        isLoadingImage = true
        
        Task {
            do {
                let loadedImage = try await ImageLoader.shared.loadImage(from: url, targetSize: CGSize(width: 120, height: 120))
                if !Task.isCancelled {
                    await MainActor.run {
                        image = loadedImage
                        isLoadingImage = false
                    }
                }
            } catch {
                isLoadingImage = false
            }
        }
    }
}
```

### 3.3 Memory Warnings Handling

```swift
// IMPLEMENT: App-wide memory warning handling
// In PRSNLApp.swift

@main
struct PRSNLApp: App {
    // Existing code...
    
    init() {
        setupMemoryWarningObserver()
    }
    
    private func setupMemoryWarningObserver() {
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { _ in
            handleMemoryWarning()
        }
    }
    
    private func handleMemoryWarning() {
        // Clear image caches
        ImageLoader.shared.clearCache()
        
        // Release any unnecessary viewmodels
        // This would require a coordinator pattern or similar
        
        // Reset any large data structures not currently in view
    }
}
```

## 4. Network Optimization

### 4.1 Request Batching

```swift
// IMPLEMENT: Batch API requests for multiple items
func syncMultipleItems(_ items: [Item]) async throws {
    // Divide items into batches of 10
    let batches = items.chunked(into: 10)
    
    for batch in batches {
        // Create a batch request
        let batchRequest = BatchRequest(items: batch)
        
        // Send as a single API call
        try await APIClient.shared.performBatchOperation(batchRequest)
        
        // Update local status
        for item in batch {
            try await CoreDataManager.shared.markItemAsSynced(id: item.id)
        }
    }
}

// Array extension for chunking
extension Array {
    func chunked(into size: Int) -> [[Element]] {
        return stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
}
```

### 4.2 Incremental Loading

```swift
// IMPLEMENT: Incremental Timeline loading
func loadTimelineIncrementally() {
    let pageSize = 20
    var currentPage = 1
    var isLoading = false
    var hasMoreItems = true
    
    func loadNextPageIfNeeded(currentIndex: Int) {
        let thresholdIndex = items.count - 5
        
        if currentIndex >= thresholdIndex && !isLoading && hasMoreItems {
            loadNextPage()
        }
    }
    
    func loadNextPage() {
        guard !isLoading && hasMoreItems else { return }
        
        isLoading = true
        
        Task {
            do {
                let response = try await APIClient.shared.fetchTimeline(page: currentPage, limit: pageSize)
                await MainActor.run {
                    items.append(contentsOf: response.items)
                    hasMoreItems = response.items.count == pageSize
                    currentPage += 1
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                }
            }
        }
    }
}
```

### 4.3 Response Compression

```swift
// IMPLEMENT: API client with compression support
func configureURLSession() -> URLSession {
    let config = URLSessionConfiguration.default
    
    // Accept compressed responses
    config.httpAdditionalHeaders = [
        "Accept-Encoding": "gzip, deflate"
    ]
    
    // Optimize cache policy
    config.requestCachePolicy = .useProtocolCachePolicy
    
    // Configure timeout
    config.timeoutIntervalForRequest = 30
    
    return URLSession(configuration: config)
}
```

### 4.4 Connection Quality Adaptation

```swift
// IMPLEMENT: Network quality-based fetching
enum NetworkQuality {
    case poor
    case moderate
    case good
    case excellent
    
    var maxConcurrentOperations: Int {
        switch self {
        case .poor: return 1
        case .moderate: return 2
        case .good: return 4
        case .excellent: return 6
        }
    }
    
    var imageFetchQuality: CGFloat {
        switch self {
        case .poor: return 0.3
        case .moderate: return 0.5
        case .good: return 0.7
        case .excellent: return 1.0
        }
    }
}

class NetworkQualityMonitor {
    static let shared = NetworkQualityMonitor()
    
    private(set) var currentQuality: NetworkQuality = .good
    
    func startMonitoring() {
        // Use NWPathMonitor to determine connection type
        // Use URLSession metrics to assess actual throughput
        // Combine with analysis of recent request durations
    }
    
    func adaptRequestsToQuality() {
        // Adjust concurrent operations based on quality
        APIClient.shared.maxConcurrentOperations = currentQuality.maxConcurrentOperations
        
        // Adjust image quality based on connection
        ImageLoader.shared.defaultCompressionQuality = currentQuality.imageFetchQuality
    }
}
```

## 5. UI Optimization

### 5.1 Lazy View Loading

```swift
// IMPLEMENT: Load views only when needed
struct LazyLoadingView<Content: View>: View {
    let content: () -> Content
    @State private var loadedView: Content?
    
    var body: some View {
        if let loadedView = loadedView {
            loadedView
        } else {
            Color.clear
                .onAppear {
                    loadedView = content()
                }
        }
    }
}

// USAGE:
ScrollView {
    VStack {
        // Always render the first few items immediately
        ForEach(items.prefix(3)) { item in
            ItemRowView(item: item)
        }
        
        // Lazy load the rest
        ForEach(items.dropFirst(3)) { item in
            LazyLoadingView {
                ItemRowView(item: item)
            }
        }
    }
}
```

### 5.2 Precomputed Values and Diffing

```swift
// IMPLEMENT: Efficient list updates with diffing
struct TimelineView: View {
    @StateObject private var viewModel = TimelineViewModel()
    
    var body: some View {
        List {
            ForEach(viewModel.itemViewModels) { itemViewModel in
                ItemRowView(viewModel: itemViewModel)
            }
        }
        .onAppear {
            viewModel.loadTimeline()
        }
    }
}

class TimelineViewModel: ObservableObject {
    @Published private(set) var items: [Item] = []
    @Published private(set) var itemViewModels: [ItemRowViewModel] = []
    
    func loadTimeline() {
        Task {
            do {
                let newItems = try await APIClient.shared.fetchTimeline().items
                
                // Apply diffing to minimize UI updates
                let changes = diff(oldItems: self.items, newItems: newItems)
                
                await MainActor.run {
                    // Update viewModels based on changes
                    applyChanges(changes)
                }
            } catch {
                // Handle error
            }
        }
    }
    
    private func diff(oldItems: [Item], newItems: [Item]) -> [Change] {
        // Calculate minimum set of changes needed
        // Return insertions, deletions, and moves
    }
    
    private func applyChanges(_ changes: [Change]) {
        // Apply only the necessary changes to itemViewModels
        // This minimizes view redraws
    }
}
```

### 5.3 Background Processing

```swift
// IMPLEMENT: Process data in background
func updateItemsInBackground() {
    let items = self.items // Capture current state
    
    // Process in background
    DispatchQueue.global(qos: .userInitiated).async {
        // Do expensive processing
        let processedData = self.processItems(items)
        
        // Update UI on main thread
        DispatchQueue.main.async {
            self.displayProcessedData(processedData)
        }
    }
}
```

## 6. Launch Time Optimization

### 6.1 Delayed Initialization

```swift
// IMPLEMENT: Progressive app initialization
class AppCoordinator {
    func setupApp() {
        // Immediate setup (required for app to function)
        setupCoreComponents()
        
        // Delayed setup (after UI appears)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.setupSecondaryComponents()
        }
        
        // Background setup (non-critical)
        DispatchQueue.global(qos: .utility).async {
            self.setupBackgroundComponents()
            
            // Update main thread when done
            DispatchQueue.main.async {
                self.notifySetupComplete()
            }
        }
    }
    
    private func setupCoreComponents() {
        // Set up Core Data stack
        // Initialize API client
        // Configure UI appearance
    }
    
    private func setupSecondaryComponents() {
        // Set up offline sync
        // Initialize caches
        // Configure WebSocket
    }
    
    private func setupBackgroundComponents() {
        // Prefetch common resources
        // Set up analytics
        // Initialize non-critical services
    }
}
```

### 6.2 Asset Optimization

- Use asset catalogs with appropriate compression
- Apply app thinning to reduce app size
- Use on-demand resources for rarely used assets
- Implement progressive loading for large images

## 7. Testing and Validation

### 7.1 Performance Testing Framework

Create automated performance tests:

```swift
// IMPLEMENT: Performance test for timeline loading
func testTimelineLoadingPerformance() {
    measure(metrics: [XCTCPUMetric(), XCTMemoryMetric(), XCTStorageMetric(), XCTClockMetric()]) {
        // Setup test environment
        let viewModel = TimelineViewModel()
        let expectation = XCTestExpectation(description: "Timeline loaded")
        
        // Perform the operation
        viewModel.loadTimeline {
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 10.0)
    }
}
```

### 7.2 Continuous Monitoring

- Add analytics to track key performance metrics in production
- Implement crash and performance reporting
- Set up automated alerts for performance regressions

## 8. Implementation Strategy

### Phase 1: Immediate Optimizations
1. Implement image resizing and caching
2. Add fetch request optimizations (batch size, property selection)
3. Optimize UI recycling and lazy loading
4. Add memory warning handlers

### Phase 2: Architecture Improvements
1. Implement background processing for expensive operations
2. Add incremental loading for lists
3. Create the diffing system for efficient updates
4. Optimize launch sequence

### Phase 3: Advanced Optimizations
1. Add network quality adaptation
2. Implement request batching
3. Create more sophisticated caching strategies
4. Set up performance monitoring

## 9. Success Metrics

- **Timeline Performance**: <500ms to load initial items
- **Memory Usage**: <100MB under normal usage
- **App Launch**: <2 seconds cold start, <1 second warm start
- **Battery Impact**: Low to moderate energy impact in Instruments
- **Scroll Performance**: 60 FPS when scrolling lists
- **Network Efficiency**: <1MB data transfer for 50 items
- **Offline Sync**: <5 seconds to synchronize 20 changes

Each optimization should be measured against these baselines to ensure actual improvement.