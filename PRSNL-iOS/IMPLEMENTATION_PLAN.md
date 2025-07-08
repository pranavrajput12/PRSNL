# PRSNL iOS App - Master Implementation Plan v2.0

## 🎯 Executive Summary

The PRSNL iOS app is a native companion to the PRSNL personal knowledge management system. This document serves as the definitive guide for implementing a feature-complete iOS application that matches and enhances the web experience with native capabilities.

### Core Philosophy
- **Feature parity** with web app plus iOS-specific enhancements
- **Offline-first** architecture with seamless sync
- **Native performance** targeting 60fps everywhere
- **Five core sections**: Dashboard, Insights, Videos, Chat, Timeline
- **AI-powered** features integrated throughout

### Critical Success Metrics
- App launch time: < 0.5 seconds
- Search response: < 200ms (local), < 500ms (remote)
- Smooth 60fps scrolling everywhere
- Offline capability for all read operations
- Background sync every 15 minutes

## 📱 The Five Pillars Architecture

### 1. Dashboard (Home)
The command center showing everything at a glance:
- **Smart Feed**: Recent items with AI-suggested relevance
- **Quick Stats**: Total items, today's captures, trending topics
- **Quick Capture**: One-tap capture from clipboard/camera
- **Global Search**: Unified search across all content
- **AI Suggestions**: Proactive content recommendations

### 2. Insights
AI-powered intelligence about your knowledge:
- **Dynamic Insights**: Real-time generated insights
- **Knowledge Graph**: Interactive visualization
- **Topic Clusters**: Content organization by themes
- **Learning Velocity**: Track knowledge growth
- **Time Patterns**: When you learn best

### 3. Videos
Rich media knowledge management:
- **Video Library**: All captured videos with transcripts
- **Mini-Courses**: AI-generated learning paths
- **Platform Filters**: YouTube, Twitter, Instagram, etc.
- **Transcript Search**: Find moments in videos
- **Watch Later**: Queue management

### 4. Chat
Conversational interface to your knowledge:
- **AI Assistant**: Chat with your knowledge base
- **Multiple Modes**: General, Deep Dive, Creative, Learning
- **Live Streaming**: Real-time responses
- **Citations**: Sources from your knowledge base
- **Suggested Questions**: Context-aware prompts

### 5. Timeline
Chronological view of everything:
- **Infinite Scroll**: Smooth pagination
- **Rich Previews**: Images, summaries, tags
- **Quick Actions**: Share, similar, delete
- **Filter & Sort**: By type, date, platform
- **Bulk Operations**: Multi-select actions

## 🏗️ Technical Architecture

### Core Stack
```
Language: Swift 5.9+
UI Framework: SwiftUI
Minimum iOS: 17.0
Architecture: MVVM-C (Coordinator pattern)
Async: Swift Concurrency (async/await)
Storage: Core Data + CloudKit
Networking: URLSession + WebSocket
AI Features: CoreML + Azure OpenAI API
```

