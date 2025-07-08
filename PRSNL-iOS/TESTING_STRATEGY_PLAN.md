# PRSNL iOS: Testing Strategy Plan

This document outlines a comprehensive testing strategy for the PRSNL iOS app, ensuring functionality, performance, and reliability across various conditions and scenarios.

## 1. Testing Levels

### 1.1 Unit Testing

Unit tests verify individual components in isolation, focusing on business logic and data transformations.

```swift
// IMPLEMENT: Unit test for ItemModel validation
final class ItemModelTests: XCTestCase {
    
    func testItemValidation() {
        // Test valid item
        let validItem = Item(
            id: "test-id-123",
            title: "Valid Title",
            content: "This is valid content for testing",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        XCTAssertTrue(validItem.isValid, "Valid item should pass validation")
        
        // Test invalid title
        var invalidItem = validItem
        invalidItem.title = ""
        XCTAssertFalse(invalidItem.isValid, "Item with empty title should fail validation")
        
        // Test invalid content
        invalidItem = validItem
        invalidItem.content = ""
        XCTAssertFalse(invalidItem.isValid, "Item with empty content should fail validation")
        
        // Test invalid ID
        invalidItem = validItem
        invalidItem.id = ""
        XCTAssertFalse(invalidItem.isValid, "Item with empty ID should fail validation")
    }
    
    func testItemCreation() {
        // Test item creation with required fields
        let item = Item.create(
            title: "New Item",
            content: "This is the content"
        )
        
        // Verify non-empty ID was generated
        XCTAssertFalse(item.id.isEmpty, "Item should have non-empty ID")
        
        // Verify dates were set
        XCTAssertNotNil(item.createdAt, "Created date should be set")
        XCTAssertNotNil(item.updatedAt, "Updated date should be set")
        
        // Verify properties were set correctly
        XCTAssertEqual(item.title, "New Item")
        XCTAssertEqual(item.content, "This is the content")
    }
}

// IMPLEMENT: Unit test for APIClient
final class APIClientTests: XCTestCase {
    var apiClient: APIClient!
    var mockSession: MockURLSession!
    
    override func setUp() {
        super.setUp()
        mockSession = MockURLSession()
        apiClient = APIClient(session: mockSession)
    }
    
    override func tearDown() {
        apiClient = nil
        mockSession = nil
        super.tearDown()
    }
    
    func testFetchTimelineSuccess() async {
        // Setup mock response
        let mockItems = [
            Item(id: "1", title: "Item 1", content: "Content 1", createdAt: Date(), updatedAt: Date()),
            Item(id: "2", title: "Item 2", content: "Content 2", createdAt: Date(), updatedAt: Date())
        ]
        
        let mockResponse = TimelineResponse(items: mockItems, page: 1, total: 2)
        let jsonData = try! JSONEncoder().encode(mockResponse)
        
        // Configure mock session
        mockSession.mockResponse = (jsonData, HTTPURLResponse(url: URL(string: "https://api.prsnl.com/timeline")!, statusCode: 200, httpVersion: nil, headerFields: nil)!, nil)
        
        do {
            // Call the method
            let response = try await apiClient.fetchTimeline(page: 1, limit: 10)
            
            // Verify results
            XCTAssertEqual(response.items.count, 2)
            XCTAssertEqual(response.items[0].id, "1")
            XCTAssertEqual(response.items[1].id, "2")
            XCTAssertEqual(response.page, 1)
            XCTAssertEqual(response.total, 2)
            
            // Verify request was properly formed
            XCTAssertEqual(mockSession.lastURL?.absoluteString, "https://api.prsnl.com/timeline?page=1&limit=10")
            XCTAssertEqual(mockSession.lastRequest?.httpMethod, "GET")
            
        } catch {
            XCTFail("Request should not fail: \(error)")
        }
    }
    
    func testFetchTimelineNetworkError() async {
        // Configure mock session with error
        let error = NSError(domain: NSURLErrorDomain, code: NSURLErrorNotConnectedToInternet, userInfo: nil)
        mockSession.mockResponse = (nil, HTTPURLResponse(url: URL(string: "https://api.prsnl.com/timeline")!, statusCode: 0, httpVersion: nil, headerFields: nil)!, error)
        
        do {
            // Call the method
            _ = try await apiClient.fetchTimeline(page: 1, limit: 10)
            XCTFail("Request should fail with network error")
        } catch let apiError as APIError {
            // Verify correct error type
            XCTAssertEqual(apiError, APIError.networkError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
}

// IMPLEMENT: Mock URLSession for testing
class MockURLSession: URLSessionProtocol {
    var mockResponse: (Data?, URLResponse, Error?)
    var lastURL: URL?
    var lastRequest: URLRequest?
    
    init() {
        mockResponse = (nil, URLResponse(), nil)
    }
    
    func data(from url: URL) async throws -> (Data, URLResponse) {
        lastURL = url
        
        if let error = mockResponse.2 {
            throw error
        }
        
        return (mockResponse.0 ?? Data(), mockResponse.1)
    }
    
    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        lastURL = request.url
        lastRequest = request
        
        if let error = mockResponse.2 {
            throw error
        }
        
        return (mockResponse.0 ?? Data(), mockResponse.1)
    }
}

// IMPLEMENT: Protocol for URLSession to enable mocking
protocol URLSessionProtocol {
    func data(from url: URL) async throws -> (Data, URLResponse)
    func data(for request: URLRequest) async throws -> (Data, URLResponse)
}

// Extension to make URLSession conform to protocol
extension URLSession: URLSessionProtocol {}
```

### 1.2 Integration Testing

Integration tests verify interactions between components, focusing on data flow between modules.

