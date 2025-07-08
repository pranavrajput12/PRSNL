# PRSNL iOS App: Simulator Testing Guide

This guide provides detailed steps for testing the PRSNL iOS app in the iOS Simulator before deploying to a physical device.

## Prerequisites

- Xcode 15 or later installed
- Backend server running (as set up in the BACKEND_SETUP.md guide)
- Basic familiarity with Xcode

## Step 1: Open the Project in Xcode

1. Launch Xcode
2. Select "Open a project or file"
3. Navigate to the `PRSNL-iOS/Implementation` folder
4. Select the `PRSNL.xcodeproj` file and click "Open"
5. Wait for Xcode to index the project (this may take a few minutes the first time)

## Step 2: Configure the Simulator

1. In the Xcode toolbar, click on the device selector (next to the Run and Stop buttons)
2. Under "iOS Simulators", select an iPhone model with iOS 17.0 or later
   - Recommended: "iPhone 15 Pro" or "iPhone 14" with iOS 17.0+
   - You can also create a new simulator if needed via "Add Additional Simulators..."

## Step 3: Build and Run the App

1. Ensure the correct scheme is selected ("PRSNL" not "PRSNLShareExtension")
2. Click the "Run" button (play icon) or press `Cmd+R`
3. Wait for the app to build and launch in the simulator
4. If prompted about permissions, allow as needed

## Step 4: Configure the App in the Simulator

1. When the app launches, navigate to the Settings tab
2. In the Server Configuration section:
   - Enter Server URL: `http://localhost:8000/api`
   - Enter API Key: `test-api-key-for-development`
3. Tap "Test Connection" to verify connectivity with your local server
4. You should see a success message if the connection is established correctly

## Step 5: Test Core Functionality

### Timeline Testing

1. Navigate to the Timeline tab
2. Verify that items load from the server and display correctly
3. Pull down to refresh and verify new data loads
4. Scroll through items and check pagination works
5. Tap on an item to view details

### Search Testing

1. Navigate to the Search tab
2. Enter search terms in the search field
3. Verify search results appear correctly
4. Test filtering by tags if implemented
5. Test pagination of search results

### Capture Testing

1. Navigate to the Capture tab
2. Test creating a new item with title and content
3. Add tags to the item
4. Save the item and verify it appears in the Timeline

## Step 6: Test Offline Functionality

The iOS Simulator includes a Network Link Conditioner to simulate network conditions:

1. With the simulator running, go to Xcode menu → Devices and Simulators
2. Select the currently running simulator
3. Click the "Settings" button
4. In the Settings window, enable "Network Link Conditioner"
5. Select "100% Loss" to simulate being completely offline

While "offline":
1. Verify the app shows offline indicators
2. Verify you can still browse previously loaded data
3. Create a new item and verify it saves locally
4. Make changes to existing items

Then restore connectivity:
1. Disable the Network Link Conditioner or select "Very High Quality"
2. Pull to refresh the Timeline
3. Verify that your offline changes sync to the server

## Step 7: Inspect Logs and Debug

1. Check the Xcode debug console for any errors or warnings
2. Use the Xcode debugger to set breakpoints if needed
3. Monitor the server console for API requests and responses

## Common Simulator Issues and Solutions

### Simulator Performance Issues
- Close other applications to free up memory
- Reset the simulator (iOS Simulator → Device → Erase All Content and Settings...)
- Restart Xcode if simulator becomes unresponsive

### Network Connection Problems
- Verify the server is running (check terminal output)
- Ensure the URL is correct with `http://localhost:8000/api`
- Check if your computer has any firewall blocking localhost connections

### Core Data Issues
- If data doesn't persist correctly, check Xcode console for Core Data errors
- You might need to reset the simulator if the Core Data model has significant changes

## Moving to Physical Device Testing

Once you've verified the app works correctly in the simulator, refer to `IPHONE_TESTING_GUIDE.md` for instructions on deploying and testing on your physical iPhone.

## Simulator Tips and Tricks

- You can rotate the simulator with `Cmd+Left Arrow` and `Cmd+Right Arrow`
- Take screenshots with `Cmd+S`
- Simulate a Home button press with `Shift+Cmd+H`
- Access Control Center by swiping down from the top-right corner
- Reset the simulator content with iOS Simulator → Device → Erase All Content and Settings...
- Enable slow animations with Debug → Slow Animations in the simulator menu