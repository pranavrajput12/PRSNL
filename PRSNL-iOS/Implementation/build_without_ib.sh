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
