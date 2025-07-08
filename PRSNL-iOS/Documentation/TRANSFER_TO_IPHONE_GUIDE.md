# Transferring PRSNL to Your iPhone

This quick guide explains how to get the PRSNL app onto your iPhone and the authentication approach used.

## Transferring to iPhone (Simple Steps)

1. **Connect iPhone to Mac**
   - Use a USB cable to connect your iPhone to your Mac
   - Unlock your iPhone and trust the computer if prompted

2. **Open Project in Xcode**
   - Open Xcode on your Mac
   - Open the PRSNL.xcodeproj file from PRSNL-iOS/Implementation

3. **Sign In with Apple ID**
   - In Xcode, go to Xcode → Preferences → Accounts
   - Add your Apple ID (free account is fine)

4. **Select Your iPhone**
   - In Xcode's toolbar, select your iPhone from the device dropdown
   - It should appear in the list once connected

5. **Configure for Personal Use**
   - Select the PRSNL project in the Project Navigator
   - Go to "Signing & Capabilities"
   - Check "Automatically manage signing"
   - Select your Personal Team
   - Change the Bundle Identifier to something unique (e.g., com.yourname.prsnl)

6. **Run on Your Device**
   - Click the Run button (play icon) or press Cmd+R
   - Xcode will build and install the app on your iPhone

7. **Trust Developer Profile**
   - On your iPhone, go to Settings → General → VPN & Device Management
   - Select your Apple ID and tap "Trust"

8. **Launch the App**
   - Find and tap the PRSNL icon on your iPhone home screen

## Authentication in PRSNL

There is **no traditional login/signup page** in PRSNL. Instead:

1. **API Key Authentication**
   - PRSNL uses an API key for authentication
   - This is configured in the Settings screen
   - Default test key: `test-api-key-for-development`

2. **First Launch**
   - When you first launch the app, you'll see the Timeline view
   - Go to the Settings tab to configure your API key
   - Enter the test API key in the appropriate field

3. **Settings Screen**
   - The Settings screen lets you configure:
     - API Key
     - Server URL
     - Other app preferences

4. **Testing Without Backend**
   - The app can work in offline mode without a backend
   - It will store data locally using Core Data

## Important Notes

- The app will expire after 7 days when installed with a free Apple ID
- Extensions might have limited functionality due to App Group limitations
- You may need to reinstall after the 7-day period expires