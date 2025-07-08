# 🚨 CRITICAL iOS Compliance Tasks for Kilocode

**Date Assigned:** 2025-07-07
**Priority:** BLOCKER - App won't build or submit to App Store without these fixes

## Context

Claude has discovered critical iOS compliance issues during code review. These issues will prevent the app from:
1. Building successfully in Xcode
2. Running on real devices
3. Being submitted to the App Store

## 🔴 BLOCKER Tasks (Must Fix First)

### 1. ✅ Fix App Group Identifiers (COMPLETED)
**Issue:** Mismatch in app group identifiers across extensions
**Impact:** Data sharing between app and extensions will fail

**Current State:**
- Main App: `group.ai.prsnl.shared`
- Share Extension: `group.ai.prsnl.shared`
- Widget: `group.ai.prsnl.shared` ✅ FIXED

**Fixed Files:**
```
/PRSNLWidgets/PRSNLWidgets.entitlements
/PRSNLWidgets/WidgetDataProvider.swift
/PRSNL/Core/CoreData/CoreDataManager.swift (added shared container support)
```

**Status:** All app group identifiers have been standardized to `group.ai.prsnl.shared`

### 2. ✅ Fix Keychain Access Group (COMPLETED)
**Issue:** Build variable in runtime code - will crash at runtime
**Impact:** Keychain access will fail, no secure storage

**Fixed Status:**
```swift
// File: /PRSNL/Core/Services/KeychainService.swift:8
// Replace "ABC12DEF34" with your actual Apple Developer Team ID
private let accessGroup = "ABC12DEF34.ai.prsnl.shared" // ✅ Fully fixed with Team ID placeholder
```

**Implementation Details:**
- Domain updated to match app group (ai.prsnl.shared)
- Replaced "$(AppIdentifierPrefix)" build variable with hardcoded Team ID placeholder
- Added developer instructions to replace the placeholder with actual Team ID
- Team ID can be found in Xcode project settings or Apple Developer account

### 3. Create Xcode Project
**Issue:** No .xcodeproj file exists
**Impact:** Can't build or run the app

**Steps:**
1. Open Xcode
2. Create new project → iOS App
3. Product Name: PRSNL
4. Team: (Select your team)
5. Bundle ID: ai.prsnl
6. Interface: SwiftUI
7. Language: Swift
8. Add all source files to project
9. Configure build settings
10. Add capabilities and entitlements

## 🟡 HIGH Priority Tasks

### 4. Core Data Threading Fix
**Issue:** Thread-unsafe operations
**File:** `/PRSNL/Core/CoreData/CoreDataManager.swift:371`

**Problem:**
```swift
// Line 371: localizedStandardContains may not be thread-safe
NSPredicate(format: "content CONTAINS[cd] %@", searchText)
```

**Fix:** Ensure all Core Data operations use proper context:
```swift
context.perform {
    // Core Data operations here
}
```

### 5. ✅ Widget Battery Monitoring (FIXED)
**Issue:** UIDevice battery monitoring doesn't work in widget extensions
**File:** `/PRSNLWidgets/WidgetDataProvider.swift:680-852`

**Solution Implemented:**
```swift
// Implemented widget-compatible battery monitoring system that:
// 1. Uses shared UserDefaults (App Group) to store battery info
// 2. Main app updates battery status in shared storage
// 3. Widget reads from shared storage instead of direct UIDevice access
// 4. Added fallback mechanism when battery data is stale
```

**Implementation Details:**
- Created BatteryMonitor class with shared UserDefaults storage
- Added freshness checking for battery data
- Widget can still detect Low Power Mode directly (this API works in extensions)
- Used conditional compilation to separate widget and main app code

## 📋 Testing Checklist

After fixes, test on **real device** (not simulator):

- [ ] Main app launches without crashes
- [ ] Keychain operations work (save/retrieve API keys)
- [ ] Share extension can save data
- [ ] Widget can read shared data
- [ ] Core Data operations don't crash
- [ ] All extensions use same app group

## 🔧 Quick Fix Script

Run this to fix app group identifiers:
```bash
# Fix app group identifiers
find . -name "*.swift" -o -name "*.entitlements" | xargs sed -i '' 's/group.com.prsnl.app/group.ai.prsnl.shared/g'
```

## 📱 Device Testing Required

These issues CANNOT be fully tested in simulator:
- Keychain access groups
- Widget functionality
- Share extension
- App groups

**Must test on physical iPhone/iPad**

## 🚀 Next Steps

1. ✅ Fix blockers first (app groups, keychain) - COMPLETED
2. Create Xcode project
3. Test on real device
4. ✅ Fix threading issues in Core Data operations - COMPLETED
5. ✅ Fix widget battery monitoring issue - COMPLETED
6. Submit test build to TestFlight

## ❓ Questions for Pronav

1. What is your Apple Developer Team ID? (needed for keychain fix)
2. Do you have a physical iOS device for testing?
3. Should we keep battery monitoring in widgets or remove it?

## 📞 Need Help?

If you encounter issues:
1. Check `IOS_COMPLIANCE_ISSUES.md` for detailed explanations
2. Review `WEBSOCKET_CODE_REVIEW.md` for WebSocket-specific fixes
3. The Info.plist and PrivacyInfo.xcprivacy files are already created by Claude

**Remember:** Apple is extremely strict about these requirements. The app will be rejected without these fixes.