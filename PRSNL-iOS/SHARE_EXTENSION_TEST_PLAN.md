# PRSNL iOS Share Extension Test Plan

## Overview
This document outlines the testing procedures for the PRSNL Share Extension.

## Test Environment Setup
1. Install the PRSNL app on an iOS device or simulator
2. Configure API settings in the main app (Settings > API Configuration)
3. Ensure the backend server is running at http://localhost:8000

## Test Cases

### 1. Sharing URLs from Safari
**Steps:**
1. Open Safari and navigate to any webpage
2. Tap the Share button
3. Select "Save to PRSNL"
4. Add tags (optional)
5. Tap "Save to PRSNL"

**Expected Result:**
- URL and page title are captured
- Item appears in timeline after sync

### 2. Sharing Selected Text from Safari
**Steps:**
1. Open Safari and navigate to any webpage
2. Select some text on the page
3. Tap Share from the selection menu
4. Select "Save to PRSNL"
5. Add tags (optional)
6. Tap "Save to PRSNL"

**Expected Result:**
- Selected text is captured as content
- URL and title are also captured
- Item type shows as "Selection"

### 3. Sharing Images from Photos
**Steps:**
1. Open Photos app
2. Select an image
3. Tap Share button
4. Select "Save to PRSNL"
5. Add tags (optional)
6. Tap "Save to PRSNL"

**Expected Result:**
- Image preview is shown in share sheet
- Image is uploaded when online
- Item type shows as "Image"

### 4. Sharing from Other Apps
**Test with:**
- Twitter/X: Share tweets
- News apps: Share articles
- Notes: Share text content
- Files: Share documents

### 5. Offline Functionality
**Steps:**
1. Enable Airplane Mode
2. Share content from any app
3. Tap "Save to PRSNL"

**Expected Result:**
- Content is saved locally
- Item shows sync pending indicator
- Item syncs when connection restored

### 6. Tag Management
**Test:**
- Adding new tags
- Using recent tags
- Removing tags
- Tag validation (lowercase, trimming)

### 7. Error Handling
**Test:**
- Invalid API key
- Server unreachable
- Network timeout
- Large file uploads

### 8. Performance Tests
- Share extension launch time < 1 second
- Content processing < 2 seconds
- No memory warnings with large images

## Known Limitations
- Single item sharing only (no batch)
- Image size limited by iOS memory constraints
- Video sharing not yet implemented

## Debugging Tips
1. Check Console logs for ShareExtension process
2. Verify app group configuration in Xcode
3. Test with clean install after configuration changes
4. Use Network Link Conditioner to test poor connections