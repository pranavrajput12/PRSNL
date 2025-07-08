#!/bin/bash

echo "🔧 Complete Xcode Fix Script"
echo "============================"
echo ""
echo "This script will help you completely reinstall Xcode"
echo ""

# Step 1: Check current Xcode status
echo "📊 Current Xcode Status:"
echo "----------------------"
xcode-select -p 2>/dev/null || echo "❌ No Xcode path set"
echo ""

# Try to get version
echo "Xcode version attempt:"
/usr/bin/xcodebuild -version 2>&1 || echo "❌ Cannot get version"
echo ""

# Check if ibtool exists
echo "Checking ibtool:"
if [ -f "/Applications/Xcode.app/Contents/Developer/usr/bin/ibtool" ]; then
    echo "✓ ibtool exists"
    ls -la "/Applications/Xcode.app/Contents/Developer/usr/bin/ibtool"
else
    echo "❌ ibtool is missing!"
fi
echo ""

# Step 2: Complete cleanup commands
echo "🧹 Cleanup Commands to Run:"
echo "-------------------------"
echo ""
echo "1. First, quit Xcode completely:"
echo "   killall Xcode 2>/dev/null"
echo ""
echo "2. Remove Xcode command line tools:"
echo "   sudo rm -rf /Library/Developer/CommandLineTools"
echo ""
echo "3. Remove Xcode application:"
echo "   sudo rm -rf /Applications/Xcode.app"
echo ""
echo "4. Clean all Xcode caches and settings:"
echo "   rm -rf ~/Library/Developer/"
echo "   rm -rf ~/Library/Caches/com.apple.dt.Xcode"
echo "   rm -rf ~/Library/Preferences/com.apple.dt.Xcode.plist"
echo "   rm -rf ~/Library/Saved\\ Application\\ State/com.apple.dt.Xcode.savedState"
echo ""
echo "5. Empty trash and restart Mac:"
echo "   (Empty trash from Dock)"
echo "   sudo shutdown -r now"
echo ""
echo "📥 After restart:"
echo "----------------"
echo "1. Download Xcode from:"
echo "   - Mac App Store (easiest)"
echo "   - OR https://developer.apple.com/xcode/ (requires Apple ID)"
echo ""
echo "2. After Xcode installs, open it and:"
echo "   - Accept license agreements"
echo "   - Let it install additional components"
echo "   - Wait for 'Installing components' to finish"
echo ""
echo "3. Install command line tools:"
echo "   xcode-select --install"
echo ""
echo "4. Set Xcode path:"
echo "   sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
echo ""

# Create a temporary workaround
echo "🔧 Creating temporary build workaround..."
echo "--------------------------------------"

# Create a no-storyboard build script
cat > build_without_ib.sh << 'EOF'
#!/bin/bash
echo "Building PRSNL without Interface Builder..."

# Set environment to skip IB
export SKIP_INSTALL=YES
export IBTOOL_LAUNCHER=NO

# Try to build with xcodebuild directly
xcodebuild -project PRSNL.xcodeproj \
           -scheme PRSNL \
           -configuration Debug \
           -destination 'platform=iOS Simulator,name=iPhone 15' \
           -derivedDataPath ./DerivedData \
           COMPILER_INDEX_STORE_ENABLE=NO \
           build

echo "Check ./DerivedData/Build/Products/Debug-iphonesimulator/ for the built app"
EOF

chmod +x build_without_ib.sh

echo ""
echo "✅ Created build_without_ib.sh as a temporary workaround"
echo "   (This probably won't work with the corrupted Xcode)"
echo ""
echo "⚠️  The only real solution is to reinstall Xcode completely."
echo ""