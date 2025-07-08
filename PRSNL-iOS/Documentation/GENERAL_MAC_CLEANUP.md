# General Mac Storage Cleanup Guide

If your Mac is showing high system data usage (94.84GB) and it's been this way for a while (not just due to Xcode), this guide will help identify and clean up the most common space-hogging culprits.

## Finding What's Taking Up Space

First, let's identify what's actually using your disk space:

### 1. Use Built-in Storage Management

1. Click Apple menu (🍎) → About This Mac
2. Click "Storage" tab
3. Click "Manage..."
4. Review each category to see what's using space

### 2. Analyze with Third-Party Tools

For a more detailed breakdown, use one of these tools:

- **GrandPerspective** (Free): Visual representation of disk usage
- **OmniDiskSweeper** (Free): Shows folder sizes in descending order
- **DaisyDisk** (Paid): Visual interface for finding large files

## Common System Data Culprits (Non-Xcode)

### 1. Time Machine Local Snapshots

Time Machine creates local backups that count as system data:

```bash
# List all local snapshots
tmutil listlocalsnapshots /

# Delete all local snapshots
sudo tmutil deletelocalsnapshots /
```

### 2. System Log Files

Log files can grow very large over time:

```bash
# Clear system logs (requires password)
sudo rm -rf /var/log/*
```

### 3. Mail Downloads and Attachments

Mail keeps copies of all attachments:

```bash
# Navigate to Mail Downloads folder
cd ~/Library/Containers/com.apple.mail/Data/Library/Mail\ Downloads/

# See how much space it's using
du -sh

# Remove files if desired
rm -rf *
```

### 4. Photos Library Cached Files

Photos keeps multiple versions of images:

1. Open Photos app
2. Go to Photos → Preferences
3. Click "Optimize Mac Storage"

### 5. iCloud Drive Cached Files

```bash
# Clear iCloud caches
rm -rf ~/Library/Application\ Support/CloudDocs/session/db
```

### 6. Spotify Cache

```bash
# Clear Spotify cache
rm -rf ~/Library/Caches/com.spotify.client/Data
```

### 7. Browser Caches

```bash
# Chrome
rm -rf ~/Library/Caches/Google/Chrome/

# Safari
rm -rf ~/Library/Caches/com.apple.Safari/
rm -rf ~/Library/Safari/LocalStorage/
```

### 8. Unused Applications and Large Files

Use the Storage Management tool to:
1. Remove unused applications
2. Find and delete large files
3. Empty the trash

### 9. System and Application Caches

```bash
# Clear system caches
sudo rm -rf /Library/Caches/*
rm -rf ~/Library/Caches/*
```

### 10. Language Files

macOS keeps language files for languages you don't use:

```bash
# Install Monolingual app to remove language files
# (Available from https://github.com/IngmarStein/Monolingual)
```

## Check for Hidden Space Hogs

### 1. Duplicate Files

Use Gemini or similar apps to find and remove duplicate files.

### 2. Old iOS Backups

```bash
# Navigate to iOS backups folder
cd ~/Library/Application\ Support/MobileSync/Backup/

# See how much space it's using
du -sh

# Remove old backups you don't need
rm -rf [backup-folder-id]
```

### 3. Docker Images (if installed)

```bash
# Remove unused Docker images
docker system prune -a
```

### 4. Virtual Machine Disk Images

Look for .vmdk files in your Documents or other folders, which can be dozens of GB each.

### 5. Old User Home Folders

Check for old user accounts you no longer use:

```bash
# List user home directories
ls -la /Users/
```

## System Data That's Hard to Clean

Some system data is protected by System Integrity Protection:

1. **System swap files**: Located in /private/var/vm/
2. **Recovery partition**: Hidden partition for recovery
3. **System binaries and libraries**: Core operating system files

## After Cleanup

1. Restart your Mac to clear memory and temporary files
2. Run Disk Utility and use "First Aid" to check your disk
3. Consider using a cleaning app like CleanMyMac X for regular maintenance

## Last Resort: Reset System Storage

If nothing else works, you might consider a clean installation:

1. Back up your important data
2. Create a bootable macOS installer
3. Erase your disk and reinstall macOS

This is a drastic step but will definitely clean up system data.

## Non-Destructive Alternatives

If you can't find what's using space:

1. **Move personal data to external storage**: Photos, videos, music
2. **Use cloud storage more aggressively**: iCloud, Google Drive, Dropbox
3. **Set up a scheduled cleaning routine**: Weekly/monthly cleanup