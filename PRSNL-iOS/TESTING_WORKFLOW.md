# PRSNL iOS App: Recommended Testing Workflow

This guide outlines the recommended testing workflow for the PRSNL iOS application, starting with local simulator testing before moving to a physical device.

## Testing Workflow Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Local Testing  │     │ Simulator       │     │ Physical Device │
│  Backend Server │────►│ Testing         │────►│ Testing         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Phase 1: Local Simulator Testing

Testing with the iOS Simulator is faster and more convenient for initial development and testing.

### Benefits of Simulator Testing First:

1. **Faster deployment** - No need to provision a physical device
2. **Quicker iterations** - Build and run cycles are faster
3. **Easier debugging** - Direct access to logs and debugging tools
4. **Multiple device simulation** - Test on different iOS device types and iOS versions
5. **Network simplicity** - Local server works with `localhost` URLs without configuration

### Setup for Simulator Testing:

1. **Start the Local Backend Server**
   ```bash
   mkdir prsnl-backend
   cd prsnl-backend
   npm init -y
   npm install express cors body-parser uuid
   # Create server.js with the content from BACKEND_SETUP.md
   node server.js
   ```

2. **Configure Xcode for Simulator**
   - Open the PRSNL project in Xcode
   - Select an iOS Simulator from the device dropdown (e.g., iPhone 15 Pro)
   - Build and run the app (⌘R)

3. **Configure the App**
   - When the app launches in the Simulator, go to Settings
   - Enter server URL: `http://localhost:8000/api`
   - Enter API key: `test-api-key-for-development`
   - Test the connection

4. **Test Core Functionality**
   - Browse the Timeline
   - Search for items
   - Create new items
   - Verify data persistence

5. **Test Offline Support**
   - Use the Network Link Conditioner in Xcode to simulate network conditions:
     - Xcode → Window → Devices and Simulators → Simulators
     - Select your running simulator
     - Click "Settings" button
     - Enable "Network Link Conditioner" and select "100% Loss" to simulate offline
   - Verify offline indicators appear
   - Test creating and modifying data while offline
   - Disable the Network Link Conditioner to test sync upon reconnection

## Phase 2: Physical Device Testing

Once the app works well in the Simulator, it's time to test on a physical device.

### When to Move to Device Testing:

Move to device testing when:
- Basic functionality works well in the Simulator
- You want to test real-world performance
- You need to test device-specific features (camera, notifications, etc.)
- You want to test on actual network conditions
- You're preparing for distribution

### Setup for iPhone Testing:

1. **Keep the Backend Server Running**
   - The same server you used for Simulator testing will work
   - Note your computer's IP address (System Preferences → Network)

2. **Deploy to Your iPhone**
   - Connect your iPhone to your Mac
   - In Xcode, select your iPhone from the device dropdown
   - Ensure signing is configured correctly
   - Build and run the app on your device (⌘R)

3. **Configure the App on Your iPhone**
   - When the app launches on your iPhone, go to Settings
   - Enter server URL: `http://YOUR_COMPUTER_IP:8000/api` (replace with your actual IP)
   - Enter API key: `test-api-key-for-development`
   - Test the connection

4. **Test Core Functionality Again**
   - Repeat the same tests you performed in the Simulator
   - Pay attention to performance differences
   - Test any device-specific features

5. **Test Offline Support in Real Conditions**
   - Enable Airplane Mode on your iPhone
   - Verify offline indicators appear
   - Test functionality while offline
   - Disable Airplane Mode to test automatic sync

## Testing Tips

1. **Version Increment Testing**
   - Increment the build number in Xcode when testing significant changes
   - This helps track which version introduced issues

2. **Database Wiping**
   - To test fresh installs, uninstall the app completely from the device/simulator
   - For the Simulator, you can also reset content and settings:
     - iOS Simulator → Device → Erase All Content and Settings...

3. **Testing Sync Conflicts**
   - Make changes on the Simulator while the device is offline
   - Then make conflicting changes on the physical device
   - Reconnect the device and observe how conflicts are resolved

4. **Network Variability**
   - Test on different WiFi networks
   - Test using cellular data (on physical device)
   - Test transitions between WiFi and cellular

5. **Background/Foreground Transitions**
   - Test how the app behaves when sent to background and brought back
   - Verify sync status is maintained correctly

## Special Testing Cases

### App Icon Verification:
- **Icon Display Testing**:
  - After installing the app, check if the correct icon appears on the home screen
  - Verify the icon is not showing as a white grid or placeholder
  - Ensure icon corners are properly rounded and match iOS styling
  - Check if the icon appears correctly in the app switcher

- **Icon Troubleshooting**:
  - If the icon appears as a white grid, try restarting the device to clear the icon cache
  - If that doesn't work, uninstall and reinstall the app
  - Verify the app's Assets.xcassets/AppIcon.appiconset contains all required icon sizes
  - Check that Contents.json in the AppIcon.appiconset is correctly formatted
  - Try running enhanced_app_icons.py to regenerate icons if needed

## Troubleshooting Common Issues

### Local Server Connectivity Issues:
- Ensure server is running
- Check for any firewall blocking connections
- Verify correct IP address is being used
- Make sure device and computer are on the same network
- Try temporarily disabling any VPNs

### App Crashes:
- Check Xcode logs (Window → Devices and Simulators → Select your device → View device logs)
- Look for any Core Data migration issues
- Check for API response handling errors

### Sync Problems:
- Verify network connectivity
- Check if API key is correct
- Look at server logs for API errors
- Verify that the server is handling requests correctly

### App Icon Problems:
- Check if iOS is caching the old icon (restart device to clear cache)
- Verify all required icon sizes are present in Assets.xcassets/AppIcon.appiconset
- Ensure proper metadata in Contents.json matches the actual icon filenames
- Confirm that icons have proper alpha channel and transparency
- Run xcodebuild clean before rebuilding to clear build cache

## Conclusion

Following this two-phase testing approach allows for efficient development:

1. Use the Simulator for rapid iteration and core functionality testing
2. Move to a physical device for real-world testing and final verification

This workflow balances development speed with thorough testing, ensuring the app works well in both controlled and real-world environments.