# PRSNL Chrome Extension Update Guide for Gemini

## 🎯 Task Overview
Update the PRSNL Chrome Extension to align with the latest backend changes in PRSNL v4.0. The extension needs significant updates to support new features including development content types, hybrid transcription, enhanced caching, and improved UI/UX.

## 📁 Chrome Extension Location
**Primary Working Directory:** `/extension/`

### Extension Files Structure:
```
/extension/
├── manifest.json        # Chrome extension manifest (v3)
├── background.js        # Service worker for background tasks
├── content.js          # Content script for page interaction
├── content.css         # Content script styles
├── popup.html          # Extension popup UI
├── popup.js            # Popup functionality
├── styles.css          # Popup styles
├── options.html        # Extension settings page
├── options.js          # Settings functionality
├── options.css         # Settings styles
└── icons/              # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## 🔍 Backend Files to Review (READ-ONLY)

### 1. API Schemas and Models
**File:** `/backend/app/models/schemas.py`
- Review the updated `CaptureRequest` schema (lines 96-150)
- New fields to support:
  - `content_type`: ["auto", "document", "video", "article", "tutorial", "image", "note", "link", "development"]
  - `programming_language`: For development content
  - `project_category`: For categorizing dev projects
  - `difficulty_level`: 1-5 scale for tutorials/learning content
  - `is_career_related`: Boolean for job/career content
  - `enable_summarization`: Toggle for AI processing
  - `uploaded_files`: Support for file uploads

### 2. Capture API Endpoint
**File:** `/backend/app/api/capture.py`
- Main capture endpoint: `POST /api/capture`
- Test endpoints for debugging
- WebSocket integration for real-time updates
- Preview service integration

### 3. New Services to Integrate
**Directory:** `/backend/app/services/`
- `hybrid_transcription.py`: Vosk + Whisper transcription
- `cache_service.py`: Redis caching for API responses
- `preview_service.py`: GitHub/URL preview generation
- `websocket_manager.py`: Real-time notifications
- `content_summarization.py`: AI summarization service

### 4. Frontend Components for Reference
**Directory:** `/frontend/src/lib/components/`
- `SafeHTML.svelte`: HTML sanitization patterns
- `development/GitHubRepoCard.svelte`: GitHub preview UI
- `development/MarkdownViewer.svelte`: Markdown rendering

### 5. Configuration Updates
**Files to check:**
- `/backend/.env.example`: Environment variables
- `/docker-compose.yml`: Service configurations
- Frontend port changed: 3002 → 3003

## 🔧 Required Updates Framework

### 1. Manifest.json Updates
```json
{
  "version": "2.0.0",  // Update version
  "host_permissions": [
    "http://localhost:8000/*",
    "http://localhost:3003/*"  // Update frontend port
  ],
  "permissions": [
    // Add if needed:
    "clipboardRead",  // For enhanced capture
    "webRequest"      // For request interception
  ]
}
```

### 2. Enhanced Capture Form (popup.html)
Add new UI elements for:
- Content type selector dropdown
- Development content fields (show/hide based on type):
  - Programming language input
  - Project category
  - Difficulty level slider (1-5)
  - Career-related checkbox
- Enable summarization toggle
- File upload support (future enhancement)

### 3. Updated Capture Logic (popup.js)
```javascript
// New capture request structure
const captureData = {
  url: currentTab.url,
  title: currentTab.title,
  content: selectedText || null,
  highlight: highlightedText || null,
  tags: tags,
  enable_summarization: enableSummarization,
  content_type: selectedContentType,
  // Development fields (if content_type === 'development')
  programming_language: programmingLanguage || null,
  project_category: projectCategory || null,
  difficulty_level: difficultyLevel || null,
  is_career_related: isCareerRelated || false
};

// API endpoint update
const response = await fetch('http://localhost:8000/api/capture', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(captureData)
});
```

### 4. Enhanced UI/UX Features
1. **Smart Content Type Detection**:
   - Auto-detect GitHub URLs → set content_type: "development"
   - Detect YouTube → set content_type: "video"
   - Programming tutorials → suggest difficulty level

2. **Visual Feedback**:
   - Loading states during capture
   - Success/error notifications
   - Progress indicators for long operations

3. **Quick Actions**:
   - One-click capture with smart defaults
   - Keyboard shortcuts for power users
   - Context menu integration

### 5. WebSocket Integration (optional)
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'capture_complete') {
    // Show success notification
  }
};
```

### 6. Styling Updates (styles.css)
- Match the neural/electrical theme from main app
- Use CSS variables for consistency:
  ```css
  :root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --bg-dark: #0a0a0a;
    --surface-dark: #1a1a1a;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
  }
  ```

## 🚀 Implementation Steps

### Phase 1: Core Updates
1. Update manifest.json with new version and permissions
2. Modify popup.html to include new form fields
3. Update popup.js with enhanced capture logic
4. Fix API endpoint URLs (port 3003)

### Phase 2: Development Content Support
1. Add content type selector UI
2. Implement conditional fields for development content
3. Add smart detection for GitHub/programming content
4. Update styles to match main app theme

### Phase 3: Enhanced Features
1. Add enable_summarization toggle
2. Implement loading states and notifications
3. Add keyboard shortcuts support
4. Create better error handling

### Phase 4: Advanced Integrations
1. WebSocket support for real-time updates
2. Preview generation for captured content
3. Offline capture queue (using chrome.storage)
4. Smart tag suggestions

## 📋 Testing Checklist
- [ ] Basic capture works with new API
- [ ] Content type selection functions properly
- [ ] Development fields appear/hide correctly
- [ ] Tags can be added and removed
- [ ] Keyboard shortcuts work
- [ ] Error handling for offline/API failures
- [ ] Visual feedback for all actions
- [ ] Settings page saves preferences
- [ ] Context menu integration works

## 🔒 Security Considerations
1. Sanitize all user inputs before sending to API
2. Use HTTPS in production (update manifest)
3. Implement proper CORS handling
4. Don't store sensitive data in extension storage

## 📝 Additional Notes
- The backend now uses PostgreSQL with pgvector for semantic search
- Redis caching is implemented for performance
- Vosk offline transcription is available as an alternative to Whisper
- The main app has comprehensive monitoring with OpenTelemetry
- Pre-commit hooks are set up for code quality

## 🎨 UI Design Principles
- Dark theme with purple/blue gradients
- Minimalist design with clear CTAs
- Smooth animations and transitions
- Accessible with proper ARIA labels
- Responsive to different popup sizes

---

**Important:** Start with Phase 1 core updates to ensure basic functionality works before adding advanced features. Test each phase thoroughly before moving to the next.