### Project Structure
```
PRSNL-iOS/
├── Implementation/
│   ├── PRSNL.xcodeproj
│   ├── PRSNL/
│   │   ├── App/
│   │   │   ├── PRSNLApp.swift
│   │   │   ├── AppCoordinator.swift
│   │   │   └── AppDelegate.swift
│   │   ├── Core/
│   │   │   ├── API/
│   │   │   │   ├── APIClient.swift
│   │   │   │   ├── APIConfiguration.swift
│   │   │   │   ├── WebSocketManager.swift
│   │   │   │   └── Endpoints/
│   │   │   ├── Models/
│   │   │   │   ├── Item.swift
│   │   │   │   ├── Insight.swift
│   │   │   │   ├── Video.swift
│   │   │   │   ├── ChatMessage.swift
│   │   │   │   └── KnowledgeGraph.swift
│   │   │   ├── CoreData/
│   │   │   │   ├── PRSNLModel.xcdatamodeld
│   │   │   │   ├── CoreDataManager.swift
│   │   │   │   └── Entities/
│   │   │   ├── Services/
│   │   │   │   ├── AuthenticationService.swift
│   │   │   │   ├── SyncManager.swift
│   │   │   │   ├── CacheService.swift
│   │   │   │   ├── AIService.swift
│   │   │   │   └── NotificationService.swift
│   │   │   └── Extensions/
│   │   ├── Features/
│   │   │   ├── Dashboard/
│   │   │   │   ├── DashboardCoordinator.swift
│   │   │   │   ├── DashboardView.swift
│   │   │   │   ├── DashboardViewModel.swift
│   │   │   │   └── Components/
│   │   │   ├── Insights/
│   │   │   │   ├── InsightsCoordinator.swift
│   │   │   │   ├── InsightsView.swift
│   │   │   │   ├── InsightsViewModel.swift
│   │   │   │   ├── KnowledgeGraphView.swift
│   │   │   │   └── Components/
│   │   │   ├── Videos/
│   │   │   │   ├── VideosCoordinator.swift
│   │   │   │   ├── VideoLibraryView.swift
│   │   │   │   ├── VideoPlayerView.swift
│   │   │   │   ├── MiniCourseView.swift
│   │   │   │   └── Components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatCoordinator.swift
│   │   │   │   ├── ChatView.swift
│   │   │   │   ├── ChatViewModel.swift
│   │   │   │   ├── MessageBubble.swift
│   │   │   │   └── Components/
│   │   │   └── Timeline/
│   │   │       ├── TimelineCoordinator.swift
│   │   │       ├── TimelineView.swift
│   │   │       ├── TimelineViewModel.swift
│   │   │       └── Components/
│   │   ├── Shared/
│   │   │   ├── UI/
│   │   │   │   ├── DesignSystem.swift
│   │   │   │   ├── GlassmorphismModifier.swift
│   │   │   │   └── Components/
│   │   │   ├── Navigation/
│   │   │   │   ├── TabBarController.swift
│   │   │   │   └── NavigationCoordinator.swift
│   │   │   └── Utils/
│   │   ├── Resources/
│   │   │   ├── Assets.xcassets
│   │   │   ├── Localizable.strings
│   │   │   └── Info.plist
│   ├── PRSNLTests/
│   ├── PRSNLUITests/
│   ├── PRSNLShareExtension/
│   └── PRSNLWidgets/
```

## 📅 Implementation Timeline (Revised - Building on Existing Code)

### Current State Analysis
✅ **Already Implemented:**
- Complete networking layer (APIClient with all endpoints)
- WebSocket infrastructure 
- Core Data setup with models
- Network monitoring
- Basic tab navigation
- Timeline view structure
- Solid MVVM architecture

❌ **Not Implemented:**
- API connection to backend
- Actual data display
- Most views (Search, Settings, ItemDetail, Dashboard, Insights, Videos, Chat)
- Capture functionality
- Share extension & widgets

### Phase 1: Connect to Backend (Day 1-2)
**Goal**: Get real data flowing into the app

#### Day 1: API Connection & Timeline
- [x] ~~APIClient already implemented~~
- [ ] Add API key configuration to Settings
- [ ] Connect TimelineViewModel to real API
- [ ] Test data flow and display
- [ ] Add error handling UI
- [ ] Implement pull-to-refresh with real data

#### Day 2: Core Views
- [ ] Implement ItemDetailView (2-3 hours)
- [ ] Create basic SearchView with existing APIClient search (2-3 hours)
- [ ] Create SettingsView with backend URL config (1-2 hours)
- [ ] Add loading states and error handling

### Phase 2: Five Core Sections (3-4 Days)
**Goal**: Implement all five main sections using existing infrastructure

#### Day 3: Dashboard & Enhanced Timeline
- [ ] Create DashboardView as new home tab (3-4 hours)
  - [ ] Quick stats using existing APIClient.getAnalytics()
  - [ ] Recent items feed
  - [ ] Quick capture button
  - [ ] Search bar integration
- [ ] Enhance Timeline with filtering (2 hours)
  - [ ] Add date/type/platform filters
  - [ ] Implement swipe actions
  - [ ] Add image loading for previews

#### Day 4: Chat Implementation
- [ ] Create ChatView using existing WebSocketManager (3-4 hours)
  - [ ] Message UI with bubbles
  - [ ] Connect to `/ws/chat/{client_id}` endpoint
  - [ ] Handle streaming responses
  - [ ] Show citations from knowledge base
- [ ] Add ChatViewModel (2 hours)
  - [ ] Message history management
  - [ ] WebSocket state handling

#### Day 5: Videos & Insights
- [ ] Create VideosView (3 hours)
  - [ ] Grid/list layout toggle
  - [ ] Use existing APIClient video endpoints
  - [ ] Platform filtering UI
  - [ ] Video player integration
- [ ] Create InsightsView (3 hours)
  - [ ] Connect to insights API endpoint
  - [ ] Display dynamic insights
  - [ ] Simple chart visualizations
  - [ ] Topic clusters list

### Phase 3: Capture & Enhancement (2-3 Days)
**Goal**: Add content creation and polish existing features

