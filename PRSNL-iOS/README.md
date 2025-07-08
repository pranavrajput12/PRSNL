# PRSNL iOS App

Native iOS companion app for PRSNL personal knowledge management system.

## Overview
This iOS app provides mobile access to your PRSNL knowledge base with features optimized for on-the-go capture and retrieval.

## Features
- 📱 **Quick Capture**: Share extension for instant content saving
- 🔍 **Smart Search**: Natural language and semantic search
- 📅 **Timeline View**: Browse your knowledge chronologically
- 🏷️ **Smart Tags**: AI-generated and manual tagging
- 🔄 **Offline Sync**: Access recent items without connection
- 🎨 **Manchester United Theme**: Consistent with web app design

## Requirements
- iOS 17.0+
- Xcode 15.0+
- Swift 5.9+
- PRSNL backend running on local network or accessible server

## Setup Instructions

### 1. Configure Backend Connection
1. Ensure PRSNL backend is running (default: http://localhost:8000)
2. Update `API_BASE_URL` in app settings
3. Generate API token from web interface

### 2. Build & Run
```bash
cd PRSNL-iOS
open PRSNL.xcodeproj
# Select target device/simulator
# Build and run (Cmd+R)
```

### 3. Configure Share Extension
1. Enable Share Extension in iOS Settings
2. Add to favorite share destinations
3. Use Cmd+Shift+S equivalent gesture

## Architecture
- **Framework**: SwiftUI with MVVM
- **Networking**: URLSession + async/await
- **Storage**: Core Data for offline cache
- **Min iOS**: 17.0 (latest features)

## Development Team
- **Claude02**: Architecture & Technical Advisory
- **Kilo Code**: Orchestration & Implementation
- Working independently from main PRSNL 3-agent team

## API Integration
Connects to PRSNL backend API:
- Capture endpoint for content saving
- Search endpoints (keyword + semantic)
- Timeline API for chronological browsing
- Analytics for insights display

## Roadmap
- [ ] Phase 1: Foundation & API Client
- [ ] Phase 2: Core Features (Timeline, Search, Capture)
- [ ] Phase 3: Advanced Features (Share Extension, Semantic Search)
- [ ] Phase 4: Polish & App Store Preparation
- [ ] Future: iPad support, widgets, Apple Watch app