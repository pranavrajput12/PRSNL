# PRSNL iOS App Architecture

## Overview
Native iOS companion app for PRSNL personal knowledge management system.

## Technology Stack
- **Framework**: SwiftUI (iOS 17+)
- **Language**: Swift 5.9+
- **Architecture**: MVVM with Combine
- **Networking**: URLSession with async/await
- **Local Storage**: Core Data + SwiftData
- **Authentication**: Keychain for API tokens
- **Minimum iOS**: 17.0

## Core Components

### 1. Data Layer
- **API Client**: RESTful communication with PRSNL backend (port 8000)
- **Local Cache**: Offline-first with Core Data
- **Sync Engine**: Background sync with conflict resolution

### 2. Features (MVP)
- **Quick Capture**: Share extension + in-app capture
- **Smart Search**: Natural language + semantic search
- **Timeline View**: Chronological content browsing
- **Item Details**: Full content view with AI insights
- **Settings**: Server configuration & preferences

### 3. Design System
- **Theme**: Manchester United red (#DC143C) accent
- **Typography**: SF Pro Display + SF Pro Text
- **Dark Mode**: Full support matching web app

## API Integration Strategy

### Endpoints to Integrate
1. **Capture**: `POST /api/capture`
2. **Search**: `GET /api/search` & `GET /api/semantic-search`
3. **Timeline**: `GET /api/timeline`
4. **Items**: `GET /api/items/{id}`
5. **Tags**: `GET /api/tags`
6. **Analytics**: `GET /api/analytics/*`

### Authentication
- Bearer token stored in Keychain
- Auto-refresh on 401 responses
- Optional biometric protection

## Asset Management

### App Icon Implementation
- **Icon Generation**: Python-based script (enhanced_app_icons.py) for programmatic icon creation
- **Icon Design**: Blue-to-purple gradient background with bold "P" letter
- **Icon Sizes**: All required iOS sizes from 20x20@2x (40×40) to 1024x1024
- **Icon Format**: PNG with proper iOS rounded corners and transparency
- **Organization**: Assets.xcassets/AppIcon.appiconset with Contents.json metadata

### Resource Organization
- **Asset Catalogs**: XCAssets for images, colors, and app icons
- **Localization**: Strings files for internationalization support
- **Dynamic Resources**: Runtime-loaded resources for flexibility

## Project Structure
```
PRSNL-iOS/
├── PRSNL/
│   ├── App/
│   │   ├── PRSNLApp.swift
│   │   └── AppDelegate.swift
│   ├── Core/
│   │   ├── API/
│   │   ├── Models/
│   │   ├── Services/
│   │   └── Extensions/
│   ├── Features/
│   │   ├── Capture/
│   │   ├── Search/
│   │   ├── Timeline/
│   │   ├── ItemDetail/
│   │   └── Settings/
│   ├── Shared/
│   │   ├── Components/
│   │   ├── Styles/
│   │   └── Utils/
│   └── Resources/
│       ├── Assets.xcassets/
│       │   ├── AppIcon.appiconset/
│       │   ├── Colors.colorset/
│       │   └── Images.imageset/
├── PRSNLShareExtension/
├── PRSNLTests/
└── PRSNLUITests/
```

## Development Phases

### Phase 1: Foundation (Week 1)
- Project setup & architecture
- API client implementation
- Core Data models
- Basic authentication

### Phase 2: Core Features (Week 2-3)
- Timeline view
- Search functionality
- Item detail view
- Basic capture

### Phase 3: Advanced Features (Week 4)
- Share extension
- Semantic search
- AI insights display
- Offline sync

### Phase 4: Polish (Week 5)
- UI animations
- Performance optimization
- Error handling
- App Store preparation

## Integration with Kilo Code

### Kilo's Responsibilities (Orchestrator)
- Project planning & task breakdown
- Code generation for views/models
- Testing coordination
- Performance optimization

### Claude02's Responsibilities (Technical Advisor)
- Architecture decisions
- API integration guidance
- Code review & quality
- Documentation

## Key Decisions

1. **SwiftUI over UIKit**: Modern, declarative, better for rapid development
2. **iOS 17+ only**: Latest features, reduced complexity
3. **Offline-first**: Core Data for reliability
4. **Share Extension**: Critical for quick capture
5. **No iPad/Mac**: Focus on iPhone experience first

## Security Considerations
- Keychain for sensitive data
- Certificate pinning for API calls
- Biometric authentication option
- No data analytics/tracking

## Performance Goals
- App launch: < 1 second
- Search results: < 500ms
- Smooth 60fps scrolling
- Offline capability for recent items