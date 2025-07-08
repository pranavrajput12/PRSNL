# Xcode Troubleshooting Guide

This guide addresses common issues encountered when building the PRSNL iOS project.

## Critical Build Issues

### Corrupted DerivedData / Disk I/O Errors

**Error symptoms:**
```
error: accessing build database "...DerivedData/.../Build/Intermediates.noindex/XCBuildData/build.db": disk I/O error

Cannot open constant extraction protocol list input file from .../PRSNL_const_extract_protocols.json

lstat(...): No such file or directory
```

**Resolution steps:**

1. **Complete DerivedData cleanup:**
   ```bash
   # Close Xcode first
   rm -rf ~/Library/Developer/Xcode/DerivedData
   rm -rf ~/Library/Caches/com.apple.dt.Xcode
   ```

2. **Reset simulator content and settings:**
   - In Xcode menu: Device → Simulator → Reset Content and Settings

3. **Verify disk health:**
   - Run Disk Utility First Aid on your system drive
   - Check available disk space (need at least 10GB free)

4. **Reset Xcode's package data:**
   ```bash
   sudo xcode-select --reset
   ```

5. **Clean build folder and rebuild:**
   - In Xcode: Product → Clean Build Folder (Shift+Cmd+K)
   - Quit and restart Xcode
   - Build again (Cmd+B)

## Installation Issues

### Missing macOS Platform / Incomplete Xcode Installation

**Error symptoms:**
```
Failed to decode version info for '/Applications/Xcode.app/Contents/Developer/usr/bin/ibtool': The data couldn't be read because it isn't in the correct format.

ibtoold failed IDE initialization: No macOS Platform was found, but Xcode requires a macOS Platform. You may have an incomplete or damaged installation of Xcode.
```

**Resolution steps:**

1. Reset Xcode's package data:
   ```bash
   sudo xcode-select --reset
   ```

2. Verify Xcode command line tools are properly installed:
   ```bash
   xcode-select --install
   ```

3. Accept Xcode license (if needed):
   ```bash
   sudo xcodebuild -license accept
   ```

4. **If the above doesn't resolve the issue, perform a complete Xcode reinstallation:**
   - Delete Xcode from Applications folder
   - Download fresh copy from App Store or Apple Developer website
   - After reinstalling, open Xcode and complete first-time setup

5. Run First Aid on your disk using Disk Utility to check for any system file corruption.

6. If you still encounter issues, try installing an older version of Xcode that might be more compatible with your macOS version.

## Signing & Provisioning Issues

### Missing Provisioning Profile / Development Team

**Error symptoms:**
```
"PRSNLShareExtension" requires a provisioning profile.
Enable development signing and select a provisioning profile in the Signing & Capabilities editor.

Signing for "PRSNLWidgets" requires a development team.
Select a development team in the Signing & Capabilities editor.
```

**Resolution steps:**

1. Open the PRSNL.xcodeproj file in Xcode.

2. Select the project in the navigator and go to the "Signing & Capabilities" tab.

3. For both the main app target and the extension targets (PRSNLShareExtension, PRSNLWidgets):
   - Select "Automatically manage signing"
   - Select your development team from the dropdown
   - If you don't have a team, you'll need to sign in with your Apple ID

4. If you don't have a paid Apple Developer account:
   - You can still build and run on simulators
   - For device testing, you can use a free account but with 7-day certificate expiration
   - See [TESTING_WITHOUT_DEVELOPER_ACCOUNT.md](TESTING_WITHOUT_DEVELOPER_ACCOUNT.md) for details

5. If using a free account, ensure all capabilities are compatible (some capabilities like App Groups require a paid account).

## Code Compatibility Issues

### iOS Version Compatibility

**Error symptoms:**
```
'NavigationStack' is only available in iOS 16.0 or newer
'callAsFunction' is only available in iOS 16.0 or newer
'ProposedViewSize' is only available in iOS 16.0 or newer
```

**Resolution steps:**

1. Check your project's deployment target in the project settings
2. Update code to use availability checks or conditional compilation:
   ```swift
   if #available(iOS 16.0, *) {
       // iOS 16+ code
   } else {
       // Fallback for earlier iOS versions
   }
   ```
3. Use compatibility wrappers for newer SwiftUI features

### Code Structure and Type Errors

**Error symptoms:**
Multiple errors related to missing types, undefined functions, or API mismatches:
```
Value of type 'CoreDataManager' has no member 'saveItem'
Cannot find 'UIApplication' in scope
Type 'SyncStatus' has no member 'needsUpload'
```

**Resolution:**
1. Ensure all required imports are present
2. Check for proper model definitions and consistency
3. Update API usage to match the current implementation

## Building Without a Developer Account

If you don't have an Apple Developer account or are experiencing persistent signing issues, you can modify the project configuration to build for simulator only:

1. Open the project.yml file
2. Comment out or remove extension targets temporarily:
   ```yaml
   # Comment out ShareExtension and Widgets targets
   ```
3. Regenerate the project using the generate_project.sh script:
   ```bash
   cd PRSNL-iOS/Implementation
   sh generate_project.sh
   ```
4. Build and run on simulator

## Complete Project Reset

If you continue to experience persistent build issues, consider a complete project reset:

1. Close Xcode
2. Delete the following:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData
   rm -rf ~/Library/Caches/com.apple.dt.Xcode
   ```
3. Delete the generated Xcode project:
   ```bash
   rm -rf PRSNL-iOS/Implementation/PRSNL.xcodeproj
   ```
4. Regenerate the project:
   ```bash
   cd PRSNL-iOS/Implementation
   sh generate_project.sh
   ```
5. Open the newly generated project and build

## General Xcode Maintenance

Periodically perform these maintenance tasks to prevent issues:

1. Clean build folder (Cmd+Shift+K)
2. Clear derived data:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData
   ```
3. Restart Xcode and your Mac
4. Update Xcode to the latest version
5. Verify adequate disk space (low disk space can cause build issues)
6. Run periodic maintenance scripts:
   ```bash
   xcrun simctl erase all  # Reset all simulators
   ```