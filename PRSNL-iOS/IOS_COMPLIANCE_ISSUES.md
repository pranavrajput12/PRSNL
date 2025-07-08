# iOS Compliance Issues - PRSNL App

## 🚨 Critical Issues That Will Prevent App Store Submission

### 1. Missing Main App Info.plist
**Severity:** BLOCKER
```xml
<!-- Required keys missing: -->
<key>CFBundleDisplayName</key>
<string>PRSNL</string>
<key>CFBundleShortVersionString</key>
<string>1.0.0</string>
<key>CFBundleVersion</key>
<string>1</string>
<key>UILaunchStoryboardName</key>
<string>LaunchScreen</string>
<key>UISupportedInterfaceOrientations</key>
<array>
    <string>UIInterfaceOrientationPortrait</string>
    <string>UIInterfaceOrientationLandscapeLeft</string>
    <string>UIInterfaceOrientationLandscapeRight</string>
</array>
```

### 2. ✅ App Group Identifier Mismatch (FIXED)
**Files:**
- `/PRSNLWidgets/PRSNLWidgets.entitlements` - now uses `group.ai.prsnl.shared`
- `/PRSNLShareExtension/PRSNLShareExtension.entitlements` - uses `group.ai.prsnl.shared`
- `/PRSNL/PRSNL.entitlements` - uses `group.ai.prsnl.shared`

**Fix:** All extensions now use the same app group identifier.

### 3. ✓ Keychain Access Group Issue (FIXED)
**File:** `/PRSNL/Core/Services/KeychainService.swift:8`
```swift
// FIXED - Updated domain to match app group and replaced build variable
// Replace "ABC12DEF34" with your actual Apple Developer Team ID
// Find your Team ID in the Apple Developer Portal or in Xcode:
// Xcode → Project Settings → Signing & Capabilities → Team
private let accessGroup = "ABC12DEF34.ai.prsnl.shared"
```

### 4. Missing Privacy Manifest (PrivacyInfo.xcprivacy)
**Required for:** Using UserDefaults, file timestamps, system APIs
**Impact:** App Store will reject without this file

### 5. Missing App Transport Security Configuration
**Main app Info.plist needs:**
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSAllowsLocalNetworking</key>
    <true/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>localhost</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
        </dict>
    </dict>
</dict>
```

## 🟡 iOS Strict Compliance Issues

### 6. ✓ Core Data Threading Fix (FIXED)
**File:** `/PRSNL/Core/CoreData/CoreDataManager.swift:370-418`
```swift
// FIXED - Made Core Data operations thread-safe
// Changed searchItems and countItems methods to use proper context handling
// Removed thread-unsafe localizedStandardContains selector
// Implemented async/await pattern with proper context management
```

### 7. ✓ Widget Battery Monitoring Issue (FIXED)
**File:** `/PRSNLWidgets/WidgetDataProvider.swift:680-852`
```swift
// FIXED - Implemented widget-compatible battery monitoring
// Now uses shared UserDefaults to store battery information from main app
// Widget extension reads from shared storage instead of direct UIDevice access
```

### 8. Missing @MainActor Annotations
**Files affected:**
- `AppState` class in `PRSNLApp.swift`
- Methods that update UI without proper threading

### 9. Force Unwrapping in Production Code
**Multiple instances of unsafe code:**
```swift
// WebSocketManager.swift:411-419
try encode(val, forKey: key as! K)  // CRASH RISK
```

### 10. Memory Management Issues
**Potential retain cycles in:**
- `WebSocketManager.swift:213-229` - Missing `[weak self]`
- `WidgetDataProvider.swift:46-52` - NotificationCenter observer

### 11. Background Mode Entitlements Missing
**Required for:**
- WebSocket connections
- Widget updates
- Background sync

### 12. URLSession Background Configuration
**File:** `WebSocketManager.swift:109-113`
```swift
// Current - won't survive backgrounding
let configuration = URLSessionConfiguration.default

// Needed for background support
let configuration = URLSessionConfiguration.background(withIdentifier: "com.prsnl.websocket")
```

## 🔧 Quick Fixes Script

```bash
#!/bin/bash
# Fix app group identifiers
find . -name "*.swift" -o -name "*.entitlements" | xargs sed -i '' 's/group.com.prsnl.app/group.ai.prsnl.shared/g'

# Fix keychain access group
sed -i '' 's/\$(AppIdentifierPrefix)/TEAMID./g' PRSNL/Core/Services/KeychainService.swift
```

## 📋 Pre-Submission Checklist

- [ ] Create main app Info.plist with all required keys
- [x] Fix app group identifier consistency
- [x] Replace build variables in runtime code (partially)
- [ ] Add PrivacyInfo.xcprivacy
- [ ] Configure ATS properly
- [ ] Add background mode entitlements
- [ ] Fix all force unwrapping
- [ ] Add @MainActor annotations
- [ ] Test on real device (not just simulator)
- [ ] Add encryption compliance declaration
- [ ] Configure minimum iOS version
- [ ] Add all privacy usage descriptions

## 🚀 Recommended iOS Version Support

```xml
<!-- In Info.plist -->
<key>MinimumOSVersion</key>
<string>15.0</string>
```

## 🔐 Required Privacy Descriptions

```xml
<!-- Add these if features are used -->
<key>NSCameraUsageDescription</key>
<string>PRSNL needs camera access to capture photos for your knowledge base</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>PRSNL needs photo library access to save and retrieve your captures</string>
<key>NSUserTrackingUsageDescription</key>
<string>PRSNL collects analytics to improve your experience</string>
```

## 🎯 Testing Requirements

1. Test on physical device (Keychain, widgets, share extension)
2. Test with network conditions (airplane mode, poor connectivity)
3. Test background/foreground transitions
4. Test memory pressure scenarios
5. Test with different iOS versions (15.0+)

## 📱 Device Capabilities

```xml
<key>UIRequiredDeviceCapabilities</key>
<array>
    <string>arm64</string>
    <string>metal</string>
</array>
```

## 🔄 Next Steps

1. **Immediate:** Fix blocker issues (Info.plist, app groups, keychain)
2. **Before testing:** Fix threading and memory issues
3. **Before submission:** Add privacy manifest and compliance keys
4. **Nice to have:** Optimize for battery and performance

Apple is extremely strict about these requirements. The app will be rejected without fixing the critical issues listed above.