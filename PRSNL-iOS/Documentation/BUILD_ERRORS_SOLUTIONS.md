# Resolving PRSNL Build Errors

This guide addresses the specific build errors shown in your screenshot:

## Error Types

1. **ibtool Decoding Error:**
   ```
   Failed to decode version info for '/Applications/Xcode.app/Contents/Developer/usr/bin/ibtool'
   ```

2. **Team Account Errors:**
   ```
   No Account for Team "ABC12DEF34". Add a new account in Accounts settings or verify that your accounts have valid credentials.
   ```

3. **Provisioning Profile Errors:**
   ```
   No profiles for 'ai.prsnl' were found: Xcode couldn't find any iOS App Development provisioning profiles matching 'ai.prsnl'.
   ```

## Solutions

### 1. Fix ibtool Error

This error typically indicates Xcode installation issues or permission problems:

**Option A: Repair Xcode permissions**
```bash
sudo chown -R $(whoami) /Applications/Xcode.app
```

**Option B: Reset Xcode**
```bash
# Close Xcode first, then run:
defaults delete com.apple.dt.Xcode
rm -rf ~/Library/Developer/Xcode/DerivedData
rm -rf ~/Library/Caches/com.apple.dt.Xcode
```

**Option C: Reinstall Command Line Tools**
```bash
# Uninstall current tools
sudo rm -rf /Library/Developer/CommandLineTools

# Reinstall
xcode-select --install
```

### 2. Fix Team Account Errors

The error shows you're trying to use a specific team "ABC12DEF34" that's not configured in Xcode:

**Step 1: Open Xcode preferences**
1. Launch Xcode
2. Go to Xcode → Preferences (or Xcode → Settings in newer versions)
3. Select the "Accounts" tab

**Step 2: Set up your personal Apple ID**
1. Click "+" button to add an account
2. Select "Apple ID" and sign in with your Apple ID
3. Wait for Xcode to verify your account

**Step 3: Update project settings**
1. Open the PRSNL project in Xcode
2. Select the project in the navigator (blue icon)
3. Select each target and update Signing & Capabilities:
   - Change Team to your personal Apple ID account
   - Enable "Automatically manage signing"
   - Ensure Bundle Identifier is unique (not just 'ai.prsnl')

### 3. Fix Bundle Identifiers

The current bundle IDs are causing problems:

**Step 1: Use unique, personal bundle IDs**
1. Open project.yml (or do this directly in Xcode project settings)
2. Update bundle IDs to follow this pattern:

```yaml
# For project.yml
targets:
  PRSNL:
    bundleId: com.yourusername.prsnl
    # Other settings...
  
  PRSNLShareExtension:
    bundleId: com.yourusername.prsnl.shareextension
    # Other settings...
    
  PRSNLWidgets:
    bundleId: com.yourusername.prsnl.widgets
    # Other settings...
```

If editing directly in Xcode:
1. Select each target in project settings
2. Change the "Bundle Identifier" field

**Step 2: Update any references to bundle IDs in code**
- Update any hardcoded references to 'ai.prsnl' in your code
- Check entitlements files for app groups references

### 4. Simplify for Free Developer Account

With a free Apple Developer account, you need to simplify the project:

**Step 1: Disable advanced capabilities**
1. Open each target's "Signing & Capabilities" tab
2. Remove App Groups capability
3. Remove other capabilities requiring a paid account

**Step 2: Update Core Data to not rely on App Groups**
1. Ensure the conditional Core Data setup is working
2. Test that it falls back to local storage correctly

**Step 3: Clean Build Folder**
1. In Xcode, select Product → Clean Build Folder
2. Close and reopen Xcode

### 5. Fixing Bundle ID Issues Without Rebuilding

If you don't want to regenerate the entire project:

**Step 1: Quick-fix in Xcode**
1. Open the project in Xcode
2. Select the project file (blue icon)
3. For each target:
   - Change the Bundle Identifier to your personalized version
   - Change Team to your personal account
   - Check "Automatically manage signing"
   - Select "iPhone Developer" for Signing Certificate

**Step 2: Update Info.plist files**
1. Open each Info.plist file
2. Update CFBundleIdentifier if present
3. Update any app group references

## Quick Start: Minimal Working Configuration

If you just want to get something building quickly:

1. **Open Xcode and create a new iOS app project**
   - Name it "PRSNLMinimal"
   - Use your personal team

2. **Copy your Core Data model**
   - Drag PRSNLModel.xcdatamodeld into the new project

3. **Copy key view files**
   - Selectively copy the essential Swift files

4. **Add extensions later**
   - Get the base app working first
   - Add extensions one by one

## Debugging Commands

If Xcode still has issues, try these diagnostic commands:

```bash
# Check Xcode installation
xcode-select -p

# Verify ibtool
/Applications/Xcode.app/Contents/Developer/usr/bin/ibtool --version

# Check available signing identities
security find-identity -v -p codesigning

# List provisioning profiles
ls ~/Library/MobileDevice/Provisioning\ Profiles/
```

## Testing on Device Without Paid Account

1. Connect your iOS device
2. Select your device as build target
3. In Project Settings → Signing & Capabilities:
   - Select your personal team
   - Let Xcode handle the free provisioning profile
4. Build and run
5. On your device, go to Settings → General → Device Management
6. Trust your developer certificate

Remember: With a free account, your app will expire after 7 days and will need to be reinstalled.