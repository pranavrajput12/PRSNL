#!/bin/bash
echo "Building PRSNL for Simulator only..."

# Clean first
xcodebuild clean -project PRSNL.xcodeproj -scheme PRSNL

# Build for simulator only (no code signing required)
xcodebuild build \
  -project PRSNL.xcodeproj \
  -scheme PRSNL \
  -configuration Debug \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  -xcconfig PRSNL_Override.xcconfig \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGNING_ALLOWED=NO

echo "Build complete!"