```swift
// IMPLEMENT: Integration test for CoreDataManager and API client synchronization
final class SyncIntegrationTests: XCTestCase {
    var coreDataManager: CoreDataManager!
    var apiClient: APIClient!
    var syncManager: SyncManager!
    var mockSession: MockURLSession!
    
    override func setUp() {
        super.setUp()
        
        // Setup in-memory Core Data stack for testing
        coreDataManager = CoreDataManager(inMemory: true)
        
        // Setup mock API client
        mockSession = MockURLSession()
        apiClient = APIClient(session: mockSession)
        
        // Setup sync manager with dependencies
        syncManager = SyncManager(apiClient: apiClient, coreDataManager: coreDataManager)
    }
    
    override func tearDown() {
        coreDataManager = nil
        apiClient = nil
        syncManager = nil
        mockSession = nil
        super.tearDown()
    }
    
    func testSyncItemsFromAPIToDatabase() async throws {
        // 1. Setup mock API response with items
        let mockItems = [
            Item(id: "sync-1", title: "Sync Item 1", content: "Content 1", createdAt: Date(), updatedAt: Date()),
            Item(id: "sync-2", title: "Sync Item 2", content: "Content 2", createdAt: Date(), updatedAt: Date())
        ]
        
        let mockResponse = TimelineResponse(items: mockItems, page: 1, total: 2)
        let jsonData = try JSONEncoder().encode(mockResponse)
        
        mockSession.mockResponse = (jsonData, HTTPURLResponse(url: URL(string: "https://api.prsnl.com/timeline")!, statusCode: 200, httpVersion: nil, headerFields: nil)!, nil)
        
        // 2. Call sync method
        try await syncManager.syncItemsFromAPI()
        
        // 3. Verify items were saved to database
        let savedItems = try coreDataManager.fetchAllItems()
        
        XCTAssertEqual(savedItems.count, 2)
        XCTAssertTrue(savedItems.contains(where: { $0.id == "sync-1" && $0.title == "Sync Item 1" }))
        XCTAssertTrue(savedItems.contains(where: { $0.id == "sync-2" && $0.title == "Sync Item 2" }))
    }
    
    func testSyncLocalChangesToAPI() async throws {
        // 1. Create local items marked for sync
        let context = coreDataManager.viewContext
        
        let localItem1 = CDItem(context: context)
        localItem1.id = "local-1"
        localItem1.title = "Local Item 1"
        localItem1.content = "Local Content 1"
        localItem1.createdAt = Date()
        localItem1.updatedAt = Date()
        localItem1.needsSync = true
        
        let localItem2 = CDItem(context: context)
        localItem2.id = "local-2"
        localItem2.title = "Local Item 2"
        localItem2.content = "Local Content 2"
        localItem2.createdAt = Date()
        localItem2.updatedAt = Date()
        localItem2.needsSync = true
        
        try context.save()
        
        // 2. Setup mock responses for each item
        let successResponse = ["status": "success"]
        let jsonData = try JSONEncoder().encode(successResponse)
        mockSession.mockResponse = (jsonData, HTTPURLResponse(url: URL(string: "https://api.prsnl.com/items")!, statusCode: 200, httpVersion: nil, headerFields: nil)!, nil)
        
        // 3. Call sync method
        try await syncManager.syncLocalChangesToAPI()
        
        // 4. Verify items were marked as synced
        let savedItems = try coreDataManager.fetchAllItems()
        
        XCTAssertEqual(savedItems.count, 2)
        XCTAssertFalse(savedItems[0].needsSync)
        XCTAssertFalse(savedItems[1].needsSync)
        
        // 5. Verify API requests were made
        XCTAssertTrue(mockSession.lastURL?.absoluteString.contains("/items") ?? false)
    }
}
```

### 1.3 UI Testing

UI tests verify the app's user interface and interactions, focusing on user flows and visual elements.

```swift
// IMPLEMENT: UI tests for timeline screen
final class TimelineUITests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        
        app = XCUIApplication()
        app.launchArguments = ["UI-TESTING"]
        app.launchEnvironment = ["ENV": "TEST"]
        app.launch()
    }
    
    func testTimelineDisplay() {
        // Verify timeline screen loads
        XCTAssertTrue(app.navigationBars["Timeline"].exists)
        
        // Verify items are displayed
        XCTAssertTrue(app.cells.count > 0, "Timeline should display items")
        
        // Verify first item has expected elements
        let firstCell = app.cells.element(boundBy: 0)
        XCTAssertTrue(firstCell.staticTexts.element(matching: .any, identifier: "item-title").exists)
        XCTAssertTrue(firstCell.staticTexts.element(matching: .any, identifier: "item-date").exists)
    }
    
    func testItemSelection() {
        // Select the first item
        let firstCell = app.cells.element(boundBy: 0)
        let title = firstCell.staticTexts.element(matching: .any, identifier: "item-title").label
        
        firstCell.tap()
        
        // Verify detail screen appears with correct title
        XCTAssertTrue(app.navigationBars.staticTexts[title].exists)
        XCTAssertTrue(app.staticTexts["item-content"].exists)
    }
    
    func testPullToRefresh() {
        // Get initial item count
        let initialItemCount = app.cells.count
        
        // Perform pull-to-refresh gesture
        let timeline = app.collectionViews["timeline-list"]
        let start = timeline.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
        let end = timeline.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.8))
        start.press(forDuration: 0.1, thenDragTo: end)
        
        // Wait for refresh to complete
        let loadingIndicator = app.activityIndicators["loading-indicator"]
        let exists = NSPredicate(format: "exists == false")
        expectation(for: exists, evaluatedWith: loadingIndicator, handler: nil)
        waitForExpectations(timeout: 5, handler: nil)
        
        // Verify items were refreshed
        XCTAssertEqual(app.cells.count, initialItemCount, "Item count should remain the same after refresh")
    }
    
    func testSearch() {
        // Tap search button
        app.buttons["search-button"].tap()
        
        // Verify search screen appears
        XCTAssertTrue(app.navigationBars["Search"].exists)
        
        // Enter search text
        let searchField = app.searchFields.firstMatch
        searchField.tap()
        searchField.typeText("test")
        
        // Wait for search results
        let loadingIndicator = app.activityIndicators["search-loading-indicator"]
        let exists = NSPredicate(format: "exists == false")
        expectation(for: exists, evaluatedWith: loadingIndicator, handler: nil)
        waitForExpectations(timeout: 5, handler: nil)
        
        // Verify search results appear
        XCTAssertTrue(app.cells.count >= 0, "Search should display results or empty state")
    }
}
```

### 1.4 End-to-End Testing

End-to-end tests verify complete user flows across the app, focusing on real-world scenarios.

```swift
// IMPLEMENT: End-to-end test for creating, editing, and deleting an item
final class ItemLifecycleTests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        
        app = XCUIApplication()
        app.launchArguments = ["UI-TESTING", "RESET-DATABASE"]
        app.launch()
    }
    
    func testItemLifecycle() {
        // 1. Create a new item
        app.buttons["create-item-button"].tap()
        
        let titleField = app.textFields["title-field"]
        let contentField = app.textViews["content-field"]
        
        // Enter item details
        titleField.tap()
        titleField.typeText("E2E Test Item")
        
        contentField.tap()
        contentField.typeText("This is a test item created during E2E testing")
        
        // Save the item
        app.buttons["save-button"].tap()
        
        // Verify we return to timeline
        XCTAssertTrue(app.navigationBars["Timeline"].waitForExistence(timeout: 2))
        
        // Verify new item appears in the list
        XCTAssertTrue(app.staticTexts["E2E Test Item"].exists)
        
        // 2. Edit the item
        app.staticTexts["E2E Test Item"].tap()
        
        // Verify detail view loads
        XCTAssertTrue(app.navigationBars["Item Details"].waitForExistence(timeout: 2))
        
        // Tap edit button
        app.buttons["edit-button"].tap()
        
        // Modify content
        let editContentField = app.textViews["content-field"]
        editContentField.tap()
        
        // Clear and enter new text
        editContentField.press(forDuration: 1.0)
        app.menuItems["Select All"].tap()
        app.menuItems["Cut"].tap()
        editContentField.typeText("This content has been updated during E2E testing")
        
        // Save changes
        app.buttons["save-button"].tap()
        
        // Verify updated content appears
        XCTAssertTrue(app.staticTexts["This content has been updated during E2E testing"].exists)
        
        // 3. Delete the item
        app.buttons["more-options-button"].tap()
        app.buttons["delete-button"].tap()
        
        // Confirm deletion
        app.alerts["Confirm Deletion"].buttons["Delete"].tap()
        
        // Verify we return to timeline
        XCTAssertTrue(app.navigationBars["Timeline"].waitForExistence(timeout: 2))
        
        // Verify item no longer appears
        XCTAssertFalse(app.staticTexts["E2E Test Item"].exists)
    }
}
```

