#!/bin/bash

# Script to generate the Xcode project using XcodeGen
# This ensures a clean project generation without stale build settings or configurations

echo "========================================================"
echo "  PRSNL-iOS Project Generation Script"
echo "  Created by Pranav Rajput"
echo "========================================================"
echo ""

# Define paths
PROJECT_ROOT="."
PROJECT_FILE="$PROJECT_ROOT/project.yml"
XCODEGEN_LOG="$PROJECT_ROOT/xcodegen_log.txt"

# Ensure we're in the right directory
cd "$(dirname "$0")"

echo "Preparing to generate Xcode project..."

# Verify project.yml exists
if [ ! -f "$PROJECT_FILE" ]; then
    echo "❌ ERROR: project.yml not found at: $PROJECT_FILE"
    echo "Please run the fix_project_yaml.sh script first."
    exit 1
fi

# Check if XcodeGen is installed
if ! command -v xcodegen &> /dev/null; then
    echo "⚠️ XcodeGen is not installed. Attempting to install..."
    
    # Try to install XcodeGen using various package managers
    if command -v brew &> /dev/null; then
        echo "Installing XcodeGen using Homebrew..."
        brew install xcodegen
    elif command -v mint &> /dev/null; then
        echo "Installing XcodeGen using Mint..."
        mint install yonaskolb/XcodeGen
    else
        echo "❌ ERROR: Could not install XcodeGen automatically."
        echo "Please install XcodeGen manually with one of the following commands:"
        echo "  • brew install xcodegen"
        echo "  • mint install yonaskolb/XcodeGen"
        echo "  • Or follow the installation instructions at: https://github.com/yonaskolb/XcodeGen"
        exit 1
    fi
    
    # Verify installation
    if ! command -v xcodegen &> /dev/null; then
        echo "❌ ERROR: XcodeGen installation failed."
        exit 1
    fi
fi

echo "XcodeGen is available. Proceeding with project generation..."

# Clean up any existing Xcode project files
echo "Cleaning up existing Xcode project files..."
rm -rf "$PROJECT_ROOT/PRSNL.xcodeproj"
rm -rf "$PROJECT_ROOT/PRSNL.xcworkspace"
rm -rf "$PROJECT_ROOT/DerivedData"

# Generate the project
echo "Generating Xcode project from project.yml..."
cd "$PROJECT_ROOT"
xcodegen generate --spec "$PROJECT_FILE" > "$XCODEGEN_LOG" 2>&1

# Check if project generation was successful
if [ $? -eq 0 ] && [ -d "$PROJECT_ROOT/PRSNL.xcodeproj" ]; then
    echo "✅ Xcode project generated successfully at: PRSNL.xcodeproj"
    
    # Check for CocoaPods integration
    if [ -f "$PROJECT_ROOT/Podfile" ]; then
        echo "Podfile detected. Integrating CocoaPods..."
        if command -v pod &> /dev/null; then
            pod install --repo-update || {
                echo "⚠️ Warning: pod install failed. You may need to run it manually."
            }
            
            if [ -d "$PROJECT_ROOT/PRSNL.xcworkspace" ]; then
                echo "✅ CocoaPods integrated successfully. Use PRSNL.xcworkspace to open the project."
            else
                echo "⚠️ Warning: CocoaPods integration may have failed. Workspace not found."
            fi
        else
            echo "⚠️ Warning: CocoaPods not installed. Skipping pod install."
        fi
    fi
else
    echo "❌ ERROR: Failed to generate Xcode project."
    echo "XcodeGen output:"
    cat "$XCODEGEN_LOG"
    echo ""
    echo "Possible issues:"
    echo "- Syntax errors in project.yml"
    echo "- Missing required files referenced in project.yml"
    echo "- XcodeGen version incompatibility"
    exit 1
fi

# Fix project specific settings that may not be handled by XcodeGen
echo "Applying post-generation fixes..."

# Ensure proper Swift version is set
SWIFT_VERSION="5.9"
echo "Setting Swift version to $SWIFT_VERSION..."
if command -v xcodeproj &> /dev/null; then
    xcodeproj set_build_setting --project "$PROJECT_ROOT/PRSNL.xcodeproj" SWIFT_VERSION $SWIFT_VERSION || {
        echo "⚠️ Warning: Failed to set Swift version using xcodeproj tool."
        echo "You may need to set it manually in Xcode."
    }
else
    echo "⚠️ Warning: xcodeproj tool not found. Swift version may need to be set manually."
fi

# Fix bundle identifier format if needed
if grep -q "bundleIdPrefix" "$PROJECT_FILE"; then
    echo "Bundle identifier prefix found in project.yml. No fixes needed."
else
    echo "⚠️ Warning: No bundle identifier prefix found in project.yml."
    echo "You may need to set the bundle identifier manually in Xcode."
fi

# Check for LaunchScreen.storyboard
if [ ! -f "$PROJECT_ROOT/Resources/LaunchScreen.storyboard" ] && [ ! -d "$PROJECT_ROOT/Resources/LaunchScreen.storyboard" ]; then
    echo "⚠️ Warning: LaunchScreen.storyboard not found in Resources directory."
    echo "Launch screen may need to be created manually."
fi

# Final success message
echo ""
echo "✅ Project generation complete!"
echo ""
echo "You can now open the project with one of the following commands:"
if [ -d "$PROJECT_ROOT/PRSNL.xcworkspace" ]; then
    echo "$ open ../PRSNL.xcworkspace"
else
    echo "$ open ../PRSNL.xcodeproj"
fi
echo ""
echo "Note: You may need to set the development team in Xcode manually."
echo ""

cd - > /dev/null
exit 0