#### Day 6-7: Capture Implementation
- [ ] Create CaptureView and CaptureViewModel (4 hours)
  - [ ] URL/text input form
  - [ ] Quick capture from clipboard
  - [ ] Tag selection/creation
  - [ ] Use existing APIClient.capture()
- [ ] Enhance all views with proper loading/error states (3 hours)
- [ ] Add pull-to-refresh everywhere (2 hours)
- [ ] Implement proper image caching (2 hours)

### Phase 4: Native iOS Features (3-4 Days)
**Goal**: iOS-specific enhancements

#### Day 8-9: Share Extension
- [ ] Configure share extension target (2 hours)
- [ ] Create mini capture UI (3 hours)
- [ ] Use App Groups for data sharing (2 hours)
- [ ] Background upload handling (2 hours)

#### Day 10: Widgets & System Integration
- [ ] Timeline widget using existing data (3 hours)
- [ ] Quick stats widget (2 hours)
- [ ] Spotlight search integration (2 hours)
- [ ] Basic Siri shortcuts (1 hour)

### Total Realistic Timeline: 10 Days (2 Weeks)

## 🎯 Immediate Action Plan (TODAY)

Since we need to show progress TODAY, here's what we can accomplish:

### Today's Goals (Day 1)
1. **Morning (2-3 hours)**
   - [ ] Add backend URL configuration to UserDefaults
   - [ ] Update TimelineViewModel to use real API
   - [ ] Test Timeline with live data
   
2. **Afternoon (3-4 hours)**
   - [ ] Create basic SettingsView with URL input
   - [ ] Implement ItemDetailView
   - [ ] Create basic SearchView
   
3. **Evening (2 hours)**
   - [ ] Test end-to-end flow
   - [ ] Fix any API connection issues
   - [ ] Commit working version with real data

## 🔧 Implementation Details

### API Integration

```swift
// APIConfiguration.swift
class APIConfiguration {
    static let shared = APIConfiguration()
    
    @AppStorage("backendURL") var baseURL = "http://localhost:8000"
    @KeychainStorage("apiKey") var apiKey: String?
    
    var headers: HTTPHeaders {
        var headers = HTTPHeaders()
        headers["Content-Type"] = "application/json"
        if let apiKey = apiKey {
            headers["X-API-Key"] = apiKey
        }
        return headers
    }
    
    // Endpoints
    var timelineURL: URL { baseURL.appendingPathComponent("/api/timeline") }
    var insightsURL: URL { baseURL.appendingPathComponent("/api/insights") }
    var videosURL: URL { baseURL.appendingPathComponent("/api/videos") }
    var searchURL: URL { baseURL.appendingPathComponent("/api/search") }
    var captureURL: URL { baseURL.appendingPathComponent("/api/capture") }
}
```

### Core Data Schema

```swift
// Item Entity
@objc(CDItem)
public class CDItem: NSManagedObject {
    @NSManaged public var id: UUID
    @NSManaged public var title: String
    @NSManaged public var content: String
    @NSManaged public var summary: String?
    @NSManaged public var url: String?
    @NSManaged public var createdAt: Date
    @NSManaged public var updatedAt: Date
    @NSManaged public var syncStatus: Int16
    @NSManaged public var tags: NSSet
    @NSManaged public var attachments: NSSet
}
```

### WebSocket Chat

```swift
// ChatViewModel.swift
class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isConnected = false
    @Published var isTyping = false
    
    private var webSocketTask: URLSessionWebSocketTask?
    
    func connect() {
        let url = URL(string: "ws://localhost:8000/ws/chat/\(UUID())")!
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        receiveMessage()
    }
    
    func sendMessage(_ text: String) {
        let message = ChatMessage(text: text, isUser: true)
        messages.append(message)
        
        let wsMessage = URLSessionWebSocketTask.Message.string(text)
        webSocketTask?.send(wsMessage) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        let chatMessage = ChatMessage(text: text, isUser: false)
                        self?.messages.append(chatMessage)
                    }
                case .data(_):
                    break
                @unknown default:
                    break
                }
                self?.receiveMessage() // Continue receiving
            case .failure(let error):
                print("WebSocket receive error: \(error)")
            }
        }
    }
}
```

### Offline Sync Strategy

```swift
// SyncManager.swift
class SyncManager {
    static let shared = SyncManager()
    
    private let queue = OperationQueue()
    private var syncTimer: Timer?
    
    func startSync() {
        // Initial sync
        performSync()
        
        // Schedule periodic sync every 15 minutes
        syncTimer = Timer.scheduledTimer(withTimeInterval: 900, repeats: true) { _ in
            self.performSync()
        }
    }
    
    private func performSync() {
        Task {
            // 1. Upload pending captures
            await uploadPendingItems()
            
            // 2. Sync timeline updates
            await syncTimelineUpdates()
            
            // 3. Update insights
            await refreshInsights()
            
            // 4. Clean old cache
            await cleanCache()
        }
    }
}
```