## 2. Test Types

### 2.1 Functional Testing

```swift
// IMPLEMENT: Test for search functionality
final class SearchFunctionalTests: XCTestCase {
    var viewModel: SearchViewModel!
    var mockAPIClient: MockAPIClient!
    
    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        viewModel = SearchViewModel(apiClient: mockAPIClient)
    }
    
    override func tearDown() {
        viewModel = nil
        mockAPIClient = nil
        super.tearDown()
    }
    
    func testSearchWithResults() async {
        // Setup mock results
        let mockItems = [
            Item(id: "search-1", title: "Test Item", content: "This contains test keyword", createdAt: Date(), updatedAt: Date()),
            Item(id: "search-2", title: "Another Test", content: "More test content", createdAt: Date(), updatedAt: Date())
        ]
        
        mockAPIClient.searchResults = mockItems
        
        // Perform search
        await viewModel.search(query: "test")
        
        // Verify results
        XCTAssertEqual(viewModel.searchResults.count, 2)
        XCTAssertEqual(viewModel.searchResults[0].id, "search-1")
        XCTAssertEqual(viewModel.searchResults[1].id, "search-2")
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.error)
    }
    
    func testSearchWithNoResults() async {
        // Setup empty results
        mockAPIClient.searchResults = []
        
        // Perform search
        await viewModel.search(query: "nonexistent")
        
        // Verify results
        XCTAssertTrue(viewModel.searchResults.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.error)
    }
    
    func testSearchWithError() async {
        // Setup error
        mockAPIClient.shouldReturnError = true
        mockAPIClient.mockError = APIError.networkError
        
        // Perform search
        await viewModel.search(query: "test")
        
        // Verify error state
        XCTAssertTrue(viewModel.searchResults.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNotNil(viewModel.error)
        if case .networkError = viewModel.error as? APIError {
            // Expected error
        } else {
            XCTFail("Unexpected error type")
        }
    }
}

// Mock API client for testing
class MockAPIClient: APIClientProtocol {
    var searchResults: [Item] = []
    var shouldReturnError = false
    var mockError: Error = APIError.unknown(NSError(domain: "test", code: 0))
    
    func search(query: String, page: Int, limit: Int) async throws -> SearchResponse {
        if shouldReturnError {
            throw mockError
        }
        return SearchResponse(items: searchResults, page: page, total: searchResults.count)
    }
    
    // Implement other required methods...
    func fetchTimeline(page: Int, limit: Int) async throws -> TimelineResponse {
        if shouldReturnError {
            throw mockError
        }
        return TimelineResponse(items: [], page: page, total: 0)
    }
    
    func fetchItem(id: String) async throws -> Item {
        if shouldReturnError {
            throw mockError
        }
        return Item(id: id, title: "Mock Item", content: "Mock content", createdAt: Date(), updatedAt: Date())
    }
}
```

### 2.2 Performance Testing

```swift
// IMPLEMENT: Performance test for database operations
final class DatabasePerformanceTests: XCTestCase {
    var coreDataManager: CoreDataManager!
    
    override func setUp() {
        super.setUp()
        coreDataManager = CoreDataManager(inMemory: true)
    }
    
    override func tearDown() {
        coreDataManager = nil
        super.tearDown()
    }
    
    func testBulkInsertPerformance() throws {
        // Create test data
        func createTestItems(count: Int) -> [Item] {
            return (0..<count).map { i in
                Item(
                    id: "perf-\(i)",
                    title: "Performance Test Item \(i)",
                    content: "This is test content for performance testing with a reasonable amount of text to simulate a real-world scenario with item \(i).",
                    createdAt: Date(),
                    updatedAt: Date()
                )
            }
        }
        
        // Test insertion of 100 items
        let items = createTestItems(count: 100)
        
        measure {
            // Insert all items
            let expectation = XCTestExpectation(description: "Bulk insert")
            
            Task {
                do {
                    try await coreDataManager.saveItems(items)
                    expectation.fulfill()
                } catch {
                    XCTFail("Failed to save items: \(error)")
                }
            }
            
            wait(for: [expectation], timeout: 10.0)
        }
    }
    
    func testBulkFetchPerformance() throws {
        // First, insert a large number of items
        let context = coreDataManager.viewContext
        
        for i in 0..<500 {
            let item = CDItem(context: context)
            item.id = "perf-\(i)"
            item.title = "Performance Test Item \(i)"
            item.content = "This is test content for performance testing with a reasonable amount of text to simulate a real-world scenario with item \(i)."
            item.createdAt = Date()
            item.updatedAt = Date()
        }
        
        try context.save()
        
        // Measure fetch performance
        measure {
            let expectation = XCTestExpectation(description: "Bulk fetch")
            
            Task {
                do {
                    let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
                    let items = try context.fetch(fetchRequest)
                    XCTAssertEqual(items.count, 500)
                    expectation.fulfill()
                } catch {
                    XCTFail("Failed to fetch items: \(error)")
                }
            }
            
            wait(for: [expectation], timeout: 10.0)
        }
    }
    
    func testPaginatedFetchPerformance() throws {
        // First, insert a large number of items
        let context = coreDataManager.viewContext
        
        for i in 0..<1000 {
            let item = CDItem(context: context)
            item.id = "perf-\(i)"
            item.title = "Performance Test Item \(i)"
            item.content = "This is test content for performance testing with a reasonable amount of text to simulate a real-world scenario with item \(i)."
            item.createdAt = Date()
            item.updatedAt = Date().addingTimeInterval(Double(i))  // Ensure sorted order
        }
        
        try context.save()
        
        // Measure paginated fetch performance
        measure {
            let expectation = XCTestExpectation(description: "Paginated fetch")
            
            Task {
                do {
                    // Simulate paginated fetches like timeline would use
                    let pageSize = 20
                    var page = 1
                    var allItems: [CDItem] = []
                    
                    while true {
                        let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
                        fetchRequest.fetchLimit = pageSize
                        fetchRequest.fetchOffset = (page - 1) * pageSize
                        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "updatedAt", ascending: false)]
                        
                        let items = try context.fetch(fetchRequest)
                        if items.isEmpty {
                            break
                        }
                        
                        allItems.append(contentsOf: items)
                        page += 1
                        
                        // Limit to first 5 pages for the test
                        if page > 5 {
                            break
                        }
                    }
                    
                    XCTAssertEqual(allItems.count, min(1000, pageSize * 5))
                    expectation.fulfill()
                } catch {
                    XCTFail("Failed to fetch items: \(error)")
                }
            }
            
            wait(for: [expectation], timeout: 10.0)
        }
    }
}
```

### 2.3 Offline Capability Testing

