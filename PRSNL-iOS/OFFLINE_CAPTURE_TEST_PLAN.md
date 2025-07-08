# PRSNL iOS Offline Capture Test Plan

## Overview
This document outlines testing procedures for the offline capture functionality in the PRSNL iOS app.

## Features Implemented
1. **Offline Detection**: CaptureViewModel checks NetworkMonitor.isConnected
2. **Offline Storage**: Items saved to Core Data with `needsUpload` sync status
3. **Offline Indicator**: Visual indicator in CaptureView when offline
4. **Automatic Sync**: SyncManager triggered when connection restored
5. **Offline Tags**: Recent tags loaded from Core Data when offline

## Test Scenarios

### 1. Basic Offline Capture
**Steps:**
1. Enable Airplane Mode on device/simulator
2. Open the Capture tab
3. Verify offline indicator appears (orange banner)
4. Fill in capture form:
   - URL: https://example.com
   - Title: Test Offline Capture
   - Tags: offline, test
5. Tap "Capture"

**Expected Results:**
- Success message: "Saved offline. Will sync when connected"
- Form clears after capture
- Item saved to Core Data with local ID (prefix: "local-")

### 2. Offline to Online Transition
**Steps:**
1. Capture item while offline (as above)
2. Navigate to Timeline tab
3. Verify item appears with sync pending indicator
4. Disable Airplane Mode
5. Wait for automatic sync

**Expected Results:**
- Item syncs to server automatically
- Local ID replaced with server ID
- Sync status updated to "synced"
- Item remains in timeline

### 3. Offline Tag Management
**Steps:**
1. Enable Airplane Mode
2. Open Capture tab
3. Check if recent tags load

**Expected Results:**
- Recent tags loaded from Core Data
- Tags can be added/removed normally
- New tags saved locally

### 4. Mixed Content Types Offline
**Test each type:**
- URL only capture
- Note only capture (no URL)
- URL with content
- All fields filled

**Expected Results:**
- All content types save successfully offline
- Appropriate item types assigned (article vs note)

### 5. Error Handling
**Test:**
1. Fill very long content (>10000 chars)
2. Invalid URLs
3. Empty form submission

**Expected Results:**
- Validation works offline
- Appropriate error messages shown
- No data loss

### 6. Performance Testing
**Measure:**
- Time to save offline capture
- Memory usage with multiple offline items
- Core Data query performance

**Target Metrics:**
- Save time < 100ms
- Smooth UI with 100+ offline items

## Verification Commands

### Check Core Data Contents
```swift
// In Xcode debugger console
po CoreDataManager.shared.fetchItems()
```

### Check Sync Status
```swift
// Check items needing sync
let needsSync = try CoreDataManager.shared.fetchItemsNeedingSync()
print("Items pending sync: \(needsSync.count)")
```

### Monitor Network Status
```swift
print("Is connected: \(NetworkMonitor.shared.isConnected)")
```

## Known Limitations
1. Full item details not available until sync completes
2. Attachments not supported in offline capture yet
3. Search may not find offline items until indexed

## Success Criteria
- [ ] All offline captures save successfully
- [ ] Sync works automatically when connection restored
- [ ] No data loss during offline/online transitions
- [ ] User clearly informed of offline status
- [ ] Performance remains acceptable