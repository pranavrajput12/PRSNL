#!/bin/bash

# Frontend Fix Script
echo "🔧 PRSNL Frontend Fix Script"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Navigate to frontend directory
FRONTEND_DIR="/Users/pronav/Personal Knowledge Base/PRSNL/frontend"
cd "$FRONTEND_DIR" || exit 1

echo "📁 Working in: $FRONTEND_DIR"
echo ""

# Step 1: Kill any process on port 3004
echo "1️⃣  Killing any process on port 3004..."
if lsof -ti:3004 > /dev/null 2>&1; then
    lsof -ti:3004 | xargs kill -9
    echo -e "${GREEN}✓${NC} Killed process on port 3004"
else
    echo -e "${GREEN}✓${NC} Port 3004 is free"
fi

# Step 2: Check Node.js version
echo ""
echo "2️⃣  Checking Node.js version..."
NODE_VERSION=$(node --version)
echo "Node.js version: $NODE_VERSION"

# Check if Node version is adequate
NODE_MAJOR_VERSION=$(echo $NODE_VERSION | cut -d. -f1 | sed 's/v//')
if [ $NODE_MAJOR_VERSION -lt 18 ]; then
    echo -e "${RED}✗${NC} Node.js version is too old. Please install Node.js 18 or higher."
    echo "   Run: brew install node@20"
    exit 1
fi

# Step 3: Clean up old files
echo ""
echo "3️⃣  Cleaning up old files..."
rm -rf node_modules package-lock.json .svelte-kit
echo -e "${GREEN}✓${NC} Cleaned up old files"

# Step 4: Clear npm cache
echo ""
echo "4️⃣  Clearing npm cache..."
npm cache clean --force
echo -e "${GREEN}✓${NC} Cleared npm cache"

# Step 5: Install dependencies
echo ""
echo "5️⃣  Installing dependencies (this may take a few minutes)..."
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Dependencies installed successfully"
else
    echo -e "${RED}✗${NC} Failed to install dependencies"
    exit 1
fi

# Step 6: Try to start the frontend
echo ""
echo "6️⃣  Starting frontend server..."
echo ""
echo -e "${YELLOW}Starting on port 3004...${NC}"
echo "If this fails, try running manually with a different port:"
echo "  npm run dev -- --port 3005"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dev server
npm run dev -- --port 3004