```swift
// IMPLEMENT: Tests for offline functionality
final class OfflineCapabilityTests: XCTestCase {
    var coreDataManager: CoreDataManager!
    var mockAPIClient: MockAPIClient!
    var syncManager: SyncManager!
    var networkMonitor: MockNetworkMonitor!
    
    override func setUp() {
        super.setUp()
        coreDataManager = CoreDataManager(inMemory: true)
        mockAPIClient = MockAPIClient()
        networkMonitor = MockNetworkMonitor()
        syncManager = SyncManager(
            apiClient: mockAPIClient,
            coreDataManager: coreDataManager,
            networkMonitor: networkMonitor
        )
    }
    
    override func tearDown() {
        coreDataManager = nil
        mockAPIClient = nil
        syncManager = nil
        networkMonitor = nil
        super.tearDown()
    }
    
    func testOfflineItemCreation() async throws {
        // 1. Simulate going offline
        networkMonitor.isConnected = false
        
        // 2. Create an item while offline
        let newItem = Item(
            id: UUID().uuidString,
            title: "Offline Item",
            content: "Created while offline",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        // 3. Save to local database
        try await coreDataManager.saveItem(newItem)
        
        // 4. Verify item is saved locally and marked for sync
        let savedItems = try coreDataManager.fetchAllItems()
        XCTAssertEqual(savedItems.count, 1)
        XCTAssertEqual(savedItems[0].title, "Offline Item")
        XCTAssertTrue(savedItems[0].needsSync)
        
        // 5. Simulate coming back online
        networkMonitor.isConnected = true
        
        // 6. Trigger sync
        try await syncManager.syncLocalChangesToAPI()
        
        // 7. Verify item was synced
        let syncedItems = try coreDataManager.fetchAllItems()
        XCTAssertEqual(syncedItems.count, 1)
        XCTAssertFalse(syncedItems[0].needsSync)
    }
    
    func testOfflineEditing() async throws {
        // 1. Create and save an item that's already synced
        let item = Item(
            id: "offline-edit-test",
            title: "Original Title",
            content: "Original content",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        try await coreDataManager.saveItem(item)
        
        // Mark as synced
        let context = coreDataManager.viewContext
        let fetchRequest: NSFetchRequest<CDItem> = CDItem.fetchRequest()
        fetchRequest.predicate = NSPredicate(format: "id == %@", item.id)
        let result = try context.fetch(fetchRequest)
        result[0].needsSync = false
        try context.save()
        
        // 2. Simulate going offline
        networkMonitor.isConnected = false
        
        // 3. Update the item while offline
        var updatedItem = item
        updatedItem.title = "Updated Title"
        updatedItem.content = "Updated while offline"
        
        try await coreDataManager.saveItem(updatedItem)
        
        // 4. Verify changes are saved locally and marked for sync
        let savedItems = try coreDataManager.fetchAllItems()
        XCTAssertEqual(savedItems.count, 1)
        XCTAssertEqual(savedItems[0].title, "Updated Title")
        XCTAssertEqual(savedItems[0].content, "Updated while offline")
        XCTAssertTrue(savedItems[0].needsSync)
        
        // 5. Simulate coming back online
        networkMonitor.isConnected = true
        
        // 6. Trigger sync
        try await syncManager.syncLocalChangesToAPI()
        
        // 7. Verify item was synced
        let syncedItems = try coreDataManager.fetchAllItems()
        XCTAssertEqual(syncedItems.count, 1)
        XCTAssertFalse(syncedItems[0].needsSync)
    }
    
    func testOfflineBrowsing() async throws {
        // 1. Populate local database with items (simulate previous sync)
        let items = [
            Item(id: "offline-1", title: "Item 1", content: "Content 1", createdAt: Date(), updatedAt: Date()),
            Item(id: "offline-2", title: "Item 2", content: "Content 2", createdAt: Date(), updatedAt: Date()),
            Item(id: "offline-3", title: "Item 3", content: "Content 3", createdAt: Date(), updatedAt: Date())
        ]
        
        try await coreDataManager.saveItems(items)
        
        // 2. Simulate going offline
        networkMonitor.isConnected = false
        
        // 3. Create a timeline view model that uses the core data manager
        let timelineViewModel = TimelineViewModel(
            apiClient: mockAPIClient,
            coreDataManager: coreDataManager,
            networkMonitor: networkMonitor
        )
        
        // 4. Load timeline
        await timelineViewModel.loadTimeline()
        
        // 5. Verify items are loaded from local database
        XCTAssertEqual(timelineViewModel.items.count, 3)
        XCTAssertTrue(timelineViewModel.items.contains(where: { $0.id == "offline-1" }))
        XCTAssertTrue(timelineViewModel.items.contains(where: { $0.id == "offline-2" }))
        XCTAssertTrue(timelineViewModel.items.contains(where: { $0.id == "offline-3" }))
        
        // 6. Verify offline status is indicated
        XCTAssertTrue(timelineViewModel.isOffline)
    }
}

// Mock network monitor for testing
class MockNetworkMonitor: NetworkMonitorProtocol {
    var isConnected: Bool = true
    private var connectionStateHandler: ((Bool) -> Void)?
    
    func startMonitoring() {}
    func stopMonitoring() {}
    
    func onConnectionChange(_ handler: @escaping (Bool) -> Void) {
        connectionStateHandler = handler
    }
    
    // Helper to simulate connection changes
    func simulateConnectionChange(connected: Bool) {
        isConnected = connected
        connectionStateHandler?(connected)
    }
}
```

### 2.4 Security Testing

```swift
// IMPLEMENT: Security tests
final class SecurityTests: XCTestCase {
    
    func testKeychainStorage() {
        let keychainService = KeychainService()
        let testKey = "test.security.key"
        let testValue = "sensitive-data-123"
        
        // Clean up from previous tests
        try? keychainService.delete(key: testKey)
        
        // Test saving
        XCTAssertNoThrow(try keychainService.save(key: testKey, data: testValue))
        
        // Test retrieval
        do {
            let retrievedValue = try keychainService.retrieve(key: testKey)
            XCTAssertEqual(retrievedValue, testValue)
        } catch {
            XCTFail("Failed to retrieve value: \(error)")
        }
        
        // Test deletion
        XCTAssertNoThrow(try keychainService.delete(key: testKey))
        
        // Verify deleted
        do {
            _ = try keychainService.retrieve(key: testKey)
            XCTFail("Should have thrown item not found")
        } catch KeychainError.itemNotFound {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testEncryptionService() {
        let encryptionService = EncryptionService.shared
        let testData = "This is sensitive data that should be encrypted".data(using: .utf8)!
        
        // Test encryption
        do {
            let encryptedData = try encryptionService.encrypt(testData)
            XCTAssertNotEqual(encryptedData, testData, "Encrypted data should be different from original")
            
            // Test decryption
            let decryptedData = try encryptionService.decrypt(encryptedData)
            XCTAssertEqual(decryptedData, testData, "Decrypted data should match original")
            
            // Verify the string can be recovered
            let decryptedString = String(data: decryptedData, encoding: .utf8)
            XCTAssertEqual(decryptedString, "This is sensitive data that should be encrypted")
            
        } catch {
            XCTFail("Encryption/decryption failed: \(error)")
        }
    }
    
    func testSecureAPIRequests() {
        // This would test certificate pinning and secure headers
        // Since we can't easily mock TLS in tests, this would typically
        // be done via manual testing or specialized tools
    }
}
```

## 3. Test Environment Setup

### 3.1 Test Database Setup

