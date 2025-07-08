#!/bin/bash

echo "🔧 Fixing PRSNL Xcode Project Settings..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Cleaning Xcode derived data and caches...${NC}"
rm -rf ~/Library/Developer/Xcode/DerivedData/*
rm -rf ~/Library/Caches/com.apple.dt.Xcode/*

echo -e "${YELLOW}Step 2: Removing code signing requirements from project...${NC}"
# This will help bypass the signing issues temporarily

# Create a minimal xcconfig file to override signing
cat > PRSNL_Override.xcconfig << 'EOF'
// Override signing settings for free account
CODE_SIGNING_REQUIRED = NO
CODE_SIGN_IDENTITY = 
CODE_SIGNING_ALLOWED = NO
ENABLE_BITCODE = NO
CODE_SIGN_ENTITLEMENTS = 
EXPANDED_CODE_SIGN_IDENTITY = 
PROVISIONING_PROFILE_SPECIFIER = 
DEVELOPMENT_TEAM = 

// Disable capabilities that require paid account
ENABLE_APP_GROUPS = NO
ENABLE_KEYCHAIN_SHARING = NO

// Bundle IDs
PRODUCT_BUNDLE_IDENTIFIER = com.local.prsnl
EOF

echo -e "${YELLOW}Step 3: Creating simulator-only build configuration...${NC}"
# Create a build script that only builds for simulator
cat > build_simulator_only.sh << 'EOF'
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
EOF

chmod +x build_simulator_only.sh

echo -e "${YELLOW}Step 4: Fixing Info.plist files...${NC}"
# Ensure Info.plist files have proper format
plutil -convert xml1 PRSNL/Info.plist 2>/dev/null || echo "Main Info.plist already in correct format"
plutil -convert xml1 PRSNLShareExtension/Info.plist 2>/dev/null || echo "Share Extension Info.plist already in correct format"
plutil -convert xml1 PRSNLWidgets/Info.plist 2>/dev/null || echo "Widget Info.plist already in correct format"

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To build the app for simulator without signing issues:"
echo "1. Open PRSNL.xcodeproj in Xcode"
echo "2. Select 'PRSNL' scheme (not the extensions)"
echo "3. Select any iPhone Simulator as the target"
echo "4. Or run: ./build_simulator_only.sh"
echo ""
echo "For device builds with free account:"
echo "1. In Xcode, select each target"
echo "2. Go to Signing & Capabilities"
echo "3. Select your personal team"
echo "4. Let Xcode handle provisioning"