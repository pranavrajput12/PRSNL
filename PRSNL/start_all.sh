#!/bin/bash

# PRSNL Start All Services Script
echo "🚀 Starting PRSNL Services..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
if check_port 8000; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✓${NC} Killed process on port 8000"
fi

if check_port 3004; then
    lsof -ti:3004 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✓${NC} Killed process on port 3004"
fi

sleep 2

# Start PostgreSQL if not running
echo ""
echo "🐘 Checking PostgreSQL..."
if ! pgrep -x "postgres" > /dev/null; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@16
    sleep 3
fi
echo -e "${GREEN}✓${NC} PostgreSQL is running"

# Start Backend
echo ""
echo "🔧 Starting Backend..."
cd "/Users/pronav/Personal Knowledge Base/PRSNL/backend"
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 5

# Check if backend started
if check_port 8000; then
    echo -e "${GREEN}✓${NC} Backend running on http://localhost:8000"
else
    echo -e "${RED}✗${NC} Backend failed to start"
    exit 1
fi

# Start Frontend
echo ""
echo "🎨 Starting Frontend..."
cd "/Users/pronav/Personal Knowledge Base/PRSNL/frontend"
npm run dev -- --port 3004 &
FRONTEND_PID=$!
sleep 5

# Check if frontend started
if check_port 3004; then
    echo -e "${GREEN}✓${NC} Frontend running on http://localhost:3004"
else
    echo -e "${RED}✗${NC} Frontend failed to start"
    exit 1
fi

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📍 Access Points:"
echo "   Frontend: http://localhost:3004"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running and handle Ctrl+C
trap 'echo ""; echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

# Wait for processes
wait