```swift
// IMPLEMENT: Test database configuration
extension CoreDataManager {
    // Create a test configuration with in-memory store
    convenience init(inMemory: Bool) {
        self.init()
        
        if inMemory {
            // Use in-memory store type for testing
            let description = NSPersistentStoreDescription()
            description.type = NSInMemoryStoreType
            
            let container = NSPersistentContainer(name: "PRSNLModel")
            container.persistentStoreDescriptions = [description]
            
            container.loadPersistentStores { _, error in
                if let error = error {
                    fatalError("Failed to load in-memory database: \(error)")
                }
            }
            
            self.persistentContainer = container
        }
    }
    
    // Utility to create test data
    func createTestData() async throws {
        let items = [
            Item(id: "test-1", title: "Test Item 1", content: "Test content 1", createdAt: Date(), updatedAt: Date()),
            Item(id: "test-2", title: "Test Item 2", content: "Test content 2", createdAt: Date(), updatedAt: Date()),
            Item(id: "test-3", title: "Test Item 3", content: "Test content 3", createdAt: Date(), updatedAt: Date())
        ]
        
        try await saveItems(items)
    }
    
    // Utility to reset database
    func resetDatabase() throws {
        let context = persistentContainer.newBackgroundContext()
        
        // Delete all entities
        let fetchRequest: NSFetchRequest<NSFetchRequestResult> = CDItem.fetchRequest()
        let batchDeleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
        batchDeleteRequest.resultType = .resultTypeObjectIDs
        
        do {
            let result = try context.execute(batchDeleteRequest) as? NSBatchDeleteResult
            if let objectIDs = result?.result as? [NSManagedObjectID] {
                let changes = [NSDeletedObjectsKey: objectIDs]
                NSManagedObjectContext.mergeChanges(fromRemoteContextSave: changes, into: [viewContext])
            }
        } catch {
            throw error
        }
    }
}
```

### 3.2 Mock Server Setup

```swift
// IMPLEMENT: Mock API server for UI testing
class MockServer {
    private var server: HttpServer?
    private let port: UInt16 = 8080
    
    func start() throws {
        server = HttpServer()
        
        // Setup endpoints
        setupTimelineEndpoint()
        setupItemsEndpoint()
        setupSearchEndpoint()
        
        // Start server
        try server?.start(port)
        print("Mock server started on port \(port)")
    }
    
    func stop() {
        server?.stop()
        server = nil
        print("Mock server stopped")
    }
    
    private func setupTimelineEndpoint() {
        server?.GET["/timeline"] = { request in
            // Parse query parameters
            let page = Int(request.queryParams.first(where: { $0.0 == "page" })?.1 ?? "1") ?? 1
            let limit = Int(request.queryParams.first(where: { $0.0 == "limit" })?.1 ?? "20") ?? 20
            
            // Generate mock items
            let items = (1...limit).map { i in
                [
                    "id": "mock-\(((page - 1) * limit) + i)",
                    "title": "Mock Item \(((page - 1) * limit) + i)",
                    "content": "This is mock content for item \(((page - 1) * limit) + i)",
                    "created_at": ISO8601DateFormatter().string(from: Date()),
                    "updated_at": ISO8601DateFormatter().string(from: Date())
                ]
            }
            
            // Create response
            let response: [String: Any] = [
                "items": items,
                "page": page,
                "total": 100
            ]
            
            // Convert to JSON
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: response)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
    }
    
    private func setupItemsEndpoint() {
        // GET item by ID
        server?.GET["/items/:id"] = { request in
            guard let id = request.params.first(where: { $0.0 == "id" })?.1 else {
                return HttpResponse.notFound
            }
            
            // Create mock item
            let item: [String: Any] = [
                "id": id,
                "title": "Mock Item \(id)",
                "content": "This is mock content for item \(id)",
                "created_at": ISO8601DateFormatter().string(from: Date()),
                "updated_at": ISO8601DateFormatter().string(from: Date())
            ]
            
            // Convert to JSON
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: item)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
        
        // POST new item
        server?.POST["/items"] = { request in
            // In a real implementation, would parse the request body
            // For tests, just return success
            
            let response = ["status": "success", "id": "new-mock-id"]
            
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: response)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
        
        // PUT update item
        server?.PUT["/items/:id"] = { request in
            guard let id = request.params.first(where: { $0.0 == "id" })?.1 else {
                return HttpResponse.notFound
            }
            
            // In a real implementation, would parse the request body
            // For tests, just return success
            
            let response = ["status": "success", "id": id]
            
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: response)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
        
        // DELETE item
        server?.DELETE["/items/:id"] = { request in
            guard let id = request.params.first(where: { $0.0 == "id" })?.1 else {
                return HttpResponse.notFound
            }
            
            let response = ["status": "success", "id": id]
            
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: response)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
    }
    
    private func setupSearchEndpoint() {
        server?.GET["/search"] = { request in
            // Parse query parameters
            let query = request.queryParams.first(where: { $0.0 == "q" })?.1 ?? ""
            let page = Int(request.queryParams.first(where: { $0.0 == "page" })?.1 ?? "1") ?? 1
            let limit = Int(request.queryParams.first(where: { $0.0 == "limit" })?.1 ?? "20") ?? 20
            
            // Generate mock search results
            let items = (1...min(limit, 5)).map { i in
                [
                    "id": "search-\(((page - 1) * limit) + i)",
                    "title": "Search Result \(((page - 1) * limit) + i) for \(query)",
                    "content": "This content matches your search for \(query)",
                    "created_at": ISO8601DateFormatter().string(from: Date()),
                    "updated_at": ISO8601DateFormatter().string(from: Date())
                ]
            }
            
            // Create response
            let response: [String: Any] = [
                "items": items,
                "page": page,
                "total": 5
            ]
            
            // Convert to JSON
            do {
                let jsonData = try JSONSerialization.data(withJSONObject: response)
                return HttpResponse.ok(.data(jsonData, contentType: "application/json"))
            } catch {
                return HttpResponse.internalServerError
            }
        }
    }
}
```

### 3.3 Test Data Generation

```swift
// IMPLEMENT: Test data generator
struct TestDataGenerator {
    static func generateItems(count: Int) -> [Item] {
        return (1...count).map { i in
            Item(
                id: "gen-\(i)",
                title: "Generated Item \(i)",
                content: "This is generated content for item \(i) that provides enough text to be realistic for testing purposes.",
                createdAt: Date().addingTimeInterval(-Double(i * 3600)), // Spread out creation times
                updatedAt: Date().addingTimeInterval(-Double(i * 1800))  // Spread out update times
            )
        }
    }
    
    static func generateItemWithAttachments() -> Item {
        var item = Item(
            id: "attachment-item",
            title: "Item with Attachments",
            content: "This item has several attachments for testing display and handling of different attachment types.",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        item.attachments = [
            Attachment(id: "att-1", type: "image", url: "https://example.com/image.jpg", createdAt: Date()),
            Attachment(id: "att-2", type: "document", url: "https://example.com/document.pdf", createdAt: Date()),
            Attachment(id: "att-3", type: "link", url: "https://example.com", createdAt: Date())
        ]
        
        return item
    }
    
    static func generateItemWithTags() -> Item {
        var item = Item(
            id: "tagged-item",
            title: "Item with Tags",
            content: "This item has several tags for testing filtering and categorization.",
            createdAt: Date(),
            updatedAt: Date()
        )
        
        item.tags = ["swift", "ios", "testing", "development"]
        
        return item
    }
    
    static func populateTestDatabase(_ coreDataManager: CoreDataManager) async throws {
        // Generate standard items
        let items = generateItems(count: 20)
        
        // Add special items
        let itemWithAttachments = generateItemWithAttachments()
        let itemWithTags = generateItemWithTags()
        
        // Save all items
        try await coreDataManager.saveItems(items + [itemWithAttachments, itemWithTags])
    }
}
```

