#!/bin/bash

echo "🔧 Attempting Quick Fix for Xcode Platform Issue"
echo "=============================================="
echo ""

# Try to fix platform issues
echo "1. Resetting Xcode developer directory..."
sudo xcode-select --reset

echo ""
echo "2. Switching to Xcode path explicitly..."
sudo xcode-select --switch /Applications/Xcode.app

echo ""
echo "3. Accepting license again..."
sudo xcodebuild -license accept 2>/dev/null || echo "License already accepted"

echo ""
echo "4. Running first launch tasks..."
sudo xcodebuild -runFirstLaunch

echo ""
echo "5. Checking platforms..."
ls -la /Applications/Xcode.app/Contents/Developer/Platforms/

echo ""
echo "6. Specifically checking for macOS platform..."
if [ -d "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform" ]; then
    echo "✅ MacOSX.platform exists"
    ls -la /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/
else
    echo "❌ MacOSX.platform is MISSING - This is the problem!"
fi

echo ""
echo "7. Trying to verify Xcode installation..."
/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild -checkFirstLaunchStatus

echo ""
echo "If you still see errors above, you need to reinstall Xcode."
echo ""
echo "Try opening Xcode now and see if it works."