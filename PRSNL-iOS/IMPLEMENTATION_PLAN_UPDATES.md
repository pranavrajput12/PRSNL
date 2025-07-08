# PRSNL iOS Implementation Plan Updates

## App Icon Enhancement (July 8, 2025)

Several improvements were made to address the persistent app icon issue:

### 1. Enhanced App Icon Implementation

**Issue**: Despite previous fixes, the app icon was still showing as a white grid on iOS devices.

**Solution**:
- Created new `enhanced_app_icons.py` script with improved icon design
- Implemented blue-to-purple gradient background with bold "P" letter
- Added proper iOS-optimized rounded corners and visual depth
- Generated all required iOS icon sizes (40x40 to 1024x1024)
- Created backup of previous icons before replacement

```python
# Key implementation from enhanced_app_icons.py
def create_app_icon(size, filename):
    """Create a highly distinctive app icon guaranteed to work with iOS."""
    # Create gradient background (blue to purple)
    for i in range(size):
        for j in range(size):
            # Calculate distance from center
            center_x, center_y = size // 2, size // 2
            distance = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
            max_distance = (size // 2) * 1.4
            
            # Only fill within the icon boundary
            if distance <= size // 2:
                # Create gradient from blue to purple
                ratio = distance / max_distance
                red = int(80 + (ratio * 120))    # 80 to 200
                green = int(10 + (ratio * 50))   # 10 to 60
                blue = int(220 - (ratio * 70))   # 220 to 150
                
                img.putpixel((i, j), (red, green, blue, 255))
```

### 2. Build and Deployment Process

**Steps Taken**:
- Built app using xcodebuild targeting the iOS device
- Initially encountered provisioning profile error (Mac vs. iOS targeting)
- Corrected by explicitly specifying iOS device ID in build command
- Successfully built and installed app on device

**Current Status**:
- App installs and runs successfully
- However, app icon still appears as white grid instead of new design
- iOS icon caching may be preventing the new icon from appearing

### 3. Next Steps for App Icon Resolution

- Clear iOS icon cache by restarting the device
- If needed, try uninstalling and reinstalling the app
- Check for any iOS 17-specific icon caching issues
- Verify all app icon metadata in Contents.json is correct
- Consider creating a completely new app icon with different name/identifiers

## Critical Fixes (July 7, 2025 - PM)

Several critical issues were identified in the initial implementation that required immediate attention:

### 1. API Base URL and Authentication Correction

**Issue**: The API client was using an incorrect base URL and authentication method.

**Fix**:
- Changed base URL from `https://api.prsnl.io/v1` to `http://localhost:8000/api`
- Changed from Bearer token to X-API-Key header authentication
- Implemented the KeychainService for proper API key storage

```swift
// Corrected API Client
class APIClient {
    static let shared = APIClient()
    
    private var baseURL: String {
        let stored = KeychainService.shared.get(.serverURL) ?? "http://localhost:8000"
        return stored + "/api"
    }
    
    private var apiKey: String? {
        return KeychainService.shared.get(.apiKey)
    }
    
    // When making requests:
    if requiresAuth {
        guard let key = apiKey else {
            throw APIError.unauthorized
        }
        request.addValue(key, forHTTPHeaderField: "X-API-Key")
    }
}
```

### 2. Item and Attachment Model Correction

**Issue**: The Item model was missing required fields and the Attachment model structure was incorrect.

**Fix**:
- Updated Item model with all required fields: url, summary, status, accessCount, etc.
- Completely redesigned Attachment model to match backend schema
- Added proper enums for ItemStatus and ItemType

```swift
struct Attachment: Codable, Hashable {
    let id: String
    let fileType: String  // "image" or "video"
    let filePath: String  // Relative path like /media/attachments/...
    let mimeType: String  // e.g., "image/jpeg"
    let metadata: AttachmentMetadata?
    
    // Rest of implementation...
}
```

### 3. Updates to UI Components

**Issue**: UI components needed updates to reflect the corrected models.

**Fix**:
- Updated TimelineView to display additional item fields like status and itemType
- Improved TimelineViewModel to better handle pagination with corrected API response structure
- Enhanced ItemDetailView with proper loading and error states

These critical fixes ensure that our implementation correctly interfaces with the backend API and displays all required information correctly.

## Previous Updates

Based on additional feedback, here are important updates and clarifications to our implementation plan:

## 1. API Client Enhancements

Update the API client to support both localhost and custom server URLs:

```swift
class APIClient {
    static let shared = APIClient()
    
    private var baseURL: String {
        // Get custom URL from Keychain or fall back to localhost
        KeychainService.shared.get(.serverURL) ?? "http://localhost:8000/api"
    }
    
    // Rest of implementation...
}
```

## 2. Attachments Display

For the Timeline view, implement attachment display with this approach:

```swift
// In ItemCard
if let firstImage = item.attachments?.first(where: { $0.fileType == "image" }) {
    AsyncImage(url: URL(string: baseURL + firstImage.filePath)) { phase in
        switch phase {
        case .empty:
            ProgressView()
        case .success(let image):
            image
                .resizable()
                .aspectRatio(contentMode: .fill)
        case .failure:
            Image(systemName: "photo")
                .foregroundColor(.gray)
        @unknown default:
            EmptyView()
        }
    }
    .frame(height: 150)
    .cornerRadius(8)
}
```

For the Item Detail view, implement a simple horizontal gallery:

```swift
// Basic attachment display
ScrollView(.horizontal) {
    HStack {
        ForEach(item.attachments ?? []) { attachment in
            AsyncImage(url: URL(string: baseURL + attachment.filePath))
                .frame(width: 200, height: 150)
                .cornerRadius(8)
        }
    }
}
```

## 3. Backend Notes

- The /media/ paths were recently fixed to handle container paths correctly
- No additional action needed on our end

## 4. Share Extension Priority

Confirmed: Keep Share Extension in Phase 3 (Week 3) as planned because:
- Core app needs to be solid first
- Share extension requires app groups setup
- Better to have working capture flow to reuse
- Week 3 timing allows proper testing

## 5. Offline Support Scope

For MVP, implement medium-effort offline support:

- **Do implement**:
  - Cache timeline items, search results, and viewed items
  - Queue capture requests when offline
  - Basic sync when connection restored

- **Skip for MVP**:
  - Complex sync conflict resolution
  - Full offline editing capabilities

Example approach for offline capture:
```swift
// Simple offline queue
if !networkMonitor.isConnected {
    offlineQueue.add(captureRequest)
    showToast("Saved offline. Will sync when connected.")
}
```

## 6. Additional Performance Requirements

Beyond the targets already defined:

- **Image Memory**: Release images when > 3 screens away
- **Search Debounce**: 300ms (already in plan)
- **Background Refresh**: Limit to once per hour
- **Video Preview**: Don't auto-play, show thumbnail first

## 7. Attachments Feature Priority

Prioritize attachments implementation as:

1. **Must have**: Display attachments if they exist
2. **Nice to have**: Gallery view in detail screen
3. **Can skip**: Image zoom/pan interactions
4. **Can skip**: Download images for offline viewing

## 8. Implementation Tips

1. **Test early**: Get Timeline working with real data ASAP
2. **Use previews**: Create SwiftUI previews with mock data
3. **Handle empty states**: Backend might have no data initially
4. **Log everything**: Helps with API debugging

## Next Steps

1. Create the Xcode project
2. Copy models from SWIFT_MODELS.md
3. Add the Attachment model
4. Build the API client
5. Test with Timeline endpoint

Let's switch to Code mode to begin implementation.