## 4. Automated Testing Setup

### 4.1 CI Configuration

```yaml
# IMPLEMENT: GitHub Actions workflow for iOS testing
name: iOS Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    name: Test iOS App
    runs-on: macos-latest
    
    steps:
    - name: Checkout Repository
      uses: actions/checkout@v3
      
    - name: Set up Ruby
      uses: ruby/setup-ruby@v1
      with:
        ruby-version: '3.0'
        bundler-cache: true
        
    - name: Install Bundler
      run: gem install bundler
      
    - name: Install Dependencies
      run: |
        bundle install
        bundle exec pod install
      
    - name: Run Tests
      run: |
        xcodebuild test -workspace PRSNL.xcworkspace -scheme PRSNL -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.0' -resultBundlePath TestResults.xcresult
      
    - name: Upload Test Results
      uses: actions/upload-artifact@v3
      if: success() || failure()
      with:
        name: test-results
        path: TestResults.xcresult
        
    - name: Generate Test Coverage Report
      run: |
        bundle exec slather coverage --html --output-directory coverage --scheme PRSNL PRSNL.xcodeproj
      
    - name: Upload Coverage Report
      uses: actions/upload-artifact@v3
      with:
        name: code-coverage
        path: coverage
```

### 4.2 XCTest Configuration

```swift
// IMPLEMENT: Custom XCTest configuration
class PRSNLTestCase: XCTestCase {
    // Common test setup code
    override func setUp() {
        super.setUp()
        
        // Reset UserDefaults for tests
        let defaultsName = "com.prsnl.testing"
        UserDefaults.standard = UserDefaults(suiteName: defaultsName)!
        UserDefaults.standard.removePersistentDomain(forName: defaultsName)
        
        // Setup environment
        setupTestEnvironment()
    }
    
    // Common test teardown code
    override func tearDown() {
        resetTestEnvironment()
        super.tearDown()
    }
    
    // Setup test environment
    private func setupTestEnvironment() {
        // Configure for testing
        AppEnvironment.isTestMode = true
        
        // Reset keychain for tests
        try? KeychainService().clearAll()
    }
    
    // Reset test environment
    private func resetTestEnvironment() {
        // Clean up any resources
        AppEnvironment.isTestMode = false
    }
    
    // Helper method to wait for async operations with timeout
    func waitForAsyncOperation(timeout: TimeInterval = 5.0, operation: @escaping () async throws -> Void) {
        let expectation = XCTestExpectation(description: "Async operation")
        
        Task {
            do {
                try await operation()
                expectation.fulfill()
            } catch {
                XCTFail("Async operation failed with error: \(error)")
            }
        }
        
        wait(for: [expectation], timeout: timeout)
    }
}

// Environment helper
class AppEnvironment {
    static var isTestMode = false
    
    static var baseURL: URL {
        if isTestMode {
            return URL(string: "http://localhost:8080")!
        } else {
            return URL(string: "https://api.prsnl.com")!
        }
    }
}
```

## 5. Manual Testing

### 5.1 Manual Test Cases

```markdown
# Manual Test Plan

## Authentication Testing
1. **New User Registration**
   - Open the app and navigate to the sign-up screen
   - Enter valid registration information
   - Verify account is created successfully
   - Verify welcome screen appears

2. **Login with Valid Credentials**
   - Open the app and navigate to the login screen
   - Enter valid username and password
   - Verify successful login
   - Verify timeline screen appears with content

3. **Login with Invalid Credentials**
   - Open the app and navigate to the login screen
   - Enter invalid username and password
   - Verify appropriate error message is shown
   - Verify user remains on login screen

4. **Password Reset**
   - Open the app and navigate to the login screen
   - Tap "Forgot Password"
   - Enter email address
   - Verify confirmation message
   - Check email for reset instructions
   - Follow instructions and reset password
   - Verify login with new password works

5. **Biometric Authentication**
   - Enable biometric authentication in settings
   - Log out
   - Attempt login with biometrics
   - Verify successful login
   - Disable biometrics
   - Log out
   - Verify biometric option is not available

## Timeline Testing
1. **Timeline Initial Load**
   - Login to the app
   - Verify timeline loads
   - Verify items are displayed in correct order (newest first)
   - Verify item previews show correct information

2. **Timeline Scrolling**
   - Scroll through timeline
   - Verify smooth scrolling
   - Verify lazy loading of additional items
   - Scroll to bottom
   - Verify loading indicator appears
   - Verify more items load

3. **Timeline Pull-to-Refresh**
   - Pull down on timeline
   - Verify refresh indicator appears
   - Verify timeline refreshes with updated data

4. **Item Interaction from Timeline**
   - Tap on an item
   - Verify navigation to detail view
   - Verify back button returns to timeline
   - Verify timeline position is maintained

## Item Detail Testing
1. **Item Detail View**
   - Select an item from timeline
   - Verify all item information is displayed correctly
   - Verify images load properly
   - Verify formatting is preserved

2. **Item Editing**
   - Select an item from timeline
   - Tap edit button
   - Modify title and content
   - Save changes
   - Verify changes are reflected
   - Navigate back to timeline
   - Verify changes appear in timeline

3. **Item Deletion**
   - Select an item from timeline
   - Tap delete option
   - Confirm deletion
   - Verify return to timeline
   - Verify item is removed from timeline

4. **Item Sharing**
   - Select an item from timeline
   - Tap share button
   - Verify share sheet appears with correct content
   - Share via available method
   - Verify sharing completes

## Search Testing
1. **Basic Search**
   - Navigate to search screen
   - Enter search term
   - Verify results appear
   - Verify results match search term

2. **Advanced Search**
   - Navigate to search screen
   - Use filters for search (if implemented)
   - Verify filtered results match criteria

3. **Empty Search Results**
   - Search for a term that should yield no results
   - Verify appropriate empty state is displayed
   - Verify user can return to search

4. **Search History**
   - Perform several searches
   - Clear search field
   - Verify recent searches appear
   - Tap a recent search
   - Verify search executes with that term

## Offline Testing
1. **App Usage while Offline**
   - Enable airplane mode
   - Open the app
   - Verify offline indicator appears
   - Verify previously loaded content is accessible
   - Try to refresh
   - Verify appropriate offline message

2. **Content Creation while Offline**
   - Remain in airplane mode
   - Create a new item
   - Save the item
   - Verify item appears in timeline with offline indicator
   - Disable airplane mode
   - Verify sync indicator appears
   - Verify item syncs to server

3. **Content Editing while Offline**
   - Enable airplane mode
   - Edit an existing item
   - Save changes
   - Verify changes appear with offline indicator
   - Disable airplane mode
   - Verify changes sync to server

4. **App Behavior during Connectivity Changes**
   - Use the app while online
   - Enable airplane mode
   - Verify offline indicator appears
   - Perform various actions
   - Disable airplane mode
   - Verify online indicator appears
   - Verify pending changes sync

## Performance Testing
1. **App Launch Time**
   - Close the app completely
   - Time how long it takes to launch and become interactive
   - Verify launch time is under 3 seconds

2. **Timeline Scrolling Performance**
   - Populate timeline with many items (50+)
   - Scroll rapidly through timeline
   - Verify smooth scrolling without dropped frames
   - Verify memory usage remains stable

3. **Image Loading Performance**
   - Navigate to items with images
   - Verify images load progressively
   - Verify scrolling remains smooth during image loading
   - Verify memory usage remains stable

4. **Background/Foreground Transitions**
   - Use the app
   - Send app to background
   - Bring app to foreground after 30 seconds
   - Verify app resumes quickly
   - Verify no data loss or UI issues

## Accessibility Testing
1. **VoiceOver Compatibility**
   - Enable VoiceOver
   - Navigate through app
   - Verify all elements are properly announced
   - Verify actions can be performed via VoiceOver

2. **Dynamic Type Support**
   - Change system font size to largest setting
   - Verify text remains readable
   - Verify UI handles large text without breaking layout

3. **Contrast and Color**
   - Enable "Increase Contrast" in accessibility settings
   - Verify text remains readable
   - Enable color filters for color blindness
   - Verify information is distinguishable

4. **Reduced Motion**
   - Enable reduced motion in accessibility settings
   - Verify animations are reduced or eliminated
   - Verify app remains functional

## Security Testing
1. **Authentication Timeout**
   - Login to app
   - Leave app in background for 15 minutes
   - Return to app
   - Verify authentication is required again

2. **Sensitive Data Display**
   - Navigate to screen with sensitive data
   - Take app screenshot
   - Verify sensitive data is obscured in app switcher

3. **App Permissions**
   - Review all app permission requests
   - Verify appropriate explanations are provided
   - Verify app functions with minimal permissions

4. **Secure Field Protection**
   - Navigate to login screen
   - Verify password field masks characters
   - Check keyboard doesn't suggest or auto-complete passwords
```

