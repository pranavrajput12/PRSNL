# PRSNL iOS

Native iOS companion app for the PRSNL personal knowledge management system, providing mobile access to your knowledge base with a beautiful, intuitive interface.

## 🚀 Quick Start

```bash
# 1. Open project
cd Implementation
open PRSNL.xcodeproj

# 2. Select iPhone simulator (iOS 17+)
# 3. Build and run (⌘R)
```

**Current Status**: UI Complete with Mock Data - Ready for Backend Integration

## 📱 Features

### Implemented (UI Complete)
- ✅ **Timeline** - Chronological knowledge feed with pull-to-refresh
- ✅ **Search** - Advanced search with filters, tags, and AI assistant UI  
- ✅ **Videos** - Media library with category filtering and player
- ✅ **Settings** - Backend configuration and app preferences
- ✅ **Launch Screen** - Animated splash with attribution

### In Progress
- 🚧 **Chat** - Basic UI ready, needs WebSocket integration
- 🚧 **Backend Integration** - APIClient ready, currently using mock data

### Planned
- 📋 Share Extension - Quick capture from any app
- 📋 Widgets - Home screen quick access
- 📋 Offline Sync - Core Data integration
- 📋 Push Notifications - Real-time updates

## 🛠 Tech Stack

- **Platform**: iOS 17.0+
- **Language**: Swift 5.9+ 
- **UI Framework**: SwiftUI
- **Architecture**: MVVM
- **Networking**: URLSession with async/await
- **Storage**: Core Data (setup complete, not integrated)
- **Design**: Manchester United red (#DC143C) accent

## 📁 Project Structure

```
Implementation/
├── PRSNL.xcodeproj          # Xcode project
└── PRSNL/
    ├── App/                 # App lifecycle
    │   └── PRSNLApp.swift   # Main entry, tab setup
    ├── Core/               
    │   ├── Models/          # Data models
    │   ├── Services/        # Business logic
    │   └── DesignSystem.swift
    ├── Features/            # UI modules
    │   ├── Timeline/
    │   ├── Search/
    │   ├── Videos/
    │   ├── Chat/
    │   └── Settings/
    ├── Networking/
    │   └── APIClient.swift  # REST API
    └── Services/
        └── MockDataProvider.swift
```

## 🔧 Configuration

### Connect to Backend
1. Run your PRSNL backend on `http://localhost:8000`
2. Open Settings tab in the app
3. Enter backend URL
4. Add API token (if required)
5. Tap "Test Connection"

### Enable Real Data
Currently using mock data. To switch to real API:
```swift
// In TimelineViewModel.swift
// Replace: MockDataProvider.shared.getTimelineItems()  
// With: APIClient.shared.getItems()
```

## 📚 Key Documentation

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Detailed implementation status
- **[API_INTEGRATION.md](API_INTEGRATION.md)** - Backend API reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - App architecture details
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common tasks and solutions

## 👨‍💻 Development

### Prerequisites
- Xcode 15.0+
- iOS Simulator or device with iOS 17.0+
- (Optional) PRSNL backend for full functionality

### Common Tasks
- **Run with mock data**: Just build and run - it works out of the box
- **Test animations**: Search view has extensive animations
- **Change theme**: Edit `Core/DesignSystem.swift`
- **Add mock data**: Edit `Services/MockDataProvider.swift`

## 🎯 Next Steps

1. **Backend Integration** - Connect ViewModels to APIClient
2. **WebSocket Chat** - Implement real-time messaging
3. **Data Persistence** - Activate Core Data for offline support
4. **Testing** - Add unit and UI tests

## 📄 License

Copyright © 2025 Pranav Rajput. All rights reserved.