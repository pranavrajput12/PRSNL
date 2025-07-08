# Testing PRSNL on a Physical Device with a Free Apple ID

This guide provides step-by-step instructions for deploying and testing the PRSNL app on your iPhone using a free Apple ID.

## Prerequisites

- Xcode 14.0+ installed on your Mac
- A free Apple ID (not requiring paid developer membership)
- iPhone running iOS 15.0 or later
- USB cable to connect your iPhone to your Mac

## Step 1: Open the Project in Xcode

1. Open Xcode on your Mac
2. Select "Open a project or file" and navigate to the PRSNL-iOS/Implementation folder
3. Select the PRSNL.xcodeproj file and click "Open"

## Step 2: Sign In with Your Apple ID

1. In Xcode, go to Xcode → Preferences (or Xcode → Settings in newer versions)
2. Go to the "Accounts" tab
3. Click the "+" button at the bottom left
4. Select "Apple ID" and click "Continue"
5. Enter your Apple ID and password
6. Click "Sign In"

## Step 3: Configure the Project for Your Personal Team

1. In Xcode's Project Navigator (left sidebar), select the PRSNL project (blue icon at the top)
2. In the main editor area, select the "PRSNL" target
3. Go to the "Signing & Capabilities" tab
4. Make sure "Automatically manage signing" is checked
5. In the "Team" dropdown, select your Personal Team (it should show your name)
6. Repeat this process for each target:
   - PRSNL (main app)
   - PRSNLWidgets (widget extension)
   - PRSNLShareExtension (share extension)

## Step 4: Create a Unique Bundle Identifier

With a free Apple ID, you need to use a unique bundle identifier to avoid conflicts:

1. Still in the "Signing & Capabilities" tab, locate the "Bundle Identifier" field
2. Change "ai.prsnl" to something unique like "com.yourname.prsnl"
3. Update this for all targets, keeping them consistent:
   - Main app: com.yourname.prsnl
   - Widget extension: com.yourname.prsnl.widgets
   - Share extension: com.yourname.prsnl.shareextension

## Step 5: Connect Your iPhone

1. Connect your iPhone to your Mac using a USB cable
2. Unlock your iPhone and trust the computer if prompted
3. In Xcode, at the top next to the Run/Stop buttons, select your iPhone from the device dropdown

## Step 6: Allow Developer Apps on Your iPhone

1. On your iPhone, go to Settings → General → VPN & Device Management
2. You should see your Apple ID listed under "Developer App"
3. Tap on your Apple ID and select "Trust"

## Step 7: Build and Run

1. In Xcode, make sure your iPhone is selected as the deployment target
2. Click the Run button (play icon) or press Cmd+R
3. The app will be installed and launched on your iPhone

## Step 8: Testing Extensions

### Widget Extension
1. After installing the app, go to your iPhone home screen
2. Long press on an empty area to enter jiggle mode
3. Tap the "+" button in the top left
4. Scroll or search for "PRSNL" in the widget gallery
5. Select and add a widget to your home screen

### Share Extension
1. Open Safari or Photos app on your iPhone
2. Find content to share (a webpage or photo)
3. Tap the Share button
4. Scroll through the share sheet to find "Share to PRSNL"
5. Tap it to use the share extension

## Important Notes for Free Apple ID Testing

1. **7-Day Expiration**: The app will stop working after 7 days and need to be reinstalled
2. **App Groups Limitations**: The app will automatically detect if App Groups are available (they typically aren't with a free Apple ID) and fall back to local storage
3. **Limited Extension Functionality**: Extensions may have limited functionality due to App Groups restrictions
4. **Status Banner**: The app shows a status banner indicating whether full or limited functionality is available

## Troubleshooting

### "Could not launch app - No code signature found"
- Go to Settings → General → VPN & Device Management
- Select your developer profile and tap "Trust"

### "Failed to register bundle identifier"
- Your bundle identifier is already in use
- Change to something more unique (add more specific identifiers)

### "App installation failed"
- Disconnect and reconnect your device
- Restart Xcode and try again

### Extensions not appearing
- This is expected with a free Apple ID due to App Groups limitations
- The app will show a banner indicating limited functionality

## Testing Strategy

Since you're working with the limitations of a free Apple ID:

1. Focus on testing the core app functionality first
2. Verify that the app properly detects the absence of App Groups
3. Check that the local storage fallback works correctly
4. Test as much extension functionality as possible, understanding some limitations
5. Use the simulator for testing features that don't work on the device due to free account limitations