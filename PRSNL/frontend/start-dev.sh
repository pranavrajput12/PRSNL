#!/bin/bash

# PRSNL Frontend Stable Start Script

echo "Starting PRSNL Frontend with auto-restart..."

# Function to cleanup on exit
cleanup() {
    echo "Stopping frontend..."
    kill $PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start the frontend with auto-restart
while true; do
    echo "Starting Vite dev server..."
    npm run dev &
    PID=$!
    
    # Wait for the process to exit
    wait $PID
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Frontend stopped normally"
        break
    else
        echo "Frontend crashed with exit code $EXIT_CODE. Restarting in 2 seconds..."
        sleep 2
    fi
done