# PRSNL Share Extension

The Share Extension allows users to share content from other apps directly to the PRSNL app. This extension integrates with iOS's native share functionality to capture various types of content and save them to the PRSNL app's Core Data store.

## Features

- Share URLs from Safari and other apps to PRSNL
- Share text from any app that supports text sharing
- Share images from Photos app or other image sources
- Add notes to shared content before saving
- Access shared Core Data container for seamless data integration

## Implementation Details

### Data Sharing Architecture

The Share Extension uses Apple's App Groups feature to access the same Core Data store as the main app. This is configured with:

- App Group identifier: `group.ai.prsnl.shared`
- Shared Core Data store located in the app group container

### ShareViewController

The `ShareViewController` is the main class that handles the share extension functionality:

1. Extracts shared content from the extension context
2. Displays UI for user to review and annotate the content
3. Saves the content to the shared Core Data store
4. Handles various content types (URLs, text, images)

### Core Data Integration

The extension accesses the shared Core Data store by:

1. Creating a persistent container with the same model as the main app
2. Configuring the store URL to point to the shared container
3. Creating and managing proper background contexts for data operations

### Security Considerations

- The extension uses the same keychain access group as the main app
- Proper entitlements are configured for app group access
- Data validation is performed before saving to the store

## Usage

1. In any app with share functionality, tap the share button
2. Select "Share to PRSNL" from the share sheet
3. Review the content in the share extension UI
4. Add any notes if desired
5. Tap "Save" to store the content in PRSNL or "Cancel" to dismiss

## Technical Requirements

- iOS 15.0+
- Xcode 16.0+
- Swift 5.0+
- App Group entitlement in provisioning profile