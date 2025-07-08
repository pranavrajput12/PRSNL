# PRSNL iOS App Deployment Guide

This guide provides instructions for deploying the PRSNL iOS app to a physical device and configuring it to work with an online server.

## Deploying to a Physical Device

### Prerequisites
- macOS computer with Xcode 15 or later installed
- Apple Developer account (can be a free Apple ID for development-only builds)
- iPhone with iOS 17.0 or later
- Lightning or USB-C cable to connect your iPhone to your Mac

### Steps to Deploy

1. **Open the Project in Xcode**
   - Open Xcode
   - Navigate to File > Open
   - Select the `PRSNL-iOS/Implementation/PRSNL.xcodeproj` file

2. **Set Up Code Signing**
   - Click on the project name in the Project Navigator
   - Select the "PRSNL" target
   - Go to the "Signing & Capabilities" tab
   - Check "Automatically manage signing"
   - Select your Team (Apple ID)
   - If you see any signing errors, click "Try Again" or "Fix Issue"

3. **Connect Your iPhone**
   - Connect your iPhone to your Mac using a USB cable
   - Unlock your iPhone
   - Trust the computer if prompted on your iPhone

4. **Select Your Device for Deployment**
   - In Xcode, click on the device selector in the toolbar (near the Run button)
   - Select your connected iPhone from the list

5. **Run the App**
   - Click the "Run" button (play icon) in Xcode
   - The app will be built and installed on your device
   - The first time you run the app on your device, you may need to go to:
     Settings > General > Device Management > [Your Apple ID] > Trust

## Configuring for Online Server

The PRSNL app is designed to work with a backend server while supporting offline use. Here's how to configure it:

### Setting the Server URL and API Key

1. **Launch the App** on your iPhone

2. **Navigate to Settings**
   - Tap on the Settings tab in the app

3. **Configure Server URL**
   - Enter your PRSNL server URL (e.g., `https://your-prsnl-server.com/api`)
   - By default, the app uses `http://localhost:8000/api` which only works on simulators

4. **Enter API Key**
   - Enter your API key in the designated field
   - For testing, you can use: `test-api-key-for-development`

5. **Test Connection**
   - Tap "Test Connection" to verify the server is reachable
   - If successful, you'll see a confirmation message

### Understanding Online/Offline Functionality

The app uses an "online-first with offline fallback" approach:

- **When Online:**
  - Data is fetched directly from the server
  - Changes are immediately sent to the server
  - Data is also cached locally in Core Data

- **When Offline:**
  - The app shows an offline indicator banner
  - You can view and search previously cached data
  - New changes are saved locally and marked for sync
  - When connectivity returns, changes are automatically synchronized

- **Synchronization Process:**
  - SyncManager handles bidirectional sync
  - Local changes are pushed to the server
  - New server data is pulled and saved locally
  - Conflicts are resolved using a "server wins" strategy

## Setting Up a Local Test Server

If you don't have access to an online PRSNL server, you can set up a local server for testing:

1. **Clone the PRSNL Backend Repository**
   ```
   git clone https://github.com/your-org/prsnl-backend.git
   cd prsnl-backend
   ```

2. **Install Dependencies**
   ```
   npm install
   ```

3. **Start the Server**
   ```
   npm run dev
   ```

4. **Find Your Computer's Local IP Address**
   - Open System Preferences > Network
   - Note your IP address (e.g., 192.168.1.10)

5. **Configure the App**
   - In the app settings, use: `http://YOUR_IP_ADDRESS:8000/api`
   - This allows your phone to connect to your computer over your local network

## Troubleshooting

### Cannot Connect to Server
- Ensure your server is running
- Verify you're using the correct URL format (including `/api` path)
- Check if your iPhone and server are on the same network for local testing
- Verify the API key is correct

### App Crashes on Launch
- Check Xcode logs for error details
- Ensure your iPhone meets the minimum iOS requirement (iOS 17.0)
- Try deleting and reinstalling the app

### App Icon Issues
- **Problem**: App shows default white grid icon instead of custom icon
- **Solutions**:
  1. **Clear iOS Icon Cache**:
     - Restart your device (iOS caches app icons and a restart may clear this cache)
     - If that doesn't work, try powering off completely, wait 30 seconds, then restart
  
  2. **Reinstall the App**:
     - Uninstall the app from your device
     - Rebuild and redeploy using Xcode
     - This forces iOS to use the new icons

  3. **Regenerate App Icons**:
     - If available, run the enhanced_app_icons.py script in the project directory:
       ```
       cd PRSNL-iOS
       python3 enhanced_app_icons.py
       ```
     - This generates all required icon sizes with proper iOS formatting
     - Rebuild and redeploy the app

  4. **Verify Icon Files**:
     - Check that Assets.xcassets/AppIcon.appiconset contains all required sizes
     - Ensure Contents.json has correct mappings for all icon files
     - Verify icons have proper transparency and alpha channel

### Data Not Syncing
- Check the network connection
- Verify server URL and API key in settings
- Pull down on the Timeline to trigger a manual sync
- Check server logs for any API errors

## Contact & Support

For issues with the app deployment or configuration, please:
- Open an issue on the project repository
- Contact the development team at support@prsnl-app.com