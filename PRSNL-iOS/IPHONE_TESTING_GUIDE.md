# PRSNL iOS App: iPhone Testing Guide

This guide will walk you through the complete process of testing the PRSNL iOS app on your iPhone, including how the app communicates with the backend database.

## Quick Start Guide

1. **Deploy the app to your iPhone** (using Xcode)
2. **Set up the test backend server** (on your computer)
3. **Configure the app** to connect to your server
4. **Test online and offline functionality**

## Step 1: Deploy to Your iPhone

### Prerequisites
- macOS computer with Xcode 15 or later
- Apple Developer account (free account works for testing)
- iPhone with iOS 17.0 or later
- USB cable to connect your iPhone to your Mac

### Deployment Steps

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
   - If you see signing errors, click "Try Again" or "Fix Issue"

3. **Connect Your iPhone**
   - Connect your iPhone to your Mac using a USB cable
   - Unlock your iPhone
   - Trust the computer if prompted

4. **Select Your Device & Run**
   - In Xcode, click on the device selector in the toolbar
   - Select your connected iPhone
   - Click the "Run" button (play icon)
   - The first time you run the app, you may need to go to:
     Settings > General > Device Management > [Your Apple ID] > Trust

## Step 2: Set Up the Test Backend Server

The app needs a server to communicate with. We'll set up a simple Express.js server on your computer.

### Prerequisites
- Node.js 16.x or later
- npm or yarn package manager

### Server Setup

1. **Create a Directory for the Server**
   ```bash
   mkdir prsnl-backend
   cd prsnl-backend
   ```

2. **Initialize the Project**
   ```bash
   npm init -y
   ```

3. **Install Dependencies**
   ```bash
   npm install express cors body-parser uuid
   ```

4. **Create the Server File**
   Create a file named `server.js` with the content from the BACKEND_SETUP.md file (it's a complete Express.js server implementation with all needed endpoints)

5. **Start the Server**
   ```bash
   node server.js
   ```

6. **Note Your Computer's IP Address**
   - On macOS, go to System Preferences > Network
   - Note your IP address (e.g., 192.168.1.10)
   - The server runs at http://YOUR_IP_ADDRESS:8000
   - Default API key: `test-api-key-for-development`

## Step 3: Connect Your iPhone App to the Server

1. **Launch the PRSNL App** on your iPhone

2. **Navigate to Settings** in the app

3. **Configure Server URL**
   - Enter: `http://YOUR_COMPUTER_IP:8000/api`
   - Replace YOUR_COMPUTER_IP with your actual IP address
   - Make sure your phone and computer are on the same network

4. **Enter API Key**
   - Enter: `test-api-key-for-development`

5. **Test Connection**
   - Tap "Test Connection" to verify
   - You should see a success message

## How the App Communicates with the Database

The PRSNL app uses a sophisticated system to manage data both online and offline:

### Database Communication Architecture

1. **Online Mode (Normal Operation)**
   - The app makes direct HTTP requests to the server API
   - `APIClient.swift` handles these network requests using URLSession
   - Data received from the server is:
     - Displayed to the user
     - Simultaneously saved to Core Data for offline access
   - Changes made in the app are immediately sent to the server

2. **Offline Mode (When No Network Connection)**
   - The app detects network status using `NetworkMonitor`
   - When offline, a status indicator appears in the UI
   - The app reads data from the local Core Data database
   - Changes made while offline are:
     - Saved to Core Data
     - Marked with a "needs upload" sync status
     - Queued for synchronization when connectivity returns

3. **Synchronization System**
   - `SyncManager.swift` handles bidirectional synchronization
   - When network connectivity is restored:
     - Local changes are pushed to the server
     - New server data is pulled and saved locally
     - Conflicts are resolved using predefined rules

4. **Data Flow Diagram**
   ```
   [User Interface] ←→ [ViewModels] ←→ [CoreDataManager] ←→ [Local Database]
                        ↑   ↓                                      ↑
                        ↑   ↓                                      ↓
                    [SyncManager] ←→ [APIClient] ←→ [Backend Server]
   ```

## Testing Online/Offline Functionality

To verify the app works correctly in both modes:

1. **Test Online Mode**
   - Ensure your server is running
   - Configure the app with correct server URL and API key
   - Browse items in the Timeline and Search views
   - Create, edit, and delete items
   - Verify changes appear both in the app and on the server

2. **Test Offline Mode**
   - First use the app while online to load some data
   - Then turn on Airplane Mode on your iPhone
   - Continue using the app - you should see offline indicators
   - Create new items and make changes
   - The app should function normally with cached data

3. **Test Synchronization**
   - While offline, make several changes
   - Turn off Airplane Mode to restore connectivity
   - The app should automatically sync your changes
   - Pull down on the Timeline to trigger a manual sync
   - Verify your offline changes appear on the server

## Troubleshooting

### Can't Connect to Server
- Ensure your iPhone and computer are on the same Wi-Fi network
- Verify the server is running (`node server.js`)
- Check the server console for errors
- Make sure you're using your computer's correct IP address
- Try disabling any firewalls temporarily

### App Shows "Offline" Even When Online
- Check Wi-Fi connectivity on your iPhone
- Restart the app
- Verify the server is running
- Try using the "Test Connection" button in Settings

### Changes Not Syncing
- Pull down on the Timeline screen to force a sync
- Check the server logs for errors
- Verify your API key is correct
- Restart both the app and server

### Data Not Persisting Offline
- This could indicate a Core Data issue
- Try restarting the app
- Check Xcode logs for Core Data errors