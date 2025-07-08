# PRSNL iOS App Co-Development Prompt for Claude

## Overview

Hello Claude! We've established a co-development workflow for the PRSNL iOS companion app where you and Kilo Code will work on separate features to avoid file conflicts. Kilo Code has already implemented several features, and now it's time for you to start working on your assigned responsibilities.

## Project Architecture

- SwiftUI (iOS 17.0+) for UI framework
- MVVM with Combine for architecture
- URLSession with async/await for networking
- Core Data (planned) for local storage
- Keychain for API key storage
- X-API-Key authentication pattern
- Manchester United red theme (#DC143C)

## Current Status

Kilo Code has completed:
- API client implementation with proper authentication
- Core models for Item and Attachment
- Timeline feature (view and view model)
- Item detail view component
- Search feature with pagination

## Your Assigned Tasks

You're assigned to implement:
1. Capture feature (immediate priority)
2. Settings screen
3. Share extension
4. Offline support

## Guidelines for Implementation

To avoid file conflicts, please:
1. Create new files in the appropriate directories
2. Don't modify files already created by Kilo Code
3. Use the existing APIClient for network requests
4. Follow the established naming conventions and architecture patterns
5. Document your work in the coordination files

## Specific Files to Create (Don't Modify Existing Files)

For the Capture feature, create these new files:
- `PRSNL-iOS/Implementation/PRSNL/Features/Capture/CaptureView.swift`
- `PRSNL-iOS/Implementation/PRSNL/Features/Capture/CaptureViewModel.swift`
- `PRSNL-iOS/Implementation/PRSNL/Features/Capture/MediaPickerView.swift` (for image/document selection)

For Settings:
- `PRSNL-iOS/Implementation/PRSNL/Features/Settings/SettingsView.swift`
- `PRSNL-iOS/Implementation/PRSNL/Features/Settings/SettingsViewModel.swift`

## Capture Feature Requirements

The Capture feature should:
- Allow users to create new Items (notes, articles, etc.)
- Support adding title, content, and tags
- Enable attachment of images or documents
- Validate input before submission
- Show progress during API submission
- Handle success and error states
- Use the `APIClient.createItem()` method for submission

## API Integration

The APIClient already has a `createItem` method you can use:
```swift
func createItem(title: String, content: String, tags: [String], itemType: ItemType = .note) async throws -> Item
```

## Coordination Mechanism

We're using these files for coordination:
- `PRSNL-iOS/Coordination/AI_COORDINATION_LOG.md` - Direct communication between AIs
- `PRSNL-iOS/Coordination/IMPLEMENTATION_STATUS.md` - Overall project status
- `PRSNL-iOS/Coordination/DAILY_UPDATES.md` - Daily progress

Please update these files when you make progress or have questions.

## Next Steps

1. Review the existing codebase to understand the architecture
2. Implement the CaptureView and CaptureViewModel 
3. Update the App navigation to connect your new view
4. Document your implementation in the coordination files

Once you've completed a feature, please note it in the AI_COORDINATION_LOG.md file so Kilo Code is aware of your progress.

Let's build this app together while working on separate components!