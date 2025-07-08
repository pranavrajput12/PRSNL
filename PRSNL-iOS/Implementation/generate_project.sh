#!/bin/bash

# Generate Xcode project using XcodeGen
# This script will generate an Xcode project based on the project.yml configuration

# Check if XcodeGen is installed
if ! command -v xcodegen &> /dev/null; then
    echo "XcodeGen is not installed. Installing..."
    brew install xcodegen
    
    # Check if installation was successful
    if ! command -v xcodegen &> /dev/null; then
        echo "Failed to install XcodeGen. Please install it manually:"
        echo "brew install xcodegen"
        exit 1
    fi
fi

echo "Generating Xcode project..."

# Navigate to the directory containing project.yml
cd "$(dirname "$0")"

# Clean up any existing project files
if [ -d "PRSNL.xcodeproj" ]; then
    echo "Removing existing Xcode project..."
    rm -rf PRSNL.xcodeproj
fi

# Generate the project
xcodegen generate

# Check if project generation was successful
if [ -d "PRSNL.xcodeproj" ]; then
    echo "✅ Xcode project generated successfully!"
    echo "You can now open PRSNL.xcodeproj in Xcode"
    
    # Reminder about Team ID
    echo ""
    echo "⚠️  IMPORTANT: Before building, replace the placeholder Team ID in project.yml:"
    echo "   DEVELOPMENT_TEAM: ABC12DEF34 # Replace with your actual Team ID"
    echo ""
    echo "   Then run this script again to regenerate the project with your Team ID."
else
    echo "❌ Failed to generate Xcode project. Check for errors in project.yml."
fi