### 5.2 Device Testing Matrix

```markdown
# Device Testing Matrix

| Device          | OS Version | Priority | Screen Size | Notes                                |
|-----------------|------------|----------|-------------|--------------------------------------|
| iPhone 15 Pro   | iOS 17.0   | High     | 6.1"        | Current flagship, primary target     |
| iPhone 13       | iOS 17.0   | High     | 6.1"        | Common device                        |
| iPhone SE (2022)| iOS 17.0   | Medium   | 4.7"        | Smallest current device              |
| iPhone 15 Pro Max| iOS 17.0  | Medium   | 6.7"        | Largest current device               |
| iPhone 12       | iOS 16.0   | Medium   | 6.1"        | Previous OS version                  |
| iPhone 11       | iOS 15.0   | Low      | 6.1"        | Older OS version                     |
| iPad Pro 12.9"  | iOS 17.0   | Low      | 12.9"       | Tablet layout (if supported)         |

## Test Environment Conditions

For each device, test under the following conditions:

### Connectivity
- Strong WiFi connection
- Weak/unstable WiFi connection
- Cellular data (4G/5G)
- Offline mode
- Transitioning between connectivity states

### Device Conditions
- Low battery mode (below 20%)
- Limited available storage (less than 1GB free)
- Multiple apps running in background

### Orientation
- Portrait
- Landscape (if supported)
- Rotation between orientations

### Interruptions
- Incoming calls
- Push notifications
- System alerts
- Background/foreground transitions
```

## 6. Testing Process

### 6.1 Test-Driven Development Workflow

```markdown
# Test-Driven Development Workflow

## Step 1: Write the Test
- Create a test file for the feature component
- Define expected behavior
- Write the test before implementing the feature
- Verify the test fails (Red)

## Step 2: Implement the Feature
- Write minimal code to make the test pass
- Focus on functionality, not optimization
- Run the test to verify it passes (Green)

## Step 3: Refactor
- Clean up the implementation
- Improve code quality and performance
- Ensure tests still pass after refactoring

## Step 4: Expand Test Coverage
- Add edge cases and error conditions
- Test different input combinations
- Verify all scenarios work correctly

## Example TDD Workflow

### Feature: Item Search

1. **Write the Test**
   ```swift
   func testSearchWithResults() async {
       // Setup
       let viewModel = SearchViewModel(apiClient: MockAPIClient())
       
       // Test
       await viewModel.search(query: "test")
       
       // Verify
       XCTAssertFalse(viewModel.isLoading)
       XCTAssertNotNil(viewModel.searchResults)
       XCTAssertNil(viewModel.error)
   }
   ```

2. **Implement the Feature**
   ```swift
   func search(query: String) async {
       isLoading = true
       searchResults = []
       error = nil
       
       do {
           let response = try await apiClient.search(query: query)
           searchResults = response.items
       } catch {
           self.error = error
       }
       
       isLoading = false
   }
   ```

3. **Refactor**
   ```swift
   func search(query: String) async {
       // Don't search if query is too short
       guard query.count >= 2 else {
           searchResults = []
           return
       }
       
       isLoading = true
       searchResults = []
       error = nil
       
       do {
           let response = try await apiClient.search(
               query: query,
               page: 1,
               limit: pageSize
           )
           
           await MainActor.run {
               searchResults = response.items
               totalResults = response.total
               currentPage = 1
           }
       } catch {
           await MainActor.run {
               self.error = error
           }
       }
       
       await MainActor.run {
           isLoading = false
       }
   }
   ```

4. **Expand Test Coverage**
   ```swift
   func testEmptySearchQuery() async {
       let viewModel = SearchViewModel(apiClient: MockAPIClient())
       
       await viewModel.search(query: "")
       
       XCTAssertFalse(viewModel.isLoading)
       XCTAssertTrue(viewModel.searchResults.isEmpty)
       XCTAssertNil(viewModel.error)
   }
   
   func testNetworkErrorDuringSearch() async {
       let mockClient = MockAPIClient()
       mockClient.shouldReturnError = true
       let viewModel = SearchViewModel(apiClient: mockClient)
       
       await viewModel.search(query: "test")
       
       XCTAssertFalse(viewModel.isLoading)
       XCTAssertTrue(viewModel.searchResults.isEmpty)
       XCTAssertNotNil(viewModel.error)
   }
   ```
```

### 6.2 Bug Reporting Template

```markdown
# Bug Report Template

## Bug Information
- **Title**: [Concise description of the issue]
- **ID**: [Unique identifier, e.g., BUG-123]
- **Reporter**: [Name of person who found the bug]
- **Date Reported**: [YYYY-MM-DD]
- **Priority**: [Critical/High/Medium/Low]
- **Status**: [New/In Progress/Fixed/Verified/Closed]
- **Affected Version**: [App version where bug was found]
- **Affected Devices**: [List of devices/OS versions where bug occurs]

## Bug Details
- **Description**: 
  [Detailed description of the issue]

- **Steps to Reproduce**:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
  ...

- **Expected Behavior**:
  [What should happen]

- **Actual Behavior**:
  [What actually happens]

- **Reproducibility**:
  [Always/Sometimes/Rarely]

## Supplementary Information
- **Screenshots/Videos**:
  [Attach or link visual evidence]

- **Logs/Stack Trace**:
  ```
  [Paste relevant logs or stack traces here]
  ```

- **Environment Information**:
  - Device: [e.g., iPhone 15 Pro]
  - OS Version: [e.g., iOS 17.0]
  - Network Condition: [e.g., WiFi/Cellular/Offline]
  - Other Relevant Conditions: [e.g., Low Battery, Background State]

## Analysis
- **Potential Cause**:
  [Initial analysis of what might be causing the issue]

- **Related Issues**:
  [Links to related bugs or features]

- **Workaround**:
  [Temporary solution, if any]

## Resolution
- **Assigned To**: [Developer name]
- **Fixed in Version**: [Version where fix will appear]
- **Resolution Description**: [How the issue was fixed]
- **Fix Verification Steps**: [How to verify the fix]
```

