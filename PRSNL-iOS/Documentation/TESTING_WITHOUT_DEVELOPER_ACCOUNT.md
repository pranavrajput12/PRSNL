# Testing PRSNL Without a Paid Developer Account

This guide explains how to test and run the PRSNL app, including its extensions, without a paid Apple Developer account.

## Running the App in Xcode Simulator

### Generating the Xcode Project

1. First, generate the Xcode project using the provided script:
   ```bash
   cd PRSNL-iOS/Implementation
   ./generate_project.sh
   ```

2. This will create a `PRSNL.xcodeproj` file that you can open in Xcode:
   ```bash
   open PRSNL.xcodeproj
   ```

### Running in the iOS Simulator

1. In Xcode, select the PRSNL target in the scheme selector
2. Choose an iOS Simulator (e.g., iPhone 14 Pro)
3. Click the "Run" button (▶️) or press Cmd+R

This will build and run the app in the iOS Simulator, where you can test most functionality:

- Timeline view with sample data
- Search functionality
- Item detail view
- Capture screen
- Settings configuration

### Testing Extensions in Simulator

#### Widget Extension

1. Run the app in the simulator first
2. Press and hold on the home screen to enter "jiggle mode"
3. Tap the "+" button to add a widget
4. Search for "PRSNL" in the widget gallery
5. Select and add the PRSNL widget

#### Share Extension

1. Run the app in the simulator
2. Open Safari or Photos app in the simulator
3. Find content to share (a webpage or image)
4. Tap the share button
5. Look for "Share to PRSNL" in the share sheet

## Testing on a Physical Device (Free Apple ID)

You can deploy the app to your physical device using just a free Apple ID, but with some limitations:

### Setup Steps

1. Sign in to Xcode with your free Apple ID (Xcode → Preferences → Accounts)
2. Connect your iPhone via USB
3. Select your device in the scheme selector
4. Modify the Bundle Identifier to be unique (e.g., add your name: "ai.prsnl.YourName")
5. In the "Signing & Capabilities" tab, check "Automatically manage signing"
6. Select your personal team from the dropdown

### Limitations with a Free Apple ID

1. **7-Day Expiration**: Apps will expire after 7 days and need to be reinstalled
2. **Limited Devices**: You can only install on a limited number of personal devices
3. **App Groups Restrictions**: App groups functionality (used for data sharing between app and extensions) may not work fully
4. **Limited Extension Support**: Widget and Share extensions may have limited functionality

### Workaround for Testing Extensions

Since app groups require a paid developer account, you can modify the code to work without them:

1. Update Core Data to use a local store instead of a shared container
2. Disable features that depend on app groups

## Adding the Privacy Manifest

You can still add the privacy manifest file regardless of developer account status:

1. Create a new file named `PrivacyInfo.xcprivacy` in the PRSNL directory
2. Add the required privacy declarations
3. Include it in the project build settings

This won't affect your ability to test the app, and it's good practice for future App Store submission.

## Viewing the App Interface

### In Xcode Interface Builder

You can preview UI components in Xcode's Interface Builder:

1. Open any SwiftUI file (e.g., `TimelineView.swift`)
2. Click the "Resume" button in the SwiftUI preview pane
3. Interact with the preview to see the interface

### In Simulator

The iOS Simulator provides the full app experience on your Mac:

1. Run the app in the simulator
2. Navigate through all screens to see the complete interface
3. Test interactions like tapping, scrolling, and form input

### Screenshot Tool

For quick UI reviews, you can use the screenshot feature in the simulator:
1. Run the app in the simulator
2. Navigate to the screen you want to capture
3. Press Cmd+S to take a screenshot

## Alternative: Web-Based Preview

If you want to share or view UI designs without running Xcode, you can:

1. Export screenshots from the simulator
2. Create a simple HTML gallery of the app's screens
3. Share this via a web browser for design reviews

## Conclusion

While a paid Apple Developer account ($99/year) provides the full development experience, you can still test most functionality with a free account. The main limitations are around app groups (used for extension data sharing) and the 7-day installation expiration.

For a complete testing experience with all features, consider getting a paid developer account before final deployment.