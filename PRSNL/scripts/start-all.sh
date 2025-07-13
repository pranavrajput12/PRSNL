#!/bin/bash
# Start all PRSNL services

echo "Starting PRSNL services..."

# Start backend in background
echo "Starting backend..."
cd backend
python -m app.main &
BACKEND_PID=$!
cd ..

# Start frontend in background
echo "Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a bit for services to start
sleep 5

# Start tunnel (this will run in foreground)
echo "Starting Cloudflare tunnel..."
./scripts/start-tunnel.sh

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT