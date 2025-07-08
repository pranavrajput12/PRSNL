# Cleaning Up System Data on Your Mac

Having high system data usage (94.84 GB) is not normal and is likely preventing you from working effectively with Xcode. This guide will help you reclaim space by cleaning up system data, with special focus on Xcode-related files which are often a major contributor.

## Understanding System Data

"System Data" on macOS is a catch-all category that includes:
- System caches
- Logs
- App support files
- Xcode device support files (often very large)
- iOS simulators
- Temporary files
- Time Machine local snapshots

## Quick Cleanup Steps

Here are steps to reclaim space quickly:

### 1. Clean Xcode Derived Data and Archives

Xcode's derived data and archives can consume massive amounts of space:

```bash
# Remove derived data (can be safely deleted)
rm -rf ~/Library/Developer/Xcode/DerivedData

# Remove archives (only if you don't need old build archives)
rm -rf ~/Library/Developer/Xcode/Archives
```

### 2. Remove Unused iOS Simulator Runtimes

iOS Simulator runtimes can take up 10+ GB each:

```bash
# List all installed simulators
xcrun simctl list

# Remove specific simulators you don't need
xcrun simctl delete unavailable
```

### 3. Remove Unused Device Support Files

Device support files for iOS devices you no longer use:

```bash
# Navigate to the device support directory
cd ~/Library/Developer/Xcode/iOS\ DeviceSupport/

# List all device support files to see what's taking space
ls -la

# Remove old iOS versions you don't need
rm -rf "14.4 (18D52)"  # Replace with versions you want to remove
```

### 4. Clear System and Application Caches

```bash
# Clear system caches
sudo rm -rf /Library/Caches/*
rm -rf ~/Library/Caches/*

# Clear application caches (be cautious - some apps may need to reconfigure)
rm -rf ~/Library/Application\ Support/MobileSync/Backup/*
```

### 5. Remove Time Machine Local Snapshots

Time Machine creates local snapshots that count as "System Data":

```bash
# List all local snapshots
tmutil listlocalsnapshots /

# Delete all local snapshots
sudo tmutil deletelocalsnapshots /
```

## Using Storage Management Tools

macOS includes built-in storage management:

1. Click Apple menu () → About This Mac
2. Click "Storage" tab
3. Click "Manage..."
4. Use the recommendations and browse through categories

## Specialized Cleanup Applications

Consider using specialized cleanup applications:

- **OmniDiskSweeper**: Free tool to visualize disk usage
- **DaisyDisk**: Paid tool with visual disk space representation
- **CleanMyMac X**: Paid tool with comprehensive cleaning

## Xcode-Specific Cleanup

Xcode is often the biggest contributor to system data. Additional Xcode cleanup:

```bash
# Remove all simulator devices
xcrun simctl delete all

# Remove all unavailable simulator runtimes
xcrun simctl delete unavailable

# Remove Core Simulator caches
rm -rf ~/Library/Developer/CoreSimulator/Caches/

# Remove all old device support files (keep only the ones you need)
rm -rf ~/Library/Developer/Xcode/iOS\ DeviceSupport/*
```

## Warning Signs You Need More Space

If you're consistently low on space:

1. Consider upgrading your storage
2. Move projects to external drives
3. Use cloud storage for large files
4. Regularly clean Xcode caches (weekly)

## Safe Minimum Space Requirements

For Xcode development:
- At least 50GB free space for comfortable development
- Minimum 20GB free for basic functionality
- Under 10GB free will cause performance issues and build failures

## Regular Maintenance Plan

To prevent space issues:

1. Run Xcode cleanup weekly
2. Empty trash regularly
3. Clear browser caches monthly
4. Run full system cleanup quarterly

## After Cleanup

After cleaning up:
1. Restart your Mac
2. Check available space again
3. Launch Xcode to let it rebuild necessary caches

This should help you reclaim significant space from system data and allow you to work with Xcode more effectively.