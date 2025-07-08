#!/bin/bash

# Script to build the PRSNL-iOS app for simulator without Interface Builder
# This avoids common Interface Builder errors and focuses on SwiftUI implementation

echo "========================================================"
echo "  PRSNL-iOS Build Script (No Interface Builder)"
echo "  Created by Pranav Rajput"
echo "========================================================"
echo ""

# Define paths
PROJECT_ROOT="."
BUILD_LOG="$PROJECT_ROOT/build_log.txt"
DERIVED_DATA="$PROJECT_ROOT/DerivedData"
SCHEME="PRSNL"

# Ensure we're in the right directory
cd "$(dirname "$0")"

echo "Preparing to build PRSNL-iOS app for simulator..."

# Determine if we should use xcworkspace or xcodeproj
if [ -d "$PROJECT_ROOT/PRSNL.xcworkspace" ]; then
    PROJECT_PATH="$PROJECT_ROOT/PRSNL.xcworkspace"
    PROJECT_TYPE="-workspace"
    echo "Using workspace: PRSNL.xcworkspace"
else
    PROJECT_PATH="$PROJECT_ROOT/PRSNL.xcodeproj"
    PROJECT_TYPE="-project"
    echo "Using project: PRSNL.xcodeproj"
fi

# Check if project exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ ERROR: Xcode project not found at: $PROJECT_PATH"
    echo "Please run the generate_project.sh script first."
    exit 1
fi

# Ensure build directory exists
mkdir -p "$DERIVED_DATA"

# Get available simulator devices
echo "Finding available iOS simulators..."
SIMULATORS=$(xcrun simctl list devices available | grep "iPhone" | grep -v "unavailable" | head -n 1)
if [ -z "$SIMULATORS" ]; then
    echo "⚠️ Warning: No iPhone simulators found. Using generic iOS Simulator."
    DESTINATION="platform=iOS Simulator,name=iPhone 15"
else
    SIM_NAME=$(echo "$SIMULATORS" | sed -E 's/.*iPhone[^(]*\(([^)]*)\).*/\1/')
    DESTINATION="platform=iOS Simulator,id=$SIM_NAME"
    echo "Using simulator: $(echo "$SIMULATORS" | sed -E 's/.*([^)]*).*/\1/')"
fi

# Clean build directory
echo "Cleaning previous build artifacts..."
xcodebuild clean $PROJECT_TYPE "$PROJECT_PATH" -scheme "$SCHEME" -destination "$DESTINATION" -derivedDataPath "$DERIVED_DATA" > /dev/null 2>&1

# Build for simulator
echo "Building app for simulator (this may take a few minutes)..."
echo "Build output will be saved to: $BUILD_LOG"
echo ""

# Disable Interface Builder integration during build
export IBSC_WARNINGS=off
export SKIP_INSTALL=yes
export SKIP_INSTALL_RESOURCES=yes

# Start the build
xcodebuild build $PROJECT_TYPE "$PROJECT_PATH" -scheme "$SCHEME" -destination "$DESTINATION" -derivedDataPath "$DERIVED_DATA" OTHER_SWIFT_FLAGS="-Xfrontend -warn-long-function-bodies=200 -Xfrontend -warn-long-expression-type-checking=100" > "$BUILD_LOG" 2>&1

# Check build status
BUILD_STATUS=$?
if [ $BUILD_STATUS -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Find the app path
    APP_PATH=$(find "$DERIVED_DATA/Build/Products" -name "*.app" -type d | head -n 1)
    if [ -n "$APP_PATH" ]; then
        echo "App built at: $APP_PATH"
        
        # Check for any warnings
        WARNING_COUNT=$(grep -c "warning:" "$BUILD_LOG")
        if [ $WARNING_COUNT -gt 0 ]; then
            echo "⚠️ Build completed with $WARNING_COUNT warnings."
            echo "View $BUILD_LOG for details."
        else
            echo "Build completed with no warnings."
        fi
        
        # Offer to launch the app in simulator
        echo ""
        echo "To launch the app in simulator, run:"
        echo "xcrun simctl install booted \"$APP_PATH\""
        echo "xcrun simctl launch booted $(defaults read \"$APP_PATH/Info.plist\" CFBundleIdentifier)"
    else
        echo "⚠️ Warning: Could not find built app in derived data directory."
    fi
else
    echo "❌ Build failed with errors."
    echo "Common build errors and solutions:"
    echo "1. Code signing issues: Update the development team in project settings"
    echo "2. Swift compiler errors: Fix any syntax or type errors in the code"
    echo "3. Missing dependencies: Run update_dependencies.sh"
    echo "4. Resource not found: Ensure all referenced resources exist"
    echo ""
    echo "For detailed error information, check: $BUILD_LOG"
    
    # Extract and display the most relevant errors
    echo ""
    echo "Top errors from build log:"
    grep -A 2 "error:" "$BUILD_LOG" | head -n 10
    
    # Count error types to help diagnose
    SWIFT_ERRORS=$(grep -c "Swift Compiler Error" "$BUILD_LOG")
    LINK_ERRORS=$(grep -c "ld: error" "$BUILD_LOG")
    SIGN_ERRORS=$(grep -c "Code Sign error" "$BUILD_LOG")
    
    echo ""
    echo "Error summary:"
    echo "- Swift compiler errors: $SWIFT_ERRORS"
    echo "- Linker errors: $LINK_ERRORS"
    echo "- Code signing errors: $SIGN_ERRORS"
    
    exit 1
fi

echo ""
echo "========================================================"
echo "  Build process complete"
echo "  Created by Pranav Rajput"
echo "========================================================"

exit $BUILD_STATUS