## 🎨 Design System

### Colors
```swift
extension Color {
    // Primary
    static let prsnlRed = Color(hex: "#DC143C")
    static let prsnlRedGradient = LinearGradient(
        colors: [Color(hex: "#FF0040"), Color(hex: "#DC143C")],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
    
    // Semantic
    static let prsnlBackground = Color("Background")
    static let prsnlSurface = Color("Surface")
    static let prsnlText = Color("Text")
    static let prsnlSecondaryText = Color("SecondaryText")
    
    // Glass morphism
    static let prsnlGlass = Color.white.opacity(0.1)
    static let prsnlGlassBorder = Color.white.opacity(0.2)
}
```

### Typography
```swift
extension Font {
    static let prsnlLargeTitle = Font.system(size: 34, weight: .bold)
    static let prsnlTitle = Font.system(size: 28, weight: .semibold)
    static let prsnlHeadline = Font.system(size: 20, weight: .semibold)
    static let prsnlBody = Font.system(size: 17, weight: .regular)
    static let prsnlCaption = Font.system(size: 15, weight: .regular)
}
```

### Glass Morphism Effect
```swift
struct GlassmorphismModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.prsnlGlassBorder, lineWidth: 1)
            )
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
    }
}
```

## 📊 Performance Requirements

| Feature | Target | Strategy |
|---------|--------|----------|
| App Launch | < 0.5s | Lazy loading, minimal startup work |
| Search Response | < 200ms local, < 500ms remote | Local index, debouncing |
| Scroll FPS | 60fps | Cell reuse, image caching, async loading |
| Memory Usage | < 150MB | Automatic cache purging, image optimization |
| Offline Sync | < 30s | Incremental sync, background processing |
| Chat Response | < 100ms first token | WebSocket streaming |

## 🧪 Testing Strategy

### Unit Tests
- Model serialization/deserialization
- Core Data operations
- Sync logic
- AI response parsing
- Cache management

### UI Tests
- User flows for all 5 sections
- Offline mode transitions
- Share extension
- Widget functionality
- Performance benchmarks

### Integration Tests
- API endpoint coverage
- WebSocket reliability
- Background sync
- Push notifications
- Deep linking

## 🚀 Launch Checklist

### Pre-Launch
- [ ] All features implemented and tested
- [ ] Performance targets met
- [ ] Offline mode fully functional
- [ ] Share extension working
- [ ] Widgets configured
- [ ] App Store assets prepared

### Launch Day
- [ ] Backend API deployed and stable
- [ ] App submitted to App Store
- [ ] TestFlight beta released
- [ ] Documentation updated
- [ ] Support channels ready

### Post-Launch
- [ ] Monitor crash reports
- [ ] Track performance metrics
- [ ] Gather user feedback
- [ ] Plan feature updates
- [ ] Regular sync improvements

## 🔮 Future Enhancements

### Version 1.1
- Apple Watch companion app
- iPad optimized UI
- macOS Catalyst support
- iCloud backup
- Advanced shortcuts

### Version 1.2
- AR knowledge visualization
- Voice capture with transcription
- Collaborative features
- Custom AI models
- Export to Obsidian/Notion

### Version 2.0
- Multi-account support
- End-to-end encryption
- Plugin system
- API for third-party apps
- Advanced analytics

## 📝 Team Coordination

### Daily Sync Points
- Morning: Review yesterday's progress
- Midday: Share blockers and updates
- Evening: Update implementation status

### Documentation
- Update IMPLEMENTATION_STATUS.md daily
- Log all API changes in API_INTEGRATION_LOG.md
- Track decisions in DECISION_LOG.md

### Communication
- Primary: Implementation folder docs
- Async: Update tracking files
- Sync: Only for critical blockers

## ✅ Success Criteria

The iOS app will be considered complete when:

1. **All 5 sections** fully implemented with feature parity
2. **Performance targets** consistently met
3. **Offline mode** seamless and reliable
4. **Native features** (widgets, share, shortcuts) working
5. **Sync** reliable with < 1% failure rate
6. **UI/UX** smooth, consistent, and delightful
7. **Crash rate** < 0.1%
8. **User satisfaction** > 4.5 stars

---

*This document is the single source of truth for the PRSNL iOS implementation. All decisions and changes should be reflected here.*

**Last Updated**: 2025-07-09
**Version**: 2.0
**Author**: Claude (Orchestrator)