# PRSNL iOS Documentation Index

## Complete Documentation Package for Kilo Code

This index provides a comprehensive overview of all documentation created for the PRSNL iOS app development. Kilo Code should review these documents in order.

### 📋 Core Documentation

1. **[PROJECT_BRIEF.md](./PROJECT_BRIEF.md)**
   - Quick start guide
   - Critical rules and boundaries
   - MVP features
   - First steps to take

2. **[KILO_CODE_GUIDE.md](./KILO_CODE_GUIDE.md)**
   - ⚠️ CRITICAL: Working directory boundaries
   - Complete API endpoint reference
   - Response formats and examples
   - Rate limits and constraints

3. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - Technology decisions (SwiftUI, iOS 17+)
   - MVVM architecture pattern
   - Project structure
   - Development phases

### 🔧 Implementation Guides

4. **[SWIFT_MODELS.md](./SWIFT_MODELS.md)**
   - Ready-to-copy Swift models
   - Exact match to backend schemas
   - Validation logic included
   - Custom date encoders/decoders

5. **[API_INTEGRATION.md](./API_INTEGRATION.md)**
   - URLSession implementation examples
   - Async/await patterns
   - Error handling
   - Offline support strategy

6. **[AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)**
   - Keychain integration for API keys
   - Settings screen implementation
   - Authentication flow
   - Future JWT migration notes

### 🚀 Advanced Features

7. **[WEBSOCKET_GUIDE.md](./WEBSOCKET_GUIDE.md)**
   - Real-time AI streaming
   - Live tag suggestions
   - URLSessionWebSocketTask implementation
   - Reconnection strategies

8. **[VIDEO_HANDLING_GUIDE.md](./VIDEO_HANDLING_GUIDE.md)**
   - Video playback with AVPlayer
   - Thumbnail loading and caching
   - Platform-specific handling (YouTube, Instagram, TikTok)
   - Performance optimizations

9. **[SHARE_EXTENSION_GUIDE.md](./SHARE_EXTENSION_GUIDE.md)**
   - Chrome extension feature parity
   - Share extension implementation
   - App group configuration
   - Offline capture queuing

10. **[ERROR_HANDLING_GUIDE.md](./ERROR_HANDLING_GUIDE.md)**
    - Comprehensive error types
    - User-friendly error presentation
    - Retry logic with exponential backoff
    - Network monitoring

### 📝 Planning & Coordination

11. **[DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md)**
    - Agent collaboration structure
    - Phased development approach
    - Testing strategy
    - Deployment preparation

### 🎯 Key Technical Decisions

Based on the codebase analysis:

1. **Backend Compatibility**
   - API running on port 8000
   - PostgreSQL with pgvector for semantic search
   - Multi-provider AI support (Ollama, Azure OpenAI, Anthropic)

2. **Design System**
   - Manchester United red theme (#DC143C)
   - Dark mode by default
   - Consistent with web app aesthetics

3. **Performance Requirements**
   - App launch < 1 second
   - Search results < 500ms
   - 60fps scrolling
   - Efficient video loading

4. **Security**
   - API keys in Keychain
   - No analytics or tracking
   - Local-first approach
   - Certificate pinning (future)

### 🚫 Critical Boundaries

**REMEMBER**: 
- Only work in `/PRSNL-iOS/` directory
- Do not modify `/PRSNL/` files
- Do not interact with other agents' task files
- The backend is complete - only consume the API

### 🏃‍♂️ Getting Started

1. Create Xcode project in `/PRSNL-iOS/`
2. Copy models from `SWIFT_MODELS.md`
3. Implement `APIClient` from examples
4. Build Timeline view first (easiest to test)
5. Test with running backend

### 📞 Support

- **Technical Questions**: Ask Claude02 for guidance
- **Backend Issues**: Do not modify - report to Claude02
- **Documentation Updates**: Request through Claude02

This documentation package provides everything needed to build a fully-featured iOS client for PRSNL. The backend team (Claude, Windsurf, Gemini) continues to work on the web application independently.

---

## Backend API Status

Current backend endpoints status (as of 2025-07-07):
- ✅ Core APIs: Working
- ✅ Semantic Search: Implemented
- ✅ Video Processing: Complete
- ✅ WebSocket Streaming: Available
- ✅ Analytics: New endpoints added
- ⚠️ AI Suggestions: Connection issues being debugged

The iOS app should gracefully handle any endpoint failures and provide appropriate fallbacks.