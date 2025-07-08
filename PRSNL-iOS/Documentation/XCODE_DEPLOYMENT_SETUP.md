# Xcode Deployment Setup for PRSNL iOS App

This guide provides specific details on how to set up Xcode for deploying the PRSNL app to your iPhone, including where to select the deployment target and the iOS support requirements.

## Required Xcode Components

To develop and deploy iOS apps, you need:

1. **Xcode**: The complete Xcode IDE (latest stable version recommended)
2. **iOS SDK**: This comes bundled with Xcode installation
3. **Command Line Tools**: Also included with Xcode

You don't need to install these separately - a standard Xcode installation includes everything you need.

## Where to Select Deployment Target

The "deployment target" in Xcode refers to two different things:

### 1. iOS Version Deployment Target

This is the minimum iOS version your app supports. For PRSNL, it's set to iOS 15.0.
This is already configured in the project.yml file and you don't need to change it.

### 2. Physical Device Selection (What You're Looking For)

To select your iPhone as the device to deploy to:

![Xcode Device Selection](https://i.imgur.com/NbUHBKP.png)

1. After opening your project in Xcode, look at the **top toolbar**
2. Next to the Play (▶️) and Stop (⏹️) buttons, you'll see a dropdown menu
3. This dropdown shows the currently selected destination (e.g., "iPhone 14 Pro" or similar)
4. When you connect your iPhone via USB, it will appear in this dropdown list
5. Click the dropdown and select your iPhone from the list

Your iPhone will only appear here if:
- It's connected to your Mac via USB cable
- It's unlocked
- You've trusted the computer on your iPhone

## Xcode iOS Support Requirements

### Required Components

Xcode comes with all the iOS support components you need:

1. **iOS SDKs**: Included with Xcode
2. **iOS Simulators**: Included with Xcode
3. **iOS Device Support**: Downloaded automatically when you connect a device

### Checking iOS Support in Xcode

To verify you have the necessary iOS support:

1. Open Xcode
2. Go to Xcode → Settings (or Preferences in older versions)
3. Click on the "Platforms" tab
4. You should see "iOS" listed with its version
5. If you see iOS 15.0 or later, you have sufficient support for the PRSNL app

### Automatic Installation

When you connect an iPhone to your Mac, Xcode will automatically:

1. Check if it has support files for that specific iOS version
2. Download any missing support files
3. Prepare the device for development

You might see a progress bar and "Preparing device for development" message when you first connect your iPhone.

## Common Issues and Solutions

### iPhone Not Appearing in Device List

If your iPhone doesn't appear in the device dropdown:

1. Make sure your iPhone is unlocked
2. Check that you've trusted the computer on your iPhone
3. Try a different USB cable or port
4. Restart Xcode
5. Restart your iPhone

### "Could not locate device support files" Error

If you see this error when connecting your iPhone:

1. Wait for Xcode to download the support files (can take a few minutes)
2. If it fails, go to Xcode → Window → Devices and Simulators
3. Select your iPhone and click "Show Provisioning Profiles"
4. Wait for Xcode to refresh and try again

## Selecting Build Destination in Xcode

Here's the complete step-by-step process:

1. Connect your iPhone to your Mac via USB
2. Unlock your iPhone
3. Trust the computer if prompted on your iPhone
4. Open the PRSNL.xcodeproj file in Xcode
5. In the Xcode toolbar, look for the device selector dropdown (next to the Run/Stop buttons)
6. Click this dropdown
7. Select your iPhone from the list of available devices
8. Click the Run button (▶️) or press Cmd+R

Your app will now build and deploy to your iPhone.