### 6.3 Regression Testing Checklist

```markdown
# Regression Testing Checklist

## Core Functionality
- [ ] Login and authentication
- [ ] Timeline display and scrolling
- [ ] Item creation
- [ ] Item editing
- [ ] Item deletion
- [ ] Search functionality
- [ ] Offline operation
- [ ] Synchronization

## User Interface
- [ ] Navigation flow between screens
- [ ] UI elements display correctly
- [ ] Animations and transitions
- [ ] Touch interactions and gestures
- [ ] Keyboard input and form submission
- [ ] Error messages and alerts
- [ ] Loading indicators

## Data Management
- [ ] Data persistence across app restarts
- [ ] Proper handling of API responses
- [ ] Offline data access
- [ ] Data synchronization when coming online
- [ ] Conflict resolution for edited items

## Performance
- [ ] App launch time
- [ ] Smooth scrolling in lists
- [ ] Memory usage remains stable
- [ ] Battery usage is reasonable
- [ ] Network operations are efficient

## Security
- [ ] Authentication token handling
- [ ] Secure storage of credentials
- [ ] Session expiration handling
- [ ] Protection of sensitive data

## Edge Cases
- [ ] Empty state handling
- [ ] Error state handling
- [ ] Network interruption handling
- [ ] Large data set handling
- [ ] Unusual input handling

## Platform Integration
- [ ] Background/foreground transitions
- [ ] Push notification handling
- [ ] Deep linking
- [ ] System permission handling
- [ ] Share sheet integration

## Accessibility
- [ ] VoiceOver compatibility
- [ ] Dynamic Type support
- [ ] Sufficient color contrast
- [ ] Support for accessibility settings

## Device Compatibility
- [ ] Displays correctly on various iPhone sizes
- [ ] Supports both portrait and landscape (if applicable)
- [ ] Works with both Face ID and Touch ID devices
- [ ] Performs well on older supported devices

## Regression Areas
[List specific areas that need testing based on recent changes]
- [ ] [Feature recently modified]
- [ ] [Components that interact with modified code]
- [ ] [Known sensitive areas of the application]
```

## 7. Test Automation Strategy

### 7.1 Continuous Integration Pipeline

```yaml
# IMPLEMENT: Fastlane configuration for CI
# Fastfile

default_platform(:ios)

platform :ios do
  desc "Run all tests"
  lane :test do
    scan(
      scheme: "PRSNL",
      devices: ["iPhone 15"],
      clean: true,
      code_coverage: true,
      output_types: "html",
      output_directory: "test_results"
    )
  end
  
  desc "Run unit tests only"
  lane :unit_test do
    scan(
      scheme: "PRSNL",
      devices: ["iPhone 15"],
      clean: true,
      code_coverage: true,
      only_testing: [
        "PRSNLTests"
      ]
    )
  end
  
  desc "Run UI tests only"
  lane :ui_test do
    scan(
      scheme: "PRSNL",
      devices: ["iPhone 15"],
      clean: true,
      code_coverage: true,
      only_testing: [
        "PRSNLUITests"
      ]
    )
  end
  
  desc "Build and analyze code"
  lane :analyze do
    scan(
      scheme: "PRSNL",
      clean: true,
      build_for_testing: true
    )
    
    swiftlint(
      mode: :lint,
      output_file: "swiftlint.result.json",
      reporter: "json",
      ignore_exit_status: true
    )
  end
  
  desc "Create test build"
  lane :beta do
    build_app(
      scheme: "PRSNL",
      export_method: "development",
      export_options: {
        provisioningProfiles: {
          "com.prsnl.app" => "PRSNL Development"
        }
      }
    )
  end
end
```

### 7.2 Test Coverage Goals

```markdown
# Test Coverage Goals

## Overall Coverage Targets
- Unit Tests: 80% line coverage
- Integration Tests: 70% line coverage
- UI Tests: Key user flows covered

## Coverage Priorities by Component

### High Priority (90%+ coverage)
- Core Data layer
- Networking layer
- Authentication system
- Sync manager
- Item model

### Medium Priority (70-90% coverage)
- View models
- Search functionality
- Timeline functionality
- Item detail functionality
- Offline capabilities

### Lower Priority (50-70% coverage)
- UI components
- Animations
- Helper utilities
- Settings screens

## Coverage Exclusions
- Generated code
- Third-party libraries
- Debug-only code
- Test code itself

## Coverage Verification
- Coverage reports generated with each CI run
- Review coverage changes with each PR
- Address coverage regressions promptly
- Quarterly review of overall coverage metrics

## Testing Debt Management
- Track areas with insufficient coverage
- Prioritize test creation for critical paths
- Add tests when fixing bugs
- Improve test coverage with each sprint
```

## 8. Testing Schedule

```markdown
# Testing Schedule

## Development Phase
- **Unit Tests**: Written simultaneously with code
- **Integration Tests**: Added after components are implemented
- **Manual Testing**: Daily on development builds

## Pre-Release Phase
- **2 Weeks Before Release**
  - Complete all automated tests
  - Run full regression test suite
  - Begin device compatibility testing
  - Start performance profiling

- **1 Week Before Release**
  - Bug fixes and verification
  - Final regression testing
  - Stress testing and edge cases
  - Accessibility compliance verification

- **3 Days Before Release**
  - Final smoke testing on all target devices
  - Verify all critical issues are resolved
  - Final performance verification
  - Sign-off from QA team

## Post-Release Phase
- **Day of Release**
  - Smoke testing on production build
  - Monitoring for crash reports

- **1 Week After Release**
  - Analysis of crash reports and user feedback
  - Prioritization of issues for hotfix or next release
  - Regression test planning for identified issues

## Ongoing Testing
- **Daily**
  - Automated tests run on each PR
  - Manual testing of new features

- **Weekly**
  - Full regression test suite
  - Performance benchmarking
  - Memory leak detection

- **Monthly**
  - Security testing
  - Comprehensive device compatibility testing
  - Test coverage analysis and improvement
```

## 9. Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. Set up testing environment and CI/CD pipeline
2. Create unit test infrastructure
3. Implement basic unit tests for core components
4. Establish test coverage tracking

### Phase 2: Component Testing (Week 3-4)
1. Implement unit tests for all major components
2. Create integration tests for component interactions
3. Set up mock server for API testing
4. Develop UI test infrastructure

### Phase 3: Advanced Testing (Week 5-6)
1. Implement UI tests for critical user flows
2. Create performance test suite
3. Develop offline capability tests
4. Implement security tests

### Phase 4: Automation and Optimization (Week 7-8)
1. Enhance CI/CD pipeline with test reports
2. Optimize test execution time
3. Create comprehensive test documentation
4. Train team on test framework and processes